from PyQt6.QtCore import QObject, QThread, pyqtSignal, QMutex, QMutexLocker
from typing import Dict, Any, List
import os
import mutagen


class MetadataWorker(QObject):
    metadata_ready = pyqtSignal(str, dict)  # filepath, metadata
    error_occurred = pyqtSignal(str, str)   # filepath, error
    finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._queue: List[str] = []
        self._cancelled = False
        self._mutex = QMutex()

    def add_file(self, filepath: str):
        with QMutexLocker(self._mutex):
            if filepath and os.path.exists(filepath) and filepath not in self._queue:
                self._queue.append(filepath)

    def cancel(self):
        with QMutexLocker(self._mutex):
            self._cancelled = True
            self._queue.clear()

    def process(self):
        while True:
            if self._cancelled:
                break

            filepath = None
            with QMutexLocker(self._mutex):
                if self._queue:
                    filepath = self._queue.pop(0)

            if filepath is None:
                break

            try:
                data = self._extract_metadata(filepath)
                if not self._cancelled:
                    self.metadata_ready.emit(filepath, data)
            except Exception as e:
                if not self._cancelled:
                    self.error_occurred.emit(filepath, str(e))

        self.finished.emit()

    def _extract_metadata(self, filepath: str) -> Dict[str, Any]:
        audio = mutagen.File(filepath)
        if audio is None:
            raise ValueError("Unsupported or unreadable file")

        info = getattr(audio, "info", None)
        md = {
            "title": "",
            "artist": "",
            "album": "",
            "duration": int(getattr(info, "length", 0) or 0),
        }

        tags = audio.tags or {}

        def first(*keys):
            for k in keys:
                if k in tags:
                    v = tags[k]
                    if isinstance(v, list) and v:
                        return str(v[0])
                    return str(v)
            return ""

        md["title"] = first("TIT2", "TITLE", "\xa9nam")
        md["artist"] = first("TPE1", "ARTIST", "\xa9ART")
        md["album"] = first("TALB", "ALBUM", "\xa9alb")

        return md


class MetadataManager:
    def __init__(self, parent=None):
        self.parent = parent
        self.thread: QThread | None = None
        self.worker: MetadataWorker | None = None

    def _has_live_thread(self) -> bool:
        # Robustly check if the thread exists and is alive without crashing if deleted
        try:
            return bool(self.thread) and self.thread.isRunning()
        except RuntimeError:
            # QThread wrapper likely deleted
            return False

    def start(self):
        # If previous thread died or was deleted, rebuild fresh
        if self._has_live_thread():
            return

        # Clear stale references if any
        self.thread = QThread()
        self.worker = MetadataWorker()
        self.worker.moveToThread(self.thread)

        # Start processing when thread starts
        self.thread.started.connect(self.worker.process)

        # Cleanup connections
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self._on_thread_finished)

        # Connect worker -> UI (slots on the GUI thread)
        if self.parent:
            self.worker.metadata_ready.connect(self.parent.on_metadata_ready)
            self.worker.error_occurred.connect(self.parent.on_metadata_error)

        self.thread.start()

    def _on_thread_finished(self):
        # Called in the GUI thread when the thread stops
        try:
            if self.thread:
                self.thread.deleteLater()
        except RuntimeError:
            pass
        # Important: drop references so future .add_file() will recreate fresh thread
        self.thread = None
        self.worker = None

    def add_file(self, filepath: str):
        # Ensure a live thread/worker exists
        if not self._has_live_thread():
            self.start()

        # After start, worker/thread should exist; guard in case start failed
        if self.worker:
            self.worker.add_file(filepath)

    def cleanup(self):
        # Graceful shutdown; safe to call multiple times
        try:
            if self.worker:
                self.worker.cancel()
        except RuntimeError:
            pass
        try:
            if self.thread:
                self.thread.quit()
                self.thread.wait(3000)
        except RuntimeError:
            pass
        # Drop references to avoid stale pointers
        self.worker = None
        self.thread = None

