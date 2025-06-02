# Tasks: Standalone Nuke-Style Media Player

## Phase 1: Project Skeleton & UI

- [x] Create `standalone_player/` directory and initial placeholder files
- [x] Implement main PyQt5 window (`main.py` or `player_window.py`)
- [x] Add placeholder for video/image display widget (OpenGLWidget or QWidget)
- [x] Add playback bar with play/pause/stop, seek slider, frame/time info
- [x] Add zoom in/out/to-fit buttons and pan controls (buttons + mouse drag)
- [x] Implement basic keyboard shortcuts for all controls
- [x] Apply dark Nuke-style theme (stylesheet)
- [x] Document all major steps in `changelog_player.md`
- [x] Prepare for Phase 2: VLC backend integration

## Phase 2: VLC Backend Integration

- [ ] Create `vlc_backend.py` with `VLCVideoWidget` class
- [ ] Replace QLabel display area in `player_window.py` with `VLCVideoWidget`
- [ ] Wire up play/pause/stop buttons to control VLC backend
- [ ] Add method to load a video file (callable by main app/CLI)
- [ ] Implement playback bar slider sync with VLC position (polling)
- [ ] Display frame/time info from VLC
- [ ] Document all steps in `changelog_player.md`
- [ ] Prepare for Phase 3: Image sequence support

## Future Phases
- [ ] Image sequence playback with OpenImageIO/OpenGL (Phase 3)
- [ ] Advanced controls, error handling, and polish (Phase 4)
