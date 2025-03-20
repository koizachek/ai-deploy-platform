"""
Cost optimization module for the AI model deployment platform.
This module provides functionality for optimizing deployment costs.
"""

import datetime
import json
import logging
import os
import time
from typing import Dict, List, Optional, Tuple

from core.deployment import DeploymentService
from core.models import Deployment, DeploymentStatus, DeploymentType
from infrastructure.kubernetes import KubernetesDeployer
from infrastructure.serverless import ServerlessDeployer

logger = logging.getLogger(__name__)


class CostOptimizer:
    """Service for optimizing deployment costs."""
    
    def __init__(
        self,
        deployment_service: DeploymentService,
        kubernetes_deployer: KubernetesDeployer,
        serverless_deployer: ServerlessDeployer,
        cost_data_path: str = "/tmp/ai-deploy-platform/cost_data",
    ):
        """Initialize the cost optimizer.
        
        Args:
            deployment_service: Service for managing deployments
            kubernetes_deployer: Deployer for Kubernetes deployments
            serverless_deployer: Deployer for serverless deployments
            cost_data_path: Path to store cost data
        """
        self.deployment_service = deployment_service
        self.kubernetes_deployer = kubernetes_deployer
        self.serverless_deployer = serverless_deployer
        self.cost_data_path = cost_data_path
        
        # Create cost data directory if it doesn't exist
        os.makedirs(cost_data_path, exist_ok=True)
    
    def optimize_all_deployments(self) -> Dict[str, Dict]:
        """Optimize all deployments for cost.
        
        Returns:
            Dictionary mapping deployment IDs to optimization results
        """
        logger.info("Optimizing all deployments for cost")
        
        # Get all deployments
        deployments = self.deployment_service.list_deployments()
        
        # Optimize each deployment
        results = {}
        for deployment in deployments:
            try:
                result = self.optimize_deployment(deployment.id)
                results[deployment.id] = result
            except Exception as e:
                logger.error(f"Error optimizing deployment {deployment.id}: {e}")
                results[deployment.id] = {"error": str(e)}
        
        return results
    
    def optimize_deployment(self, deployment_id: str) -> Dict:
        """Optimize a deployment for cost.
        
        Args:
            deployment_id: ID of the deployment to optimize
            
        Returns:
            Optimization results
        """
        logger.info(f"Optimizing deployment {deployment_id} for cost")
        
        # Get deployment
        deployment = self.deployment_service.get_deployment(deployment_id)
        if not deployment:
            raise ValueError(f"Deployment {deployment_id} not found")
        
        # Skip deployments that are not active
        if deployment.status != DeploymentStatus.ACTIVE:
            logger.info(f"Skipping optimization for non-active deployment {deployment_id}")
            return {"status": "skipped", "reason": f"Deployment is {deployment.status.value}"}
        
        # Apply cost optimization strategies
        results = {}
        
        # Check for hibernation opportunity
        hibernation_result = self._check_hibernation(deployment)
        results["hibernation"] = hibernation_result
        
        # Check for spot/preemptible instance opportunity
        spot_result = self._check_spot_instances(deployment)
        results["spot_instances"] = spot_result
        
        # Check for resource right-sizing opportunity
        sizing_result = self._check_resource_sizing(deployment)
        results["resource_sizing"] = sizing_result
        
        # Check for multi-cloud arbitrage opportunity
        if deployment.cost_optimization_policy.multi_cloud_enabled:
            arbitrage_result = self._check_multi_cloud_arbitrage(deployment)
            results["multi_cloud_arbitrage"] = arbitrage_result
        
        # Save optimization results
        self._save_optimization_results(deployment_id, results)
        
        logger.info(f"Completed cost optimization for deployment {deployment_id}")
        
        return results
    
    def _check_hibernation(self, deployment: Deployment) -> Dict:
        """Check if a deployment should be hibernated.
        
        Args:
            deployment: Deployment to check
            
        Returns:
            Hibernation check results
        """
        # Skip if hibernation is not enabled
        if not deployment.cost_optimization_policy.hibernation_enabled:
            return {"status": "skipped", "reason": "Hibernation not enabled"}
        
        # Check if deployment has been inactive for longer than the idle timeout
        now = datetime.datetime.utcnow()
        last_active = deployment.last_active_at or deployment.created_at
        idle_time = (now - last_active).total_seconds()
        
        if idle_time > deployment.cost_optimization_policy.hibernation_idle_timeout:
            # Hibernate deployment
            try:
                self.deployment_service.hibernate_deployment(deployment.id)
                return {
                    "status": "hibernated",
                    "idle_time_seconds": idle_time,
                    "estimated_savings": self._estimate_hibernation_savings(deployment),
                }
            except Exception as e:
                logger.error(f"Error hibernating deployment {deployment.id}: {e}")
                return {"status": "error", "reason": str(e)}
        else:
            return {
                "status": "active",
                "idle_time_seconds": idle_time,
                "hibernation_threshold_seconds": deployment.cost_optimization_policy.hibernation_idle_timeout,
            }
    
    def _check_spot_instances(self, deployment: Deployment) -> Dict:
        """Check if a deployment should use spot/preemptible instances.
        
        Args:
            deployment: Deployment to check
            
        Returns:
            Spot instance check results
        """
        # Skip if spot instances are not enabled
        if not deployment.cost_optimization_policy.use_spot_instances:
            return {"status": "skipped", "reason": "Spot instances not enabled"}
        
        # Skip for serverless deployments (handled differently)
        if deployment.deployment_type == DeploymentType.SERVERLESS:
            return {"status": "skipped", "reason": "Not applicable for serverless deployments"}
        
        # Check if deployment is already using spot instances
        # This would be stored in the deployment metadata in a real implementation
        if deployment.metadata.get("using_spot_instances", False):
            return {"status": "already_optimized", "reason": "Already using spot instances"}
        
        # Check spot instance availability and pricing
        spot_available, spot_price, on_demand_price = self._check_spot_pricing(deployment)
        
        if spot_available and spot_price < on_demand_price:
            # Update deployment to use spot instances
            try:
                # In a real implementation, this would update the Kubernetes deployment
                # to use spot instances
                
                # Update deployment metadata
                self.deployment_service.update_deployment(
                    deployment_id=deployment.id,
                    metadata={"using_spot_instances": True, "spot_price": spot_price},
                )
                
                savings_percentage = ((on_demand_price - spot_price) / on_demand_price) * 100
                
                return {
                    "status": "converted",
                    "spot_price": spot_price,
                    "on_demand_price": on_demand_price,
                    "savings_percentage": savings_percentage,
                }
            except Exception as e:
                logger.error(f"Error converting deployment {deployment.id} to spot instances: {e}")
                return {"status": "error", "reason": str(e)}
        else:
            return {
                "status": "not_beneficial",
                "reason": "Spot instances not available or not cost-effective",
                "spot_available": spot_available,
                "spot_price": spot_price if spot_available else None,
                "on_demand_price": on_demand_price,
            }
    
    def _check_resource_sizing(self, deployment: Deployment) -> Dict:
        """Check if a deployment's resources should be resized.
        
        Args:
            deployment: Deployment to check
            
        Returns:
            Resource sizing check results
        """
        # Get resource utilization metrics
        # In a real implementation, this would query metrics from a monitoring system
        cpu_utilization, memory_utilization = self._get_resource_utilization(deployment)
        
        # Check if resources are over-provisioned
        cpu_over_provisioned = cpu_utilization < 30  # Less than 30% CPU utilization
        memory_over_provisioned = memory_utilization < 30  # Less than 30% memory utilization
        
        if cpu_over_provisioned or memory_over_provisioned:
            # Calculate new resource requirements
            current_cpu = float(deployment.resource_requirements.cpu)
            current_memory = float(deployment.resource_requirements.memory.rstrip("Gi"))
            
            new_cpu = current_cpu
            new_memory = current_memory
            
            if cpu_over_provisioned:
                # Reduce CPU by 25%, but not below 0.25 vCPU
                new_cpu = max(0.25, current_cpu * 0.75)
            
            if memory_over_provisioned:
                # Reduce memory by 25%, but not below 0.5 Gi
                new_memory = max(0.5, current_memory * 0.75)
            
            # Update deployment resource requirements
            try:
                self.deployment_service.update_deployment(
                    deployment_id=deployment.id,
                    resource_requirements={
                        "cpu": str(new_cpu),
                        "memory": f"{new_memory}Gi",
                        "gpu": deployment.resource_requirements.gpu,
                        "timeout": deployment.resource_requirements.timeout,
                    },
                )
                
                cpu_savings_percentage = ((current_cpu - new_cpu) / current_cpu) * 100 if cpu_over_provisioned else 0
                memory_savings_percentage = ((current_memory - new_memory) / current_memory) * 100 if memory_over_provisioned else 0
                
                return {
                    "status": "resized",
                    "cpu": {
                        "before": current_cpu,
                        "after": new_cpu,
                        "utilization": cpu_utilization,
                        "savings_percentage": cpu_savings_percentage,
                    },
                    "memory": {
                        "before": current_memory,
                        "after": new_memory,
                        "utilization": memory_utilization,
                        "savings_percentage": memory_savings_percentage,
                    },
                }
            except Exception as e:
                logger.error(f"Error resizing deployment {deployment.id}: {e}")
                return {"status": "error", "reason": str(e)}
        else:
            return {
                "status": "optimal",
                "cpu_utilization": cpu_utilization,
                "memory_utilization": memory_utilization,
            }
    
    def _check_multi_cloud_arbitrage(self, deployment: Deployment) -> Dict:
        """Check if a deployment should be moved to a different cloud provider.
        
        Args:
            deployment: Deployment to check
            
        Returns:
            Multi-cloud arbitrage check results
        """
        # Get current cloud provider and region
        current_provider = deployment.metadata.get("cloud_provider", "aws")
        current_region = deployment.metadata.get("cloud_region", "us-east-1")
        
        # Get pricing for current and alternative providers
        pricing_data = self._get_multi_cloud_pricing(deployment, current_provider, current_region)
        
        # Find the cheapest provider
        cheapest_provider = min(pricing_data, key=lambda x: pricing_data[x]["price"])
        
        if cheapest_provider != current_provider and pricing_data[cheapest_provider]["price"] < pricing_data[current_provider]["price"] * 0.9:
            # The cheapest provider is at least 10% cheaper than the current provider
            
            # In a real implementation, this would migrate the deployment to the new provider
            # For this implementation, we'll just update the metadata
            
            try:
                self.deployment_service.update_deployment(
                    deployment_id=deployment.id,
                    metadata={
                        "cloud_provider": cheapest_provider,
                        "cloud_region": pricing_data[cheapest_provider]["region"],
                    },
                )
                
                savings_percentage = (
                    (pricing_data[current_provider]["price"] - pricing_data[cheapest_provider]["price"])
                    / pricing_data[current_provider]["price"]
                ) * 100
                
                return {
                    "status": "migrated",
                    "from_provider": current_provider,
                    "to_provider": cheapest_provider,
                    "from_region": current_region,
                    "to_region": pricing_data[cheapest_provider]["region"],
                    "from_price": pricing_data[current_provider]["price"],
                    "to_price": pricing_data[cheapest_provider]["price"],
                    "savings_percentage": savings_percentage,
                }
            except Exception as e:
                logger.error(f"Error migrating deployment {deployment.id} to {cheapest_provider}: {e}")
                return {"status": "error", "reason": str(e)}
        else:
            return {
                "status": "optimal",
                "current_provider": current_provider,
                "current_region": current_region,
                "current_price": pricing_data[current_provider]["price"],
                "cheapest_provider": cheapest_provider,
                "cheapest_price": pricing_data[cheapest_provider]["price"],
            }
    
    def _estimate_hibernation_savings(self, deployment: Deployment) -> float:
        """Estimate cost savings from hibernating a deployment.
        
        Args:
            deployment: Deployment to estimate savings for
            
        Returns:
            Estimated monthly cost savings in USD
        """
        # In a real implementation, this would calculate the actual cost savings
        # based on the deployment's resource usage and cloud provider pricing
        
        # For this implementation, we'll use a simple heuristic
        if deployment.deployment_type == DeploymentType.KUBERNETES:
            # Kubernetes deployments have higher fixed costs
            cpu_cost = float(deployment.resource_requirements.cpu) * 30  # $30 per CPU per month
            memory_cost = float(deployment.resource_requirements.memory.rstrip("Gi")) * 5  # $5 per GB per month
            gpu_cost = 0
            if deployment.resource_requirements.gpu:
                gpu_cost = float(deployment.resource_requirements.gpu) * 300  # $300 per GPU per month
            
            return cpu_cost + memory_cost + gpu_cost
        else:  # DeploymentType.SERVERLESS
            # Serverless dep<response clipped><NOTE>To save on context only part of this file has been shown to you. You should retry this tool after you have searched inside the file with `grep -n` in order to find the line numbers of what you are looking for.</NOTE>