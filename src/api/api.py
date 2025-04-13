"""
API service for the AI model deployment platform.
This module provides a RESTful API for interacting with the platform.
"""

import datetime
import json
import logging
import os
import uuid
from typing import Dict, List, Optional, Union

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from core.deployment import DeploymentService
from core.models import (
    Deployment,
    DeploymentStatus,
    DeploymentType,
    Model,
    OptimizedModel,
    OptimizationMethod,
    OptimizationStatus,
    ResourceRequirements,
    ScalingPolicy,
    CostOptimizationPolicy,
)
from core.repository import ModelRepository
from monitoring.analytics import AnalyticsService
from monitoring.monitoring import MonitoringService
from optimization.cost_optimizer import CostOptimizer
from optimization.multi_cloud import MultiCloudArbitrage
from optimization.optimization import ModelOptimizer
from optimization.storage_tiering import StorageTiering

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AI Deploy Platform API",
    description="API for the AI model deployment platform",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
model_repository = ModelRepository()
deployment_service = DeploymentService(model_repository)
model_optimizer = ModelOptimizer(model_repository)
cost_optimizer = CostOptimizer(deployment_service)
multi_cloud_arbitrage = MultiCloudArbitrage(deployment_service)
storage_tiering = StorageTiering(model_repository)
monitoring_service = MonitoringService(deployment_service, model_repository)
analytics_service = AnalyticsService(deployment_service, monitoring_service)


# Define API models
class ModelResponse(BaseModel):
    id: str
    name: str
    framework: str
    version: str
    storage_path: str
    created_at: str
    updated_at: str
    metadata: Dict = Field(default_factory=dict)


class OptimizedModelResponse(BaseModel):
    id: str
    original_model_id: str
    optimization_method: str
    status: str
    storage_path: Optional[str] = None
    size_reduction_percentage: float = 0.0
    latency_reduction_percentage: float = 0.0
    accuracy_change_percentage: float = 0.0
    created_at: str
    updated_at: str
    metadata: Dict = Field(default_factory=dict)


class ModelUploadResponse(BaseModel):
    model_id: str
    name: str
    framework: str
    version: str
    storage_path: str
    created_at: str


class OptimizeModelRequest(BaseModel):
    method: str
    target_size: Optional[str] = None
    target_latency: Optional[float] = None
    metadata: Dict = Field(default_factory=dict)


class OptimizeModelResponse(BaseModel):
    id: str
    original_model_id: str
    optimization_method: str
    status: str
    created_at: str


class ResourceRequirementsModel(BaseModel):
    cpu: str
    memory: str
    gpu: Optional[str] = None
    timeout: int = 30


class ScalingPolicyModel(BaseModel):
    min_instances: int = 1
    max_instances: int = 10
    target_cpu_utilization: int = 70


class CostOptimizationPolicyModel(BaseModel):
    use_spot_instances: bool = False
    hibernation_enabled: bool = False
    hibernation_idle_timeout: int = 1800
    multi_cloud_enabled: bool = False


class CreateDeploymentRequest(BaseModel):
    name: str
    model_id: str
    model_type: str = "original"
    deployment_type: str = "serverless"
    resource_requirements: ResourceRequirementsModel
    scaling_policy: ScalingPolicyModel
    cost_optimization_policy: CostOptimizationPolicyModel
    metadata: Dict = Field(default_factory=dict)


class UpdateDeploymentRequest(BaseModel):
    resource_requirements: Optional[ResourceRequirementsModel] = None
    scaling_policy: Optional[ScalingPolicyModel] = None
    cost_optimization_policy: Optional[CostOptimizationPolicyModel] = None
    metadata: Optional[Dict] = None


class DeploymentResponse(BaseModel):
    id: str
    name: str
    model_id: str
    model_type: str
    deployment_type: str
    status: str
    endpoint: Optional[str] = None
    resource_requirements: Dict
    scaling_policy: Dict
    cost_optimization_policy: Dict
    created_at: str
    updated_at: str
    metadata: Dict = Field(default_factory=dict)


# API routes
@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to the AI Deploy Platform API"}


# Model routes
@app.get("/models", response_model=List[ModelResponse])
async def list_models():
    """List all models."""
    models = model_repository.list_models()
    return [model.dict() for model in models]


@app.get("/models/{model_id}", response_model=ModelResponse)
async def get_model(model_id: str):
    """Get a model."""
    model = model_repository.get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model.dict()


