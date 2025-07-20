import vlc
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
import random
import os

class PlayerController(QObject):
    """Controls playback and playlist state using VLC."""
    song_ended_signal: pyqtSignal = pyqtSignal()
    length_known_signal: pyqtSignal = pyqtSignal(int)

    def __init__(self) -> None:
        """Initialize the player controller and VLC instance."""
        super().__init__()
        self.vlc_instance = vlc.Instance()
        self.player = self.vlc_instance.media_player_new()
        event_manager = self.player.event_manager()
        event_manager.event_attach(vlc.EventType.MediaPlayerEndReached, self._handle_song_end)
        event_manager.event_attach(vlc.EventType.MediaPlayerLengthChanged, self._on_length_known)
        self.media = None
        self.playlist: list[str] = []
        self.current_index: int = -1
        self.shuffle: bool = False
        self.repeat_mode: str = "off"
        self.duration_ms: int = 0
        self.volume: int = 70

    def set_playlist(self, files: list[str]) -> None:
        """Set the playlist and reset the current index."""
        self.playlist = files
        self.current_index = 0 if files else -1

    def play_song(self, index: int) -> None:
        """Play the song at the given index."""
        if not (0 <= index < len(self.playlist)):
            return
        self.current_index = index
        path = self.playlist[index]
        if self.vlc_instance is not None:
            self.media = self.vlc_instance.media_new(path)
            self.player.set_media(self.media)
            self.player.play()
            self.player.audio_set_volume(self.volume)
            QTimer.singleShot(300, self.check_duration)

    def play(self) -> None:
        """Resume playback."""
        self.player.play()

    def pause(self) -> None:
        """Pause playback."""
        self.player.pause()

    def stop(self) -> None:
        """Stop playback."""
        self.player.stop()

    def is_playing(self) -> bool:
        """Return True if the player is currently playing."""
        return self.player.is_playing()

    def play_next(self) -> None:
        """Play the next song in the playlist, respecting shuffle and repeat."""
        if not self.playlist:
            return
        next_index = random.randint(0, len(self.playlist) - 1) if self.shuffle else self.current_index + 1
        if next_index >= len(self.playlist):
            next_index = 0 if self.repeat_mode == "all" else len(self.playlist) - 1
        self.play_song(next_index)

    def play_previous(self) -> None:
        """Play the previous song in the playlist."""
        if not self.playlist:
            return
        prev_index = self.current_index - 1
        if prev_index < 0:
            prev_index = len(self.playlist) - 1 if self.repeat_mode == "all" else 0
        self.play_song(prev_index)

    def set_shuffle(self, shuffle: bool) -> None:
        """Enable or disable shuffle mode."""
        self.shuffle = shuffle

    def set_repeat_mode(self, mode: str) -> None:
        """Set the repeat mode (off, one, all)."""
        self.repeat_mode = mode

    def set_volume(self, val: int) -> None:
        """Set the playback volume."""
        self.volume = val
        self.player.audio_set_volume(val)

    def seek(self, value: int) -> None:
        """Seek to a position in the current song."""
        if self.duration_ms > 0:
            new_time = value / 1000 * self.duration_ms
            self.player.set_time(int(new_time))

    def check_duration(self, retries: int = 10) -> None:
        """Check the duration of the current song, retrying if necessary."""
        length = self.player.get_length()
        if length > 0:
            self.duration_ms = length
            self.length_known_signal.emit(length)
        elif retries > 0:
            QTimer.singleShot(300, lambda: self.check_duration(retries - 1))
        else:
            self.duration_ms = 0

    def get_time(self) -> int:
        """Get the current playback time in ms."""
        return self.player.get_time()

    def get_length(self) -> int:
        """Get the length of the current song in ms."""
        return self.player.get_length()

    def _handle_song_end(self, event) -> None:
        """Handle the end of a song and emit the signal."""
        self.song_ended_signal.emit()

    def _on_length_known(self, event) -> None:
        """Handle when the song length is known and emit the signal."""
        self.length_known_signal.emit(self.player.get_length())

    def get_current_song_path(self) -> str | None:
        """Get the path of the current song, or None if not available."""
        if 0 <= self.current_index < len(self.playlist):
            return self.playlist[self.current_index]
        return None

    def reorder_playlist(self, new_order: list[str]) -> None:
        """Reorder the playlist to match the new order."""
        self.playlist = new_order 