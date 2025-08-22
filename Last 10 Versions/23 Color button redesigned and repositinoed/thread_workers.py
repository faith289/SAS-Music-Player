import threading
import queue
import time
import os
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Callable, Any, Optional
import weakref
from dataclasses import dataclass
from enum import Enum

class TaskPriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class ThreadTask:
    func: Callable
    args: tuple = ()
    kwargs: dict = None
    callback: Optional[Callable] = None
    priority: TaskPriority = TaskPriority.NORMAL
    task_id: str = None
    
    def __post_init__(self):
        if self.kwargs is None:
            self.kwargs = {}
        if self.task_id is None:
            self.task_id = f"task_{int(time.time() * 1000)}"

class ThreadWorkerManager:
    """Main thread manager for handling all background operations"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.task_queue = queue.PriorityQueue()
        self.active_tasks = {}
        self.is_running = True
        self._start_worker_thread()
    
    def _start_worker_thread(self):
        """Start the main worker thread that processes tasks"""
        self.worker_thread = threading.Thread(target=self._process_tasks, daemon=True)
        self.worker_thread.start()
    
    def _process_tasks(self):
        """Process tasks from the priority queue"""
        while self.is_running:
            try:
                priority, task = self.task_queue.get(timeout=1)
                if task:
                    future = self.executor.submit(self._execute_task, task)
                    self.active_tasks[task.task_id] = future
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error processing task: {e}")
    
    def _execute_task(self, task: ThreadTask):
        """Execute a single task"""
        try:
            result = task.func(*task.args, **task.kwargs)
            if task.callback:
                # Schedule callback on main thread if needed
                task.callback(result)
            return result
        except Exception as e:
            print(f"Task execution error: {e}")
            if task.callback:
                task.callback(None, error=str(e))
        finally:
            # Clean up completed task
            if task.task_id in self.active_tasks:
                del self.active_tasks[task.task_id]
    
    def submit_task(self, task: ThreadTask) -> str:
        """Submit a task to be executed"""
        priority_value = -task.priority.value  # Negative for priority queue (higher priority = lower number)
        self.task_queue.put((priority_value, task))
        return task.task_id
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a task if it hasn't started yet"""
        if task_id in self.active_tasks:
            return self.active_tasks[task_id].cancel()
        return False
    
    def shutdown(self):
        """Shutdown the thread manager"""
        self.is_running = False
        self.executor.shutdown(wait=True)

# Global thread manager instance
thread_manager = ThreadWorkerManager()

# Specific worker classes for different operations

class AudioWorker:
    """Handle audio-related heavy operations"""
    
    @staticmethod
    def load_audio_file(file_path: str, callback: Callable = None):
        """Load audio file in background"""
        def _load_audio():
            try:
                # Simulate heavy audio loading operation
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"Audio file not found: {file_path}")
                
                # Your actual audio loading logic here
                time.sleep(0.1)  # Simulate processing time
                return {"file_path": file_path, "loaded": True}
            except Exception as e:
                return {"error": str(e), "loaded": False}
        
        task = ThreadTask(
            func=_load_audio,
            callback=callback,
            priority=TaskPriority.HIGH,
            task_id=f"audio_load_{os.path.basename(file_path)}"
        )
        return thread_manager.submit_task(task)
    
    @staticmethod
    def process_audio_effects(audio_data: Any, effects: dict, callback: Callable = None):
        """Process audio effects in background"""
        def _process_effects():
            try:
                # Your audio effects processing logic here
                time.sleep(0.2)  # Simulate processing time
                return {"processed": True, "effects_applied": effects}
            except Exception as e:
                return {"error": str(e), "processed": False}
        
        task = ThreadTask(
            func=_process_effects,
            callback=callback,
            priority=TaskPriority.NORMAL
        )
        return thread_manager.submit_task(task)

class BlurWorker:
    """Handle blur effects and image processing operations"""
    
    @staticmethod
    def apply_blur_effect(image_data: Any, blur_radius: int = 5, callback: Callable = None):
        """Apply blur effect to image data in background"""
        def _apply_blur():
            try:
                # Your blur processing logic here
                # Example: PIL Image blur, OpenCV blur, etc.
                time.sleep(0.08)  # Simulate blur processing time
                return {
                    "blurred": True, 
                    "blur_radius": blur_radius,
                    "processed_image": f"blurred_image_r{blur_radius}"
                }
            except Exception as e:
                return {"error": str(e), "blurred": False}
        
        task = ThreadTask(
            func=_apply_blur,
            callback=callback,
            priority=TaskPriority.NORMAL,
            task_id=f"blur_{blur_radius}_{int(time.time() * 1000)}"
        )
        return thread_manager.submit_task(task)
    
    @staticmethod
    def apply_gaussian_blur(image_data: Any, sigma: float = 1.0, callback: Callable = None):
        """Apply Gaussian blur to image data"""
        def _apply_gaussian():
            try:
                # Your Gaussian blur logic here
                time.sleep(0.06)
                return {
                    "gaussian_blurred": True,
                    "sigma": sigma,
                    "processed_image": f"gaussian_blur_s{sigma}"
                }
            except Exception as e:
                return {"error": str(e), "gaussian_blurred": False}
        
        task = ThreadTask(
            func=_apply_gaussian,
            callback=callback,
            priority=TaskPriority.LOW
        )
        return thread_manager.submit_task(task)
    
    @staticmethod
    def apply_motion_blur(image_data: Any, angle: int = 0, distance: int = 10, callback: Callable = None):
        """Apply motion blur effect"""
        def _apply_motion_blur():
            try:
                # Your motion blur logic here
                time.sleep(0.1)
                return {
                    "motion_blurred": True,
                    "angle": angle,
                    "distance": distance,
                    "processed_image": f"motion_blur_a{angle}_d{distance}"
                }
            except Exception as e:
                return {"error": str(e), "motion_blurred": False}
        
        task = ThreadTask(
            func=_apply_motion_blur,
            callback=callback,
            priority=TaskPriority.LOW
        )
        return thread_manager.submit_task(task)