@app.post("/models", response_model=ModelUploadResponse)
async def upload_model(
    name: str = Form(...),
    framework: str = Form(...),
    version: str = Form(...),
    file: UploadFile = File(...),
    metadata: str = Form("{}"),
):
    """Upload a model."""
    try:
        # Parse metadata
        metadata_dict = json.loads(metadata)
        
        # Save model file
        model_id = str(uuid.uuid4())
        storage_dir = os.path.join("/tmp/ai-deploy-platform/models", model_id)
        os.makedirs(storage_dir, exist_ok=True)
        
        storage_path = os.path.join(storage_dir, file.filename)
        
        with open(storage_path, "wb") as f:
            f.write(await file.read())
        
        # Create model
        model = Model(
            id=model_id,
            name=name,
            framework=framework,
            version=version,
            storage_path=storage_path,
            created_at=datetime.datetime.utcnow(),
            updated_at=datetime.datetime.utcnow(),
            metadata=metadata_dict,
        )
        
        # Save model
        model_repository._save_model_metadata(model)
        
        return {
            "model_id": model.id,
            "name": model.name,
            "framework": model.framework,
            "version": model.version,
            "storage_path": model.storage_path,
            "created_at": model.created_at.isoformat(),
        }
    
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON metadata")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/models/{model_id}")
async def delete_model(model_id: str):
    """Delete a model."""
    model = model_repository.get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    # Check if model is used by any deployments
    deployments = deployment_service.list_deployments()
    for deployment in deployments:
        if deployment.model_id == model_id:
            raise HTTPException(
                status_code=400,
                detail=f"Model is used by deployment {deployment.id}",
            )
    
    # Delete model
    try:
        # Delete model file
        if os.path.exists(model.storage_path):
            os.remove(model.storage_path)
        
        # Delete model directory
        storage_dir = os.path.dirname(model.storage_path)
        if os.path.exists(storage_dir):
            os.rmdir(storage_dir)
        
        # Delete model metadata
        model_repository._delete_model_metadata(model)
        
        return {"message": f"Model {model_id} deleted successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/models/{model_id}/optimize", response_model=OptimizeModelResponse)
