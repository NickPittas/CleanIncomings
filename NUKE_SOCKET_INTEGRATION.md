# Nuke Socket Integration

The CleanIncomings application now supports sending media files and sequences directly to Nuke via socket communication, eliminating the need to launch separate Nuke processes.

## Overview

Instead of the previous "Open with Nuke" functionality that tried to launch Nuke with command-line arguments (which often failed with sequences), we now use **"Send to Nuke"** which communicates with a running Nuke session to create Read nodes directly.

## Requirements

1. **Nuke** (any recent version)
2. **NukeServerSocket plugin** loaded in Nuke
3. Socket server running on `127.0.0.1:49512`

## Setup

### 1. Install NukeServerSocket Plugin

The NukeServerSocket plugin allows external applications to send Python commands to Nuke via TCP socket.

**Installation varies by setup - consult your Nuke administrator or:**
- Place the plugin in your Nuke plugins directory
- Load via Nuke's plugin manager
- Or add to your `init.py`/`menu.py`

### 2. Start the Socket Server

In Nuke's Script Editor, run:
```python
# Start the NukeServerSocket server
import nukescripts
nukescripts.start_socket_server()
```

Or if using a custom implementation:
```python
# Your specific NukeServerSocket startup code here
```

The server should start listening on `127.0.0.1:49512`.

## Usage

### From CleanIncomings GUI

1. Right-click on any file or sequence in CleanIncomings
2. Select **"Send to Nuke"** from context menu
3. The application will:
   - Connect to the Nuke socket server
   - Create a Read node with the appropriate file/sequence path
   - Set up frame ranges automatically (for sequences)
   - Display the result in Nuke's viewer

### Supported Media Types

- **Single files**: Any format Nuke can read (EXR, DPX, JPG, PNG, etc.)
- **Image sequences**: Automatically detects and converts to Nuke notation
  - `image.0001.exr` → `image.####.exr` 
  - `render_v001.1001.dpx` → `render_v001.####.dpx`
- **Frame range detection**: Automatically sets project frame range for sequences

## Technical Details

### Socket Communication

The integration uses JSON messages sent over TCP socket:

```json
{
  "text": "Python code to execute in Nuke",
  "formatText": "0"
}
```

### Sequence Pattern Detection

The system intelligently converts file paths to Nuke sequence notation:

- **Input**: `C:\renders\beauty.0001.exr`
- **Output**: `C:/renders/beauty.####.exr` (note forward slashes)

### Error Handling

- **Connection failed**: Check if Nuke is running and NukeServerSocket is loaded
- **Command failed**: Check Nuke's Script Editor for error messages
- **Pattern detection failed**: Will fall back to single file mode

## Testing

### Test Socket Connection

Run the standalone test client:
```bash
cd python/utils
python nuke_socket_client.py
```

This will test the connection and show Nuke version if successful.

### Test Read Node Creation

```bash
python nuke_socket_client.py "path/to/your/image.0001.exr"
```

This will create a Read node in Nuke for the specified file/sequence.

## Troubleshooting

### "Could not connect to Nuke server"

**Solution:**
1. Ensure Nuke is running
2. Check that NukeServerSocket plugin is loaded
3. Verify server is listening on port 49512
4. Check firewall settings

### "Command executed but result uncertain"

**Solution:**
1. Check Nuke's Script Editor for Python errors
2. Verify file paths are valid and accessible
3. Ensure Nuke can read the file format

### "Sequence pattern not detected"

**Solution:**
- The system will fall back to single file mode
- Manually verify sequence numbering is consistent
- Check that files have numeric patterns in filenames

## Advanced Usage

### Custom Commands

You can extend the socket client to send custom Nuke commands:

```python
from python.utils.media_player import MediaPlayerUtils

# Create media player instance
app = YourAppInstance()
media_utils = MediaPlayerUtils(app)

# Send custom file/sequence
result = media_utils.send_to_nuke("/path/to/sequence.####.exr")
print(f"Success: {result}")
```

### Batch Operations

The socket approach enables batch operations:

```python
# Send multiple sequences to Nuke
sequences = [
    "/renders/beauty.####.exr",
    "/renders/diffuse.####.exr", 
    "/renders/specular.####.exr"
]

for seq in sequences:
    media_utils.send_to_nuke(seq)
```

## Benefits Over Previous Approach

1. **Reliability**: No more command-line parsing issues
2. **Speed**: Uses existing Nuke session instead of launching new processes  
3. **Integration**: Real-time communication with running Nuke
4. **Flexibility**: Can send any Python command, not just file opens
5. **Feedback**: Immediate response from Nuke about success/failure

## Migration

The old `launch_nuke_player()` and `launch_nuke()` methods are now deprecated but still available for compatibility. They will try the socket approach first, then fall back to the old process-launching method if the socket is unavailable.

**Recommended migration:**
- Replace calls to `launch_nuke_player()` with `send_to_nuke()`
- Replace calls to `launch_nuke()` with `send_to_nuke()`
- Update UI labels from "Open with Nuke" to "Send to Nuke" 