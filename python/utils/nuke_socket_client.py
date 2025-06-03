#!/usr/bin/env python3
"""
Nuke Socket Client - Simple client for sending commands to NukeServerSocket

This script demonstrates how to send Python commands to a running Nuke session
via the NukeServerSocket plugin.

Usage:
    python nuke_socket_client.py [file_path]
    
Requirements:
    - Nuke running with NukeServerSocket plugin loaded
    - Server listening on 127.0.0.1:49512
"""

import os
import json
import socket
import sys
import re
from pathlib import Path


def connect_to_nuke():
    """
    Create a connection to the Nuke socket server.
    
    Returns:
        socket.socket: Connected socket, or None if failed
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5.0)
        s.connect(('127.0.0.1', 49512))
        return s
    except socket.error as e:
        print(f"❌ Could not connect to Nuke server at 127.0.0.1:49512")
        print(f"Error: {e}")
        print("\nMake sure:")
        print("1. Nuke is running")
        print("2. NukeServerSocket plugin is loaded")
        print("3. Server is listening on port 49512")
        return None


def send_command(socket_conn, command, format_text="0"):
    """
    Send a Python command to Nuke via socket.
    
    Args:
        socket_conn: Connected socket
        command: Python code to execute
        format_text: "0" for plain text, "1" for formatted text
        
    Returns:
        str: Response from Nuke
    """
    try:
        data = {
            "text": command,
            "formatText": format_text
        }
        
        message = json.dumps(data)
        socket_conn.sendall(message.encode('utf-8'))
        
        response_data = socket_conn.recv(4096)
        return response_data.decode('utf-8')
        
    except Exception as e:
        return f"Error sending command: {e}"


def test_connection():
    """Test basic connection to Nuke and get version info."""
    print("🔌 Testing connection to Nuke...")
    
    s = connect_to_nuke()
    if not s:
        return False
    
    try:
        # Test basic command
        response = send_command(s, "import nuke; print(f'Nuke {nuke.NUKE_VERSION_STRING} connected')")
        print(f"✅ Connection successful!")
        print(f"Response: {response.strip()}")
        return True
        
    except Exception as e:
        print(f"❌ Error testing connection: {e}")
        return False
        
    finally:
        s.close()


def create_read_node(file_path):
    """
    Create a Read node in Nuke for the given file or sequence.
    
    Args:
        file_path: Path to file or sequence pattern
    """
    print(f"📁 Creating Read node for: {file_path}")
    
    s = connect_to_nuke()
    if not s:
        return False
    
    try:
        # Normalize path for Nuke (forward slashes)
        nuke_path = file_path.replace('\\', '/')
        
        # Detect if this might be part of a sequence
        is_sequence = detect_sequence_pattern(file_path)
        
        if is_sequence:
            sequence_pattern = convert_to_nuke_pattern(file_path)
            nuke_command = f"""
import nuke

# Create Read node for sequence
read_node = nuke.createNode('Read')
read_node['file'].setValue('{sequence_pattern}')

# Try to detect frame range
try:
    first_frame = read_node['first'].value()
    last_frame = read_node['last'].value()
    
    if first_frame and last_frame and first_frame != last_frame:
        root = nuke.root()
        root['first_frame'].setValue(int(first_frame))
        root['last_frame'].setValue(int(last_frame))
        
    print(f"Added sequence: {{read_node.name()}} [{{first_frame}}-{{last_frame}}]")
except:
    print(f"Added sequence: {{read_node.name()}}")

# Position node nicely
read_node.setXYpos(int(read_node.xpos()), int(read_node.ypos()) + 100)

# Show in viewer
viewer = nuke.activeViewer()
if viewer:
    viewer.setInput(0, read_node)

print("Read node created successfully")
"""
        else:
            nuke_command = f"""
import nuke

# Create Read node for single file
read_node = nuke.createNode('Read')
read_node['file'].setValue('{nuke_path}')

print(f"Added file: {{read_node.name()}}")

# Position node nicely
read_node.setXYpos(int(read_node.xpos()), int(read_node.ypos()) + 100)

# Show in viewer
viewer = nuke.activeViewer()
if viewer:
    viewer.setInput(0, read_node)

print("Read node created successfully")
"""
        
        response = send_command(s, nuke_command.strip())
        
        if "Read node created successfully" in response:
            print("✅ Read node created successfully!")
            print(f"Nuke response: {response.strip()}")
            return True
        else:
            print("⚠️ Command executed but result uncertain")
            print(f"Nuke response: {response.strip()}")
            return False
            
    except Exception as e:
        print(f"❌ Error creating Read node: {e}")
        return False
        
    finally:
        s.close()


def detect_sequence_pattern(file_path):
    """
    Detect if a file path appears to be part of an image sequence.
    
    Args:
        file_path: Path to check
        
    Returns:
        bool: True if appears to be part of a sequence
    """
    # Check for common image extensions
    image_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.exr', '.dpx', '.cin'}
    if Path(file_path).suffix.lower() not in image_extensions:
        return False
    
    # Check for numeric pattern in filename
    filename = Path(file_path).stem
    return bool(re.search(r'\d+', filename))


def convert_to_nuke_pattern(file_path):
    """
    Convert a file path to Nuke sequence pattern.
    
    Args:
        file_path: Original file path
        
    Returns:
        str: Nuke-style pattern (e.g., "image.####.exr")
    """
    path_obj = Path(file_path)
    directory = path_obj.parent
    filename = path_obj.stem
    extension = path_obj.suffix
    
    # Find numeric sequences in filename
    match = re.search(r'(\d+)', filename)
    if match:
        number_part = match.group(1)
        digits = len(number_part)
        # Replace number with hash pattern
        pattern_name = filename.replace(number_part, '#' * digits)
        return str(directory / f"{pattern_name}{extension}").replace('\\', '/')
    
    # No pattern found, return original
    return str(file_path).replace('\\', '/')


def main():
    """Main function - handle command line arguments and run appropriate action."""
    print("🎬 Nuke Socket Client")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        if os.path.exists(file_path):
            create_read_node(file_path)
        else:
            print(f"❌ File not found: {file_path}")
    else:
        # Just test connection
        if test_connection():
            print("\n📝 Usage examples:")
            print(f"python {sys.argv[0]} path/to/image.jpg")
            print(f"python {sys.argv[0]} path/to/sequence.0001.exr")
            print("\nFor sequences, the script will auto-detect patterns and create")
            print("appropriate Nuke sequence notation (e.g., image.####.exr)")


if __name__ == "__main__":
    main() 