async def optimize_model(model_id: str, request: OptimizeModelRequest):
    """Optimize a model."""
    model = model_repository.get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    try:
        # Validate optimization method
        try:
            method = OptimizationMethod(request.method)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid optimization method: {request.method}",
            )
        
        # Create optimized model
        optimized_model_id = str(uuid.uuid4())
        optimized_model = OptimizedModel(
            id=optimized_model_id,
            original_model_id=model_id,
            optimization_method=method,
            status=OptimizationStatus.OPTIMIZING,
            created_at=datetime.datetime.utcnow(),
            updated_at=datetime.datetime.utcnow(),
            metadata={
                "target_size": request.target_size,
                "target_latency": request.target_latency,
                **request.metadata,
            },
        )
        
        # Save optimized model metadata
        model_repository._save_optimized_model_metadata(optimized_model)
        
        # Start optimization in background
        # In a real implementation, this would be done asynchronously
        # For this implementation, we'll simulate optimization
        
        # Simulate optimization
        import threading
        
        def optimize():
            try:
                # Simulate optimization delay
                import time
                import random
                
                time.sleep(5)
                
                # Create optimized model file
                storage_dir = os.path.join("/tmp/ai-deploy-platform/optimized_models", optimized_model_id)
                os.makedirs(storage_dir, exist_ok=True)
                
                storage_path = os.path.join(storage_dir, f"optimized_{os.path.basename(model.storage_path)}")
                
                # Copy original model file
                import shutil
                
                shutil.copy2(model.storage_path, storage_path)
                
                # Update optimized model
                optimized_model.status = OptimizationStatus.COMPLETED
                optimized_model.storage_path = storage_path
                optimized_model.size_reduction_percentage = random.uniform(20, 80)
                optimized_model.latency_reduction_percentage = random.uniform(10, 50)
                optimized_model.accuracy_change_percentage = random.uniform(-5, 0)
                optimized_model.updated_at = datetime.datetime.utcnow()
                
                # Save optimized model metadata
                model_repository._save_optimized_model_metadata(optimized_model)
            
            except Exception as e:
                # Update optimized model with error
                optimized_model.status = OptimizationStatus.FAILED
                optimized_model.updated_at = datetime.datetime.utcnow()
                optimized_model.metadata["error"] = str(e)
                
                # Save optimized model metadata
                model_repository._save_optimized_model_metadata(optimized_model)
        
        # Start optimization thread
        threading.Thread(target=optimize).start()
        
        return {
            "id": optimized_model.id,
            "original_model_id": optimized_model.original_model_id,
            "optimization_method": optimized_model.optimization_method.value,
            "status": optimized_model.status.value,
            "created_at": optimized_model.created_at.isoformat(),
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/models/{model_id}/optimized", response_model=List[OptimizedModelResponse])
async def list_optimized_models(model_id: str):
    """List optimized versions of a model."""
    model = model_repository.get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    optimized_models = model_repository.list_optimized_models(model)
    
    return [
        {
            "id": model.id,
            "original_model_id": model.original_model_id,
            "optimization_method": model.optimization_method.value,
            "status": model.status.value,
            "storage_path": model.storage_path,
            "size_reduction_percentage": model.size_reduction_percentage,
            "latency_reduction_percentage": model.latency_reduction_percentage,
            "accuracy_change_percentage": model.accuracy_change_percentage,
            "created_at": model.created_at.isoformat(),
            "updated_at": model.updated_at.isoformat(),
            "metadata": model.metadata,
        }
        for model in optimized_models
    ]


# Deployment routes
@app.get("/deployments", response_model=List[DeploymentResponse])
async def list_deployments():
    """List all deployments."""
    deployments = deployment_service.list_deployments()
    
    return [
        {
            "id": deployment.id,
            "name": deployment.name,
            "model_id": deployment.model_id,
            "model_type": deployment.model_type,
            "deployment_type": deployment.deployment_type.value,
            "status": deployment.status.value,
            "endpoint": deployment.endpoint,
            "resource_requirements": deployment.resource_requirements.dict(),
            "scaling_policy": deployment.scaling_policy.dict(),
            "cost_optimization_policy": deployment.cost_optimization_policy.dict(),
            "created_at": deployment.created_at.isoformat(),
            "updated_at": deployment.updated_at.isoformat(),
            "metadata": deployment.metadata,
        }
        for deployment in deployments
    ]


@app.get("/deployments/{deployment_id}", response_model=DeploymentResponse)
async def get_deployment(deployment_id: str):
    """Get a deployment."""
    deployment = deployment_service.get_deployment(deployment_id)
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    return {
        "id": deployment.id,
        "name": deployment.name,
        "model_id": deployment.model_id,
        "model_type": deployment.model_type,
        "deployment_type": deployment.deployment_type.value,
        "status": deployment.status.value,
        "endpoint": deployment.endpoint,
        "resource_requirements": deployment.resource_requirements.dict(),
        "scaling_policy": deployment.scaling_policy.dict(),
        "cost_optimization_policy": deployment.cost_optimization_policy.dict(),
        "created_at": deployment.created_at.isoformat(),
        "updated_at": deployment.updated_at.isoformat(),
        "metadata": deployment.metadata,
    }


@app.post("/deployments", response_model=DeploymentResponse)
async def create_deployment(request: CreateDeploymentRequest):
    """Create a deployment."""
    try:
        # Validate model
        model = model_repository.get_model(request.model_id)
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")
        
        # Validate model type
        if request.model_type == "optimized":
            # Check if optimized models exist
            optimized_models = model_repository.list_optimized_models(model)
            if not optimized_models:
                raise HTTPException(
                    status_code=400,
                    detail="No optimized versions of the model found",
                )
        
        # Validate deployment type
        try:
            deployment_type = DeploymentType(request.deployment_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid deployment type: {request.deployment_type}",
            )
        
        # Create resource requirements
        resource_requirements = ResourceRequirements(
            cpu=request.resource_requirements.cpu,
            memory=request.resource_requirements.memory,
            gpu=request.resource_requirements.gpu,
            timeout=request.resource_requirements.timeout,
        )
        
        # Create scaling policy
        scaling_policy = ScalingPolicy(
            min_instances=request.scaling_policy.min_instances,
            max_instances=request.scaling_policy.max_instances,
            target_cpu_utilization=request.scaling_policy.target_cpu_utilization,
        )
        
        # Create cost optimization policy
        cost_optimization_policy = CostOptimizationPolicy(
            use_spot_instances=request.cost_optimization_policy.use_spot_instances,
            hibernation_enabled=request.cost_optimization_policy.hibernation_enabled,
            hibernation_idle_timeout=request.cost_optimization_policy.hibernation_idle_timeout,
            multi_cloud_enabled=request.cost_optimization_policy.multi_cloud_enabled,
        )
        
        # Create deployment
        deployment_id = str(uuid.uuid4())
        deployment = Deployment(
            id=deployment_id,
            name=request.name,
            model_id=request.model_id,
            model_type=request.model_type,
            deployment_type=deployment_type,
            status=DeploymentStatus.CREATING,
            resource_requirements=resource_requirements,
            scaling_policy=scaling_policy,
            cost_optimization_policy=cost_optimization_policy,
            created_at=datetime.datetime.utcnow(),
            updated_at=datetime.datetime.utcnow(),
            metadata=request.metadata,
        )
        
        # Save deployment
        deployment_service.create_deployment(deployment)
        
        # Start deployment in background
        # In a real implementation, this would be done asynchronously
        # For this implementation, we'll simulate deployment
        
        # Simulate deployment
        import threading
        
        def deploy():
            try:
                # Simulate deployment delay
                import time
                
                time.sleep(5)
                
                # Update deployment
                deployment.status = DeploymentStatus.RUNNING
                deployment.endpoint = f"https://api.ai-deploy-platform.example.com/deployments/{deployment_id}/predict"
                deployment.updated_at = datetime.datetime.utcnow()
                
                # Save deployment
                deployment_service.update_deployment(deployment)
            
            except Exception as e:
                # Update deployment with error
                deployment.status = DeploymentStatus.FAILED
                deployment.updated_at = datetime.datetime.utcnow()
                deployment.metadata["error"] = str(e)
                
                # Save deployment
                deployment_service.update_deployment(deployment)
        
        # Start deployment thread
        threading.Thread(target=deploy).start()
        
        return {
            "id": deployment.id,
            "name": deployment.name,
            "model_id": deployment.model_id,
            "model_type": deployment.model_type,
            "deployment_type": deployment.deployment_type.value,
            "status": deployment.status.value,
            "endpoint": deployment.endpoint,
            "resource_requirements": deployment.resource_requirements.dict(),
            "scaling_policy": deployment.scaling_policy.dict(),
            "cost_optimization_policy": deployment.cost_optimization_policy.dict(),
            "created_at": deployment.created_at.isoformat(),
            "updated_at": deployment.updated_at.isoformat(),
            "metadata": deployment.metadata,
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/deployments/{deployment_id}", response_model=DeploymentResponse)
async def update_deployment(deployment_id: str, request: UpdateDeploymentRequest):
    """Update a deployment."""
    try:
        # Get deployment
        deployment = deployment_service.get_deployment(deployment_id)
        if not deployment:
            raise HTTPException(status_code=404, detail="Deployment not found")
        
        # Update deployment
        if request.resource_requirements:
            deployment.resource_requirements = ResourceRequirements(
                cpu=request.resource_requirements.cpu,
                memory=request.resource_requirements.memory,
                gpu=request.resource_requirements.gpu,
                timeout=request.resource_requirements.timeout,
            )
        
        if request.scaling_policy:
            deployment.scaling_policy = ScalingPolicy(
                min_instances=request.scaling_policy.min_instances,
                max_instances=request.scaling_policy.max_instances,
                target_cpu_utilization=request.scaling_policy.target_cpu_utilization,
            )
        
        if request.cost_optimization_policy:
            deployment.cost_optimization_policy = CostOptimizationPolicy(
                use_spot_instances=request.cost_optimization_policy.use_spot_instances,
                hibernation_enabled=request.cost_optimization_policy.hibernation_enabled,
                hibernation_idle_timeout=request.cost_optimization_policy.hibernation_idle_timeout,
                multi_cloud_enabled=request.cost_optimization_policy.multi_cloud_enabled,
            )
        
        if request.metadata:
            deployment.metadata.update(request.metadata)
        
        deployment.updated_at = datetime.datetime.utcnow()
        
        # Save deployment
        deployment_service.update_deployment(deployment)
        
        return {
            "id": deployment.id,
            "name": deployment.name,
            "model_id": deployment.model_id,
            "model_type": deployment.model_type,
            "deployment_type": deployment.deployment_type.value,
            "status": deployment.status.value,
            "endpoint": deployment.endpoint,
            "resource_requirements": deployment.resource_requirements.dict(),
            "scaling_policy": deployment.scaling_policy.dict(),
            "cost_optimization_policy": deployment.cost_optimization_policy.dict(),
            "created_at": deployment.created_at.isoformat(),
            "updated_at": deployment.updated_at.isoformat(),
            "metadata": deployment.metadata,
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/deployments/{deployment_id}")
async def delete_deployment(deployment_id: str):
    """Delete a deployment."""
    try:
        # Get deployment
        deployment = deployment_service.get_deployment(deployment_id)
        if not deployment:
            raise HTTPException(status_code=404, detail="Deployment not found")
        
        # Delete deployment
        deployment_service.delete_deployment(deployment)
        
        return {"message": f"Deployment {deployment_id} deleted successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/deployments/{deployment_id}/stop")
async def stop_deployment(deployment_id: str):
    """Stop a deployment."""
    try:
        # Get deployment
        deployment = deployment_service.get_deployment(deployment_id)
        if not deployment:
            raise HTTPException(status_code=404, detail="Deployment not found")
        
        # Check if deployment is already stopped
        if deployment.status == DeploymentStatus.STOPPED:
            return {"message": f"Deployment {deployment_id} is already stopped"}
        
        # Update deployment
        deployment.status = DeploymentStatus.STOPPED
        deployment.updated_at = datetime.datetime.utcnow()
        
        # Save deployment
        deployment_service.update_deployment(deployment)
        
        return {"message": f"Deployment {deployment_id} stopped successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/deployments/{deployment_id}/start")
async def start_deployment(deployment_id: str):
    """Start a deployment."""
    try:
        # Get deployment
        deployment = deployment_service.get_deployment(deployment_id)
        if not deployment:
            raise HTTPException(status_code=404, detail="Deployment not found")
        
        # Check if deployment is already running
        if deployment.status == DeploymentStatus.RUNNING:
            return {"message": f"Deployment {deployment_id} is already running"}
        
        # Update deployment
        deployment.status = DeploymentStatus.STARTING
        deployment.updated_at = datetime.datetime.utcnow()
        
        # Save deployment
        deployment_service.update_deployment(deployment)
        
        # Start deployment in background
        # In a real implementation, this would be done asynchronously
        # For this implementation, we'll simulate deployment
        
        # Simulate deployment
        import threading
        
        def start():
            try:
                # Simulate deployment delay
                import time
                
                time.sleep(5)
                
                # Update deployment
                deployment.status = DeploymentStatus.RUNNING
                deployment.updated_at = datetime.datetime.utcnow()
                
                # Save deployment
                deployment_service.update_deployment(deployment)
            
            except Exception as e:
                # Update deployment with error
                deployment.status = DeploymentStatus.FAILED
                deployment.updated_at = datetime.datetime.utcnow()
                deployment.metadata["error"] = str(e)
                
                # Save deployment
                deployment_service.update_deployment(deployment)
        
        # Start deployment thread
        threading.Thread(target=start).start()
        
        return {"message": f"Deployment {deployment_id} starting..."}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Metrics and analytics routes
@app.get("/deployments/{deployment_id}/metrics")
async def get_deployment_metrics(
    deployment_id: str,
    start_time: Optional[str] = Query(None),
    end_time: Optional[str] = Query(None),
    metrics: List[str] = Query(["cpu", "memory", "requests"]),
):
    """Get deployment metrics."""
    try:
        # Get deployment
        deployment = deployment_service.get_deployment(deployment_id)
        if not deployment:
            raise HTTPException(status_code=404, detail="Deployment not found")
        
        # Parse time range
        try:
            start = datetime.datetime.fromisoformat(start_time) if start_time else datetime.datetime.utcnow() - datetime.timedelta(hours=1)
            end = datetime.datetime.fromisoformat(end_time) if end_time else datetime.datetime.utcnow()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid time format")
        
        # Get metrics
        try:
            metrics_data = monitoring_service.get_metrics(deployment, metrics, start, end)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")
        
        return metrics_data
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/deployments/{deployment_id}/analytics")
async def get_deployment_analytics(
    deployment_id: str,
    start_time: Optional[str] = Query(None),
    end_time: Optional[str] = Query(None),
    metrics: List[str] = Query(["requests", "latency", "error_rate", "cost"]),
):
    """Get deployment analytics."""
    try:
        # Get deployment
        deployment = deployment_service.get_deployment(deployment_id)
        if not deployment:
            raise HTTPException(status_code=404, detail="Deployment not found")
        
        # Parse time range
        try:
            start = datetime.datetime.fromisoformat(start_time) if start_time else datetime.datetime.utcnow() - datetime.timedelta(days=7)
            end = datetime.datetime.fromisoformat(end_time) if end_time else datetime.datetime.utcnow()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid time format")
        
        # Get analytics
        try:
            analytics_data = analytics_service.get_analytics(deployment, metrics, start, end)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")
        
        return analytics_data
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Start the app for development
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
