# AI Deploy Platform - Developer Guide

This guide is intended for developers who want to extend or integrate with the AI Deploy Platform. It provides detailed information about the platform's architecture, APIs, and development workflows.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Core Components](#core-components)
3. [API Integration](#api-integration)
4. [SDK Usage](#sdk-usage)
5. [Custom Model Optimization](#custom-model-optimization)
6. [Custom Deployers](#custom-deployers)
7. [Contributing](#contributing)

## Architecture Overview

The AI Deploy Platform is built with a modular architecture that separates concerns and allows for extensibility. The high-level components include:

- **Core**: Model and deployment management
- **Infrastructure**: Kubernetes and serverless deployers
- **Optimization**: Model optimization and cost optimization
- **Monitoring**: Metrics collection and analytics
- **API**: RESTful API for platform interaction
- **UI**: Web dashboard and CLI interfaces

![Architecture Diagram](../images/architecture.png)

## Core Components

### Model Repository

The `ModelRepository` class handles model storage, retrieval, and metadata management:

```python
from core.repository import ModelRepository

# Initialize repository
repository = ModelRepository()

# List models
models = repository.list_models()

# Get model by ID
model = repository.get_model("model-id")

# List optimized versions of a model
optimized_models = repository.list_optimized_models(model)
```

### Deployment Service

The `DeploymentService` class manages the lifecycle of model deployments:

```python
from core.deployment import DeploymentService
from core.repository import ModelRepository

# Initialize services
repository = ModelRepository()
deployment_service = DeploymentService(repository)

# List deployments
deployments = deployment_service.list_deployments()

# Get deployment by ID
deployment = deployment_service.get_deployment("deployment-id")

# Create deployment
from core.models import Deployment, DeploymentType, ResourceRequirements, ScalingPolicy, CostOptimizationPolicy
import datetime
import uuid

deployment = Deployment(
    id=str(uuid.uuid4()),
    name="my-deployment",
    model_id="model-id",
    model_type="original",
    deployment_type=DeploymentType.SERVERLESS,
    status=DeploymentStatus.CREATING,
    resource_requirements=ResourceRequirements(
        cpu="1",
        memory="2Gi",
        timeout=30
    ),
    scaling_policy=ScalingPolicy(
        min_instances=1,
        max_instances=5,
        target_cpu_utilization=70
    ),
    cost_optimization_policy=CostOptimizationPolicy(
        use_spot_instances=True,
        hibernation_enabled=True,
        hibernation_idle_timeout=1800,
        multi_cloud_enabled=True
    ),
    created_at=datetime.datetime.utcnow(),
    updated_at=datetime.datetime.utcnow()
)

deployment_service.create_deployment(deployment)
```

## API Integration

### Authentication

The API uses token-based authentication. To authenticate:

```python
import requests

url = "https://api.aideploy.example.com/auth/token"
data = {
    "username": "your-username",
    "password": "your-password"
}

response = requests.post(url, json=data)
token = response.json()["token"]

# Use the token in subsequent requests
headers = {
    "Authorization": f"Bearer {token}"
}
```

### Model Management

```python
import requests

# List models
response = requests.get(
    "https://api.aideploy.example.com/models",
    headers=headers
)
models = response.json()

# Upload model
with open("/path/to/model.pt", "rb") as f:
    files = {"file": f}
    data = {
        "name": "my-model",
        "framework": "pytorch",
        "version": "1.0"
    }
    response = requests.post(
        "https://api.aideploy.example.com/models",
        headers=headers,
        files=files,
        data=data
    )
    model_id = response.json()["model_id"]

# Optimize model
data = {
    "method": "quantization",
    "target_latency": 10.0
}
response = requests.post(
    f"https://api.aideploy.example.com/models/{model_id}/optimize",
    headers=headers,
    json=data
)
optimized_model_id = response.json()["id"]
```

### Deployment Management

```python
import requests

# List deployments
response = requests.get(
    "https://api.aideploy.example.com/deployments",
    headers=headers
)
deployments = response.json()

# Create deployment
data = {
    "name": "my-deployment",
    "model_id": "model-id",
    "model_type": "original",
    "deployment_type": "serverless",
    "resource_requirements": {
        "cpu": "1",
        "memory": "2Gi",
        "timeout": 30
    },
    "scaling_policy": {
        "min_instances": 1,
        "max_instances": 5,
        "target_cpu_utilization": 70
    },
    "cost_optimization_policy": {
        "use_spot_instances": True,
        "hibernation_enabled": True,
        "hibernation_idle_timeout": 1800,
        "multi_cloud_enabled": True
    }
}
response = requests.post(
    "https://api.aideploy.example.com/deployments",
    headers=headers,
    json=data
)
deployment_id = response.json()["id"]

# Hibernate deployment
response = requests.post(
    f"https://api.aideploy.example.com/deployments/{deployment_id}/hibernate",
    headers=headers
)

# Activate deployment
response = requests.post(
    f"https://api.aideploy.example.com/deployments/{deployment_id}/activate",
    headers=headers
)
```

### Analytics

```python
import requests

# Get cost analysis
response = requests.get(
    "https://api.aideploy.example.com/analytics/cost",
    headers=headers
)
cost_analysis = response.json()

# Get performance analysis
response = requests.get(
    "https://api.aideploy.example.com/analytics/performance",
    headers=headers
)
performance_analysis = response.json()

# Get usage forecast
response = requests.get(
    "https://api.aideploy.example.com/analytics/forecast?days=30",
    headers=headers
)
forecast = response.json()

# Get optimization suggestions
response = requests.get(
    "https://api.aideploy.example.com/analytics/suggestions",
    headers=headers
)
suggestions = response.json()
```

## SDK Usage

The AI Deploy Platform provides SDKs for Python, JavaScript, and Go. Here's how to use the Python SDK:

```python
from aideploy import AIDeploy

# Initialize client
client = AIDeploy(api_key="your-api-key")

# Upload model
model = client.models.upload(
    name="my-model",
    framework="pytorch",
    version="1.0",
    file_path="/path/to/model.pt"
)

# Optimize model
optimized_model = client.models.optimize(
    model_id=model.id,
    method="quantization",
    target_latency=10.0
)

# Create deployment
deployment = client.deployments.create(
    name="my-deployment",
    model_id=model.id,
    deployment_type="serverless",
    resource_requirements={
        "cpu": "1",
        "memory": "2Gi",
        "timeout": 30
    },
    scaling_policy={
        "min_instances": 1,
        "max_instances": 5,
        "target_cpu_utilization": 70
    },
    cost_optimization_policy={
        "use_spot_instances": True,
        "hibernation_enabled": True,
        "hibernation_idle_timeout": 1800,
        "multi_cloud_enabled": True
    }
)

# Get deployment endpoint
endpoint = deployment.endpoint

# Make prediction
import requests
import json

data = {
    "inputs": [...]  # Model-specific input format
}
response = requests.post(endpoint, json=data)
prediction = response.json()

# Get cost analysis
cost_analysis = client.analytics.get_cost_analysis()

# Get optimization suggestions
suggestions = client.analytics.get_optimization_suggestions()
```

## Custom Model Optimization

You can extend the platform with custom optimization methods by implementing the `Optimizer` interface:

```python
from optimization.optimization import Optimizer, OptimizationMethod
from core.models import Model, OptimizedModel, OptimizationStatus
import datetime
import uuid

class CustomOptimizer(Optimizer):
    def optimize(self, model: Model, method: OptimizationMethod, **kwargs) -> OptimizedModel:
        # Create optimized model
        optimized_model = OptimizedModel(
            id=str(uuid.uuid4()),
            original_model_id=model.id,
            optimization_method=method,
            status=OptimizationStatus.OPTIMIZING,
            created_at=datetime.datetime.utcnow(),
            updated_at=datetime.datetime.utcnow(),
            metadata=kwargs
        )
        
        try:
            # Implement your custom optimization logic here
            # ...
            
            # Update optimized model
            optimized_model.status = OptimizationStatus.COMPLETED
            optimized_model.storage_path = "/path/to/optimized/model"
            optimized_model.size_reduction_percentage = 50.0
            optimized_model.latency_reduction_percentage = 30.0
            optimized_model.accuracy_change_percentage = -2.0
            optimized_model.updated_at = datetime.datetime.utcnow()
        except Exception as e:
            # Handle optimization failure
            optimized_model.status = OptimizationStatus.FAILED
            optimized_model.metadata["error"] = str(e)
            optimized_model.updated_at = datetime.datetime.utcnow()
        
        return optimized_model
```

Register your custom optimizer:

```python
from optimization.optimization import ModelOptimizer

# Initialize model optimizer
model_optimizer = ModelOptimizer(model_repository)

# Register custom optimizer
model_optimizer.register_optimizer(OptimizationMethod.CUSTOM, CustomOptimizer())
```

## Custom Deployers

You can extend the platform with custom deployers by implementing the `Deployer` interface:

```python
from infrastructure.kubernetes import Deployer
from core.models import Deployment, DeploymentStatus
import datetime

class CustomDeployer(Deployer):
    def deploy(self, deployment: Deployment) -> Deployment:
        try:
            # Implement your custom deployment logic here
            # ...
            
            # Update deployment
            deployment.status = DeploymentStatus.ACTIVE
            deployment.endpoint = "https://custom-endpoint.example.com"
            deployment.updated_at = datetime.datetime.utcnow()
        except Exception as e:
            # Handle deployment failure
            deployment.status = DeploymentStatus.FAILED
            deployment.metadata["error"] = str(e)
            deployment.updated_at = datetime.datetime.utcnow()
        
        return deployment
    
    def undeploy(self, deployment: Deployment) -> Deployment:
        try:
            # Implement your custom undeployment logic here
            # ...
            
            # Update deployment
            deployment.status = DeploymentStatus.DELETED
            deployment.endpoint = None
            deployment.updated_at = datetime.datetime.utcnow()
        except Exception as e:
            # Handle undeployment failure
            deployment.metadata["error"] = str(e)
            deployment.updated_at = datetime.datetime.utcnow()
        
        return deployment
    
    def hibernate(self, deployment: Deployment) -> Deployment:
        try:
            # Implement your custom hibernation logic here
            # ...
            
            # Update deployment
            deployment.status = DeploymentStatus.HIBERNATED
            deployment.updated_at = datetime.datetime.utcnow()
        except Exception as e:
            # Handle hibernation failure
            deployment.metadata["error"] = str(e)
            deployment.updated_at = datetime.datetime.utcnow()
        
        return deployment
    
    def activate(self, deployment: Deployment) -> Deployment:
        try:
            # Implement your custom activation logic here
            # ...
            
            # Update deployment
            deployment.status = DeploymentStatus.ACTIVE
            deployment.updated_at = datetime.datetime.utcnow()
        except Exception as e:
            # Handle activation failure
            deployment.metadata["error"] = str(e)
            deployment.updated_at = datetime.datetime.utcnow()
        
        return deployment
```

Register your custom deployer:

```python
from core.deployment import DeploymentService
from core.models import DeploymentType

# Initialize deployment service
deployment_service = DeploymentService(model_repository)

# Register custom deployer
deployment_service.register_deployer(DeploymentType.CUSTOM, CustomDeployer())
```

## Contributing

We welcome contributions to the AI Deploy Platform! Here's how to get started:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write tests
5. Submit a pull request

### Development Setup

```bash
# Clone the repository
git clone https://github.com/example/ai-deploy-platform.git
cd ai-deploy-platform

# Create a virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run tests
pytest
```

### Coding Standards

We follow PEP 8 for Python code style. Please ensure your code passes the linting checks:

```bash
flake8 src tests
```

### Documentation

Please update the documentation when adding new features or making changes to existing ones. We use Markdown for documentation.
