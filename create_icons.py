#!/usr/bin/env python3
"""
Icon Generator Script

Creates professional-looking icon files for the Clean Incomings GUI application.
Uses PIL to generate clean, modern icons in PNG format.
"""

from PIL import Image, ImageDraw, ImageFont
import os


def create_folder_icon(size=32, color="#4A90E2"):
    """Create a folder icon."""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Main folder body
    folder_width = int(size * 0.8)
    folder_height = int(size * 0.6)
    folder_x = (size - folder_width) // 2
    folder_y = int(size * 0.3)
    
    # Draw folder tab
    tab_width = int(folder_width * 0.4)
    tab_height = int(folder_height * 0.2)
    draw.rectangle([folder_x, folder_y - tab_height, folder_x + tab_width, folder_y], fill=color)
    
    # Draw main folder body
    draw.rectangle([folder_x, folder_y, folder_x + folder_width, folder_y + folder_height], fill=color)
    
    # Add some depth with a darker border
    border_color = darken_color(color, 0.3)
    draw.rectangle([folder_x, folder_y, folder_x + folder_width, folder_y + folder_height], outline=border_color, width=1)
    
    return img


def create_file_icon(size=32, color="#7D8B99"):
    """Create a file icon."""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # File body
    file_width = int(size * 0.6)
    file_height = int(size * 0.8)
    file_x = (size - file_width) // 2
    file_y = (size - file_height) // 2
    
    # Draw main file body
    draw.rectangle([file_x, file_y, file_x + file_width, file_y + file_height], fill=color)
    
    # Draw folded corner
    corner_size = int(file_width * 0.25)
    corner_points = [
        (file_x + file_width - corner_size, file_y),
        (file_x + file_width, file_y + corner_size),
        (file_x + file_width, file_y)
    ]
    draw.polygon(corner_points, fill=darken_color(color, 0.2))
    
    # Add border
    border_color = darken_color(color, 0.3)
    draw.rectangle([file_x, file_y, file_x + file_width, file_y + file_height], outline=border_color, width=1)
    
    return img


