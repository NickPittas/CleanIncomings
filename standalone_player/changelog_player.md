# Changelog: Standalone Nuke-Style Media Player

## [Phase 1] Project Skeleton & UI Initialization

### 2025-06-01
- Project kickoff: Created `standalone_player/` directory for the new media player.
- Documented architecture, requirements, and integration points.
- Planned UI: main window, playback bar, zoom/pan controls, dark Nuke-inspired theme.
- To Do:
  - Implement project structure and placeholder files.
  - Create main PyQt5 window and UI skeleton.
  - Add placeholder widgets for video/image display, playback controls, and zoom/pan.
  - Set up dark theme stylesheet.
  - Prepare for VLC and OpenImageIO integration in later phases.

## [Phase 2] VLC Backend Integration

### 2025-06-01
- Created `vlc_backend.py` with `VLCVideoWidget` for embedding VLC video playback in the player window.
- Replaced display area in `player_window.py` with `VLCVideoWidget`.
- Wired up play/pause/stop buttons, slider, and time/frame label to VLC backend in `player_window.py`.
- Added method to load a video file from CLI or main app.
- Implemented polling of VLC playback position and slider/time label sync.
- Keyboard shortcuts for play/pause/stop and frame stepping.
- Next: Prepare for Phase 3 (image sequence support).
