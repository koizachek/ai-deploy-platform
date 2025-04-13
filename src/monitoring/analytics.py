"""
Analytics service for the AI model deployment platform.
This module provides functionality for analyzing deployment metrics and generating insights.
"""

import datetime
import json
import logging
import os
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union

from core.deployment import DeploymentService
from core.models import Deployment, DeploymentStatus, DeploymentType
from monitoring.monitoring import MonitoringService

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for analyzing deployment metrics and generating insights."""
    
    def __init__(
        self,
        deployment_service: DeploymentService,
        monitoring_service: MonitoringService,
        analytics_path: str = "/tmp/ai-deploy-platform/analytics",
    ):
        """Initialize the analytics service.
        
        Args:
            deployment_service: Service for managing deployments
            monitoring_service: Service for monitoring deployments
            analytics_path: Path to store analytics data
        """
        self.deployment_service = deployment_service
        self.monitoring_service = monitoring_service
        self.analytics_path = analytics_path
        
        # Create analytics directory if it doesn't exist
        os.makedirs(analytics_path, exist_ok=True)
    
    def generate_cost_analysis(
        self, start_time: Optional[str] = None, end_time: Optional[str] = None
    ) -> Dict:
        """Generate cost analysis for all deployments.
        
        Args:
            start_time: Start time for analysis (ISO format)
            end_time: End time for analysis (ISO format)
            
        Returns:
            Cost analysis results
        """
        logger.info("Generating cost analysis")
        
        # Get cost metrics for all deployments
        cost_metrics = self.monitoring_service.get_cost_metrics(start_time, end_time)
        
        # Calculate total cost
        total_cost = sum(
            metrics["total_cost"] for deployment_id, metrics in cost_metrics.items()
            if "error" not in metrics
        )
        
        # Calculate cost breakdown
        cost_breakdown = {
            "compute": 0,
            "storage": 0,
            "network": 0,
        }
        
        for deployment_id, metrics in cost_metrics.items():
            if "error" not in metrics:
                cost_breakdown["compute"] += metrics["cost_breakdown"]["compute"]
                cost_breakdown["storage"] += metrics["cost_breakdown"]["storage"]
                cost_breakdown["network"] += metrics["cost_breakdown"]["network"]
        
        # Calculate cost by deployment type
        cost_by_type = {
            "kubernetes": 0,
            "serverless": 0,
        }
        
        for deployment_id, metrics in cost_metrics.items():
            if "error" not in metrics:
                deployment = self.deployment_service.get_deployment(deployment_id)
                if deployment:
                    deployment_type = deployment.deployment_type.value
                    cost_by_type[deployment_type] += metrics["total_cost"]
        
        # Calculate cost by deployment
        cost_by_deployment = {
            metrics["deployment_name"]: metrics["total_cost"]
            for deployment_id, metrics in cost_metrics.items()
            if "error" not in metrics
        }
        
        # Sort deployments by cost (descending)
        cost_by_deployment = dict(
            sorted(cost_by_deployment.items(), key=lambda x: x[1], reverse=True)
        )
        
        # Generate cost optimization recommendations
        recommendations = self._generate_cost_recommendations(cost_metrics)
        
        # Calculate cost forecast
        forecast = self._generate_cost_forecast(cost_metrics)
        
        # Calculate cost comparison with major cloud platforms
        comparison = self._generate_cost_comparison(total_cost)
        
        # Save analysis results
        analysis_results = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "start_time": start_time,
            "end_time": end_time,
            "total_cost": total_cost,
            "cost_breakdown": cost_breakdown,
            "cost_by_type": cost_by_type,
            "cost_by_deployment": cost_by_deployment,
            "recommendations": recommendations,
            "forecast": forecast,
            "comparison": comparison,
        }
        
        self._save_analysis_results("cost_analysis", analysis_results)
        
        return analysis_results
    
    def generate_performance_analysis(
        self, start_time: Optional[str] = None, end_time: Optional[str] = None
    ) -> Dict:
        """Generate performance analysis for all deployments.
        
        Args:
            start_time: Start time for analysis (ISO format)
            end_time: End time for analysis (ISO format)
            
        Returns:
            Performance analysis results
        """
        logger.info("Generating performance analysis")
        
        # Get performance metrics for all deployments
        performance_metrics = self.monitoring_service.get_performance_metrics(start_time, end_time)
        
        # Calculate total requests
        total_requests = sum(
            metrics["total_requests"] for deployment_id, metrics in performance_metrics.items()
            if "error" not in metrics
        )
        
        # Calculate average latency
        total_weighted_latency = sum(
            metrics["avg_latency"] * metrics["total_requests"]
            for deployment_id, metrics in performance_metrics.items()
            if "error" not in metrics and metrics["total_requests"] > 0
        )
        
        avg_latency = (
            total_weighted_latency / total_requests if total_requests > 0 else 0
        )
        
        # Calculate error rate
        total_errors = sum(
            metrics["error_rate"] * metrics["total_requests"] / 100
            for deployment_id, metrics in performance_metrics.items()
            if "error" not in metrics and metrics["total_requests"] > 0
        )
        
        error_rate = (total_errors / total_requests) * 100 if total_requests > 0 else 0
        
        # Calculate performance by deployment type
        performance_by_type = {
            "kubernetes": {"requests": 0, "avg_latency": 0, "error_rate": 0},
            "serverless": {"requests": 0, "avg_latency": 0, "error_rate": 0},
        }
        
        for deployment_id, metrics in performance_metrics.items():
            if "error" not in metrics and metrics["total_requests"] > 0:
                deployment = self.deployment_service.get_deployment(deployment_id)
                if deployment:
                    deployment_type = deployment.deployment_type.value
                    performance_by_type[deployment_type]["requests"] += metrics["total_requests"]
                    performance_by_type[deployment_type]["avg_latency"] += (
                        metrics["avg_latency"] * metrics["total_requests"]
                    )
                    performance_by_type[deployment_type]["error_rate"] += (
                        metrics["error_rate"] * metrics["total_requests"] / 100
                    )
        
        # Calculate averages
        for deployment_type in performance_by_type:
            if performance_by_type[deployment_type]["requests"] > 0:
                performance_by_type[deployment_type]["avg_latency"] /= performance_by_type[deployment_type]["requests"]
                performance_by_type[deployment_type]["error_rate"] = (
                    performance_by_type[deployment_type]["error_rate"]
                    / performance_by_type[deployment_type]["requests"]
                    * 100
                )
        
        # Calculate performance by deployment
        performance_by_deployment = {
            metrics["deployment_name"]: {
                "requests": metrics["total_requests"],
                "avg_latency": metrics["avg_latency"],
                "error_rate": metrics["error_rate"],
            }
            for deployment_id, metrics in performance_metrics.items()
            if "error" not in metrics
        }
        
        # Sort deployments by requests (descending)
        performance_by_deployment = dict(
            sorted(
                performance_by_deployment.items(),
                key=lambda x: x[1]["requests"],
                reverse=True,
            )
        )
        
        # Generate performance optimization recommendations
        recommendations = self._generate_performance_recommendations(performance_metrics)
        
        # Detect anomalies
        anomalies = self.monitoring_service.detect_anomalies()
        
        # Save analysis results
        analysis_results = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "start_time": start_time,
            "end_time": end_time,
            "total_requests": total_requests,
            "avg_latency": avg_latency,
            "error_rate": error_rate,
            "performance_by_type": performance_by_type,
            "performance_by_deployment": performance_by_deployment,
            "recommendations": recommendations,
            "anomalies": anomalies,
        }
        
        self._save_analysis_results("performance_analysis", analysis_results)
        
        return analysis_results
    
    def generate_usage_forecast(
        self, days: int = 30, start_time: Optional[str] = None, end_time: Optional[str] = None
    ) -> Dict:
        """Generate usage forecast for all deployments.
        
        Args:
            days: Number of days to forecast
            start_time: Start time for analysis (ISO format)
            end_time: End time for analysis (ISO format)
            
        Returns:
            Usage forecast results
        """
        logger.info(f"Generating usage forecast for next {days} days")
        
        # Get all deployments
        deployments = self.deployment_service.list_deployments()
        
        # Get performance metrics for all deployments
        performance_metrics = self.monitoring_service.get_performance_metrics(start_time, end_time)
        
        # Get cost metrics for all deployments
        cost_metrics = self.monitoring_service.get_cost_metrics(start_time, end_time)
        
        # Generate forecast for each deployment
        forecast_by_deployment = {}
        for deployment in deployments:
            if deployment.id in performance_metrics and "error" not in performance_metrics[deployment.id]:
                # Get current metrics
                current_requests = performance_metrics[deployment.id]["total_requests"]
                current_cost = cost_metrics[deployment.id]["total_cost"] if deployment.id in cost_metrics else 0
                
                # Generate forecast
                # In a real implementation, this would use time series forecasting
                # For this implementation, we'll use a simple growth model
                growth_rate = 0.05  # 5% growth per day
                
                requests_forecast = []
                cost_forecast = []
                
                for day in range(1, days + 1):
                    # Calculate forecasted requests and cost
                    forecasted_requests = current_requests * (1 + growth_rate) ** day
                    forecasted_cost = current_cost * (1 + growth_rate) ** day
                    
                    requests_forecast.append(forecasted_requests)
                    cost_forecast.append(forecasted_cost)
                
                forecast_by_deployment[deployment.id] = {
                    "deployment_name": deployment.name,
                    "current_requests": current_requests,
                    "current_cost": current_cost,
                    "requests_forecast": requests_forecast,
                    "cost_forecast": cost_forecast,
                }
        
        # Calculate total forecast
        total_requests_forecast = [0] * days
        total_cost_forecast = [0] * days
        
        for deployment_id, forecast in forecast_by_deployment.items():
            for day in range(days):
                total_requests_forecast[day] += forecast["requests_forecast"][day]
                total_cost_forecast[day] += forecast["cost_forecast"][day]
        
        # Save forecast results
        forecast_results = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "start_time": start_time,
            "end_time": end_time,
            "days": days,
            "total_requests_forecast": total_requests_forecast,
            "total_cost_forecast": total_cost_forecast,
            "forecast_by_deployment": forecast_by_deployment,
        }
        
        self._save_analysis_results("usage_forecast", forecast_results)
        
        return forecast_results
    
    def generate_optimization_suggestions(self) -> Dict:
        """Generate optimization suggestions for all deployments.
        
        Returns:
            Optimization suggestions
        """
        logger.info("Generating optimization suggestions")
        
        # Get all deployments
        deployments = self.deployment_service.list_deployments()
        
        # Generate suggestions for each deployment
        suggestions_by_deployment = {}
        for deployment in deployments:
            try:
                # Get deployment metrics
                metrics = self.monitoring_service.get_deployment_metrics(deployment.id)
                
                # Skip if no metrics
                if not metrics:
                    continue
                
                # Generate suggestions
                suggestions = []
                
                # Check for resource optimization opportunities
                resource_suggestions = self._generate_resource_optimization_suggestions(deployment, metrics)
                suggestions.extend(resource_suggestions)
                
                # Check for cost optimization opportunities
                cost_suggestions = self._generate_cost_optimization_suggestions(deployment, metrics)
                suggestions.extend(cost_suggestions)
                
                # Check for performance optimization opportunities
                performance_suggestions = self._generate_performance_optimization_suggestions(deployment, metrics)
                suggestions.extend(performance_suggestions)
                
                if suggestions:
                    suggestions_by_deployment[deployment.id] = {
                        "deployment_name": deployment.name,
                        "suggestions": suggestions,
                    }
            except Exception as e:
                logger.error(f"Error generating suggestions for deployment {deployment.id}: {e}")
        
        # Save suggestions
        suggestions_results = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "suggestions_by_deployment": suggestions_by_deployment,
        }
        
        self._save_analysis_results("optimization_suggestions", suggestions_results)
        
        return suggestions_results
    
    def _save_analysis_results(self, analysis_type: str, results: Dict) -> None:
        """Save analysis results to disk.
        
        Args:
            analysis_type: Type of analysis
            results: Analysis results
        """
        # Create results file
        results_path = os.path.join(self.analytics_path, f"{analysis_type}.json")
        
        # Save results
        with open(results_path, "w") as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Saved {analysis_type} results to {results_path}")
    
    def _generate_cost_recommendations(self, cost_metrics: Dict[str, <response clipped><NOTE>To save on context only part of this file has been shown to you. You should retry this tool after you have searched inside the file with `grep -n` in order to find the line numbers of what you are looking for.</NOTE>