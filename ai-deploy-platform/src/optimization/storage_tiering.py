"""
Storage tiering module for the AI model deployment platform.
This module provides functionality for optimizing storage costs through tiering.
"""

import datetime
import json
import logging
import os
import shutil
from typing import Dict, List, Optional, Tuple

from core.models import Model, OptimizedModel
from core.repository import ModelRepository

logger = logging.getLogger(__name__)


class StorageTiering:
    """Service for optimizing storage costs through tiering."""
    
    def __init__(
        self,
        model_repository: ModelRepository,
        storage_data_path: str = "/tmp/ai-deploy-platform/storage_data",
        hot_storage_path: str = "/tmp/ai-deploy-platform/hot_storage",
        cold_storage_path: str = "/tmp/ai-deploy-platform/cold_storage",
        archive_storage_path: str = "/tmp/ai-deploy-platform/archive_storage",
    ):
        """Initialize the storage tiering service.
        
        Args:
            model_repository: Repository for model storage and retrieval
            storage_data_path: Path to store storage tiering data
            hot_storage_path: Path for frequently accessed models
            cold_storage_path: Path for infrequently accessed models
            archive_storage_path: Path for rarely accessed models
        """
        self.model_repository = model_repository
        self.storage_data_path = storage_data_path
        self.hot_storage_path = hot_storage_path
        self.cold_storage_path = cold_storage_path
        self.archive_storage_path = archive_storage_path
        
        # Create directories if they don't exist
        os.makedirs(storage_data_path, exist_ok=True)
        os.makedirs(hot_storage_path, exist_ok=True)
        os.makedirs(cold_storage_path, exist_ok=True)
        os.makedirs(archive_storage_path, exist_ok=True)
        
        # Initialize access tracking
        self.access_tracking_path = os.path.join(storage_data_path, "access_tracking.json")
        self._init_access_tracking()
    
    def optimize_storage(self) -> Dict[str, Dict]:
        """Optimize storage for all models.
        
        Returns:
            Dictionary mapping model IDs to optimization results
        """
        logger.info("Optimizing storage for all models")
        
        # Get all models
        models = self.model_repository.list_models()
        
        # Optimize storage for each model
        results = {}
        for model in models:
            try:
                result = self.optimize_model_storage(model.id)
                results[model.id] = result
            except Exception as e:
                logger.error(f"Error optimizing storage for model {model.id}: {e}")
                results[model.id] = {"error": str(e)}
            
            # Also optimize storage for optimized versions of the model
            optimized_models = self.model_repository.list_optimized_models(model)
            for optimized_model in optimized_models:
                try:
                    result = self.optimize_optimized_model_storage(optimized_model.id, model)
                    results[f"optimized_{optimized_model.id}"] = result
                except Exception as e:
                    logger.error(f"Error optimizing storage for optimized model {optimized_model.id}: {e}")
                    results[f"optimized_{optimized_model.id}"] = {"error": str(e)}
        
        return results
    
    def optimize_model_storage(self, model_id: str) -> Dict:
        """Optimize storage for a model.
        
        Args:
            model_id: ID of the model to optimize
            
        Returns:
            Optimization results
        """
        logger.info(f"Optimizing storage for model {model_id}")
        
        # Get model
        model = self.model_repository.get_model(model_id)
        if not model:
            raise ValueError(f"Model {model_id} not found")
        
        # Get access pattern
        access_pattern = self._get_access_pattern(model_id)
        
        # Determine appropriate storage tier
        current_tier = self._get_current_storage_tier(model.storage_path)
        target_tier = self._determine_storage_tier(access_pattern)
        
        # If already in the right tier, no action needed
        if current_tier == target_tier:
            return {
                "status": "already_optimized",
                "tier": target_tier,
                "access_pattern": access_pattern,
            }
        
        # Move model to target tier
        new_storage_path = self._move_to_storage_tier(model.storage_path, target_tier)
        
        # Update model storage path
        model.storage_path = new_storage_path
        self.model_repository._save_model_metadata(model)
        
        return {
            "status": "optimized",
            "from_tier": current_tier,
            "to_tier": target_tier,
            "access_pattern": access_pattern,
            "new_storage_path": new_storage_path,
        }
    
    def optimize_optimized_model_storage(self, optimized_model_id: str, original_model: Model) -> Dict:
        """Optimize storage for an optimized model.
        
        Args:
            optimized_model_id: ID of the optimized model to optimize
            original_model: Original model
            
        Returns:
            Optimization results
        """
        logger.info(f"Optimizing storage for optimized model {optimized_model_id}")
        
        # Get optimized model
        optimized_model = self.model_repository.get_optimized_model(optimized_model_id, original_model)
        if not optimized_model:
            raise ValueError(f"Optimized model {optimized_model_id} not found")
        
        # Get access pattern
        access_pattern = self._get_access_pattern(f"optimized_{optimized_model_id}")
        
        # Determine appropriate storage tier
        current_tier = self._get_current_storage_tier(optimized_model.storage_path)
        target_tier = self._determine_storage_tier(access_pattern)
        
        # If already in the right tier, no action needed
        if current_tier == target_tier:
            return {
                "status": "already_optimized",
                "tier": target_tier,
                "access_pattern": access_pattern,
            }
        
        # Move model to target tier
        new_storage_path = self._move_to_storage_tier(optimized_model.storage_path, target_tier)
        
        # Update optimized model storage path
        optimized_model.storage_path = new_storage_path
        self.model_repository._save_optimized_model_metadata(optimized_model)
        
        return {
            "status": "optimized",
            "from_tier": current_tier,
            "to_tier": target_tier,
            "access_pattern": access_pattern,
            "new_storage_path": new_storage_path,
        }
    
    def record_model_access(self, model_id: str, is_optimized: bool = False) -> None:
        """Record an access to a model.
        
        Args:
            model_id: ID of the accessed model
            is_optimized: Whether the model is an optimized model
        """
        # Load access tracking data
        access_data = self._load_access_tracking()
        
        # Get model key
        model_key = f"optimized_{model_id}" if is_optimized else model_id
        
        # Initialize model access data if not exists
        if model_key not in access_data:
            access_data[model_key] = {
                "total_accesses": 0,
                "last_access": None,
                "access_history": [],
            }
        
        # Update access data
        now = datetime.datetime.utcnow().isoformat()
        access_data[model_key]["total_accesses"] += 1
        access_data[model_key]["last_access"] = now
        access_data[model_key]["access_history"].append(now)
        
        # Trim access history to last 100 accesses
        if len(access_data[model_key]["access_history"]) > 100:
            access_data[model_key]["access_history"] = access_data[model_key]["access_history"][-100:]
        
        # Save access tracking data
        self._save_access_tracking(access_data)
    
    def _init_access_tracking(self) -> None:
        """Initialize access tracking data."""
        if not os.path.exists(self.access_tracking_path):
            self._save_access_tracking({})
    
    def _load_access_tracking(self) -> Dict:
        """Load access tracking data.
        
        Returns:
            Access tracking data
        """
        with open(self.access_tracking_path, "r") as f:
            return json.load(f)
    
    def _save_access_tracking(self, access_data: Dict) -> None:
        """Save access tracking data.
        
        Args:
            access_data: Access tracking data
        """
        with open(self.access_tracking_path, "w") as f:
            json.dump(access_data, f, indent=2)
    
    def _get_access_pattern(self, model_key: str) -> str:
        """Get access pattern for a model.
        
        Args:
            model_key: Model key (model ID or "optimized_" + optimized model ID)
            
        Returns:
            Access pattern: "frequent", "infrequent", or "rare"
        """
        # Load access tracking data
        access_data = self._load_access_tracking()
        
        # If no access data, assume rare
        if model_key not in access_data:
            return "rare"
        
        # Get access data
        model_access = access_data[model_key]
        
        # If no accesses, assume rare
        if model_access["total_accesses"] == 0:
            return "rare"
        
        # Check last access time
        last_access = datetime.datetime.fromisoformat(model_access["last_access"])
        now = datetime.datetime.utcnow()
        days_since_last_access = (now - last_access).days
        
        # If not accessed in the last 30 days, consider rare
        if days_since_last_access > 30:
            return "rare"
        
        # If not accessed in the last 7 days, consider infrequent
        if days_since_last_access > 7:
            return "infrequent"
        
        # Check access frequency
        access_history = model_access["access_history"]
        
        # If less than 5 accesses, consider infrequent
        if len(access_history) < 5:
            return "infrequent"
        
        # If more than 10 accesses in the last 7 days, consider frequent
        recent_accesses = 0
        for access_time in access_history:
            access_datetime = datetime.datetime.fromisoformat(access_time)
            if (now - access_datetime).days <= 7:
                recent_accesses += 1
        
        if recent_accesses >= 10:
            return "frequent"
        
        # Default to infrequent
        return "infrequent"
    
    def _get_current_storage_tier(self, storage_path: str) -> str:
        """Get current storage tier for a model.
        
        Args:
            storage_path: Model storage path
            
        Returns:
            Storage tier: "hot", "cold", or "archive"
        """
        if storage_path.startswith(self.hot_storage_path):
            return "hot"
        elif storage_path.startswith(self.cold_storage_path):
            return "cold"
        elif storage_path.startswith(self.archive_storage_path):
            return "archive"
        else:
            # If not in a known tier, assume hot
            return "hot"
    
    def _determine_storage_tier(self, access_pattern: str) -> str:
        """Determine appropriate storage tier based on access pattern.
        
        Args:
            access_pattern: Access pattern: "frequent", "infrequent", or "rare"
            
        Returns:
            Storage tier: "hot", "cold", or "archive"
        """
        if access_pattern == "frequent":
            return "hot"
        elif access_pattern == "infrequent":
            return "cold"
        else:  # "rare"
            return "archive"
    
    def _move_to_storage_tier(self, storage_path: str, target_tier: str) -> str:
        """Move a model to a different storage tier.
        
        Args:
            storage_path: Current model storage path
            target_tier: Target storage tier: "hot", "cold", or "archive"
            
        Returns:
            New storage path
        """
        # Determine target directory
        if target_tier == "hot":
            target_dir = self.hot_storage_path
        elif target_tier == "cold":
            target_dir = self.cold_storage_path
        else:  # "archive"
            target_dir = self.archive_storage_path
        
        # Create target path
        filename = os.path.basename(storage_path)
        new_storage_path = os.path.join(target_dir, filename)
        
        # Move file
        shutil.copy2(storage_path, new_storage_path)
        os.remove(storage_path)
        
        logger.info(f"Moved model from {storage_path} to {new_storage_path}")
        
        return new_storage_path
