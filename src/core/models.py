"""
Core models for the AI model deployment platform.
This module defines the data models for AI models, deployments, and related entities.
"""

import datetime
import enum
import uuid
from typing import Dict, List, Optional, Union


class ModelFramework(str, enum.Enum):
    """Supported AI model frameworks."""
    TENSORFLOW = "tensorflow"
    PYTORCH = "pytorch"
    ONNX = "onnx"
    SKLEARN = "sklearn"
    XGBOOST = "xgboost"
    CUSTOM = "custom"


class OptimizationTechnique(str, enum.Enum):
    """Supported model optimization techniques."""
    QUANTIZATION = "quantization"
    PRUNING = "pruning"
    DISTILLATION = "distillation"
    OPERATOR_FUSION = "operator_fusion"
    NONE = "none"


class HardwareTarget(str, enum.Enum):
    """Supported hardware targets for optimization."""
    CPU = "cpu"
    GPU = "gpu"
    TPU = "tpu"
    EDGE = "edge"


class DeploymentType(str, enum.Enum):
    """Supported deployment types."""
    SERVERLESS = "serverless"
    KUBERNETES = "kubernetes"
    EDGE = "edge"


class DeploymentStatus(str, enum.Enum):
    """Possible deployment statuses."""
    PENDING = "pending"
    DEPLOYING = "deploying"
    ACTIVE = "active"
    SCALING = "scaling"
    HIBERNATED = "hibernated"
    FAILED = "failed"
    TERMINATING = "terminating"
    TERMINATED = "terminated"


