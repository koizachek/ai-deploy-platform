"""
Kubernetes deployer for deploying models to Kubernetes clusters.
This module provides functionality for deploying models to Kubernetes.
"""

import logging
import os
import tempfile
import time
import yaml
from typing import Dict, Optional

from core.models import Deployment, Model, OptimizedModel
from kubernetes import client, config

logger = logging.getLogger(__name__)


class KubernetesDeployer:
    """Deployer for Kubernetes deployments."""
    
    def __init__(
        self,
        namespace: str = "ai-deploy-platform",
        registry_url: str = "localhost:5000",
        config_path: Optional[str] = None,
    ):
        """Initialize the Kubernetes deployer.
        
        Args:
            namespace: Kubernetes namespace to deploy to
            registry_url: Container registry URL
            config_path: Path to kubeconfig file
        """
        self.namespace = namespace
        self.registry_url = registry_url
        
        # Load Kubernetes configuration
        if config_path and os.path.exists(config_path):
            config.load_kube_config(config_file=config_path)
        else:
            try:
                config.load_kube_config()
            except:
                config.load_incluster_config()
        
        # Initialize Kubernetes clients
        self.core_api = client.CoreV1Api()
        self.apps_api = client.AppsV1Api()
        self.autoscaling_api = client.AutoscalingV1Api()
        self.networking_api = client.NetworkingV1Api()
        
        # Create namespace if it doesn't exist
        self._create_namespace()
    
    def deploy(self, deployment: Deployment, model: Model) -> str:
        """Deploy a model to Kubernetes.
        
        Args:
            deployment: Deployment configuration
            model: Model to deploy
            
        Returns:
            Endpoint URL for the deployed model
        """
        logger.info(f"Deploying model {model.id} to Kubernetes")
        
        # Generate container image name
        image_name = self._build_container_image(deployment, model)
        
        # Create Kubernetes deployment
        self._create_k8s_deployment(deployment, image_name)
        
        # Create Kubernetes service
        self._create_k8s_service(deployment)
        
        # Create horizontal pod autoscaler if scaling is enabled
        if deployment.scaling_policy.max_instances > 1:
            self._create_horizontal_pod_autoscaler(deployment)
        
        # Create ingress for external access
        endpoint = self._create_k8s_ingress(deployment)
        
        logger.info(f"Model {model.id} deployed to Kubernetes at {endpoint}")
        
        return endpoint
    
    def update(self, deployment: Deployment) -> None:
        """Update a Kubernetes deployment.
        
        Args:
            deployment: Deployment to update
        """
        logger.info(f"Updating deployment {deployment.id} in Kubernetes")
        
        # Update Kubernetes deployment
        self._update_k8s_deployment(deployment)
        
        # Update horizontal pod autoscaler if scaling is enabled
        if deployment.scaling_policy.max_instances > 1:
            self._update_horizontal_pod_autoscaler(deployment)
        
        logger.info(f"Deployment {deployment.id} updated in Kubernetes")
    
    def delete(self, deployment: Deployment) -> None:
        """Delete a Kubernetes deployment.
        
        Args:
            deployment: Deployment to delete
        """
        logger.info(f"Deleting deployment {deployment.id} from Kubernetes")
        
        # Delete Kubernetes resources
        self._delete_k8s_ingress(deployment)
        self._delete_horizontal_pod_autoscaler(deployment)
        self._delete_k8s_service(deployment)
        self._delete_k8s_deployment(deployment)
        
        logger.info(f"Deployment {deployment.id} deleted from Kubernetes")
    
    def hibernate(self, deployment: Deployment) -> None:
        """Hibernate a Kubernetes deployment to reduce costs.
        
        Args:
            deployment: Deployment to hibernate
        """
        logger.info(f"Hibernating deployment {deployment.id} in Kubernetes")
        
        # Scale deployment to 0 replicas
        self._scale_k8s_deployment(deployment, 0)
        
        logger.info(f"Deployment {deployment.id} hibernated in Kubernetes")
    
    def activate(self, deployment: Deployment) -> None:
        """Activate a hibernated Kubernetes deployment.
        
        Args:
            deployment: Deployment to activate
        """
        logger.info(f"Activating deployment {deployment.id} in Kubernetes")
        
        # Scale deployment to min_instances replicas
        self._scale_k8s_deployment(deployment, deployment.scaling_policy.min_instances)
        
        logger.info(f"Deployment {deployment.id} activated in Kubernetes")
    
    def _create_namespace(self) -> None:
        """Create Kubernetes namespace if it doesn't exist."""
        try:
            self.core_api.read_namespace(name=self.namespace)
        except client.rest.ApiException as e:
            if e.status == 404:
                namespace = client.V1Namespace(
                    metadata=client.V1ObjectMeta(name=self.namespace)
                )
                self.core_api.create_namespace(body=namespace)
                logger.info(f"Created namespace {self.namespace}")
            else:
                raise
    
    def _build_container_image(self, deployment: Deployment, model: Model) -> str:
        """Build container image for the model.
        
        Args:
            deployment: Deployment configuration
            model: Model to deploy
            
        Returns:
            Container image name
        """
        # In a real implementation, this would build a container image for the model
        # For this implementation, we'll just return a placeholder image name
        model_type = "optimized" if isinstance(model, OptimizedModel) else "original"
        image_name = f"{self.registry_url}/{model_type}-{model.id}:latest"
        
        logger.info(f"Using container image {image_name} for deployment {deployment.id}")
        
        return image_name
    
    def _create_k8s_deployment(self, deployment: Deployment, image_name: str) -> None:
        """Create Kubernetes deployment.
        
        Args:
            deployment: Deployment configuration
            image_name: Container image name
        """
        # Define container resources
        resources = client.V1ResourceRequirements(
            requests={
                "cpu": deployment.resource_requirements.cpu,
                "memory": deployment.resource_requirements.memory,
            },
            limits={
                "cpu": deployment.resource_requirements.cpu,
                "memory": deployment.resource_requirements.memory,
            },
        )
        
        # Add GPU resources if specified
        if deployment.resource_requirements.gpu:
            resources.limits["nvidia.com/gpu"] = deployment.resource_requirements.gpu
        
        # Define container
        container = client.V1Container(
            name=f"model-{deployment.id}",
            image=image_name,
            ports=[client.V1ContainerPort(container_port=8080)],
            resources=resources,
            env=[
                client.V1EnvVar(name="MODEL_ID", value=deployment.model_id),
                client.V1EnvVar(name="DEPLOYMENT_ID", value=deployment.id),
            ],
            readiness_probe=client.V1Probe(
                http_get=client.V1HTTPGetAction(
                    path="/health",
                    port=8080,
                ),
                initial_delay_seconds=10,
                period_seconds=5,
            ),
        )
        
        # Define deployment spec
        spec = client.V1DeploymentSpec(
            replicas=deployment.scaling_policy.min_instances,
            selector=client.V1LabelSelector(
                match_labels={
                    "app": f"model-{deployment.id}",
                }
            ),
            template=client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(
                    labels={
                        "app": f"model-{deployment.id}",
                    }
                ),
                spec=client.V1PodSpec(
                    containers=[container],
                ),
            ),
        )
        
        # Define deployment
        k8s_deployment = client.V1Deployment(
            api_version="apps/v1",
            kind="Deployment",
            metadata=client.V1ObjectMeta(
                name=f"model-{deployment.id}",
                namespace=self.namespace,
                labels={
                    "app": f"model-{deployment.id}",
                    "deployment-id": deployment.id,
                    "model-id": deployment.model_id,
                },
            ),
            spec=spec,
        )
        
        # Create deployment
        self.apps_api.create_namespaced_deployment(
            namespace=self.namespace,
            body=k8s_deployment,
        )
        
        logger.info(f"Created Kubernetes deployment for {deployment.id}")
    
    def _create_k8s_service(self, deployment: Deployment) -> None:
        """Create Kubernetes service for the deployment.
        
        Args:
            deployment: Deployment configuration
        """
        # Define service
        service = client.V1Service(
            api_version="v1",
            kind="Service",
            metadata=client.V1ObjectMeta(
                name=f"model-{deployment.id}",
                namespace=self.namespace,
                labels={
                    "app": f"model-{deployment.id}",
                    "deployment-id": deployment.id,
                    "model-id": deployment.model_id,
                },
            ),
            spec=client.V1ServiceSpec(
                selector={
                    "app": f"model-{deployment.id}",
                },
                ports=[
                    client.V1ServicePort(
                        port=80,
                        target_port=8080,
                    )
                ],
            ),
        )
        
        # Create service
        self.core_api.create_namespaced_service(
            namespace=self.namespace,
            body=service,
        )
        
        logger.info(f"Created Kubernetes service for {deployment.id}")
    
    def _create_horizontal_pod_autoscaler(self, deployment: Deployment) -> None:
        """Create horizontal pod autoscaler for the deployment.
        
        Args:
            deployment: Deployment configuration
        """
        # Define horizontal pod autoscaler
        hpa = client.V1HorizontalPodAutoscaler(
            api_version="autoscaling/v1",
            kind="HorizontalPodAutoscaler",
            metadata=client.V1ObjectMeta(
                name=f"model-{deployment.id}",
                namespace=self.namespace,
                labels={
                    "app": f"model-{deployment.id}",
                    "deployment-id": deployment.id,
                    "model-id": deployment.model_id,
                },
            ),
            spec=client.V1HorizontalPodAutoscalerSpec(
                scale_target_ref=client.V1CrossVersionObjectReference(
                    api_version="apps/v1",
                    kind="Deployment",
                    name=f"model-{deployment.id}",
                ),
                min_replicas=deployment.scaling_policy.min_instances,
                max_replicas=deployment.scaling_policy.max_instances,
                target_cpu_utilization_percentage=deployment.scaling_policy.target_cpu_utilization,
            ),
        )
        
        # Create horizontal pod autoscaler
        self.autoscaling_api.create_namespaced_horizontal_pod_autoscaler(
            namespace=self.namespace,
            body=hpa,
        )
        
        logger.info(f"Created horizontal pod autoscaler for {deployment.id}")
    
    def _create_k8s_ingress(self, deployment: Deployment) -> str:
        """Create Kubernetes ingress for the deployment.
        
        Args:
            deployment: Deployment configuration
            
        Returns:
            Endpoint URL for the deployed model
        """
        # Define ingress
        ingress = client.V1Ingress(
            api_version="networking.k8s.io/v1",
            kind="Ingress",
            metadata=client.V1ObjectMeta(
                name=f"model-{deployment.id}",
                namespace=self.namespace,
                labels={
                    "app": f"model-{deployment.id}",
                    "deployment-id": deployment.id,
                    "model-id": deployment.model_id,
                },
                annotations={
                    "kubernetes.io/ingress.class": "nginx",
                },
            ),
            spec=client.V1IngressSpec(
                rules=[
                    client.V1IngressRule(
                        host=f"model-{deployment.id}.example.com",
                        http=client.V1HTTPIngressRuleValue(
                            paths=[
                                client.V1HTTPIngressPath(
                                    path="/",
                                    path_type="Prefix",
                                    backend=client.V1IngressBackend(
                                        service=client.V1IngressServiceBackend(
                                            name=f"model-{deployment.id}",
                                            port=client.V1ServiceBackendPort(
                                                number=80,
                                            ),
                                        ),
                                    ),
                                )
                            ]
                        ),
                    )
                ]
            ),
        )
        
        # Create ingress
        self.networking_api.create_namespaced_ingress(
            namespace=self.namespace,
            body=ingress,
        )
        
        logger.info(f"Created Kubernetes ingress for {deployment.id}")
        
        # Return endpoint URL
        return f"https://model-{deployment.id}.example.com"
    
    def _update_k8s_deployment(self, deployment: Deployment) -> None:
        """Update Kubernetes deployment.
        
        Args:
            deployment: Deployment to update
        """
        # Get current deployment
        k8s_deployment = self.apps_api.read_namespaced_deployment(
            name=f"model-{deployment.id}",
            namespace=self.namespace,
        )
        
        # Update resource requirements
        container = k8s_deployment.spec.template.spec.containers[0]
        container.resources = client.V1ResourceRequirements(
            requests={
                "cpu": deployment.resource_requirements.cpu,
                "memory": deployment.resource_requirements.memory,
            },
            limits={
                "cpu": deployment.resource_requirements.cpu,
                "memory": deployment.resource_requirements.memory,
            },
        )
        
        # Add GPU resources if specified
        if deployment.resource_requirements.gpu:
            container.resources.limits["nvidia.com/gpu"] = deployment.resource_requirements.gpu
        
        # Update deployment
        self.apps_api.replace_namespaced_deployment(
            name=f"model-{deployment.id}",
            namespace=self.namespace,
            body=k8s_deployment,
        )
        
        logger.info(f"Updated Kubernetes deployment for {deployment.id}")
    
    def _update_horizontal_pod_autoscaler(self, deployment: Deployment) -> None:
        """Update horizontal pod autoscaler for the deployment.
        
        Args:
            deployment:<response clipped><NOTE>To save on context only part of this file has been shown to you. You should retry this tool after you have searched inside the file with `grep -n` in order to find the line numbers of what you are looking for.</NOTE>