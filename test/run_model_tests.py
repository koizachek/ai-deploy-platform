"""
Test script for running model deployment tests on the AI model deployment platform.
This script tests the deployment of various model types through the platform's interfaces.
"""

import os
import subprocess
import json
import time
import requests
from pathlib import Path

# Configuration
API_URL = "http://localhost:8000"
TEST_MODELS_DIR = "/home/ubuntu/ai-deploy-platform/test/models"
TEST_RESULTS_DIR = "/home/ubuntu/ai-deploy-platform/test/results"

# Ensure results directory exists
os.makedirs(TEST_RESULTS_DIR, exist_ok=True)

def run_command(command):
    """Run a shell command and return the output."""
    print(f"Running command: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Command failed with error: {result.stderr}")
    return result.stdout, result.stderr, result.returncode

def test_pytorch_model_deployment():
    """Test deploying a PyTorch model."""
    print("\n=== Testing PyTorch Model Deployment ===")
    
    # First, create the PyTorch model
    print("Creating PyTorch model...")
    cmd = f"cd {TEST_MODELS_DIR} && python create_pytorch_model.py"
    stdout, stderr, returncode = run_command(cmd)
    
    if returncode != 0:
        print("Failed to create PyTorch model")
        return False
    
    # Check if model files were created
    model_path = os.path.join(TEST_MODELS_DIR, "mnist_cnn.pt")
    script_model_path = os.path.join(TEST_MODELS_DIR, "mnist_cnn_script.pt")
    
    if not os.path.exists(model_path) or not os.path.exists(script_model_path):
        print("PyTorch model files not found")
        return False
    
    print(f"PyTorch model created successfully: {model_path}")
    print(f"TorchScript model created successfully: {script_model_path}")
    
    # Test API deployment
    print("\nTesting API deployment of PyTorch model...")
    
    # Start the API server in the background
    api_process = subprocess.Popen(
        f"cd /home/ubuntu/ai-deploy-platform && python src/api/api.py",
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for API server to start
    print("Waiting for API server to start...")
    time.sleep(5)
    
    try:
        # Upload model via API
        with open(script_model_path, "rb") as f:
            files = {"file": f}
            data = {
                "name": "pytorch-mnist",
                "framework": "pytorch",
                "version": "1.0",
                "metadata": json.dumps({"task": "image_classification", "dataset": "mnist"})
            }
            
            response = requests.post(f"{API_URL}/models", files=files, data=data)
            
            if response.status_code != 200:
                print(f"Failed to upload model: {response.text}")
                return False
            
            model_response = response.json()
            model_id = model_response["model_id"]
            print(f"Model uploaded successfully with ID: {model_id}")
            
            # Create deployment via API
            deployment_data = {
                "name": "pytorch-mnist-deployment",
                "model_id": model_id,
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
                },
                "metadata": {
                    "test": True,
                    "framework": "pytorch"
                }
            }
            
            response = requests.post(f"{API_URL}/deployments", json=deployment_data)
            
            if response.status_code != 200:
                print(f"Failed to create deployment: {response.text}")
                return False
            
            deployment_response = response.json()
            deployment_id = deployment_response["id"]
            print(f"Deployment created successfully with ID: {deployment_id}")
            
            # Wait for deployment to become active
            print("Waiting for deployment to become active...")
            max_retries = 10
            for i in range(max_retries):
                response = requests.get(f"{API_URL}/deployments/{deployment_id}")
                if response.status_code != 200:
                    print(f"Failed to get deployment status: {response.text}")
                    return False
                
                deployment_status = response.json()["status"]
                print(f"Deployment status: {deployment_status}")
                
                if deployment_status == "active":
                    print("Deployment is active!")
                    break
                elif deployment_status == "failed":
                    print("Deployment failed")
                    return False
                
                time.sleep(3)
            
            # Test optimization
            print("\nTesting model optimization...")
            optimization_data = {
                "method": "quantization",
                "target_latency": 10.0,
                "metadata": {
                    "test": True,
                    "precision": "int8"
                }
            }
            
            response = requests.post(f"{API_URL}/models/{model_id}/optimize", json=optimization_data)
            
            if response.status_code != 200:
                print(f"Failed to optimize model: {response.text}")
                return False
            
            optimization_response = response.json()
            optimized_model_id = optimization_response["id"]
            print(f"Model optimization started with ID: {optimized_model_id}")
            
            # Wait for optimization to complete
            print("Waiting for optimization to complete...")
            max_retries = 10
            for i in range(max_retries):
                response = requests.get(f"{API_URL}/models/{model_id}/optimized")
                if response.status_code != 200:
                    print(f"Failed to get optimization status: {response.text}")
                    return False
                
                optimized_models = response.json()
                for opt_model in optimized_models:
                    if opt_model["id"] == optimized_model_id:
                        print(f"Optimization status: {opt_model['status']}")
                        if opt_model["status"] == "completed":
                            print("Optimization completed successfully!")
                            break
                        elif opt_model["status"] == "failed":
                            print("Optimization failed")
                            return False
                
                time.sleep(3)
            
            # Test hibernation
            print("\nTesting deployment hibernation...")
            response = requests.post(f"{API_URL}/deployments/{deployment_id}/hibernate")
            
            if response.status_code != 200:
                print(f"Failed to hibernate deployment: {response.text}")
                return False
            
            print("Deployment hibernated successfully")
            
            # Test activation
            print("\nTesting deployment activation...")
            response = requests.post(f"{API_URL}/deployments/{deployment_id}/activate")
            
            if response.status_code != 200:
                print(f"Failed to activate deployment: {response.text}")
                return False
            
            print("Deployment activated successfully")
            
            # Test analytics
            print("\nTesting analytics endpoints...")
            
            # Cost analysis
            response = requests.get(f"{API_URL}/analytics/cost")
            if response.status_code != 200:
                print(f"Failed to get cost analysis: {response.text}")
                return False
            
            print("Cost analysis retrieved successfully")
            
            # Performance analysis
            response = requests.get(f"{API_URL}/analytics/performance")
            if response.status_code != 200:
                print(f"Failed to get performance analysis: {response.text}")
                return False
            
            print("Performance analysis retrieved successfully")
            
            # Forecast
            response = requests.get(f"{API_URL}/analytics/forecast")
            if response.status_code != 200:
                print(f"Failed to get forecast: {response.text}")
                return False
            
            print("Forecast retrieved successfully")
            
            # Suggestions
            response = requests.get(f"{API_URL}/analytics/suggestions")
            if response.status_code != 200:
                print(f"Failed to get suggestions: {response.text}")
                return False
            
            print("Suggestions retrieved successfully")
            
            # Clean up
            print("\nCleaning up...")
            
            # Delete deployment
            response = requests.delete(f"{API_URL}/deployments/{deployment_id}")
            if response.status_code != 200:
                print(f"Failed to delete deployment: {response.text}")
                return False
            
            print(f"Deployment {deployment_id} deleted successfully")
            
            # Delete model
            response = requests.delete(f"{API_URL}/models/{model_id}")
            if response.status_code != 200:
                print(f"Failed to delete model: {response.text}")
                return False
            
            print(f"Model {model_id} deleted successfully")
            
            print("\nPyTorch model deployment test completed successfully!")
            return True
    
    except Exception as e:
        print(f"Error during API testing: {e}")
        return False
    
    finally:
        # Stop the API server
        api_process.terminate()
        print("API server stopped")

