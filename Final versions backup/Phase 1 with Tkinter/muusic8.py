import tkinter as tk
from tkinter import filedialog
import vlc
import os
import random
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC
from mutagen.easyid3 import EasyID3
from PIL import Image, ImageTk, ImageDraw, ImageFilter
import io

class MinimalMusicPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("FAiTH Music Player")
        self.root.geometry("850x620")
        self.root.configure(bg="#121212")

        self.vlc_instance = vlc.Instance()
        self.player = self.vlc_instance.media_player_new()
        self.media = None

        self.playlist = []
        self.current_index = -1
        self.shuffle = False
        self.repeat_mode = "off"
        self.duration_ms = 0
        self.duration_str = "00:00"
        self.album_original_image = None
        self.album_art_cache = {}

        self.create_ui()
        self.bg_image_label = tk.Label(self.main_area, bg="#121212")
        self.bg_image_label.place(relx=0.5, rely=0.5, anchor="center")
        self.bg_image_label.lower()

        self.bind_events()
        self.update_seek_bar()

    def bind_events(self):
        self.player.event_manager().event_attach(vlc.EventType.MediaPlayerEndReached, self.song_finished)

    def create_ui(self):
        
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
        if not (0 <= index < len(self.playlist)): return

        self.current_index = index
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(index)
        self.listbox.activate(index)
        self.listbox.see(index)

        path = self.playlist[index]
        self.media = self.vlc_instance.media_new(path)
        self.player.set_media(self.media)

        self.fade_label(self.song_label, 255, 50, -25, callback=lambda: self.update_song_text(os.path.basename(path)))
        self.fade_label(self.meta_label, 255, 50, -25, callback=lambda: self.display_metadata(path))
        self.display_album_art(path)

        self.player.play()
        self.player.audio_set_volume(self.volume_slider.get())
        self.root.after(300, self.check_duration)

        self.play_btn.config(state="normal")
        self.pause_btn.config(state="normal")
        self.stop_btn.config(state="normal")

    def update_song_text(self, text):
        self.song_label.config(text=text)
        self.fade_label(self.song_label, 50, 255, 25)

    def display_metadata(self, file_path):
        try:
            tags = EasyID3(file_path)
            artist = tags.get('artist', ['Unknown Artist'])[0]
            album = tags.get('album', ['Unknown Album'])[0]
            title = tags.get('title', ['Unknown Title'])[0]
            text = f"{artist} — {album} — {title}"
        except:
            text = "Metadata not found"
        self.meta_label.config(text=text)
        self.fade_label(self.meta_label, 50, 255, 25)

    def display_album_art(self, file_path):
        if file_path in self.album_art_cache:
            self.fade_album_art(self.album_art_cache[file_path])
            return
        try:
            audio = MP3(file_path, ID3=ID3)
            for tag in audio.tags.values():
                if isinstance(tag, APIC):
                    image = Image.open(io.BytesIO(tag.data)).resize((200, 200), Image.Resampling.LANCZOS)
                    self.album_art_cache[file_path] = image
                    self.fade_album_art(image)
                    return
        except:
            pass
        self.set_default_album_art()

    def set_default_album_art(self):
        try:
            image = Image.open('icons/default_art.png').resize((200, 200), Image.Resampling.LANCZOS)
            self.fade_album_art(image)
        except:
            self.album_art_label.config(image='', text='No Album Art', fg='gray')

    def fade_album_art(self, new_image_pil):
        if self.album_original_image and self.album_original_image.tobytes() == new_image_pil.tobytes():
            return

        def blend(alpha):
            if alpha <= 1.0:
                blended = (
                    Image.blend(self.album_original_image, new_image_pil, alpha)
                    if self.album_original_image else new_image_pil
                )
                self.album_art_image = ImageTk.PhotoImage(blended)
                self.album_art_label.config(image=self.album_art_image)

                if alpha == 0.5:
                    blurred = blended.resize((850, 620), Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(18))
                    overlay = Image.new("RGBA", blurred.size, (0, 0, 0, 120))
                    blurred.paste(overlay, (0, 0), overlay)
                    self.bg_image = ImageTk.PhotoImage(blurred)
                    self.bg_image_label.config(image=self.bg_image)

                self.root.after(30, lambda: blend(round(alpha + 0.1, 2)))
            else:
                self.album_original_image = new_image_pil

        blend(0.0)

    def fade_label(self, label, start=255, end=0, step=-15, delay=30, callback=None):
        def fade(c):
            if (step < 0 and c > end) or (step > 0 and c < end):
                label.config(fg=f"#{c:02x}{c:02x}{c:02x}")
                self.root.after(delay, lambda: fade(c + step))
            else:
                if callback: callback()
        fade(start)

    def toggle_shuffle(self):
        self.shuffle = not self.shuffle
        text = "Shuffle: ON" if self.shuffle else "Shuffle: OFF"
        bg = "#1DB954" if self.shuffle else "#333333"
        fg = "black" if self.shuffle else "white"
        self.shuffle_btn.config(text=text, bg=bg, fg=fg)

    def toggle_repeat(self):
        modes = {"off": "one", "one": "all", "all": "off"}
        self.repeat_mode = modes[self.repeat_mode]
        if self.repeat_mode != "off":
            self.repeat_btn.config(text=f"Repeat: {self.repeat_mode.upper()}", bg="#1DB954", fg="black")
        else:
            self.repeat_btn.config(text="Repeat: OFF", bg="#333333", fg="white")

    def play_song(self): self.player.play()
    def pause_song(self): self.player.pause()
    def stop_song(self):
        self.player.stop()
        self.seek_slider.set(0)
        self.time_label.config(text=f"00:00 / {self.duration_str}")

    def change_volume(self, val): self.player.audio_set_volume(int(float(val)))
    def volume_click(self, e):
        vol = int((e.x / e.widget.winfo_width()) * 100)
        self.volume_slider.set(max(0, min(100, vol)))
        self.player.audio_set_volume(self.volume_slider.get())

    def seek_song(self, e):
        if self.duration_ms > 0:
            new_time = self.seek_slider.get() / 1000 * self.duration_ms
            self.player.set_time(int(new_time))

    def seek_click(self, e):
        if self.duration_ms > 0:
            frac = max(0, min(e.x / e.widget.winfo_width(), 1))
            self.player.set_time(int(frac * self.duration_ms))
            self.seek_slider.set(int(frac * 1000))

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
        self.load_song(index)

    def play_next(self):
        if not self.playlist: return
        next_index = random.randint(0, len(self.playlist) - 1) if self.shuffle else self.current_index + 1
        if next_index >= len(self.playlist):
            next_index = 0 if self.repeat_mode == "all" else len(self.playlist) - 1
        self.load_song(next_index)

    def play_previous(self):
        if not self.playlist: return
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
                self.load_song((self.current_index + 1) % len(self.playlist))
            elif self.current_index + 1 < len(self.playlist):
                self.load_song(self.current_index + 1)
        self.root.after(100, next_song)

# ----------- Run Application -----------
if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = MinimalMusicPlayer(root)
        root.mainloop()
    except Exception as e:
        print("Error:", e)
        input("Press Enter to exit...")
