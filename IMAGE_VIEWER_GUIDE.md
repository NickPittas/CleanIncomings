# Collapsible Image Viewer Guide

## Overview

The CleanIncomings application now includes a **Collapsible Image Viewer Panel** that displays the middle frame of image sequences directly within the application interface. This feature provides instant visual feedback when selecting sequences without launching external applications.

## Features

### 🎯 Core Functionality
- **Collapsible Panel**: Starts collapsed by default, expandable with a single click
- **Embedded Image Display**: Shows images directly within the panel using Qt's native image handling
- **Automatic Middle Frame Detection**: Automatically finds and displays the middle frame of any selected image sequence
- **Smart Format Support**: Handles common formats natively, with fallback conversion for professional formats
- **Sequence Integration**: Seamlessly integrates with the existing sequence detection and management system

### 🎨 User Interface
- **Right-Side Panel**: Positioned on the right side of the main application window
- **Toggle Button**: Click ▶ to expand, ◀ to collapse the panel
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
- **Fast Preview**: Optimized for quick middle-frame preview rather than full sequence playback

## How to Use

### 1. **Expand the Panel**
- Look for the small ▶ button on the right edge of the application
- Click it to expand the image viewer panel
- The panel will resize to show the image display area and controls

### 2. **Select a Sequence**
- Click on any image sequence in the main preview tree
- The viewer will automatically load and display the middle frame
- Sequence information (name, frame count) appears at the top

### 3. **View and Navigate**
- The middle frame appears directly in the panel
- Frame information shows: "Frame X/Y: filename.ext"
- Image dimensions are displayed below the frame info

### 4. **Image Controls**
- **🔄 Refresh**: Reload the current image
- **⊞ Fit**: Scale image to fit the panel window
- **1:1**: Show image at actual pixel size (may require scrolling)

### 5. **Collapse When Done**
- Click the ◀ button to collapse the panel back to minimal width
- This gives more space to the main preview area

## Technical Details

### Image Loading Process
1. **Sequence Selection**: When a sequence is selected, the middle frame index is calculated
2. **Background Loading**: Image loading happens in a separate thread to avoid UI blocking
3. **Format Detection**: Qt tries to load the image directly first
4. **Fallback Conversion**: For unsupported formats (like EXR), FFmpeg conversion is attempted
5. **Placeholder Generation**: If all else fails, an informative placeholder is shown
6. **Smart Scaling**: Images are scaled to fit the panel while preserving aspect ratio

### Supported Workflow
- **Standard Formats**: Immediate preview for JPG, PNG, BMP, GIF, and basic TIFF files
- **Professional Formats**: Conversion-based preview for EXR, HDR, DPX, CIN files (requires FFmpeg)
- **Unsupported Formats**: Informative placeholder with recommendation to use external viewers

### Memory Management
- **Single Image**: Only one image is loaded at a time to conserve memory
- **Automatic Cleanup**: Previous images are properly cleaned up when loading new ones
- **Thread Management**: Background threads are properly terminated when collapsing the panel

## Integration with External Players

The image viewer complements rather than replaces external media players:

- **Quick Preview**: Use the embedded viewer for instant visual feedback
- **Professional Review**: Right-click sequences to launch Nuke, MRV2, DJV, or other professional viewers
- **Full Sequence Playback**: Use external players for frame-by-frame navigation and full sequence review
- **Color-Critical Work**: Professional viewers provide better color management for critical work

## Settings and Configuration

### Panel Behavior
- **Default State**: Panel starts collapsed to maximize main window space
- **Width Control**: Preferred width is 450px when expanded, 30px when collapsed
- **Responsive Design**: Panel adapts to different window sizes and resolutions

### Image Loading
- **Max Preview Size**: Images are scaled to fit within the panel (typically 400x300 or larger)
- **Aspect Ratio**: Always preserved during scaling operations
- **Quality**: Uses Qt's SmoothTransformation for high-quality scaling

## Troubleshooting

### Common Issues

**Q: Image viewer shows "Preview not available"**
- A: This appears for formats that Qt cannot load natively (like EXR)
- Solution: Install FFmpeg for automatic conversion, or use external professional viewers

**Q: Images appear blurry or pixelated**
- A: This may occur with very large images scaled down to fit the panel
- Solution: Use the "1:1" button to view at actual size, or launch external viewers for full quality

**Q: Panel seems slow to load images**
- A: Loading happens in background threads; complex conversions may take time
- Solution: Standard formats (JPG, PNG) load instantly; professional formats may take a moment

**Q: EXR files don't show previews**
- A: EXR requires FFmpeg for conversion to displayable format
- Solution: Install FFmpeg, or right-click to use Nuke Player/MRV2 for native EXR viewing

### Performance Tips
- **Standard Formats**: Use JPG or PNG for fastest preview performance
- **Professional Workflows**: Use embedded viewer for quick checks, external viewers for detailed work
- **Large Sequences**: The viewer shows only the middle frame, keeping memory usage low

## Keyboard Shortcuts

Currently the image viewer operates through mouse interactions:
- **Click ▶/◀**: Toggle panel expansion
- **Click Fit**: Fit image to panel
- **Click 1:1**: Show actual size
- **Click Refresh**: Reload current image

## Future Enhancements

Potential future features:
- Frame navigation (previous/next frame buttons)
- Zoom controls with mouse wheel
- Image information overlay (EXIF data, color space)
- Multiple format export options
- Thumbnail strip for sequence overview

---

## Summary

The Collapsible Image Viewer provides instant visual feedback directly within CleanIncomings, making sequence review faster and more intuitive. It handles most common image formats natively and provides fallback support for professional formats, all while maintaining the responsive performance of the main application.

**Key Benefits:**
- ✅ Instant middle-frame preview for any selected sequence
- ✅ No external windows to manage
- ✅ Supports both standard and professional image formats
- ✅ Responsive design that doesn't interfere with main workflow
- ✅ Smart memory management and performance optimization
- ✅ Perfect complement to existing external player integrations 