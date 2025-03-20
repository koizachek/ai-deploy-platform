"""
Model repository for storing and retrieving AI models.
This module provides functionality for managing model storage and retrieval.
"""

import json
import os
import shutil
from typing import Dict, List, Optional, Union

from core.models import Model, OptimizedModel


class ModelRepository:
    """Repository for storing and retrieving AI models."""
    
    def __init__(self, storage_base_path: str):
        """Initialize the model repository.
        
        Args:
            storage_base_path: Base path for model storage
        """
        self.storage_base_path = storage_base_path
        self.models_path = os.path.join(storage_base_path, "models")
        self.optimized_models_path = os.path.join(storage_base_path, "optimized_models")
        self.metadata_path = os.path.join(storage_base_path, "metadata")
        
        # Create directories if they don't exist
        os.makedirs(self.models_path, exist_ok=True)
        os.makedirs(self.optimized_models_path, exist_ok=True)
        os.makedirs(self.metadata_path, exist_ok=True)
    
    def save_model(self, model: Model, model_file_path: str) -> Model:
        """Save a model to the repository.
        
        Args:
            model: Model to save
            model_file_path: Path to the model file
            
        Returns:
            Updated model with storage path
        """
        # Create model directory
        model_dir = os.path.join(self.models_path, model.id)
        os.makedirs(model_dir, exist_ok=True)
        
        # Copy model file to repository
        model_filename = os.path.basename(model_file_path)
        model_storage_path = os.path.join(model_dir, model_filename)
        shutil.copy2(model_file_path, model_storage_path)
        
        # Update model with storage path
        model.storage_path = model_storage_path
        model.metadata["file_size"] = os.path.getsize(model_storage_path)
        
        # Save model metadata
        self._save_model_metadata(model)
        
        return model
    
    def save_optimized_model(self, optimized_model: OptimizedModel, model_file_path: str) -> OptimizedModel:
        """Save an optimized model to the repository.
        
        Args:
            optimized_model: Optimized model to save
            model_file_path: Path to the optimized model file
            
        Returns:
            Updated optimized model with storage path
        """
        # Create optimized model directory
        optimized_model_dir = os.path.join(self.optimized_models_path, optimized_model.id)
        os.makedirs(optimized_model_dir, exist_ok=True)
        
        # Copy model file to repository
        model_filename = os.path.basename(model_file_path)
        model_storage_path = os.path.join(optimized_model_dir, model_filename)
        shutil.copy2(model_file_path, model_storage_path)
        
        # Update optimized model with storage path
        optimized_model.storage_path = model_storage_path
        optimized_model.metadata["file_size"] = os.path.getsize(model_storage_path)
        
        # Save optimized model metadata
        self._save_optimized_model_metadata(optimized_model)
        
        return optimized_model
    
    def get_model(self, model_id: str) -> Optional[Model]:
        """Get a model from the repository.
        
        Args:
            model_id: ID of the model to retrieve
            
        Returns:
            Model if found, None otherwise
        """
        metadata_path = os.path.join(self.metadata_path, f"model_{model_id}.json")
        if not os.path.exists(metadata_path):
            return None
        
        with open(metadata_path, "r") as f:
            model_data = json.load(f)
        
        return Model.from_dict(model_data)
    
    def get_optimized_model(self, optimized_model_id: str, original_model: Model) -> Optional[OptimizedModel]:
        """Get an optimized model from the repository.
        
        Args:
            optimized_model_id: ID of the optimized model to retrieve
            original_model: Original model
            
        Returns:
            OptimizedModel if found, None otherwise
        """
        metadata_path = os.path.join(self.metadata_path, f"optimized_model_{optimized_model_id}.json")
        if not os.path.exists(metadata_path):
            return None
        
        with open(metadata_path, "r") as f:
            optimized_model_data = json.load(f)
        
        return OptimizedModel.from_dict(optimized_model_data, original_model)
    
    def list_models(self) -> List[Model]:
        """List all models in the repository.
        
        Returns:
            List of models
        """
        models = []
        for filename in os.listdir(self.metadata_path):
            if filename.startswith("model_") and filename.endswith(".json"):
                model_id = filename[6:-5]  # Remove "model_" prefix and ".json" suffix
                model = self.get_model(model_id)
                if model:
                    models.append(model)
        return models
    
    def list_optimized_models(self, original_model: Model) -> List[OptimizedModel]:
        """List all optimized models for a given original model.
        
        Args:
            original_model: Original model
            
        Returns:
            List of optimized models
        """
        optimized_models = []
        for filename in os.listdir(self.metadata_path):
            if filename.startswith("optimized_model_") and filename.endswith(".json"):
                optimized_model_id = filename[16:-5]  # Remove "optimized_model_" prefix and ".json" suffix
                with open(os.path.join(self.metadata_path, filename), "r") as f:
                    optimized_model_data = json.load(f)
                
                if optimized_model_data["original_model_id"] == original_model.id:
                    optimized_model = OptimizedModel.from_dict(optimized_model_data, original_model)
                    optimized_models.append(optimized_model)
        
        return optimized_models
    
    def delete_model(self, model_id: str) -> bool:
        """Delete a model from the repository.
        
        Args:
            model_id: ID of the model to delete
            
        Returns:
            True if model was deleted, False otherwise
        """
        model = self.get_model(model_id)
        if not model:
            return False
        
        # Delete model directory
        model_dir = os.path.join(self.models_path, model_id)
        if os.path.exists(model_dir):
            shutil.rmtree(model_dir)
        
        # Delete model metadata
        metadata_path = os.path.join(self.metadata_path, f"model_{model_id}.json")
        if os.path.exists(metadata_path):
            os.remove(metadata_path)
        
        # Delete associated optimized models
        for filename in os.listdir(self.metadata_path):
            if filename.startswith("optimized_model_") and filename.endswith(".json"):
                with open(os.path.join(self.metadata_path, filename), "r") as f:
                    optimized_model_data = json.load(f)
                
                if optimized_model_data["original_model_id"] == model_id:
                    optimized_model_id = filename[16:-5]
                    self.delete_optimized_model(optimized_model_id)
        
        return True
    
    def delete_optimized_model(self, optimized_model_id: str) -> bool:
        """Delete an optimized model from the repository.
        
        Args:
            optimized_model_id: ID of the optimized model to delete
            
        Returns:
            True if optimized model was deleted, False otherwise
        """
        # Delete optimized model directory
        optimized_model_dir = os.path.join(self.optimized_models_path, optimized_model_id)
        if os.path.exists(optimized_model_dir):
            shutil.rmtree(optimized_model_dir)
        
        # Delete optimized model metadata
        metadata_path = os.path.join(self.metadata_path, f"optimized_model_{optimized_model_id}.json")
        if os.path.exists(metadata_path):
            os.remove(metadata_path)
            return True
        
        return False
    
    def _save_model_metadata(self, model: Model) -> None:
        """Save model metadata to disk.
        
        Args:
            model: Model to save metadata for
        """
        metadata_path = os.path.join(self.metadata_path, f"model_{model.id}.json")
        with open(metadata_path, "w") as f:
            json.dump(model.to_dict(), f, indent=2)
    
    def _save_optimized_model_metadata(self, optimized_model: OptimizedModel) -> None:
        """Save optimized model metadata to disk.
        
        Args:
            optimized_model: Optimized model to save metadata for
        """
        metadata_path = os.path.join(self.metadata_path, f"optimized_model_{optimized_model.id}.json")
        with open(metadata_path, "w") as f:
            json.dump(optimized_model.to_dict(), f, indent=2)
