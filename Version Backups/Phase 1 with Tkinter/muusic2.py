import tkinter as tk
from tkinter import filedialog
import vlc
import os
import random

class GradientFrame(tk.Canvas):
    def __init__(self, parent, color1, color2, **kwargs):
        super().__init__(parent, **kwargs)
        self.color1 = color1
        self.color2 = color2
        self.bind("<Configure>", self._draw_gradient)

    def _draw_gradient(self, event=None):
        self.delete("gradient")
        width = self.winfo_width()
        height = self.winfo_height()
        r1, g1, b1 = self.winfo_rgb(self.color1)
        r2, g2, b2 = self.winfo_rgb(self.color2)
        r_ratio = (r2 - r1) / height
        g_ratio = (g2 - g1) / height
        b_ratio = (b2 - b1) / height

        for i in range(height):
            nr = int(r1 + (r_ratio * i))
            ng = int(g1 + (g_ratio * i))
            nb = int(b1 + (b_ratio * i))
            color = f"#{nr//256:02x}{ng//256:02x}{nb//256:02x}"
            self.create_line(0, i, width, i, tags=("gradient",), fill=color)

        self.lower("gradient")

class MinimalMusicPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("Minimal Music Player")
        self.root.geometry("640x440")
        self.root.resizable(False, False)

        self.bg = GradientFrame(root, "#1e3c72", "#2a5298")
        self.bg.pack(fill="both", expand=True)

        self.player = vlc.Instance().media_player_new()
        self.media = None

        self.playlist = []
        self.current_index = -1
        self.shuffle = False
        self.repeat_mode = "off"
        self.duration_ms = 0
        self.duration_str = "00:00"

        self.song_label = tk.Label(self.bg, text="No song loaded", bg="#1e3c72", fg="white", font=("Segoe UI", 12))
        self.song_label.place(x=20, y=20)

        btn_color = "#3c5f91"

        self.load_btn = tk.Button(self.bg, text="Load Songs", command=self.load_songs, bg=btn_color, fg="white", relief="flat")
        self.load_btn.place(x=20, y=60)

        self.play_btn = tk.Button(self.bg, text="▶", command=self.play_song, state="disabled", width=3, bg=btn_color, fg="white", relief="flat")
        self.play_btn.place(x=120, y=60)

        self.pause_btn = tk.Button(self.bg, text="⏸", command=self.pause_song, state="disabled", width=3, bg=btn_color, fg="white", relief="flat")
        self.pause_btn.place(x=160, y=60)

        self.stop_btn = tk.Button(self.bg, text="⏹", command=self.stop_song, state="disabled", width=3, bg=btn_color, fg="white", relief="flat")
        self.stop_btn.place(x=200, y=60)

        self.shuffle_btn = tk.Button(self.bg, text="Shuffle: OFF", command=self.toggle_shuffle, bg=btn_color, fg="white", relief="flat")
        self.shuffle_btn.place(x=260, y=60)

        self.repeat_btn = tk.Button(self.bg, text="Repeat: OFF", command=self.toggle_repeat, bg=btn_color, fg="white", relief="flat")
        self.repeat_btn.place(x=380, y=60)

        self.prev_btn = tk.Button(self.bg, text="⏮", command=self.play_previous, width=3, bg=btn_color, fg="white", relief="flat")
        self.prev_btn.place(x=480, y=60)

        self.next_btn = tk.Button(self.bg, text="⏭", command=self.play_next, width=3, bg=btn_color, fg="white", relief="flat")
        self.next_btn.place(x=520, y=60)

        self.volume_slider = tk.Scale(self.bg, from_=0, to=100, orient="horizontal", label="Volume",
                                      bg="#1e3c72", fg="white", troughcolor="white")
        self.volume_slider.set(70)
        self.volume_slider.place(x=20, y=110)
        self.volume_slider.config(command=self.change_volume)
        self.volume_slider.bind("<Button-1>", self.volume_click)

        self.seek_slider = tk.Scale(self.bg, from_=0, to=1000, orient="horizontal", length=300, label="Progress",
                                    bg="#1e3c72", fg="white", troughcolor="white")
        self.seek_slider.place(x=200, y=110)
        self.seek_slider.bind("<ButtonRelease-1>", self.seek_song)
        self.seek_slider.bind("<Button-1>", self.seek_click)

        self.time_label = tk.Label(self.bg, text="00:00 / 00:00", fg="white", bg="#1e3c72")
        self.time_label.place(x=520, y=150)

        self.listbox = tk.Listbox(self.bg, width=70, bg="#1e3c72", fg="white", relief="flat", highlightthickness=0,
                                  selectbackground="#4f9eea", selectforeground="white")
        self.listbox.place(x=20, y=180)
        self.listbox.bind("<Button-1>", self.select_song)
        self.listbox.bind("<Double-Button-1>", self.play_selected)

        self.player.event_manager().event_attach(vlc.EventType.MediaPlayerEndReached, self.song_finished)
        self.update_seek_bar()

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
        self.song_label.config(text=os.path.basename(path))
        self.player.play()
        self.player.audio_set_volume(self.volume_slider.get())

        self.root.after(300, self.check_duration)

        self.play_btn.config(state="normal")
        self.pause_btn.config(state="normal")
        self.stop_btn.config(state="normal")

    def check_duration(self):
        length = self.player.get_length()
        if length > 0:
            self.duration_ms = length
            self.duration_str = self.format_time(length / 1000)
        else:
            self.root.after(300, self.check_duration)

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
        new_volume = max(0, min(100, new_volume))  # clamp
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

    def format_time(self, seconds):
        m, s = divmod(int(seconds), 60)
        return f"{m:02}:{s:02}"

    def select_song(self, event):
        index = self.listbox.nearest(event.y)
        if 0 <= index < len(self.playlist):
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(index)
            self.listbox.activate(index)
            self.listbox.see(index)

    def play_selected(self, event):
        index = self.listbox.nearest(event.y)
        if 0 <= index < len(self.playlist):
            self.load_song(index)

    def toggle_shuffle(self):
        self.shuffle = not self.shuffle
        self.shuffle_btn.config(text=f"Shuffle: {'ON' if self.shuffle else 'OFF'}")

    def toggle_repeat(self):
        if self.repeat_mode == "off":
            self.repeat_mode = "one"
            self.repeat_btn.config(text="Repeat: ONE")
        elif self.repeat_mode == "one":
            self.repeat_mode = "all"
            self.repeat_btn.config(text="Repeat: ALL")
        else:
            self.repeat_mode = "off"
            self.repeat_btn.config(text="Repeat: OFF")

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
