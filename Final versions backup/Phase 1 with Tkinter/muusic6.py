import tkinter as tk
from tkinter import filedialog
import vlc
import os
import random
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC
from mutagen.easyid3 import EasyID3
from PIL import Image, ImageTk
import io

class MinimalMusicPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("Spotify-like Music Player")
        self.root.geometry("850x620")
        self.root.configure(bg="#121212")

        self.player = vlc.Instance().media_player_new()
        self.media = None

        self.playlist = []
        self.current_index = -1
        self.shuffle = False
        self.repeat_mode = "off"
        self.duration_ms = 0
        self.duration_str = "00:00"

        self.album_original_image = None
        self.album_art_image = None

        self.create_ui()
        self.player.event_manager().event_attach(vlc.EventType.MediaPlayerEndReached, self.song_finished)
        self.update_seek_bar()

    def create_ui(self):
        self.top_bar = tk.Frame(self.root, height=50, bg="#181818")
        self.top_bar.pack(side="top", fill="x")
        tk.Label(self.top_bar, text="Spotify-like Player", fg="white", bg="#181818", font=("Segoe UI", 14, "bold")).pack(pady=10)

        self.sidebar = tk.Frame(self.root, width=200, bg="#000000")
        self.sidebar.pack(side="left", fill="y")

        self.load_btn = tk.Button(self.sidebar, text="Load Songs", command=self.load_songs, bg="#1DB954", fg="black", relief="flat")
        self.load_btn.pack(pady=10, padx=10, fill="x")

        self.shuffle_btn = tk.Button(self.sidebar, text="Shuffle: OFF", command=self.toggle_shuffle, bg="#333333", fg="white", relief="flat")
        self.shuffle_btn.pack(pady=5, padx=10, fill="x")

        self.repeat_btn = tk.Button(self.sidebar, text="Repeat: OFF", command=self.toggle_repeat, bg="#333333", fg="white", relief="flat")
        self.repeat_btn.pack(pady=5, padx=10, fill="x")

        self.listbox = tk.Listbox(self.sidebar, bg="#000000", fg="white", selectbackground="#1DB954", relief="flat", highlightthickness=0)
        self.listbox.pack(fill="both", expand=True, padx=10, pady=10)
        self.listbox.bind("<Double-Button-1>", self.play_selected)

        self.main_area = tk.Frame(self.root, bg="#121212")
        self.main_area.pack(side="left", fill="both", expand=True)

        self.album_art_label = tk.Label(self.main_area, bg="#121212")
        self.album_art_label.pack(pady=10)

        self.song_label = tk.Label(self.main_area, text="No song loaded", fg="white", bg="#121212", font=("Segoe UI", 12))
        self.song_label.pack(pady=5)

        self.meta_label = tk.Label(self.main_area, text="", fg="gray", bg="#121212", font=("Segoe UI", 10))
        self.meta_label.pack(pady=(0, 15))

        self.seek_slider = tk.Scale(self.main_area, from_=0, to=1000, orient="horizontal", bg="#1DB954",
                                    fg="black", troughcolor="#404040", highlightthickness=0, length=400)
        self.seek_slider.pack(pady=10)
        self.seek_slider.bind("<ButtonRelease-1>", self.seek_song)
        self.seek_slider.bind("<Button-1>", self.seek_click)

        self.time_label = tk.Label(self.main_area, text="00:00 / 00:00", fg="gray", bg="#121212")
        self.time_label.pack(pady=(0, 20))

        self.controls = tk.Frame(self.main_area, bg="#121212")
        self.controls.pack(pady=10)

        btn_style = {"bg": "#121212", "fg": "white", "relief": "flat", "font": ("Segoe UI", 12)}

        self.prev_btn = tk.Button(self.controls, text="⏮", command=self.play_previous, **btn_style)
        self.prev_btn.pack(side="left", padx=10)

        self.play_btn = tk.Button(self.controls, text="▶", command=self.play_song, state="disabled", **btn_style)
        self.play_btn.pack(side="left", padx=10)

        self.pause_btn = tk.Button(self.controls, text="⏸", command=self.pause_song, state="disabled", **btn_style)
        self.pause_btn.pack(side="left", padx=10)

        self.stop_btn = tk.Button(self.controls, text="⏹", command=self.stop_song, state="disabled", **btn_style)
        self.stop_btn.pack(side="left", padx=10)

        self.next_btn = tk.Button(self.controls, text="⏭", command=self.play_next, **btn_style)
        self.next_btn.pack(side="left", padx=10)

        self.volume_slider = tk.Scale(self.main_area, from_=0, to=100, orient="horizontal", label="Volume",
                                      bg="#121212", fg="white", troughcolor="#1DB954", highlightthickness=0)
        self.volume_slider.set(70)
        self.volume_slider.pack(pady=20)
        self.volume_slider.config(command=self.change_volume)
        self.volume_slider.bind("<Button-1>", self.volume_click)

    def fade_label(self, label, start=255, end=0, step=-15, delay=30, callback=None):
        def fade(current):
            gray = max(0, min(current, 255))
            color = f"#{gray:02x}{gray:02x}{gray:02x}"
            label.config(fg=color)
            if (step < 0 and current > end) or (step > 0 and current < end):
                self.root.after(delay, lambda: fade(current + step))
            else:
                if callback:
                    callback()
        fade(start)

    def fade_album_art(self, new_image_pil):
        def blend_images(alpha):
            blended = Image.blend(self.album_original_image, new_image_pil, alpha)
            self.album_art_image = ImageTk.PhotoImage(blended)
            self.album_art_label.config(image=self.album_art_image)
            if alpha < 1.0:
                self.root.after(30, lambda: blend_images(alpha + 0.1))
            else:
                self.album_original_image = new_image_pil
        blend_images(0.0)

    def update_song_text(self, text):
        self.song_label.config(text=text)
        self.fade_label(self.song_label, start=50, end=255, step=25)

    def toggle_shuffle(self):
        self.shuffle = not self.shuffle
        if self.shuffle:
            self.shuffle_btn.config(text="Shuffle: ON", bg="#1DB954", fg="black")
        else:
            self.shuffle_btn.config(text="Shuffle: OFF", bg="#333333", fg="white")

    def toggle_repeat(self):
        if self.repeat_mode == "off":
            self.repeat_mode = "one"
        elif self.repeat_mode == "one":
            self.repeat_mode = "all"
        else:
            self.repeat_mode = "off"

        if self.repeat_mode != "off":
            self.repeat_btn.config(text=f"Repeat: {self.repeat_mode.upper()}", bg="#1DB954", fg="black")
        else:
            self.repeat_btn.config(text="Repeat: OFF", bg="#333333", fg="white")

    def load_songs(self):
        files = filedialog.askopenfilenames(filetypes=[("Audio", "*.mp3 *.wav *.flac")])
        if files:
            self.playlist = list(files)
            self.listbox.delete(0, tk.END)
            for file in self.playlist:
                self.listbox.insert(tk.END, os.path.basename(file))
            self.current_index = 0
            self.load_song(0)

    def load_song(self, index):
        self.current_index = index
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(index)
        self.listbox.activate(index)
        self.listbox.see(index)

        path = self.playlist[index]
        self.media = vlc.Instance().media_new(path)
        self.player.set_media(self.media)

        self.fade_label(self.song_label, start=255, end=50, step=-25, callback=lambda: self.update_song_text(os.path.basename(path)))
        self.fade_label(self.meta_label, start=255, end=50, step=-25, callback=lambda: self.display_metadata(path))
        self.display_album_art(path)

        self.player.play()
        self.player.audio_set_volume(self.volume_slider.get())
        self.root.after(300, self.check_duration)
        self.play_btn.config(state="normal")
        self.pause_btn.config(state="normal")
        self.stop_btn.config(state="normal")

    def display_metadata(self, file_path):
        try:
            tags = EasyID3(file_path)
            artist = tags.get('artist', ['Unknown Artist'])[0]
            title = tags.get('title', ['Unknown Title'])[0]
            album = tags.get('album', ['Unknown Album'])[0]
            self.meta_label.config(text=f"{artist} — {album} — {title}")
        except Exception:
            self.meta_label.config(text="Metadata not found")
        self.fade_label(self.meta_label, start=50, end=255, step=25)

    def display_album_art(self, file_path):
        try:
            audio = MP3(file_path, ID3=ID3)
            tags = audio.tags
            if tags:
                for key in tags.keys():
                    if key.startswith('APIC'):
                        image_data = tags[key].data
                        image = Image.open(io.BytesIO(image_data)).resize((200, 200), Image.Resampling.LANCZOS)
                        if self.album_original_image is None:
                            self.album_original_image = image
                        self.fade_album_art(image)
                        return
            self.set_default_album_art()
        except Exception as e:
            print("Album Art Error:", e)
            self.set_default_album_art()

    def set_default_album_art(self):
        try:
            image = Image.open('icons/default_art.png').resize((200, 200), Image.Resampling.LANCZOS)
            if self.album_original_image is None:
                self.album_original_image = image
            self.fade_album_art(image)
        except Exception:
            self.album_art_label.config(image='', text='No Album Art', fg='gray')

    def play_song(self):
        self.player.play()

    def pause_song(self):
        self.player.pause()

    def stop_song(self):
        self.player.stop()
        self.seek_slider.set(0)
        self.time_label.config(text=f"00:00 / {self.duration_str}")

    def change_volume(self, val):
        try:
            self.player.audio_set_volume(int(float(val)))
        except:
            pass

    def volume_click(self, event):
        widget = event.widget
        widget_width = widget.winfo_width()
        click_x = event.x
        new_volume = int((click_x / widget_width) * 100)
        new_volume = max(0, min(100, new_volume))
        self.volume_slider.set(new_volume)
        self.player.audio_set_volume(new_volume)

    def seek_song(self, event):
        if self.duration_ms > 0:
            new_time = self.seek_slider.get() / 1000 * self.duration_ms
            self.player.set_time(int(new_time))

    def seek_click(self, event):
        if self.duration_ms > 0:
            widget = event.widget
            widget_width = widget.winfo_width()
            click_fraction = event.x / widget_width
            click_fraction = max(0, min(click_fraction, 1))
            new_time = click_fraction * self.duration_ms
            self.player.set_time(int(new_time))
            self.seek_slider.set(int(click_fraction * 1000))

    def update_seek_bar(self):
        if self.player and self.player.is_playing():
            current_ms = self.player.get_time()
            if current_ms >= 0 and self.duration_ms > 0:
                current_sec = current_ms / 1000
                self.seek_slider.set(int((current_ms / self.duration_ms) * 1000))
                self.time_label.config(text=f"{self.format_time(current_sec)} / {self.duration_str}")
        self.root.after(500, self.update_seek_bar)

    def check_duration(self):
        length = self.player.get_length()
        if length > 0:
            self.duration_ms = length
            self.duration_str = self.format_time(length / 1000)
        else:
            self.root.after(300, self.check_duration)

    def format_time(self, seconds):
        m, s = divmod(int(seconds), 60)
        return f"{m:02}:{s:02}"

    def play_selected(self, event):
        index = self.listbox.nearest(event.y)
        if 0 <= index < len(self.playlist):
            self.load_song(index)

    def play_next(self):
        if not self.playlist:
            return
        if self.shuffle:
            next_index = random.randint(0, len(self.playlist) - 1)
        else:
            next_index = self.current_index + 1
            if next_index >= len(self.playlist):
                next_index = 0 if self.repeat_mode == "all" else len(self.playlist) - 1
        self.load_song(next_index)

    def play_previous(self):
        if not self.playlist:
            return
        prev_index = self.current_index - 1
        if prev_index < 0:
            prev_index = len(self.playlist) - 1 if self.repeat_mode == "all" else 0
        self.load_song(prev_index)

    def song_finished(self, event):
        def next_song():
            if self.repeat_mode == "one":
                self.load_song(self.current_index)
            elif self.shuffle:
                self.load_song(random.randint(0, len(self.playlist) - 1))
            elif self.repeat_mode == "all":
                next_index = self.current_index + 1
                if next_index >= len(self.playlist):
                    next_index = 0
                self.load_song(next_index)
            else:
                next_index = self.current_index + 1
                if next_index < len(self.playlist):
                    self.load_song(next_index)
        self.root.after(100, next_song)

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = MinimalMusicPlayer(root)
        root.mainloop()
    except Exception as e:
        print("Error:", e)
        input("Press Enter to exit...")
