# SAS Music Player

A modern, feature-rich music player built with PyQt6 and VLC, supporting MP3/FLAC/WAV playback, album art, playlist management, mini player, sleep timer, and more.

---


[ To run the app: First go through the requirement part then download the "Testing Files" folder and run the muuusic.py in your local system ]

[ All the files required to modify the app further resides inside the "Testing Files" folder ]



## Features
- Play MP3, FLAC, WAV files
- Playlist management (drag-and-drop, reorder, remove)
- Shuffle and repeat modes
- Album art display and blurred backgrounds
- Mini player mode
- Sleep timer
- System tray integration (Windows)
- Modern, animated UI

---

## Requirements
- **Python 3.9+**
- **VLC media player** (must be installed and accessible in PATH)
- **pip** (Python package manager)


### Python Dependencies
Install these with pip:
```
pip install PyQt6 python-vlc mutagen pillow
```

- `PyQt6` — for the UI
- `python-vlc` — for audio playback
- `mutagen` — for reading MP3 metadata and album art
- `pillow` — for image processing
- (Windows only) `pywin32` for taskbar integration (optional, only needed for advanced taskbar features)

---

## Setup & Running
1. **Install VLC**
   - Download and install VLC from [https://www.videolan.org/vlc/](https://www.videolan.org/vlc/)
   - Ensure `vlc` is in your system PATH (or install python-vlc wheel matching your VLC version)

2. **Install Python dependencies**
   - Run:
     ```
     pip install PyQt6 python-vlc mutagen pillow
     # (Optional, Windows only)
     pip install pywin32
     ```

3. **Run the player**
   - From the `Testing version` directory, run:
     ```
     python muuusic.py
     ```

---

## Project Structure

- `muuusic.py` — Main application window and logic
- `player_controller.py` — Handles playback, playlist, and VLC integration
- `mini_player.py` — Mini player window
- `widgets.py` — Custom PyQt widgets (labels, buttons, playlist, album art)
- `styles.py` — UI style and icon constants
- `assets/` — Icons and images

---

## How to Modify / Extend

### 1. **UI Changes**
- **Main window UI:** Edit `muuusic.py` in the `SASPlayer` class, especially the `setup_ui`, `_setup_sidebar`, `_setup_main_area`, and related methods.
- **Mini player UI:** Edit `mini_player.py` in the `MiniPlayer` class.
- **Custom widgets:** Edit or add new widgets in `widgets.py`.
- **Styles and icons:** Change colors, icons, and button styles in `styles.py` and the `assets/` folder.

### 2. **Playback Logic**
- **Playback, playlist, shuffle, repeat:** Edit `player_controller.py` in the `PlayerController` class.
- **Add new audio formats:** Extend the logic in `player_controller.py` and update file dialogs in `muuusic.py`.

### 3. **Adding Features**
- **New buttons or panels:** Add UI elements in `muuusic.py` (see `setup_ui` and related methods).
- **System tray actions:** Edit tray menu setup in `muuusic.py` (`SASPlayer.__init__`).
- **Sleep timer:** Logic is in `muuusic.py` (`SleepTimerDialog` and related methods).

### 4. **Album Art & Metadata**
- **Album art extraction:** See `display_album_art` and `set_album_art` in `muuusic.py`.
- **Metadata display:** See `display_metadata` in `muuusic.py`.

---

## Packaging as an EXE (Optional)
- Use [PyInstaller](https://pyinstaller.org/) to bundle the app:
  ```
  pip install pyinstaller
  pyinstaller muuusic.spec
  ```
- The `.spec` file is preconfigured for this project.
- After building, the EXE will be in the `dist/` folder.

---

## Troubleshooting
- **VLC not found:** Ensure VLC is installed and accessible in your system PATH.
- **Missing icons:** Check the `assets/` folder and `styles.py` for correct icon paths.
- **PyQt6 errors:** Make sure you have the correct version of PyQt6 for your Python version.

---

## Credits
App created by FAiTH in collaboration with LazyCr0w and subhaNAG2001. 
