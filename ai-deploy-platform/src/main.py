"""
Main application entry point for the AI model deployment platform.
This module initializes and starts the platform services.
"""

import argparse
import logging
import os
import sys

from api.api import app
from core.deployment import DeploymentService
from core.repository import ModelRepository
from infrastructure.kubernetes import KubernetesDeployer
from infrastructure.serverless import ServerlessDeployer
from optimization.optimization import OptimizationService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("ai-deploy-platform.log"),
    ],
)

logger = logging.getLogger(__name__)


def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description="AI Deploy Platform")
    parser.add_argument(
        "--storage-path",
        type=str,
        default="/tmp/ai-deploy-platform",
        help="Base path for model storage",
    )
    parser.add_argument(
        "--provider",
        type=str,
        default="aws",
        choices=["aws", "gcp", "azure"],
        help="Cloud provider for serverless deployments",
    )
    parser.add_argument(
        "--region", type=str, default="us-east-1", help="Cloud region for serverless deployments"
    )
    parser.add_argument(
        "--k8s-namespace",
        type=str,
        default="ai-deploy-platform",
        help="Kubernetes namespace for deployments",
    )
    parser.add_argument(
        "--k8s-config",
        type=str,
        default=None,
        help="Path to Kubernetes configuration file",
    )
    parser.add_argument(
        "--registry-url",
        type=str,
        default="localhost:5000",
        help="Container registry URL",
    )
    parser.add_argument(
        "--host", type=str, default="0.0.0.0", help="Host to bind the API server to"
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="Port to bind the API server to"
    )
    
    args = parser.parse_args()
    
    # Create storage directory if it doesn't exist
    os.makedirs(args.storage_path, exist_ok=True)
    
    # Initialize services
    logger.info("Initializing AI Deploy Platform services")
    
    # Initialize model repository
    model_repository = ModelRepository(storage_base_path=args.storage_path)
    logger.info(f"Initialized model repository at {args.storage_path}")
    
    # Initialize Kubernetes deployer
    kubernetes_deployer = KubernetesDeployer(
        namespace=args.k8s_namespace,
        registry_url=args.registry_url,
        config_path=args.k8s_config,
    )
    logger.info(f"Initialized Kubernetes deployer for namespace {args.k8s_namespace}")
    
    # Initialize serverless deployer
    serverless_deployer = ServerlessDeployer(
        provider=args.provider,
        region=args.region,
    )
    logger.info(f"Initialized serverless deployer for provider {args.provider} in region {args.region}")
    
    # Initialize deployment service
    deployment_service = DeploymentService(
        model_repository=model_repository,
        kubernetes_deployer=kubernetes_deployer,
        serverless_deployer=serverless_deployer,
    )
    logger.info("Initialized deployment service")
    
    # Initialize optimization service
    optimization_service = OptimizationService(model_repository=model_repository)
    logger.info("Initialized optimization service")
    
    # Start API server
    logger.info(f"Starting API server on {args.host}:{args.port}")
    import uvicorn
    
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
