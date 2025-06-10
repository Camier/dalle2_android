"""
Offline mode functionality for DALL-E Android app
"""

import json
from typing import Dict, Any, List, Optional
from pathlib import Path
import time
import threading
import queue

class OfflineModeManager:
    """Manage offline functionality and sync"""
    
    def __init__(self, cache_dir: str = "offline_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        self.pending_requests_file = self.cache_dir / "pending_requests.json"
        self.offline_queue = queue.Queue()
        self.is_offline = False
        
        self._load_pending_requests()
        self._start_connectivity_monitor()
        
    def _load_pending_requests(self):
        """Load pending requests from disk"""
        if self.pending_requests_file.exists():
            try:
                with open(self.pending_requests_file, 'r') as f:
                    pending = json.load(f)
                    for request in pending:
                        self.offline_queue.put(request)
            except:
                pass
    
    def _save_pending_requests(self):
        """Save pending requests to disk"""
        pending = []
        temp_queue = queue.Queue()
        
        # Extract all items from queue
        while not self.offline_queue.empty():
            try:
                item = self.offline_queue.get_nowait()
                pending.append(item)
                temp_queue.put(item)
            except queue.Empty:
                break
        
        # Restore queue
        while not temp_queue.empty():
            self.offline_queue.put(temp_queue.get())
        
        # Save to disk
        with open(self.pending_requests_file, 'w') as f:
            json.dump(pending, f, indent=2)
    
    def _start_connectivity_monitor(self):
        """Monitor network connectivity"""
        def monitor():
            while True:
                # Check connectivity
                was_offline = self.is_offline
                self.is_offline = not self._check_connectivity()
                
                # Handle state change
                if was_offline and not self.is_offline:
                    # Back online - process pending requests
                    self._process_pending_requests()
                
                time.sleep(5)  # Check every 5 seconds
        
        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()
    
    def _check_connectivity(self) -> bool:
        """Check if we have internet connectivity"""
        import socket
        try:
            # Try to connect to OpenAI
            socket.create_connection(("api.openai.com", 443), timeout=3)
            return True
        except:
            return False
    
    def queue_request(self, request_data: Dict[str, Any]):
        """Queue a request for later processing"""
        request_data['queued_at'] = time.time()
        self.offline_queue.put(request_data)
        self._save_pending_requests()
    
    def _process_pending_requests(self):
        """Process pending requests when back online"""
        processed = []
        
        while not self.offline_queue.empty():
            try:
                request = self.offline_queue.get_nowait()
                
                # Process request (placeholder - would call actual API)
                print(f"Processing offline request: {request.get('prompt', '')[:50]}...")
                processed.append(request)
                
            except queue.Empty:
                break
            except Exception as e:
                print(f"Failed to process offline request: {e}")
                # Re-queue failed request
                self.offline_queue.put(request)
        
        # Clear processed requests from disk
        self._save_pending_requests()
        
        return processed
    
    def get_offline_features(self) -> Dict[str, bool]:
        """Get available offline features"""
        return {
            "view_history": True,
            "edit_prompts": True,
            "manage_styles": True,
            "queue_requests": True,
            "generate_images": False,
            "share_online": False
        }
    
    def can_use_feature(self, feature: str) -> bool:
        """Check if a feature is available offline"""
        if not self.is_offline:
            return True
        
        offline_features = self.get_offline_features()
        return offline_features.get(feature, False)

class LocalHistoryManager:
    """Manage local history of generated images"""
    
    def __init__(self, history_dir: str = "generation_history"):
        self.history_dir = Path(history_dir)
        self.history_dir.mkdir(exist_ok=True)
        
        self.history_file = self.history_dir / "history.json"
        self.history = self._load_history()
        
    def _load_history(self) -> List[Dict[str, Any]]:
        """Load history from disk"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return []
    
    def add_generation(self, prompt: str, image_path: str, metadata: Dict[str, Any]):
        """Add a generation to history"""
        entry = {
            "id": str(time.time()),
            "timestamp": time.time(),
            "prompt": prompt,
            "image_path": image_path,
            "metadata": metadata,
            "favorite": False,
            "tags": []
        }
        
        self.history.append(entry)
        self._save_history()
        
        return entry["id"]
    
    def _save_history(self):
        """Save history to disk"""
        # Keep only last 1000 entries
        if len(self.history) > 1000:
            self.history = self.history[-1000:]
        
        with open(self.history_file, 'w') as f:
            json.dump(self.history, f, indent=2)
    
    def get_history(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Get generation history"""
        # Return in reverse chronological order
        return self.history[::-1][offset:offset + limit]
    
    def search_history(self, query: str) -> List[Dict[str, Any]]:
        """Search history by prompt"""
        query_lower = query.lower()
        results = []
        
        for entry in self.history:
            if query_lower in entry["prompt"].lower():
                results.append(entry)
        
        return results[::-1]  # Reverse chronological
    
    def toggle_favorite(self, generation_id: str) -> bool:
        """Toggle favorite status"""
        for entry in self.history:
            if entry["id"] == generation_id:
                entry["favorite"] = not entry["favorite"]
                self._save_history()
                return entry["favorite"]
        
        return False
    
    def add_tags(self, generation_id: str, tags: List[str]):
        """Add tags to a generation"""
        for entry in self.history:
            if entry["id"] == generation_id:
                entry["tags"] = list(set(entry.get("tags", []) + tags))
                self._save_history()
                break
    
    def get_favorites(self) -> List[Dict[str, Any]]:
        """Get all favorited generations"""
        return [entry for entry in self.history if entry.get("favorite", False)][::-1]
    
    def delete_generation(self, generation_id: str) -> bool:
        """Delete a generation from history"""
        for i, entry in enumerate(self.history):
            if entry["id"] == generation_id:
                # Delete image file if exists
                image_path = Path(entry["image_path"])
                if image_path.exists():
                    image_path.unlink()
                
                # Remove from history
                del self.history[i]
                self._save_history()
                return True
        
        return False
