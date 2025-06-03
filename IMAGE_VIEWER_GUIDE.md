# Collapsible Image Viewer Guide

## Overview

The CleanIncomings application now includes a **Collapsible Image Viewer Panel** with **frame scrubbing capabilities** that displays any frame from image sequences directly within the application interface. This feature provides instant visual feedback and frame-by-frame navigation when working with sequences.

## Features

### 🎯 Core Functionality
- **Collapsible Panel**: Starts collapsed by default, expandable with a single click
- **Embedded Image Display**: Shows images directly within the panel using Qt's native image handling
- **Frame Scrubbing**: Navigate through any frame in the sequence using a timeline slider
- **Frame Navigation**: Step through frames with dedicated navigation buttons
- **Smart Format Support**: Handles common formats natively, with fallback conversion for professional formats
- **Sequence Integration**: Seamlessly integrates with the existing sequence detection and management system

### 🎨 User Interface
- **Right-Side Panel**: Positioned on the right side of the main application window
- **Toggle Button**: Click ▶ to expand, ◀ to collapse the panel
- **Timeline Scrub Bar**: Horizontal slider for scrubbing through all frames in the sequence
- **Navigation Controls**: First, previous, next, and last frame buttons
- **Frame Counter**: Shows current frame position (e.g., "127 / 450")
- **Image Controls**: Fit to window, actual size, and refresh controls
- **Status Display**: Shows sequence name, frame count, and current frame info
- **Scroll Support**: Large images can be scrolled within the display area

### 🖼️ Image Format Support
- **Native Qt Formats**: JPG, PNG, BMP, GIF, TIFF (basic), and other standard formats
- **Professional Formats**: EXR, HDR, DPX, CIN with fallback conversion using FFmpeg
- **Placeholder Display**: For unsupported formats, shows informative placeholder with filename
- **Smart Scaling**: Automatically scales images to fit the panel while maintaining aspect ratio

### ⚡ Performance Features
- **Threaded Loading**: Images load in background threads to keep UI responsive
- **Memory Efficient**: Only loads one image at a time, with proper cleanup
- **Real-time Scrubbing**: Instant frame updates when scrubbing through sequences
- **Optimized Navigation**: Fast frame switching for smooth workflow

## How to Use

### 1. **Expand the Panel**
- Look for the small ▶ button on the right edge of the application
- Click it to expand the image viewer panel
- The panel will resize to show the image display area and all controls

### 2. **Select a Sequence**
- Click on any image sequence in the main preview tree
- The viewer will automatically load and display the middle frame
- Sequence information (name, frame count) appears at the top
- Frame navigation controls become enabled

### 3. **Navigate Through Frames**

#### **Timeline Scrub Bar**
- **Drag the orange slider** to scrub through frames instantly
- The slider represents the entire sequence from first to last frame
- Frame updates in real-time as you drag

#### **Navigation Buttons**
- **⏮ First**: Jump to the first frame of the sequence
- **◀ Previous**: Go to the previous frame (or use left arrow key intent)
- **▶ Next**: Go to the next frame (or use right arrow key intent) 
- **⏭ Last**: Jump to the last frame of the sequence

#### **Frame Counter**
- Shows current position as "Frame X / Total" (e.g., "127 / 450")
- Updates in real-time as you navigate

### 4. **Image Controls**
- **🔄 Refresh**: Reload the current frame
- **⊞ Fit**: Scale image to fit the panel window
- **1:1**: Show image at actual pixel size (may require scrolling)

### 5. **Collapse When Done**
- Click the ◀ button to collapse the panel back to minimal width
- This gives more space to the main preview area

## Advanced Usage

### Frame Review Workflow
1. **Quick Overview**: Start by scrubbing through the sequence to get a general sense
2. **Detailed Review**: Use navigation buttons to step through frames one by one
3. **Problem Areas**: Jump to specific frames using the scrub bar for closer inspection
4. **Quality Check**: Use "Fit" and "1:1" buttons to examine image quality at different scales

### Professional Workflows
- **Animation Review**: Scrub through to check for continuity and motion
- **VFX Sequences**: Step through frames to verify effects and compositing
- **Color Grading**: Navigate to key frames to check color consistency
- **Technical QC**: Jump between first/last frames to check for issues

### Keyboard Workflow (Future Enhancement)
While currently mouse-driven, the interface is designed to eventually support:
- **Left/Right arrows**: Previous/next frame
- **Home/End**: First/last frame  
- **Page Up/Down**: Jump by 10 frames
- **Space**: Toggle between middle frame and current frame

## Technical Details

### Frame Navigation System
1. **Sequence Loading**: When a sequence is selected, all frame paths are indexed
2. **Smart Caching**: Only the current frame is loaded into memory
3. **Real-time Updates**: Frame changes trigger immediate image loading
4. **Threaded Loading**: Background threads prevent UI blocking during frame switches
5. **Error Handling**: Graceful fallback for missing or corrupted frames

