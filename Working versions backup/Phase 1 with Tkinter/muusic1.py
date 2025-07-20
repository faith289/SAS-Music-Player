import tkinter as tk
from tkinter import filedialog
import vlc
import os
import threading
import time
import random

class OfflineMusicPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("Offline Music Player - PyVLC")
        self.root.geometry("600x420")
        self.root.resizable(False, False)

        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()
        self.media = None

        self.playlist = []  # List of file paths
        self.current_index = -1
        self.shuffle = False
        self.repeat = False

        # UI Components
        self.song_label = tk.Label(root, text="No file loaded", font=("Arial", 12), wraplength=350)
        self.song_label.pack(pady=10)

        btn_frame = tk.Frame(root)
        btn_frame.pack()

        tk.Button(btn_frame, text="Load Songs", command=self.load_songs).pack(side="left", padx=5)
        self.play_button = tk.Button(btn_frame, text="Play", command=self.play_song, state="disabled")
        self.play_button.pack(side="left", padx=5)
        self.pause_button = tk.Button(btn_frame, text="Pause", command=self.pause_song, state="disabled")
        self.pause_button.pack(side="left", padx=5)
        self.stop_button = tk.Button(btn_frame, text="Stop", command=self.stop_song, state="disabled")
        self.stop_button.pack(side="left", padx=5)

        self.shuffle_button = tk.Button(root, text="Shuffle: OFF", command=self.toggle_shuffle)
        self.shuffle_button.pack(pady=2)

        self.repeat_button = tk.Button(root, text="Repeat: OFF", command=self.toggle_repeat)
        self.repeat_button.pack(pady=2)

        self.volume_label = tk.Label(root, text="Volume")
        self.volume_label.pack()
        self.volume_slider = tk.Scale(root, from_=0, to=100, orient="horizontal", command=self.set_volume)
        self.volume_slider.set(70)
        self.volume_slider.pack()

        self.seek_slider = tk.Scale(root, from_=0, to=1000, orient="horizontal", length=300)
        self.seek_slider.pack(pady=(10, 0))
        self.seek_slider.bind("<ButtonRelease-1>", self.seek_song)

        self.time_label = tk.Label(root, text="00:00 / 00:00")
        self.time_label.pack()

        self.listbox = tk.Listbox(root, width=60)
        self.listbox.pack(pady=5)
        self.listbox.bind("<Double-Button-1>", self.play_selected)

        self.updating_seek = False
        self.duration_ms = 0

        # Event listener for song end
        self.events = self.player.event_manager()
        self.events.event_attach(vlc.EventType.MediaPlayerEndReached, self.song_finished)

    def load_songs(self):
        files = filedialog.askopenfilenames(filetypes=[("Audio files", "*.mp3 *.wav *.flac")])
        if files:
            self.playlist = list(files)
            self.listbox.delete(0, tk.END)
            for file in self.playlist:
                self.listbox.insert(tk.END, os.path.basename(file))
            self.current_index = 0
            self.load_song(self.current_index)

    def load_song(self, index):
        if 0 <= index < len(self.playlist):
            self.current_index = index
            path = self.playlist[index]
            self.media = self.instance.media_new(path)
            self.player.set_media(self.media)
            self.song_label.config(text=os.path.basename(path))
            self.player.play()
            time.sleep(0.5)
            self.player.audio_set_volume(self.volume_slider.get())

            for _ in range(20):
                self.duration_ms = self.player.get_length()
                if self.duration_ms > 0:
                    break
                time.sleep(0.1)

            self.duration_str = self.format_time(self.duration_ms / 1000)

            self.play_button.config(state="normal")
            self.pause_button.config(state="normal")
            self.stop_button.config(state="normal")

            self.updating_seek = True
            threading.Thread(target=self.update_seek_bar, daemon=True).start()

    def play_selected(self, event):
        index = self.listbox.curselection()
        if index:
            self.load_song(index[0])

    def play_song(self):
        self.player.play()

    def pause_song(self):
        self.player.pause()

    def stop_song(self):
        self.player.stop()
        self.seek_slider.set(0)
        self.time_label.config(text=f"00:00 / {self.duration_str}")

    def set_volume(self, val):
        self.player.audio_set_volume(int(val))

    def seek_song(self, event):
        if self.duration_ms > 0:
            target_time = self.seek_slider.get() / 1000 * self.duration_ms
            self.player.set_time(int(target_time))

    def update_seek_bar(self):
        while self.updating_seek:
            if self.player.is_playing():
                current_ms = self.player.get_time()
                if current_ms >= 0 and self.duration_ms > 0:
                    current_sec = current_ms / 1000
                    self.seek_slider.set(int((current_ms / self.duration_ms) * 1000))
                    self.time_label.config(
                        text=f"{self.format_time(current_sec)} / {self.duration_str}"
                    )
            time.sleep(0.5)

    def format_time(self, seconds):
        if seconds < 0:
            return "00:00"
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"

    def toggle_shuffle(self):
        self.shuffle = not self.shuffle
        self.shuffle_button.config(text=f"Shuffle: {'ON' if self.shuffle else 'OFF'}")

    def toggle_repeat(self):
        self.repeat = not self.repeat
        self.repeat_button.config(text=f"Repeat: {'ON' if self.repeat else 'OFF'}")

    def song_finished(self, event):
        # Run this in main thread to avoid crash/hang
        def safe_next_song():
            if self.repeat:
                self.load_song(self.current_index)
            elif self.shuffle:
                next_index = random.randint(0, len(self.playlist) - 1)
                self.load_song(next_index)
            else:
                next_index = self.current_index + 1
                if next_index < len(self.playlist):
                    self.load_song(next_index)

        self.root.after(100, safe_next_song)

if __name__ == "__main__":
    root = tk.Tk()
    app = OfflineMusicPlayer(root)
    root.mainloop()
