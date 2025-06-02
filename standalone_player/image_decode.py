"""
Image Decode: Loads images using OpenCV and imageio, applies color transforms.
"""
import cv2
import numpy as np
import imageio

COLOR_TRANSFORMS = {
    'linear': lambda arr: arr,
    'srgb': lambda arr: np.clip(np.power(arr, 1/2.2), 0, 1),
    'rec709': lambda arr: np.clip(np.where(arr < 0.018, arr * 4.5, 1.099 * np.power(arr, 0.45) - 0.099), 0, 1),
    'acescg': lambda arr: arr,  # Placeholder, real ACEScg transform would need OCIO
}

def load_image(path):
    """Load image using OpenEXR for .exr, imageio for DPX/TIFF, OpenCV for others."""
    import numpy as np
    ext = path.lower().split('.')[-1]
    if ext == 'exr':
        # Try both openexr and OpenEXR import styles for Windows compatibility
        openexr = None
        Imath = None
        import_error = None
        try:
            import openexr
            import Imath
        except ImportError as e1:
            try:
                import OpenEXR as openexr
                import Imath
            except ImportError as e2:
                import_error = (e1, e2)
        if openexr is not None and Imath is not None:
            try:
                exr_file = openexr.InputFile(path)
                dw = exr_file.header()['dataWindow']
                width, height = (dw.max.x - dw.min.x + 1, dw.max.y - dw.min.y + 1)
                # Try RGB(A) channels
                channels = ['R', 'G', 'B']
                if 'A' in exr_file.header()['channels']:
                    channels.append('A')
                arr = [
                    np.frombuffer(exr_file.channel(c, Imath.PixelType(Imath.PixelType.FLOAT)), dtype=np.float32)
                    for c in channels
                ]
                arr = np.stack(arr, axis=-1).reshape(height, width, len(channels))
                if arr.shape[2] > 3:
                    arr = arr[..., :3]  # Drop alpha for display
                return arr
            except Exception as e:
                openexr_error = e
        else:
            openexr_error = import_error
        # Fallback to imageio freeimage if OpenEXR fails
        try:
            import imageio
            arr = imageio.imread(path, plugin='freeimage')
            if arr.dtype == np.uint16:
                arr = arr.astype(np.float32) / 65535.0
            elif arr.dtype == np.uint8:
                arr = arr.astype(np.float32) / 255.0
            else:
                arr = arr.astype(np.float32)
            return arr
        except Exception as e2:
            raise IOError(f"Could not load EXR file {path}: OpenEXR error: {openexr_error}, imageio error: {e2}")
    elif ext in {'dpx', 'tif', 'tiff'}:
        try:
            import imageio
            arr = imageio.imread(path, plugin='freeimage')
            if arr.dtype == np.uint16:
                arr = arr.astype(np.float32) / 65535.0
            elif arr.dtype == np.uint8:
                arr = arr.astype(np.float32) / 255.0
            else:
                arr = arr.astype(np.float32)
            return arr
        except Exception as e:
            raise IOError(f"Could not load {path} with freeimage plugin: {e}")
    else:
        import cv2
        img = cv2.imread(path, cv2.IMREAD_UNCHANGED | cv2.IMREAD_ANYDEPTH | cv2.IMREAD_COLOR)
        if img is None:
            raise IOError(f"Could not load image: {path}")
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        if img.dtype == np.uint16:
            img = img.astype(np.float32) / 65535.0
        elif img.dtype == np.uint8:
            img = img.astype(np.float32) / 255.0
        else:
            img = img.astype(np.float32)
        return img

def apply_color_transform(arr, transform):
    """Apply selected color transform to the image array."""
    if transform not in COLOR_TRANSFORMS:
        return arr
    return COLOR_TRANSFORMS[transform](arr)
