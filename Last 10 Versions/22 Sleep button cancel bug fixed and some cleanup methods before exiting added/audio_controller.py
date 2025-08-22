# audio_controller.py
import vlc
from PyQt6.QtCore import QObject, pyqtSignal

class AudioController(QObject):
    """Handles all audio playback operations"""
    
    # Signals for communicating with UI
    position_changed = pyqtSignal(int)  # Current position in ms
    length_changed = pyqtSignal(int)    # Track length in ms
    state_changed = pyqtSignal(str)     # 'playing', 'paused', 'stopped'
    volume_changed = pyqtSignal(int)    # Volume level 0-100
    track_ended = pyqtSignal()          # Track finished playing
    
    def __init__(self):
        super().__init__()
        self.vlc_instance = vlc.Instance()
        self.player = self.vlc_instance.media_player_new()
        self.current_file = None
        self._setup_event_manager()
    
    def _setup_event_manager(self):
        """Setup VLC event callbacks"""
        event_manager = self.player.event_manager()
        event_manager.event_attach(vlc.EventType.MediaPlayerTimeChanged, self._on_time_changed)
        event_manager.event_attach(vlc.EventType.MediaPlayerEndReached, self._on_track_ended)
        # Add other event handlers...
    
    def load_file(self, file_path):
        """Load an audio file for playback"""
        try:
            media = self.vlc_instance.media_new(file_path)
            self.player.set_media(media)
            self.current_file = file_path
            return True
        except Exception as e:
            print(f"Error loading file: {e}")
            return False
    
    def play(self):
        """Start or resume playback"""
        if self.player.play() == 0:
            self.state_changed.emit('playing')
            return True
        return False
    
    def pause(self):
        """Pause playback"""
        self.player.pause()
        self.state_changed.emit('paused')
    
    def stop(self):
        """Stop playback"""
        self.player.stop()
        self.state_changed.emit('stopped')
    
    def set_position(self, position_ms):
        """Set playback position in milliseconds"""
        if self.get_length() > 0:
            position = position_ms / self.get_length()
            self.player.set_position(position)
    
    def get_position(self):
        """Get current position in milliseconds"""
        return self.player.get_time()
    
    def get_length(self):
        """Get track length in milliseconds"""
        return self.player.get_length()
    
    def set_volume(self, volume):
        """Set volume (0-100)"""
        self.player.audio_set_volume(volume)
        self.volume_changed.emit(volume)
    
    def get_volume(self):
        """Get current volume (0-100)"""
        return self.player.audio_get_volume()
    
    def is_playing(self):
        """Check if audio is currently playing"""
        return self.player.is_playing()
    
    def _on_time_changed(self, event):
        """Handle VLC time change events"""
        self.position_changed.emit(self.get_position())
    
    def _on_track_ended(self, event):
        """Handle track end events"""
        self.track_ended.emit()
    
    def cleanup(self):
        """Clean up resources"""
        self.stop()
        self.player.release()
        self.vlc_instance.release()

    def cleanup(self):
        """Proper VLC cleanup to prevent callback errors"""
        try:
            if hasattr(self, 'player') and self.player:
                # Stop playback first
                self.player.stop()
                
                # Detach all event callbacks
                event_manager = self.player.event_manager()
                if event_manager:
                    # Remove all callbacks to prevent cleanup errors
                    event_manager.event_detach(vlc.EventType.MediaPlayerEndReached)
                    event_manager.event_detach(vlc.EventType.MediaPlayerTimeChanged)
                    # Add any other events you're listening to
                
                # Release the media player
                self.player.release()
                self.player = None
                
        except Exception as e:
            print(f"VLC cleanup error (non-fatal): {e}")

    def __del__(self):
        """Destructor to ensure cleanup"""
        self.cleanup()

