"""
Monitoring service for the AI model deployment platform.
This module provides functionality for monitoring deployments and collecting metrics.
"""

import datetime
import json
import logging
import os
import random
import time
from typing import Dict, List, Optional, Tuple, Union

from core.deployment import DeploymentService
from core.models import Deployment, DeploymentStatus, DeploymentType
from core.repository import ModelRepository

logger = logging.getLogger(__name__)


class MonitoringService:
    """Service for monitoring deployments and collecting metrics."""
    
    def __init__(
        self,
        deployment_service: DeploymentService,
        model_repository: ModelRepository,
        metrics_path: str = "/tmp/ai-deploy-platform/metrics",
        collection_interval: int = 60,  # 1 minute
    ):
        """Initialize the monitoring service.
        
        Args:
            deployment_service: Service for managing deployments
            model_repository: Repository for model storage and retrieval
            metrics_path: Path to store metrics data
            collection_interval: Interval in seconds between metrics collection
        """
        self.deployment_service = deployment_service
        self.model_repository = model_repository
        self.metrics_path = metrics_path
        self.collection_interval = collection_interval
        
        # Create metrics directory if it doesn't exist
        os.makedirs(metrics_path, exist_ok=True)
        
        # Initialize metrics tracking
        self.metrics_tracking_path = os.path.join(metrics_path, "metrics_tracking.json")
        self._init_metrics_tracking()
    
    def collect_metrics(self) -> Dict[str, Dict]:
        """Collect metrics for all deployments.
        
        Returns:
            Dictionary mapping deployment IDs to metrics
        """
        logger.info("Collecting metrics for all deployments")
        
        # Get all deployments
        deployments = self.deployment_service.list_deployments()
        
        # Collect metrics for each deployment
        results = {}
        for deployment in deployments:
            try:
                metrics = self.collect_deployment_metrics(deployment.id)
                results[deployment.id] = metrics
            except Exception as e:
                logger.error(f"Error collecting metrics for deployment {deployment.id}: {e}")
                results[deployment.id] = {"error": str(e)}
        
        return results
    
    def collect_deployment_metrics(self, deployment_id: str) -> Dict:
        """Collect metrics for a specific deployment.
        
        Args:
            deployment_id: ID of the deployment to collect metrics for
            
        Returns:
            Collected metrics
        """
        logger.info(f"Collecting metrics for deployment {deployment_id}")
        
        # Get deployment
        deployment = self.deployment_service.get_deployment(deployment_id)
        if not deployment:
            raise ValueError(f"Deployment {deployment_id} not found")
        
        # Skip deployments that are not active or hibernated
        if deployment.status not in [DeploymentStatus.ACTIVE, DeploymentStatus.HIBERNATED]:
            return {
                "status": "skipped",
                "reason": f"Deployment is {deployment.status.value}",
                "timestamp": datetime.datetime.utcnow().isoformat(),
            }
        
        # Collect metrics based on deployment type
        if deployment.status == DeploymentStatus.HIBERNATED:
            # For hibernated deployments, only collect basic metrics
            metrics = self._collect_hibernated_deployment_metrics(deployment)
        elif deployment.deployment_type == DeploymentType.KUBERNETES:
            metrics = self._collect_kubernetes_deployment_metrics(deployment)
        elif deployment.deployment_type == DeploymentType.SERVERLESS:
            metrics = self._collect_serverless_deployment_metrics(deployment)
        else:
            raise ValueError(f"Unsupported deployment type: {deployment.deployment_type}")
        
        # Add common metrics
        metrics.update({
            "deployment_id": deployment.id,
            "deployment_name": deployment.name,
            "deployment_type": deployment.deployment_type.value,
            "deployment_status": deployment.status.value,
            "model_id": deployment.model_id,
            "model_type": deployment.model_type,
            "timestamp": datetime.datetime.utcnow().isoformat(),
        })
        
        # Save metrics
        self._save_deployment_metrics(deployment_id, metrics)
        
        return metrics
    
    def get_deployment_metrics(
        self, deployment_id: str, start_time: Optional[str] = None, end_time: Optional[str] = None
    ) -> List[Dict]:
        """Get metrics for a specific deployment.
        
        Args:
            deployment_id: ID of the deployment to get metrics for
            start_time: Start time for metrics query (ISO format)
            end_time: End time for metrics query (ISO format)
            
        Returns:
            List of metrics
        """
        logger.info(f"Getting metrics for deployment {deployment_id}")
        
        # Get deployment
        deployment = self.deployment_service.get_deployment(deployment_id)
        if not deployment:
            raise ValueError(f"Deployment {deployment_id} not found")
        
        # Load metrics tracking data
        metrics_data = self._load_metrics_tracking()
        
        # Get metrics for deployment
        if deployment_id not in metrics_data:
            return []
        
        deployment_metrics = metrics_data[deployment_id]
        
        # Filter by time range if specified
        if start_time or end_time:
            start_datetime = (
                datetime.datetime.fromisoformat(start_time) if start_time else datetime.datetime.min
            )
            end_datetime = (
                datetime.datetime.fromisoformat(end_time) if end_time else datetime.datetime.max
            )
            
            filtered_metrics = []
            for metrics in deployment_metrics:
                metrics_time = datetime.datetime.fromisoformat(metrics["timestamp"])
                if start_datetime <= metrics_time <= end_datetime:
                    filtered_metrics.append(metrics)
            
            return filtered_metrics
        else:
            return deployment_metrics
    
    def get_cost_metrics(
        self, start_time: Optional[str] = None, end_time: Optional[str] = None
    ) -> Dict[str, Dict]:
        """Get cost metrics for all deployments.
        
        Args:
            start_time: Start time for metrics query (ISO format)
            end_time: End time for metrics query (ISO format)
            
        Returns:
            Dictionary mapping deployment IDs to cost metrics
        """
        logger.info("Getting cost metrics for all deployments")
        
        # Get all deployments
        deployments = self.deployment_service.list_deployments()
        
        # Get cost metrics for each deployment
        results = {}
        for deployment in deployments:
            try:
                metrics = self.get_deployment_metrics(deployment.id, start_time, end_time)
                
                # Calculate cost metrics
                total_cost = 0
                cost_breakdown = {
                    "compute": 0,
                    "storage": 0,
                    "network": 0,
                }
                
                for metric in metrics:
                    if "cost" in metric:
                        total_cost += metric["cost"].get("total", 0)
                        cost_breakdown["compute"] += metric["cost"].get("compute", 0)
                        cost_breakdown["storage"] += metric["cost"].get("storage", 0)
                        cost_breakdown["network"] += metric["cost"].get("network", 0)
                
                results[deployment.id] = {
                    "deployment_id": deployment.id,
                    "deployment_name": deployment.name,
                    "total_cost": total_cost,
                    "cost_breakdown": cost_breakdown,
                }
            except Exception as e:
                logger.error(f"Error getting cost metrics for deployment {deployment.id}: {e}")
                results[deployment.id] = {"error": str(e)}
        
        return results
    
    def get_performance_metrics(
        self, start_time: Optional[str] = None, end_time: Optional[str] = None
    ) -> Dict[str, Dict]:
        """Get performance metrics for all deployments.
        
        Args:
            start_time: Start time for metrics query (ISO format)
            end_time: End time for metrics query (ISO format)
            
        Returns:
            Dictionary mapping deployment IDs to performance metrics
        """
        logger.info("Getting performance metrics for all deployments")
        
        # Get all deployments
        deployments = self.deployment_service.list_deployments()
        
        # Get performance metrics for each deployment
        results = {}
        for deployment in deployments:
            try:
                metrics = self.get_deployment_metrics(deployment.id, start_time, end_time)
                
                # Calculate performance metrics
                total_requests = 0
                total_latency = 0
                total_errors = 0
                
                for metric in metrics:
                    if "requests" in metric:
                        total_requests += metric["requests"].get("count", 0)
                        total_latency += metric["requests"].get("total_latency", 0)
                        total_errors += metric["requests"].get("errors", 0)
                
                avg_latency = total_latency / total_requests if total_requests > 0 else 0
                error_rate = (total_errors / total_requests) * 100 if total_requests > 0 else 0
                
                results[deployment.id] = {
                    "deployment_id": deployment.id,
                    "deployment_name": deployment.name,
                    "total_requests": total_requests,
                    "avg_latency": avg_latency,
                    "error_rate": error_rate,
                }
            except Exception as e:
                logger.error(f"Error getting performance metrics for deployment {deployment.id}: {e}")
                results[deployment.id] = {"error": str(e)}
        
        return results
    
    def detect_anomalies(self) -> Dict[str, List[Dict]]:
        """Detect anomalies in deployment metrics.
        
        Returns:
            Dictionary mapping deployment IDs to lists of anomalies
        """
        logger.info("Detecting anomalies in deployment metrics")
        
        # Get all deployments
        deployments = self.deployment_service.list_deployments()
        
        # Detect anomalies for each deployment
        results = {}
        for deployment in deployments:
            try:
                # Get recent metrics (last 24 hours)
                now = datetime.datetime.utcnow()
                start_time = (now - datetime.timedelta(hours=24)).isoformat()
                metrics = self.get_deployment_metrics(deployment.id, start_time)
                
                # Detect anomalies
                anomalies = self._detect_deployment_anomalies(deployment, metrics)
                
                if anomalies:
                    results[deployment.id] = anomalies
            except Exception as e:
                logger.error(f"Error detecting anomalies for deployment {deployment.id}: {e}")
                results[deployment.id] = [{"type": "error", "message": str(e)}]
        
        return results
    
    def _init_metrics_tracking(self) -> None:
        """Initialize metrics tracking data."""
        if not os.path.exists(self.metrics_tracking_path):
            self._save_metrics_tracking({})
    
    def _load_metrics_tracking(self) -> Dict:
        """Load metrics tracking data.
        
        Returns:
            Metrics tracking data
        """
        with open(self.metrics_tracking_path, "r") as f:
            return json.load(f)
    
    def _save_metrics_tracking(self, metrics_data: Dict) -> None:
        """Save metrics tracking data.
        
        Args:
            metrics_data: Metrics tracking data
        """
        with open(self.metrics_tracking_path, "w") as f:
            json.dump(metrics_data, f, indent=2)
    
    def _save_deployment_metrics(self, deployment_id: str, metrics: Dict) -> None:
        """Save metrics for a deployment.
        
        Args:
            deployment_id: ID of the deployment
            metrics: Metrics to save
        """
        # Load metrics tracking data
        metrics_data = self._load_metrics_tracking()
        
        # Initialize deployment metrics if not exists
        if deployment_id not in metrics_data:
            metrics_data[deployment_id] = []
        
        # Add metrics
        metrics_data[deployment_id].append(metrics)
        
        # Limit to last 1000 metrics per deployment
        if len(metrics_data[deployment_id]) > 1000:
            metrics_data[deployment_id] = metrics_data[deployment_id][-1000:]
        
        # Save metrics tracking data
        self._save_metrics_tracking(metrics_data)
    
    def _collect_hibernated_deployment_metrics(self, deployment: Deployment) -> Dict:
        """Collect metrics for a hibernated deployment.
        
        Args:
            deployment: Deployment to collect metrics for
            
        Returns:
            Collected metrics
        """
        # For hibernated deployments, we only collect cost metrics
        # In a real implementation, this would calculate actual costs
        # For this implementation, we'll use placeholder values
        
        # Calculate storage cost
        storage_cost = 0.01  # $0.01 per hour for storage
        
        return {
            "cost": {
                "total": storage_cost,
                "compute": 0,
                "storage": storage_cost,
                "network": 0,
            },
            "hibernated_since": deployment.updated_at.isoformat(),
        }
    
    def _collect_kubernetes_deployment_metrics(self, deployment: Deployment) -> Dict:
        """Collect metrics for a Kubernetes deployment.
        
        Args:
            deployment: Deployment to collect metrics for
            
        Returns:
            Collected metrics
        """
        # In a real implementation, this would query Kubernetes metrics API
        # For this implementation, we'll generate simulated metrics
        
        # Generate resource utilization metrics
        cpu_utilization = random.uniform(10, 90)
        memory_utilization = random.uniform(10, 90)
        
        # Generate request metrics
        request_count = random.randint(10, 1000)
        avg_latency = random.uniform(10, 500)  # ms
        error_count = int(request_count * random.uniform(0, 0.05))  # 0-5% error rate
        
        # Calculate costs
        cpu_cost = float(deployment.resource_requirements.cpu) * 0.04  # $0.04 per CPU per hour
        memory_cost = float(deployment.resource_requirements.memory.rstrip("Gi")) * 0.01  # $0.01 per GB per hour
        gpu_cost = 0
        if deployment.resource_requirements.gpu:
            gpu_cost = float(deployment.resource_requirements.gpu) * 0.5  # $0.5 per GPU per hour
        
        compute_cost = cpu_cost + memory_cost + gpu_cost
        storage_cost = 0.01  # $0.01 per hour for storage
        network_cost = request_count * 0.0001  # $0.0001 per request
        
        total_cost = compute_cost + storage_cost + network_cost
        
        return {
            "resources": {
             <response clipped><NOTE>To save on context only part of this file has been shown to you. You should retry this tool after you have searched inside the file with `grep -n` in order to find the line numbers of what you are looking for.</NOTE>