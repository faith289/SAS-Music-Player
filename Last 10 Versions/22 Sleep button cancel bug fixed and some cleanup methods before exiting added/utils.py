# utils.py - CORRECTED VERSION

def format_time(seconds):
    """
    Convert seconds to MM:SS format.
    
    Args:
        seconds: Time in seconds (int or float)
        
    Returns:
        Formatted time string (e.g., "3:45")
    """
    m, s = divmod(int(seconds), 60)
    return f"{m}:{s:02d}"

def is_audio_file(file_path):
    """
    Check if file has a supported audio extension.
    
    Args:
        file_path: Path to the file (string)
        
    Returns:
        bool: True if file has audio extension, False otherwise
    """
    if not file_path:
        return False
    
    audio_extensions = {'.mp3', '.wav', '.flac', '.m4a', '.ogg', '.aac', '.wma'}
    try:
        return file_path.lower().endswith(tuple(audio_extensions))
    except (AttributeError, TypeError):
        return False

def calculate_brightness(hex_color):
    """
    Calculate perceived brightness of a hex color (0.0 to 1.0).
    
    Args:
        hex_color: Hex color string (e.g., "#1DB954")
        
    Returns:
        float: Brightness value from 0.0 (dark) to 1.0 (bright)
    """
    try:
        # Remove # if present
        hex_color = hex_color.lstrip('#')
        
        # Convert to RGB
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16) 
        b = int(hex_color[4:6], 16)
        
        # Calculate perceived brightness using luminance formula
        brightness = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
        return brightness
        
    except (ValueError, IndexError):
        return 0.5  # Return middle brightness for invalid input

def get_safe_basename(file_path):
    """
    Get filename from path, handling edge cases safely.
    
    Args:
        file_path: Path to the file (string or Path-like)
        
    Returns:
        str: Safe basename, or "Unknown File" for invalid paths
    """
    if not file_path:
        return "Unknown File"
    
    try:
        import os
        basename = os.path.basename(str(file_path))
        return basename if basename else "Unknown File"
    except (AttributeError, TypeError, OSError):
        return "Unknown File"

def create_color_variants(base_color):
    """
    Create lighter and darker variants of a base color for UI effects.
    
    Args:
        base_color: Hex color string (e.g., "#1DB954")
        
    Returns:
        dict: Contains 'hover', 'pressed', 'light', 'dark' color variants
    """
    try:
        # Remove # if present
        hex_color = base_color.lstrip('#')
        
        # Convert to RGB
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16) 
        b = int(hex_color[4:6], 16)
        
        # Create variants
        def adjust_brightness(r, g, b, factor):
            """Adjust RGB values by factor (1.0 = no change, >1.0 = lighter, <1.0 = darker)"""
            r = min(255, max(0, int(r * factor)))
            g = min(255, max(0, int(g * factor)))
            b = min(255, max(0, int(b * factor)))
            return f"#{r:02x}{g:02x}{b:02x}"
        
        return {
            'hover': adjust_brightness(r, g, b, 1.2),    # 20% lighter
            'pressed': adjust_brightness(r, g, b, 0.8),  # 20% darker  
            'light': adjust_brightness(r, g, b, 1.4),    # 40% lighter
            'dark': adjust_brightness(r, g, b, 0.6)      # 40% darker
        }
        
    except (ValueError, IndexError):
        # Return safe defaults for invalid input
        return {
            'hover': '#2ECC71',
            'pressed': '#148A3C', 
            'light': '#58D68D',
            'dark': '#0E6B2A'
        }