def test_tensorflow_model_deployment():
    """Test deploying a TensorFlow model."""
    print("\n=== Testing TensorFlow Model Deployment ===")
    
    # First, create the TensorFlow model
    print("Creating TensorFlow model...")
    cmd = f"cd {TEST_MODELS_DIR} && python create_tensorflow_model.py"
    stdout, stderr, returncode = run_command(cmd)
    
    if returncode != 0:
        print("Failed to create TensorFlow model")
        return False
    
    # Check if model files were created
    model_path = os.path.join(TEST_MODELS_DIR, "mnist_cnn.h5")
    saved_model_path = os.path.join(TEST_MODELS_DIR, "mnist_cnn_tf")
    tflite_model_path = os.path.join(TEST_MODELS_DIR, "mnist_cnn.tflite")
    
    if not os.path.exists(model_path) or not os.path.exists(saved_model_path) or not os.path.exists(tflite_model_path):
        print("TensorFlow model files not found")
        return False
    
    print(f"TensorFlow H5 model created successfully: {model_path}")
    print(f"TensorFlow SavedModel created successfully: {saved_model_path}")
    print(f"TensorFlow Lite model created successfully: {tflite_model_path}")
    
    # Test CLI deployment
    print("\nTesting CLI deployment of TensorFlow model...")
    
    # Create CLI command to upload model
    upload_cmd = f"cd /home/ubuntu/ai-deploy-platform && python src/ui/cli/aideploy.py models upload --name tensorflow-mnist --framework tensorflow --version 1.0 --file {model_path}"
    stdout, stderr, returncode = run_command(upload_cmd)
    
    if returncode != 0:
        print("Failed to upload model via CLI")
        return False
    
    # Extract model ID from output
    import re
    model_id_match = re.search(r"Model uploaded successfully: ([a-f0-9-]+)", stdout)
    if not model_id_match:
        print("Failed to extract model ID from CLI output")
        return False
    
    model_id = model_id_match.group(1)
    print(f"Model uploaded successfully with ID: {model_id}")
    
    # Create deployment via CLI
    deploy_cmd = f"cd /home/ubuntu/ai-deploy-platform && python src/ui/cli/aideploy.py deployments create --name tensorflow-mnist-deployment --model-id {model_id} --deployment-type kubernetes --cpu 2 --memory 4Gi --min-instances 2 --max-instances 5 --target-cpu 80 --use-spot --enable-hibernation --enable-multi-cloud"
    stdout, stderr, returncode = run_command(deploy_cmd)
    
    if returncode != 0:
        print("Failed to create deployment via CLI")
        return False
    
    # Extract deployment ID from output
    deployment_id_match = re.search(r"Deployment created successfully: ([a-f0-9-]+)", stdout)
    if not deployment_id_match:
        print("Failed to extract deployment ID from CLI output")
        return False
    
    deployment_id = deployment_id_match.group(1)
    print(f"Deployment created successfully with ID: {deployment_id}")
    
    # Wait for deployment to become active
    print("Waiting for deployment to become active...")
    max_retries = 10
    for i in range(max_retries):
        get_cmd = f"cd /home/ubuntu/ai-deploy-platform && python src/ui/cli/aideploy.py deployments get --id {deployment_id}"
        stdout, stderr, returncode = run_command(get_cmd)
        
        if returncode != 0:
            print("Failed to get deployment status via CLI")
            return False
        
        status_match = re.search(r"status: ([a-z]+)", stdout)
        if not status_match:
            print("Failed to extract deployment status from CLI output")
            return False
        
        deployment_status = status_match.group(1)
        print(f"Deployment status: {deployment_status}")
        
        if deployment_status == "active":
            print("Deployment is active!")
            break
        elif deployment_status == "failed":
            print("Deployment failed")
            return False
        
        time.sleep(3)
    
    # Test optimization
    print("\nTesting model optimization...")
    optimize_cmd = f"cd /home/ubuntu/ai-deploy-platform && python src/ui/cli/aideploy.py models optimize --id {model_id} --method quantization --target-latency 15.0"
    stdout, stderr, returncode = run_command(optimize_cmd)
    
    if returncode != 0:
        print("Failed to optimize model via CLI")
        return False
    
    print("Model optimization started successfully")
    
    # Test hibernation
    print("\nTesting deployment hibernation...")
    hibernate_cmd = f"cd /home/ubuntu/ai-deploy-platform && python src/ui/cli/aideploy.py deployments hibernate --id {deployment_id}"
    stdout, stderr, returncode = run_command(hibernate_cmd)
    
    if returncode != 0:
        print("Failed to hibernate deployment via CLI")
        return False
    
    print("Deployment hibernated successfully")
    
    # Test activation
    print("\nTesting deployment activation...")
    activate_cmd = f"cd /home/ubuntu/ai-deploy-platform && python src/ui/cli/aideploy.py deployments activate --id {deployment_id}"
    stdout, stderr, returncode = run_command(activate_cmd)
    
    if returncode != 0:
        print("Failed to activate deployment via CLI")
        return False
    
    print("Deployment activated successfully")
    
    # Test analytics
    print("\nTesting analytics via CLI...")
    
    # Cost analysis
    cost_cmd = f"cd /home/ubuntu/ai-deploy-platform && python s<response clipped><NOTE>To save on context only part of this file has been shown to you. You should retry this tool after you have searched inside the file with `grep -n` in order to find the line numbers of what you are looking for.</NOTE>