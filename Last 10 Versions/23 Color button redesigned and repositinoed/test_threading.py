from thread_workers import (
    load_audio_async, 
    load_album_art_async, 
    scan_directory_async,
    cleanup_threads
)
import time

def test_threading():
    print("Testing threaded operations...")
    
    # Test audio loading
    def audio_callback(result):
        print(f"Audio loaded: {result}")
    
    # Test album art loading
    def art_callback(result):
        print(f"Album art loaded: {result}")
    
    # Test directory scanning
    def scan_callback(result):
        print(f"Directory scan complete: {result.get('count', 0)} files found")
    
    # Submit tasks
    load_audio_async("test.mp3", audio_callback)
    load_album_art_async("test.jpg", (200, 200), art_callback)
    scan_directory_async("./music", scan_callback)
    
    # Wait for completion
    time.sleep(2)
    cleanup_threads()

if __name__ == "__main__":
    test_threading()
