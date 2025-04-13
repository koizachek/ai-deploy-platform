# AI Deploy Platform - API Reference

This document provides a comprehensive reference for the AI Deploy Platform API.

## Base URL

```
https://api.aideploy.example.com
```

## Authentication

All API requests require authentication using a bearer token.

```
Authorization: Bearer <your_token>
```

To obtain a token, make a POST request to `/auth/token` with your credentials:

```
POST /auth/token
Content-Type: application/json

{
  "username": "your-username",
  "password": "your-password"
}
```

Response:

```json
{
  "token": "your-token",
  "expires_at": "2025-04-20T18:00:00Z"
}
```

## Models

### List Models

```
GET /models
```

Response:

```json
[
  {
    "id": "model-id-1",
    "name": "model-name-1",
    "framework": "pytorch",
    "version": "1.0",
    "storage_path": "/path/to/model",
    "created_at": "2025-03-20T18:00:00Z",
    "updated_at": "2025-03-20T18:00:00Z",
    "metadata": {}
  },
  {
    "id": "model-id-2",
    "name": "model-name-2",
    "framework": "tensorflow",
    "version": "1.0",
    "storage_path": "/path/to/model",
    "created_at": "2025-03-20T18:00:00Z",
    "updated_at": "2025-03-20T18:00:00Z",
    "metadata": {}
  }
]
```

### Get Model

```
GET /models/{model_id}
```

Response:

```json
{
  "id": "model-id",
  "name": "model-name",
  "framework": "pytorch",
  "version": "1.0",
  "storage_path": "/path/to/model",
  "created_at": "2025-03-20T18:00:00Z",
  "updated_at": "2025-03-20T18:00:00Z",
  "metadata": {}
}
```

### Upload Model

```
POST /models
Content-Type: multipart/form-data

name: model-name
framework: pytorch
version: 1.0
file: <file>
metadata: {"key": "value"}
```

Response:

```json
{
  "model_id": "model-id",
  "name": "model-name",
  "framework": "pytorch",
  "version": "1.0",
  "storage_path": "/path/to/model",
  "created_at": "2025-03-20T18:00:00Z"
}
```

### Delete Model

```
DELETE /models/{model_id}
```

Response:

```json
{
  "message": "Model model-id deleted successfully"
}
```

### Optimize Model

```
POST /models/{model_id}/optimize
Content-Type: application/json

{
  "method": "quantization",
  "target_size": "10MB",
  "target_latency": 10.0,
  "metadata": {
    "precision": "int8"
  }
}
```

Response:

```json
{
  "id": "optimized-model-id",
  "original_model_id": "model-id",
  "optimization_method": "quantization",
  "status": "optimizing",
  "created_at": "2025-03-20T18:00:00Z"
}
```

### List Optimized Models

```
GET /models/{model_id}/optimized
```

Response:

```json
[
  {
    "id": "optimized-model-id-1",
    "original_model_id": "model-id",
    "optimization_method": "quantization",
    "status": "completed",
    "storage_path": "/path/to/optimized/model",
    "size_reduction_percentage": 50.0,
    "latency_reduction_percentage": 30.0,
    "accuracy_change_percentage": -2.0,
    "created_at": "2025-03-20T18:00:00Z",
    "updated_at": "2025-03-20T18:00:00Z",
    "metadata": {
      "precision": "int8"
    }
  },
  {
    "id": "optimized-model-id-2",
    "original_model_id": "model-id",
    "optimization_method": "pruning",
    "status": "completed",
    "storage_path": "/path/to/optimized/model",
    "size_reduction_percentage": 40.0,
    "latency_reduction_percentage": 20.0,
    "accuracy_change_percentage": -1.0,
    "created_at": "2025-03-20T18:00:00Z",
    "updated_at": "2025-03-20T18:00:00Z",
    "metadata": {
      "sparsity": 0.5
    }
  }
]
```

## Deployments

### List Deployments

```
GET /deployments
```

Response:

```json
[
  {
    "id": "deployment-id-1",
    "name": "deployment-name-1",
    "model_id": "model-id-1",
    "model_type": "original",
    "deployment_type": "serverless",
    "status": "active",
    "endpoint": "https://endpoint-1.example.com",
    "resource_requirements": {
      "cpu": "1",
      "memory": "2Gi",
      "gpu": null,
      "timeout": 30
    },
    "scaling_policy": {
      "min_instances": 1,
      "max_instances": 5,
      "target_cpu_utilization": 70
    },
    "cost_optimization_policy": {
      "use_spot_instances": true,
      "hibernation_enabled": true,
      "hibernation_idle_timeout": 1800,
      "multi_cloud_enabled": true
    },
    "created_at": "2025-03-20T18:00:00Z",
    "updated_at": "2025-03-20T18:00:00Z",
    "metadata": {}
  },
  {
    "id": "deployment-id-2",
    "name": "deployment-name-2",
    "model_id": "model-id-2",
    "model_type": "optimized",
    "deployment_type": "kubernetes",
    "status": "active",
    "endpoint": "https://endpoint-2.example.com",
    "resource_requirements": {
      "cpu": "2",
      "memory": "4Gi",
      "gpu": null,
      "timeout": 60
    },
    "scaling_policy": {
      "min_instances": 2,
      "max_instances": 10,
      "target_cpu_utilization": 80
    },
    "cost_optimization_policy": {
      "use_spot_instances": false,
      "hibernation_enabled": false,
      "hibernation_idle_timeout": 1800,
      "multi_cloud_enabled": false
    },
    "created_at": "2025-03-20T18:00:00Z",
    "updated_at": "2025-03-20T18:00:00Z",
    "metadata": {}
  }
]
```

### Get Deployment

```
GET /deployments/{deployment_id}
```

Response:

```json
{
  "id": "deployment-id",
  "name": "deployment-name",
  "model_id": "model-id",
  "model_type": "original",
  "deployment_type": "serverless",
  "status": "active",
  "endpoint": "https://endpoint.example.com",
  "resource_requirements": {
    "cpu": "1",
    "memory": "2Gi",
    "gpu": null,
    "timeout": 30
  },
  "scaling_policy": {
    "min_instances": 1,
    "max_instances": 5,
    "target_cpu_utilization": 70
  },
  "cost_optimization_policy": {
    "use_spot_instances": true,
    "hibernation_enabled": true,
    "hibernation_idle_timeout": 1800,
    "multi_cloud_enabled": true
  },
  "created_at": "2025-03-20T18:00:00Z",
  "updated_at": "2025-03-20T18:00:00Z",
  "metadata": {}
}
```

### Create Deployment

```
POST /deployments
Content-Type: application/json

{
  "name": "deployment-name",
  "model_id": "model-id",
  "model_type": "original",
  "deployment_type": "serverless",
  "resource_requirements": {
    "cpu": "1",
    "memory": "2Gi",
    "gpu": null,
    "timeout": 30
  },
  "scaling_policy": {
    "min_instances": 1,
    "max_instances": 5,
    "target_cpu_utilization": 70
  },
  "cost_optimization_policy": {
    "use_spot_instances": true,
    "hibernation_enabled": true,
    "hibernation_idle_timeout": 1800,
    "multi_cloud_enabled": true
  },
  "metadata": {}
}
```

Response:

```json
{
  "id": "deployment-id",
  "name": "deployment-name",
  "model_id": "model-id",
  "model_type": "original",
  "deployment_type": "serverless",
  "status": "creating",
  "endpoint": null,
  "resource_requirements": {
    "cpu": "1",
    "memory": "2Gi",
    "gpu": null,
    "timeout": 30
  },
  "scaling_policy": {
    "min_instances": 1,
    "max_instances": 5,
    "target_cpu_utilization": 70
  },
  "cost_optimization_policy": {
    "use_spot_instances": true,
    "hibernation_enabled": true,
    "hibernation_idle_timeout": 1800,
    "multi_cloud_enabled": true
  },
  "created_at": "2025-03-20T18:00:00Z",
  "updated_at": "2025-03-20T18:00:00Z",
  "metadata": {}
}
```

### Update Deployment

```
PUT /deployments/{deployment_id}
Content-Type: application/json

{
  "resource_requirements": {
    "cpu": "2",
    "memory": "4Gi",
    "gpu": null,
    "timeout": 60
  },
  "scaling_policy": {
    "min_instances": 2,
    "max_instances": 10,
    "target_cpu_utilization": 80
  },
  "cost_optimization_policy": {
    "use_spot_instances": false,
    "hibernation_enabled": false,
    "hibernation_idle_timeout": 1800,
    "multi_cloud_enabled": false
  },
  "metadata": {
    "key": "value"
  }
}
```

Response:

```json
{
  "id": "deployment-id",
  "name": "deployment-name",
  "model_id": "model-id",
  "model_type": "original",
  "deployment_type": "serverless",
  "status": "active",
  "endpoint": "https://endpoint.example.com",
  "resource_requirements": {
    "cpu": "2",
    "memory": "4Gi",
    "gpu": null,
    "timeout": 60
  },
  "scaling_policy": {
    "min_instances": 2,
    "max_instances": 10,
    "target_cpu_utilization": 80
  },
  "cost_optimization_policy": {
    "use_spot_instances": false,
    "hibernation_enabled": false,
    "hibernation_idle_timeout": 1800,
    "multi_cloud_enabled": false
  },
  "created_at": "2025-03-20T18:00:00Z",
  "updated_at": "2025-03-20T18:00:00Z",
  "metadata": {
    "key": "value"
  }
}
```

### Delete Deployment

```
DELETE /deployments/{deployment_id}
```

Response:

```json
{
  "message": "Deployment deployment-id deleted successfully"
}
```

### Hibernate Deployment

```
POST /deployments/{deployment_id}/hibernate
```

Response:

```json
{
  "message": "Deployment deployment-id hibernated successfully"
}
```

### Activate Deployment

```
POST /deployments/{deployment_id}/activate
```

Response:

```json
{
  "message": "Deployment deployment-id activated successfully"
}
```

## Analytics

### Cost Analysis

```
GET /analytics/cost
```

Query Parameters:

- `start_time` (optional): Start time for analysis (ISO 8601 format)
- `end_time` (optional): End time for analysis (ISO 8601 format)

Response:

```json
{
  "timestamp": "2025-03-20T18:00:00Z",
  "total_cost": 125.75,
  "cost_breakdown": {
    "compute": 85.25,
    "storage": 25.50,
    "network": 15.00
  },
  "cost_by_type": {
    "kubernetes": 75.50,
    "serverless": 50.25
  },
  "cost_by_deployment": {
    "deployment-id-1": 45.25,
    "deployment-id-2": 35.75,
    "deployment-id-3": 25.50,
    "deployment-id-4": 15.25,
    "deployment-id-5": 4.00
  },
  "comparison": {
    "our_platform": 125.75,
    "aws": 180.25,
    "azure": 175.50,
    "gcp": 165.75,
    "savings_percentage": {
      "aws": 30.25,
      "azure": 28.35,
      "gcp": 24.15
    }
  },
  "recommendations": [
    {
      "type": "high_cost_deployments",
      "message": "Consider optimizing high-cost deployments: deployment-id-1, deployment-id-2",
      "impact": "high"
    },
    {
      "type": "serverless_migration",
      "message": "Consider migrating low-traffic deployments to serverless for cost savings",
      "impact": "medium"
    },
    {
      "type": "spot_instances",
      "message": "Use spot/preemptible instances for non-critical workloads to reduce costs",
      "impact": "high"
    }
  ]
}
```

### Performance Analysis

```
GET /analytics/performance
```

Query Parameters:

- `start_time` (optional): Start time for analysis (ISO 8601 format)
- `end_time` (optional): End time for analysis (ISO 8601 format)

Response:

```json
{
  "timestamp": "2025-03-20T18:00:00Z",
  "total_requests": 125000,
  "avg_latency": 85.5,
  "error_rate": 0.75,
  "performance_by_type": {
    "kubernetes": {
      "requests": 75000,
      "avg_latency": 95.25,
      "error_rate": 0.85
    },
    "serverless": {
      "requests": 50000,
      "avg_latency": 70.50,
      "error_rate": 0.60
    }
  },
  "performance_by_deployment": {
    "deployment-id-1": {
      "requests": 45000,
      "avg_latency": 120.75,
      "error_rate": 0.95
    },
    "deployment-id-2": {
      "requests": 35000,
      "avg_latency": 105.50,
      "error_rate": 0.80
    },
    "deployment-id-3": {
      "requests": 25000,
      "avg_latency": 65.25,
      "error_rate": 0.50
    },
    "deployment-id-4": {
      "requests": 15000,
      "avg_latency": 85.75,
      "error_rate": 0.65
    },
    "deployment-id-5": {
      "requests": 5000,
      "avg_latency": 45.25,
      "error_rate": 0.35
    }
  },
  "recommendations": [
    {
      "type": "high_latency_deployments",
      "message": "Consider optimizing high-latency deployments: deployment-id-1, deployment-id-2",
      "impact": "high"
    },
    {
      "type": "model_optimization",
      "message": "Consider optimizing models using quantization, pruning, or distillation to improve performance",
      "impact": "medium"
    },
    {
      "type": "caching",
      "message": "Implement caching for frequent requests to reduce latency and costs",
      "impact": "medium"
    }
  ],
  "anomalies": {
    "deployment-id-1": [
      {
        "type": "high_error_rate",
        "message": "High error rate detected: 5.5% (threshold: 5%)",
        "timestamp": "2025-03-20T17:45:00Z"
      },
      {
        "type": "high_latency",
        "message": "High latency detected: 1250ms (threshold: 1000ms)",
        "timestamp": "2025-03-20T17:30:00Z"
      }
    ]
  }
}
```