def create_video_icon(size=32, color="#E94B3C"):
    """Create a video file icon."""
    img = create_file_icon(size, color)
    draw = ImageDraw.Draw(img)
    
    # Add play button overlay
    center_x, center_y = size // 2, size // 2
    play_size = size // 4
    
    # Play triangle
    play_points = [
        (center_x - play_size//2, center_y - play_size//2),
        (center_x - play_size//2, center_y + play_size//2),
        (center_x + play_size//2, center_y)
    ]
    draw.polygon(play_points, fill="white")
    
    return img


def create_image_icon(size=32, color="#F5A623"):
    """Create an image file icon."""
    img = create_file_icon(size, color)
    draw = ImageDraw.Draw(img)
    
    # Add image elements
    center_x, center_y = size // 2, size // 2
    
    # Sun/mountain scene
    sun_radius = size // 8
    draw.ellipse([center_x - sun_radius, center_y - size//4, center_x, center_y - size//8], fill="white")
    
    # Mountain
    mountain_points = [
        (center_x - size//4, center_y + size//8),
        (center_x, center_y - size//8),
        (center_x + size//4, center_y + size//8)
    ]
    draw.polygon(mountain_points, fill="white")
    
    return img


def create_sequence_icon(size=32, color="#9013FE"):
    """Create a sequence/film icon."""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Film strip
    strip_width = int(size * 0.8)
    strip_height = int(size * 0.6)
    strip_x = (size - strip_width) // 2
    strip_y = (size - strip_height) // 2
    
    # Main strip
    draw.rectangle([strip_x, strip_y, strip_x + strip_width, strip_y + strip_height], fill=color)
    
    # Sprocket holes
    hole_size = int(strip_height * 0.15)
    hole_spacing = strip_width // 4
    
    for i in range(4):
        hole_x = strip_x + hole_spacing * i + hole_spacing // 2 - hole_size // 2
        # Top holes
        draw.rectangle([hole_x, strip_y + 2, hole_x + hole_size, strip_y + 2 + hole_size], fill=(0, 0, 0, 0))
        # Bottom holes  
        draw.rectangle([hole_x, strip_y + strip_height - 2 - hole_size, hole_x + hole_size, strip_y + strip_height - 2], fill=(0, 0, 0, 0))
    
    # Border
    border_color = darken_color(color, 0.3)
    draw.rectangle([strip_x, strip_y, strip_x + strip_width, strip_y + strip_height], outline=border_color, width=1)
    
    return img


def create_audio_icon(size=32, color="#50C878"):
    """Create an audio file icon."""
    img = create_file_icon(size, color)
    draw = ImageDraw.Draw(img)
    
    # Add sound waves
    center_x, center_y = size // 2, size // 2
    
    # Multiple arcs for sound waves
    for i in range(3):
        radius = (i + 1) * size // 8
        bbox = [center_x - radius, center_y - radius, center_x + radius, center_y + radius]
        draw.arc(bbox, -30, 30, fill="white", width=2)
    
    return img


def create_settings_icon(size=32, color="#424242"):
    """Create a settings/gear icon."""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    center_x, center_y = size // 2, size // 2
    outer_radius = size // 2 - 2
    inner_radius = size // 4
    
    # Draw gear teeth (simplified as octagon)
    import math
    teeth = 8
    points = []
    
    for i in range(teeth * 2):
        angle = (i * math.pi) / teeth
        radius = outer_radius if i % 2 == 0 else outer_radius * 0.8
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        points.append((x, y))
    
    draw.polygon(points, fill=color)
    
    # Inner circle
    draw.ellipse([center_x - inner_radius, center_y - inner_radius, 
                  center_x + inner_radius, center_y + inner_radius], fill=(0, 0, 0, 0))
    
    return img


def create_arrow_icon(direction="right", size=32, color="#2196F3"):
    """Create an arrow icon."""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    center_x, center_y = size // 2, size // 2
    arrow_size = size // 3
    
    if direction == "right":
        points = [
            (center_x - arrow_size, center_y - arrow_size),
            (center_x + arrow_size, center_y),
            (center_x - arrow_size, center_y + arrow_size)
        ]
    elif direction == "down":
        points = [
            (center_x - arrow_size, center_y - arrow_size),
            (center_x, center_y + arrow_size),
            (center_x + arrow_size, center_y - arrow_size)
        ]
    elif direction == "up":
        points = [
            (center_x - arrow_size, center_y + arrow_size),
            (center_x, center_y - arrow_size),
            (center_x + arrow_size, center_y + arrow_size)
        ]
    
    draw.polygon(points, fill=color)
    return img


def create_refresh_icon(size=32, color="#2196F3"):
    """Create a refresh/reload icon."""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    center_x, center_y = size // 2, size // 2
    radius = size // 3
    
    # Draw circular arrow (arc)
    bbox = [center_x - radius, center_y - radius, center_x + radius, center_y + radius]
    draw.arc(bbox, 30, 300, fill=color, width=3)
    
    # Add arrow head
    import math
    end_angle = math.radians(300)
    end_x = center_x + radius * math.cos(end_angle)
    end_y = center_y + radius * math.sin(end_angle)
    
    # Arrow head points
    head_size = 4
    head_points = [
        (end_x, end_y),
        (end_x - head_size, end_y - head_size),
        (end_x + head_size, end_y - head_size)
    ]
    draw.polygon(head_points, fill=color)
    
    return img


def darken_color(hex_color, factor):
    """Darken a hex color by a factor."""
    # Remove # if present
    hex_color = hex_color.lstrip('#')
    
    # Convert to RGB
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    
    # Darken
    r = int(r * (1 - factor))
    g = int(g * (1 - factor))
    b = int(b * (1 - factor))
    
    return f"#{r:02x}{g:02x}{b:02x}"


def main():
    """Generate all icon files."""
    icons_dir = "icons"
    if not os.path.exists(icons_dir):
        os.makedirs(icons_dir)
    
    # Icon specifications
    icon_specs = [
        ("folder_closed", create_folder_icon, {"color": "#4A90E2"}),
        ("folder_open", create_folder_icon, {"color": "#5BA0F2"}),
        ("file", create_file_icon, {"color": "#7D8B99"}),
        ("sequence", create_sequence_icon, {"color": "#9013FE"}),
        ("video", create_video_icon, {"color": "#E94B3C"}),
        ("image", create_image_icon, {"color": "#F5A623"}),
        ("audio", create_audio_icon, {"color": "#50C878"}),
        ("settings", create_settings_icon, {"color": "#424242"}),
        ("refresh", create_refresh_icon, {"color": "#2196F3"}),
        ("arrow_right", lambda **kwargs: create_arrow_icon("right", **kwargs), {"color": "#2196F3"}),
        ("arrow_down", lambda **kwargs: create_arrow_icon("down", **kwargs), {"color": "#2196F3"}),
        ("arrow_up", lambda **kwargs: create_arrow_icon("up", **kwargs), {"color": "#2196F3"}),
        ("asset", create_settings_icon, {"color": "#FF6B35"}),
        ("task", create_settings_icon, {"color": "#616161"}),
        ("success", lambda **kwargs: create_file_icon(color="#4CAF50", **kwargs), {"color": "#4CAF50"}),
        ("warning", lambda **kwargs: create_file_icon(color="#FF9800", **kwargs), {"color": "#FF9800"}),
        ("error", lambda **kwargs: create_file_icon(color="#F44336", **kwargs), {"color": "#F44336"}),
        ("info", lambda **kwargs: create_file_icon(color="#2196F3", **kwargs), {"color": "#2196F3"}),
    ]
    
    print("Generating icons...")
    for name, create_func, kwargs in icon_specs:
        try:
            # Create icon in multiple sizes
            for size in [16, 24, 32]:
                icon = create_func(size=size, **kwargs)
                filename = f"{name}_{size}.png"
                filepath = os.path.join(icons_dir, filename)
                icon.save(filepath, "PNG")
                print(f"Created: {filepath}")
        except Exception as e:
            print(f"Error creating {name}: {e}")
    
    print(f"\nGenerated icons in ./{icons_dir}/")


if __name__ == "__main__":
    main() 