class AlbumArtWorker:
    """Handle album artwork operations"""
    
    @staticmethod
    def load_album_art(file_path: str, size: tuple = (300, 300), callback: Callable = None):
        """Load and resize album artwork in background"""
        def _load_artwork():
            try:
                if not os.path.exists(file_path):
                    # Return default artwork or None
                    return {"artwork": None, "default": True}
                
                # Your image loading and resizing logic here
                # Example: PIL Image operations, artwork extraction from audio files
                time.sleep(0.15)  # Simulate processing time
                return {"artwork": f"processed_{os.path.basename(file_path)}", "size": size}
            except Exception as e:
                return {"error": str(e), "artwork": None}
        
        task = ThreadTask(
            func=_load_artwork,
            callback=callback,
            priority=TaskPriority.NORMAL,
            task_id=f"artwork_{os.path.basename(file_path)}"
        )
        return thread_manager.submit_task(task)
    
    @staticmethod
    def extract_artwork_from_audio(audio_file_path: str, callback: Callable = None):
        """Extract embedded artwork from audio files"""
        def _extract_artwork():
            try:
                # Your artwork extraction logic (mutagen, etc.)
                time.sleep(0.1)
                return {"extracted": True, "has_artwork": True}
            except Exception as e:
                return {"error": str(e), "extracted": False}
        
        task = ThreadTask(
            func=_extract_artwork,
            callback=callback,
            priority=TaskPriority.LOW
        )
        return thread_manager.submit_task(task)

class VisualEffectsWorker:
    """Handle visual effects and animations"""
    
    @staticmethod
    def generate_visualizer_data(audio_data: Any, callback: Callable = None):
        """Generate data for audio visualizer"""
        def _generate_viz_data():
            try:
                # Your FFT/visualization processing here
                import random
                # Simulate heavy computation
                viz_data = [random.randint(0, 100) for _ in range(64)]
                return {"visualizer_data": viz_data, "generated": True}
            except Exception as e:
                return {"error": str(e), "generated": False}
        
        task = ThreadTask(
            func=_generate_viz_data,
            callback=callback,
            priority=TaskPriority.HIGH
        )
        return thread_manager.submit_task(task)
    
    @staticmethod
    def apply_color_effects(image_data: Any, color_scheme: dict, callback: Callable = None):
        """Apply color effects to images"""
        def _apply_effects():
            try:
                # Your color processing logic here
                time.sleep(0.05)
                return {"processed": True, "color_scheme": color_scheme}
            except Exception as e:
                return {"error": str(e), "processed": False}
        
        task = ThreadTask(
            func=_apply_effects,
            callback=callback,
            priority=TaskPriority.LOW
        )
        return thread_manager.submit_task(task)

class FileIOWorker:
    """Handle file I/O operations"""
    
    @staticmethod
    def scan_music_directory(directory_path: str, callback: Callable = None):
        """Scan directory for music files"""
        def _scan_directory():
            try:
                music_files = []
                for root, dirs, files in os.walk(directory_path):
                    for file in files:
                        if file.lower().endswith(('.mp3', '.flac', '.wav', '.m4a', '.ogg')):
                            music_files.append(os.path.join(root, file))
                return {"files": music_files, "count": len(music_files)}
            except Exception as e:
                return {"error": str(e), "files": []}
        
        task = ThreadTask(
            func=_scan_directory,
            callback=callback,
            priority=TaskPriority.NORMAL,
            task_id=f"scan_{directory_path.replace('/', '_')}"
        )
        return thread_manager.submit_task(task)
    
    @staticmethod
    def save_playlist(playlist_data: dict, file_path: str, callback: Callable = None):
        """Save playlist data to file"""
        def _save_playlist():
            try:
                import json
                with open(file_path, 'w') as f:
                    json.dump(playlist_data, f, indent=2)
                return {"saved": True, "file_path": file_path}
            except Exception as e:
                return {"error": str(e), "saved": False}
        
        task = ThreadTask(
            func=_save_playlist,
            callback=callback,
            priority=TaskPriority.LOW
        )
        return thread_manager.submit_task(task)

# Convenience functions for easy integration
def load_audio_async(file_path: str, callback: Callable = None):
    """Convenient function to load audio asynchronously"""
    return AudioWorker.load_audio_file(file_path, callback)

def load_album_art_async(file_path: str, size: tuple = (300, 300), callback: Callable = None):
    """Convenient function to load album art asynchronously"""
    return AlbumArtWorker.load_album_art(file_path, size, callback)

def generate_visualizer_async(audio_data: Any, callback: Callable = None):
    """Convenient function to generate visualizer data asynchronously"""
    return VisualEffectsWorker.generate_visualizer_data(audio_data, callback)

def scan_directory_async(directory_path: str, callback: Callable = None):
    """Convenient function to scan directory asynchronously"""
    return FileIOWorker.scan_music_directory(directory_path, callback)

def apply_blur_async(image_data: Any, blur_radius: int = 5, callback: Callable = None):
    """Convenient function to apply blur asynchronously"""
    return BlurWorker.apply_blur_effect(image_data, blur_radius, callback)

def apply_gaussian_blur_async(image_data: Any, sigma: float = 1.0, callback: Callable = None):
    """Convenient function to apply Gaussian blur asynchronously"""
    return BlurWorker.apply_gaussian_blur(image_data, sigma, callback)



# Cleanup function
def cleanup_threads():
    """Call this when shutting down your application"""
    thread_manager.shutdown()