### Usage Forecast

```
GET /analytics/forecast
```

Query Parameters:

- `days` (optional): Number of days to forecast (default: 30)
- `start_time` (optional): Start time for analysis (ISO 8601 format)
- `end_time` (optional): End time for analysis (ISO 8601 format)

Response:

```json
{
  "timestamp": "2025-03-20T18:00:00Z",
  "days": 30,
  "total_requests_forecast": [131250, 137812, 144702, ...],
  "total_cost_forecast": [132.03, 138.63, 145.56, ...],
  "forecast_by_deployment": {
    "deployment-id-1": {
      "deployment_name": "deployment-name-1",
      "current_requests": 45000,
      "current_cost": 45.25,
      "requests_forecast": [47250, 49612, 52092, ...],
      "cost_forecast": [47.51, 49.88, 52.37, ...]
    },
    "deployment-id-2": {
      "deployment_name": "deployment-name-2",
      "current_requests": 35000,
      "current_cost": 35.75,
      "requests_forecast": [36750, 38587, 40516, ...],
      "cost_forecast": [37.53, 39.40, 41.37, ...]
    },
    "deployment-id-3": {
      "deployment_name": "deployment-name-3",
      "current_requests": 25000,
      "current_cost": 25.50,
      "requests_forecast": [26250, 27562, 28940, ...],
      "cost_forecast": [26.77, 28.10, 29.51, ...]
    },
    "deployment-id-4": {
      "deployment_name": "deployment-name-4",
      "current_requests": 15000,
      "current_cost": 15.25,
      "requests_forecast": [15750, 16537, 17364, ...],
      "cost_forecast": [16.01, 16.81, 17.65, ...]
    },
    "deployment-id-5": {
      "deployment_name": "deployment-name-5",
      "current_requests": 5000,
      "current_cost": 4.00,
      "requests_forecast": [5250, 5512, 5788, ...],
      "cost_forecast": [4.20, 4.41, 4.63, ...]
    }
  }
}
```

### Optimization Suggestions

```
GET /analytics/suggestions
```

Response:

```json
{
  "timestamp": "2025-03-20T18:00:00Z",
  "suggestions_by_deployment": {
    "deployment-id-1": {
      "deployment_name": "deployment-name-1",
      "suggestions": [
        {
          "type": "cpu_over_provisioned",
          "message": "CPU is over-provisioned. Average utilization: 25.50%",
          "current_value": "4",
          "recommended_value": "2",
          "impact": "medium"
        },
        {
          "type": "enable_spot_instances",
          "message": "Enable spot/preemptible instances to reduce costs",
          "impact": "high"
        },
        {
          "type": "high_latency",
          "message": "High latency detected. Consider optimizing the model or increasing resources",
          "impact": "high"
        }
      ]
    },
    "deployment-id-2": {
      "deployment_name": "deployment-name-2",
      "suggestions": [
        {
          "type": "memory_over_provisioned",
          "message": "Memory is over-provisioned. Average utilization: 28.75%",
          "current_value": "8Gi",
          "recommended_value": "4Gi",
          "impact": "medium"
        },
        {
          "type": "enable_hibernation",
          "message": "Enable hibernation for inactive deployments to reduce costs",
          "impact": "high"
        }
      ]
    },
    "deployment-id-3": {
      "deployment_name": "deployment-name-3",
      "suggestions": [
        {
          "type": "migrate_to_serverless",
          "message": "Consider migrating to serverless deployment for low-traffic workload",
          "impact": "high"
        }
      ]
    }
  }
}
```

## Error Handling

The API uses standard HTTP status codes to indicate the success or failure of a request:

- `200 OK`: The request was successful
- `400 Bad Request`: The request was invalid
- `401 Unauthorized`: Authentication fai<response clipped><NOTE>To save on context only part of this file has been shown to you. You should retry this tool after you have searched inside the file with `grep -n` in order to find the line numbers of what you are looking for.</NOTE>