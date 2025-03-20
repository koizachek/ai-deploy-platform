"""
Deployment service for managing model deployments.
This module provides functionality for deploying and managing AI models.
"""

import datetime
import logging
import os
from typing import Dict, List, Optional, Union

from core.models import (
    CostOptimizationPolicy,
    Deployment,
    DeploymentStatus,
    DeploymentType,
    Model,
    OptimizedModel,
    ResourceRequirements,
    ScalingPolicy,
)
from core.repository import ModelRepository
from infrastructure.kubernetes import KubernetesDeployer
from infrastructure.serverless import ServerlessDeployer

logger = logging.getLogger(__name__)


class DeploymentService:
    """Service for deploying and managing AI models."""
    
    def __init__(
        self,
        model_repository: ModelRepository,
        kubernetes_deployer: KubernetesDeployer,
        serverless_deployer: ServerlessDeployer,
    ):
        """Initialize the deployment service.
        
        Args:
            model_repository: Repository for model storage and retrieval
            kubernetes_deployer: Deployer for Kubernetes deployments
            serverless_deployer: Deployer for serverless deployments
        """
        self.model_repository = model_repository
        self.kubernetes_deployer = kubernetes_deployer
        self.serverless_deployer = serverless_deployer
        self.deployments_path = os.path.join(model_repository.storage_base_path, "deployments")
        os.makedirs(self.deployments_path, exist_ok=True)
    
    def deploy_model(
        self,
        name: str,
        model: Union[Model, OptimizedModel],
        deployment_type: DeploymentType = DeploymentType.SERVERLESS,
        resource_requirements: Optional[ResourceRequirements] = None,
        scaling_policy: Optional[ScalingPolicy] = None,
        cost_optimization_policy: Optional[CostOptimizationPolicy] = None,
        metadata: Optional[Dict] = None,
    ) -> Deployment:
        """Deploy a model.
        
        Args:
            name: Name of the deployment
            model: Model to deploy
            deployment_type: Type of deployment
            resource_requirements: Resource requirements for the deployment
            scaling_policy: Scaling policy for the deployment
            cost_optimization_policy: Cost optimization policy for the deployment
            metadata: Additional metadata for the deployment
            
        Returns:
            Created deployment
        """
        # Create deployment object
        deployment = Deployment(
            name=name,
            model=model,
            deployment_type=deployment_type,
            resource_requirements=resource_requirements,
            scaling_policy=scaling_policy,
            cost_optimization_policy=cost_optimization_policy,
            metadata=metadata or {},
        )
        
        # Update deployment status
        deployment.status = DeploymentStatus.DEPLOYING
        self._save_deployment(deployment)
        
        try:
            # Deploy model based on deployment type
            if deployment_type == DeploymentType.KUBERNETES:
                endpoint = self.kubernetes_deployer.deploy(
                    deployment=deployment,
                    model=model,
                )
            elif deployment_type == DeploymentType.SERVERLESS:
                endpoint = self.serverless_deployer.deploy(
                    deployment=deployment,
                    model=model,
                )
            else:
                raise ValueError(f"Unsupported deployment type: {deployment_type}")
            
            # Update deployment with endpoint and status
            deployment.endpoint = endpoint
            deployment.status = DeploymentStatus.ACTIVE
            deployment.updated_at = datetime.datetime.utcnow()
            self._save_deployment(deployment)
            
            logger.info(f"Deployed model {model.id} as {deployment.id} at {endpoint}")
            
            return deployment
        
        except Exception as e:
            # Update deployment status to failed
            deployment.status = DeploymentStatus.FAILED
            deployment.metadata["error"] = str(e)
            deployment.updated_at = datetime.datetime.utcnow()
            self._save_deployment(deployment)
            
            logger.error(f"Failed to deploy model {model.id}: {e}")
            raise
    
    def get_deployment(self, deployment_id: str) -> Optional[Deployment]:
        """Get a deployment by ID.
        
        Args:
            deployment_id: ID of the deployment to retrieve
            
        Returns:
            Deployment if found, None otherwise
        """
        deployment_path = os.path.join(self.deployments_path, f"{deployment_id}.json")
        if not os.path.exists(deployment_path):
            return None
        
        import json
        with open(deployment_path, "r") as f:
            deployment_data = json.load(f)
        
        # Get the model or optimized model
        model_id = deployment_data["model_id"]
        model_type = deployment_data["model_type"]
        
        if model_type == "original":
            model = self.model_repository.get_model(model_id)
            if not model:
                logger.warning(f"Model {model_id} not found for deployment {deployment_id}")
                return None
        else:  # model_type == "optimized"
            # Need to get the original model first
            with open(deployment_path, "r") as f:
                deployment_data = json.load(f)
            
            optimized_model_data = None
            optimized_model_path = os.path.join(
                self.model_repository.metadata_path, f"optimized_model_{model_id}.json"
            )
            if os.path.exists(optimized_model_path):
                with open(optimized_model_path, "r") as f:
                    optimized_model_data = json.load(f)
            
            if not optimized_model_data:
                logger.warning(f"Optimized model {model_id} not found for deployment {deployment_id}")
                return None
            
            original_model = self.model_repository.get_model(optimized_model_data["original_model_id"])
            if not original_model:
                logger.warning(
                    f"Original model {optimized_model_data['original_model_id']} not found "
                    f"for optimized model {model_id}"
                )
                return None
            
            model = self.model_repository.get_optimized_model(model_id, original_model)
            if not model:
                logger.warning(f"Optimized model {model_id} not found for deployment {deployment_id}")
                return None
        
        return Deployment.from_dict(deployment_data, model)
    
    def list_deployments(self) -> List[Deployment]:
        """List all deployments.
        
        Returns:
            List of deployments
        """
        deployments = []
        for filename in os.listdir(self.deployments_path):
            if filename.endswith(".json"):
                deployment_id = filename[:-5]  # Remove ".json" suffix
                deployment = self.get_deployment(deployment_id)
                if deployment:
                    deployments.append(deployment)
        return deployments
    
    def update_deployment(
        self,
        deployment_id: str,
        resource_requirements: Optional[ResourceRequirements] = None,
        scaling_policy: Optional[ScalingPolicy] = None,
        cost_optimization_policy: Optional[CostOptimizationPolicy] = None,
        metadata: Optional[Dict] = None,
    ) -> Optional[Deployment]:
        """Update a deployment.
        
        Args:
            deployment_id: ID of the deployment to update
            resource_requirements: New resource requirements
            scaling_policy: New scaling policy
            cost_optimization_policy: New cost optimization policy
            metadata: New metadata
            
        Returns:
            Updated deployment if found, None otherwise
        """
        deployment = self.get_deployment(deployment_id)
        if not deployment:
            return None
        
        # Update deployment properties
        if resource_requirements:
            deployment.resource_requirements = resource_requirements
        
        if scaling_policy:
            deployment.scaling_policy = scaling_policy
        
        if cost_optimization_policy:
            deployment.cost_optimization_policy = cost_optimization_policy
        
        if metadata:
            deployment.metadata.update(metadata)
        
        # Update deployment status and timestamp
        deployment.status = DeploymentStatus.SCALING
        deployment.updated_at = datetime.datetime.utcnow()
        self._save_deployment(deployment)
        
        try:
            # Update deployment based on deployment type
            if deployment.deployment_type == DeploymentType.KUBERNETES:
                self.kubernetes_deployer.update(deployment)
            elif deployment.deployment_type == DeploymentType.SERVERLESS:
                self.serverless_deployer.update(deployment)
            else:
                raise ValueError(f"Unsupported deployment type: {deployment.deployment_type}")
            
            # Update deployment status
            deployment.status = DeploymentStatus.ACTIVE
            deployment.updated_at = datetime.datetime.utcnow()
            self._save_deployment(deployment)
            
            logger.info(f"Updated deployment {deployment_id}")
            
            return deployment
        
        except Exception as e:
            # Update deployment status to failed
            deployment.status = DeploymentStatus.FAILED
            deployment.metadata["error"] = str(e)
            deployment.updated_at = datetime.datetime.utcnow()
            self._save_deployment(deployment)
            
            logger.error(f"Failed to update deployment {deployment_id}: {e}")
            raise
    
    def delete_deployment(self, deployment_id: str) -> bool:
        """Delete a deployment.
        
        Args:
            deployment_id: ID of the deployment to delete
            
        Returns:
            True if deployment was deleted, False otherwise
        """
        deployment = self.get_deployment(deployment_id)
        if not deployment:
            return False
        
        # Update deployment status
        deployment.status = DeploymentStatus.TERMINATING
        self._save_deployment(deployment)
        
        try:
            # Delete deployment based on deployment type
            if deployment.deployment_type == DeploymentType.KUBERNETES:
                self.kubernetes_deployer.delete(deployment)
            elif deployment.deployment_type == DeploymentType.SERVERLESS:
                self.serverless_deployer.delete(deployment)
            else:
                raise ValueError(f"Unsupported deployment type: {deployment.deployment_type}")
            
            # Delete deployment metadata
            deployment_path = os.path.join(self.deployments_path, f"{deployment_id}.json")
            if os.path.exists(deployment_path):
                os.remove(deployment_path)
            
            logger.info(f"Deleted deployment {deployment_id}")
            
            return True
        
        except Exception as e:
            # Update deployment status to failed
            deployment.status = DeploymentStatus.FAILED
            deployment.metadata["error"] = str(e)
            deployment.updated_at = datetime.datetime.utcnow()
            self._save_deployment(deployment)
            
            logger.error(f"Failed to delete deployment {deployment_id}: {e}")
            raise
    
    def hibernate_deployment(self, deployment_id: str) -> Optional[Deployment]:
        """Hibernate a deployment to reduce costs.
        
        Args:
            deployment_id: ID of the deployment to hibernate
            
        Returns:
            Hibernated deployment if found, None otherwise
        """
        deployment = self.get_deployment(deployment_id)
        if not deployment:
            return None
        
        # Check if hibernation is enabled
        if not deployment.cost_optimization_policy.hibernation_enabled:
            logger.warning(f"Hibernation not enabled for deployment {deployment_id}")
            return deployment
        
        # Update deployment status
        deployment.status = DeploymentStatus.HIBERNATED
        deployment.updated_at = datetime.datetime.utcnow()
        self._save_deployment(deployment)
        
        try:
            # Hibernate deployment based on deployment type
            if deployment.deployment_type == DeploymentType.KUBERNETES:
                self.kubernetes_deployer.hibernate(deployment)
            elif deployment.deployment_type == DeploymentType.SERVERLESS:
                self.serverless_deployer.hibernate(deployment)
            else:
                raise ValueError(f"Unsupported deployment type: {deployment.deployment_type}")
            
            logger.info(f"Hibernated deployment {deployment_id}")
            
            return deployment
        
        except Exception as e:
            # Update deployment status to failed
            deployment.status = DeploymentStatus.FAILED
            deployment.metadata["error"] = str(e)
            deployment.updated_at = datetime.datetime.utcnow()
            self._save_deployment(deployment)
            
            logger.error(f"Failed to hibernate deployment {deployment_id}: {e}")
            raise
    
    def activate_deployment(self, deployment_id: str) -> Optional[Deployment]:
        """Activate a hibernated deployment.
        
        Args:
            deployment_id: ID of the deployment to activate
            
        Returns:
            Activated deployment if found, None otherwise
        """
        deployment = self.get_deployment(deployment_id)
        if not deployment:
            return None
        
        # Check if deployment is hibernated
        if deployment.status != DeploymentStatus.HIBERNATED:
            logger.warning(f"Deployment {deployment_id} is not hibernated")
            return deployment
        
        # Update deployment status
        deployment.status = DeploymentStatus.DEPLOYING
        deployment.updated_at = datetime.datetime.utcnow()
        self._save_deployment(deployment)
        
        try:
            # Activate deployment based on deployment type
            if deployment.deployment_type == DeploymentType.KUBERNETES:
                self.kubernetes_deployer.activate(deployment)
            elif deployment.deployment_type == DeploymentType.SERVERLESS:
                self.serverless_deployer.activate(deployment)
            else:
                raise ValueError(f"Unsupported deployment type: {deployment.deployment_type}")
            
            # Update deployment status
            deployment.status = DeploymentStatus.ACTIVE
            deployment.updated_at = datetime.datetime.utcnow()
            deployment.last_active_at = datetime.datetime.utcnow()
            self._save_deployment(deployment)
            
            logger.info(f"Activated deployment {deployment_id}")
            
            return deployment
        
        except Exception as e:
            # Update deployment status to failed
            deployment.status = DeploymentStatus.FAILED
            deployment.metadata["error"] = str(e)
            deployment.updated_at = datetime.datetime.utcnow()
            self._save_deployment(deployment)
            
            logger.error(f"Failed to activate deployment {deployment_id}: {e}")
            raise
    
    def _save_deployment(self, deployment: Deployment) -> None:
        """Save deployment metadata to disk.
        
        Args:
            deployment: Deployment to<response clipped><NOTE>To save on context only part of this file has been shown to you. You should retry this tool after you have searched inside the file with `grep -n` in order to find the line numbers of what you are looking for.</NOTE>