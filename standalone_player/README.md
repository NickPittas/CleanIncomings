# Standalone Nuke-Style Media Player

## Overview
This is a standalone PyQt5-based media player inspired by The Foundry's Nuke viewer. It supports:
- VLC backend for video playback with true zoom/pan (Phase 2+)
- Image sequence playback (EXR, DPX, PNG, JPG) with OpenGL (Phase 3+)
- Dark Nuke-style theme, playback bar, zoom/pan controls, keyboard shortcuts

## Usage
- Launched by the main CleanIncomings app with file/sequence info
- Only plays the selected file/sequence (no browsing)

## Development Phases
- Phase 1: UI skeleton and theme
- Phase 2: VLC backend integration
- Phase 3: Image sequence support
- Phase 4: Advanced controls and polish

See `tasks_player.md` and `changelog_player.md` for progress and implementation details.