### Timeline Slider Behavior
- **Range**: Automatically set to sequence length (0 to frame_count-1)
- **Sensitivity**: Each slider position represents exactly one frame
- **Visual Feedback**: Orange handle with smooth animation
- **Precision**: Frame-accurate positioning for exact navigation

### Memory Management
- **Single Frame**: Only one frame loaded at a time to conserve memory
- **Automatic Cleanup**: Previous frames are unloaded when switching
- **Thread Management**: Background loaders are properly terminated
- **Resource Optimization**: No unnecessary frame pre-loading

## Integration with External Players

The image viewer with scrub functionality complements external media players:

- **Quick Review**: Use the embedded viewer for rapid frame-by-frame inspection
- **Detailed Analysis**: Right-click sequences to launch professional viewers for advanced tools
- **Workflow Bridge**: Preview sequences in the viewer, then send to external tools for detailed work
- **Quality Control**: Use scrubbing for initial QC, external viewers for final approval

## Settings and Configuration

### Panel Behavior
- **Default State**: Panel starts collapsed, scrub controls hidden until expanded
- **Width Control**: Preferred width is 450px when expanded (fits scrub controls comfortably)
- **Frame Memory**: Starts at middle frame, remembers position during session

### Scrub Bar Settings
- **Timeline Range**: Automatically adjusts to sequence length
- **Handle Style**: Orange handle for visibility against dark interface
- **Smooth Scrubbing**: Real-time frame updates during drag operations
- **Precision Mode**: Each pixel of movement represents precise frame positioning

## Troubleshooting

### Common Issues

**Q: Scrub bar is grayed out**
- A: This happens when no sequence is selected or the sequence has only one frame
- Solution: Select a valid image sequence with multiple frames

**Q: Frame changes are slow during scrubbing**
- A: Large images or complex formats may take time to load
- Solution: Professional formats (EXR) may need conversion; standard formats load instantly

**Q: Frame counter shows "0 / 0"**
- A: This indicates no valid sequence data is loaded
- Solution: Ensure the selected item is a properly detected image sequence

**Q: Some frames show "Preview not available"**
- A: Individual frames in the sequence may be corrupted or in unsupported formats
- Solution: Check frame integrity, or use external viewers for problematic frames

**Q: Navigation buttons don't respond**
- A: Controls are disabled when no sequence is loaded or during frame loading
- Solution: Wait for current frame to load, or refresh the sequence data

### Performance Tips
- **Standard Formats**: JPG/PNG sequences provide smoothest scrubbing experience
- **Large Sequences**: Use external viewers for sequences with 1000+ frames for better performance
- **Professional Review**: Use scrub bar for quick inspection, external tools for detailed work
- **Memory Usage**: Close viewer panel when not in use to free memory

## Keyboard Shortcuts

Current mouse-driven controls:
- **Drag Scrub Bar**: Navigate to any frame
- **Click Navigation Buttons**: Step through frames
- **Click ▶/◀**: Toggle panel expansion
- **Click Fit/1:1**: Control image scaling

## Future Enhancements

Planned features for the scrub system:
- **Keyboard Navigation**: Arrow keys for frame stepping
- **Playback Mode**: Automatic frame cycling with speed control  
- **Thumbnail Strip**: Visual overview of sequence with mini-frames
- **Frame Marking**: Bookmark important frames for quick access
- **Range Selection**: Select frame ranges for batch operations
- **Zoom Scrubbing**: Detailed scrubbing with frame interpolation

---

## Summary

The enhanced Image Viewer with frame scrubbing provides **professional-grade sequence navigation** directly within CleanIncomings. The timeline scrub bar and navigation controls make it easy to inspect any frame in a sequence, greatly improving workflow efficiency for animation, VFX, and media review tasks.

**Key Benefits:**
- ✅ **Frame-by-frame navigation** through any sequence
- ✅ **Real-time scrubbing** with timeline slider
- ✅ **Professional navigation controls** (first, previous, next, last)
- ✅ **Frame-accurate positioning** with visual feedback
- ✅ **Memory-efficient design** that scales to large sequences
- ✅ **Seamless integration** with existing CleanIncomings workflow
- ✅ **Professional format support** with intelligent fallbacks

**Perfect For:**
- 🎬 **Animation Review**: Check motion and timing frame-by-frame
- 🎨 **VFX Inspection**: Verify effects and compositing quality
- 📹 **Media QC**: Quick quality control of rendered sequences
- 🔍 **Technical Analysis**: Detailed frame inspection for troubleshooting
- 🎯 **Asset Management**: Preview sequences before organizing or copying 