class Model:
    """Represents an AI model in the platform."""
    
    def __init__(
        self,
        name: str,
        framework: ModelFramework,
        version: str = "1.0.0",
        description: Optional[str] = None,
        metadata: Optional[Dict] = None,
        storage_path: Optional[str] = None,
    ):
        self.id = str(uuid.uuid4())
        self.name = name
        self.framework = framework
        self.version = version
        self.description = description
        self.metadata = metadata or {}
        self.storage_path = storage_path
        self.created_at = datetime.datetime.utcnow()
        self.updated_at = self.created_at
        self.optimized_models: List["OptimizedModel"] = []
        self.deployments: List["Deployment"] = []
    
    def to_dict(self) -> Dict:
        """Convert model to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "framework": self.framework.value,
            "version": self.version,
            "description": self.description,
            "metadata": self.metadata,
            "storage_path": self.storage_path,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "optimized_models": [om.to_dict() for om in self.optimized_models],
            "deployments": [d.to_dict() for d in self.deployments],
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Model":
        """Create model from dictionary representation."""
        model = cls(
            name=data["name"],
            framework=ModelFramework(data["framework"]),
            version=data["version"],
            description=data.get("description"),
            metadata=data.get("metadata", {}),
            storage_path=data.get("storage_path"),
        )
        model.id = data["id"]
        model.created_at = datetime.datetime.fromisoformat(data["created_at"])
        model.updated_at = datetime.datetime.fromisoformat(data["updated_at"])
        return model


class OptimizedModel:
    """Represents an optimized version of an AI model."""
    
    def __init__(
        self,
        original_model: Model,
        optimization_technique: OptimizationTechnique,
        hardware_target: HardwareTarget,
        metadata: Optional[Dict] = None,
        storage_path: Optional[str] = None,
    ):
        self.id = str(uuid.uuid4())
        self.original_model_id = original_model.id
        self.optimization_technique = optimization_technique
        self.hardware_target = hardware_target
        self.metadata = metadata or {}
        self.storage_path = storage_path
        self.created_at = datetime.datetime.utcnow()
        self.performance_metrics: Dict = {}
        self.deployments: List["Deployment"] = []
    
    def to_dict(self) -> Dict:
        """Convert optimized model to dictionary representation."""
        return {
            "id": self.id,
            "original_model_id": self.original_model_id,
            "optimization_technique": self.optimization_technique.value,
            "hardware_target": self.hardware_target.value,
            "metadata": self.metadata,
            "storage_path": self.storage_path,
            "created_at": self.created_at.isoformat(),
            "performance_metrics": self.performance_metrics,
            "deployments": [d.to_dict() for d in self.deployments],
        }
    
    @classmethod
    def from_dict(cls, data: Dict, original_model: Model) -> "OptimizedModel":
        """Create optimized model from dictionary representation."""
        optimized_model = cls(
            original_model=original_model,
            optimization_technique=OptimizationTechnique(data["optimization_technique"]),
            hardware_target=HardwareTarget(data["hardware_target"]),
            metadata=data.get("metadata", {}),
            storage_path=data.get("storage_path"),
        )
        optimized_model.id = data["id"]
        optimized_model.created_at = datetime.datetime.fromisoformat(data["created_at"])
        optimized_model.performance_metrics = data.get("performance_metrics", {})
        return optimized_model


class ResourceRequirements:
    """Represents resource requirements for a deployment."""
    
    def __init__(
        self,
        cpu: str = "100m",
        memory: str = "128Mi",
        gpu: Optional[str] = None,
        storage: Optional[str] = None,
    ):
        self.cpu = cpu
        self.memory = memory
        self.gpu = gpu
        self.storage = storage
    
    def to_dict(self) -> Dict:
        """Convert resource requirements to dictionary representation."""
        return {
            "cpu": self.cpu,
            "memory": self.memory,
            "gpu": self.gpu,
            "storage": self.storage,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "ResourceRequirements":
        """Create resource requirements from dictionary representation."""
        return cls(
            cpu=data.get("cpu", "100m"),
            memory=data.get("memory", "128Mi"),
            gpu=data.get("gpu"),
            storage=data.get("storage"),
        )


class ScalingPolicy:
    """Represents a scaling policy for a deployment."""
    
    def __init__(
        self,
        min_instances: int = 0,
        max_instances: int = 5,
        target_cpu_utilization: int = 70,
        scale_to_zero_delay: int = 300,  # seconds
    ):
        self.min_instances = min_instances
        self.max_instances = max_instances
        self.target_cpu_utilization = target_cpu_utilization
        self.scale_to_zero_delay = scale_to_zero_delay
    
    def to_dict(self) -> Dict:
        """Convert scaling policy to dictionary representation."""
        return {
            "min_instances": self.min_instances,
            "max_instances": self.max_instances,
            "target_cpu_utilization": self.target_cpu_utilization,
            "scale_to_zero_delay": self.scale_to_zero_delay,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "ScalingPolicy":
        """Create scaling policy from dictionary representation."""
        return cls(
            min_instances=data.get("min_instances", 0),
            max_instances=data.get("max_instances", 5),
            target_cpu_utilization=data.get("target_cpu_utilization", 70),
            scale_to_zero_delay=data.get("scale_to_zero_delay", 300),
        )


class CostOptimizationPolicy:
    """Represents cost optimization policies for a deployment."""
    
    def __init__(
        self,
        use_spot_instances: bool = True,
        hibernation_enabled: bool = True,
        multi_cloud_arbitrage: bool = False,
        storage_tiering: bool = True,
    ):
        self.use_spot_instances = use_spot_instances
        self.hibernation_enabled = hibernation_enabled
        self.multi_cloud_arbitrage = multi_cloud_arbitrage
        self.storage_tiering = storage_tiering
    
    def to_dict(self) -> Dict:
        """Convert cost optimization policy to dictionary representation."""
        return {
            "use_spot_instances": self.use_spot_instances,
            "hibernation_enabled": self.hibernation_enabled,
            "multi_cloud_arbitrage": self.multi_cloud_arbitrage,
            "storage_tiering": self.storage_tiering,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "CostOptimizationPolicy":
        """Create cost optimization policy from dictionary representation."""
        return cls(
            use_spot_instances=data.get("use_spot_instances", True),
            hibernation_enabled=data.get("hibernation_enabled", True),
            multi_cloud_arbitrage=data.get("multi_cloud_arbitrage", False),
            storage_tiering=data.get("storage_tiering", True),
        )


class Deployment:
    """Represents a deployment of a model in the platform."""
    
    def __init__(
        self,
        name: str,
        model: Union[Model, OptimizedModel],
        deployment_type: DeploymentType = DeploymentType.SERVERLESS,
        resource_requirements: Optional[ResourceRequirements] = None,
        scaling_policy: Optional[ScalingPolicy] = None,
        cost_optimization_policy: Optional[CostOptimizationPolicy] = None,
        metadata: Optional[Dict] = None,
    ):
        self.id = str(uuid.uuid4())
        self.name = name
        self.model_id = model.id
        self.model_type = "optimized" if isinstance(model, OptimizedModel) else "original"
        self.deployment_type = deployment_type
        self.resource_requirements = resource_requirements or ResourceRequirements()
        self.scaling_policy = scaling_policy or ScalingPolicy()
        self.cost_optimization_policy = cost_optimization_policy or CostOptimizationPolicy()
        self.metadata = metadata or {}
        self.status = DeploymentStatus.PENDING
        self.endpoint = None
        self.created_at = datetime.datetime.utcnow()
        self.updated_at = self.created_at
        self.last_active_at = self.created_at
    
    def to_dict(self) -> Dict:
        """Convert deployment to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "model_id": self.model_id,
            "model_type": self.model_type,
            "deployment_type": self.deployment_type.value,
            "resource_requirements": self.resource_requirements.to_dict(),
            "scaling_policy": self.scaling_policy.to_dict(),
            "cost_optimization_policy": self.cost_optimization_policy.to_dict(),
            "metadata": self.metadata,
            "status": self.status.value,
            "endpoint": self.endpoint,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_active_at": self.last_active_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict, model: Union[Model, OptimizedModel]) -> "Deployment":
        """Create deployment from dictionary representation."""
        deployment = cls(
            name=data["name"],
            model=model,
            deployment_type=DeploymentType(data["deployment_type"]),
            resource_requirements=ResourceRequirements.from_dict(data["resource_requirements"]),
            scaling_policy=ScalingPolicy.from_dict(data["scaling_policy"]),
            cost_optimization_policy=CostOptimizationPolicy.from_dict(data["cost_optimization_policy"]),
            metadata=data.get("metadata", {}),
        )
        deployment.id = data["id"]
        deployment.status = DeploymentStatus(data["status"])
        deployment.endpoint = data.get("endpoint")
        deployment.created_at = datetime.datetime.fromisoformat(data["created_at"])
        deployment.updated_at = datetime.datetime.fromisoformat(data["updated_at"])
        deployment.last_active_at = datetime.datetime.fromisoformat(data["last_active_at"])
        return deployment
