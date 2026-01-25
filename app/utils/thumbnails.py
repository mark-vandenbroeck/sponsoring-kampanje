import os
import subprocess
from PIL import Image
from pdf2image import convert_from_path
try:
    import cairosvg
except ImportError:
    cairosvg = None
try:
    from psd_tools import PSDImage
except ImportError:
    PSDImage = None

def generate_thumbnail(file_path, thumbnail_path, size=(200, 200)):
    """Generate a thumbnail from various file types (PDF, EPS, SVG, AI, PSD)."""
    try:
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.pdf':
            return generate_pdf_thumbnail(file_path, thumbnail_path, size)
        elif file_ext == '.eps':
            return generate_eps_thumbnail(file_path, thumbnail_path, size)
        elif file_ext == '.svg':
            return generate_svg_thumbnail(file_path, thumbnail_path, size)
        elif file_ext == '.ai':
            return generate_ai_thumbnail(file_path, thumbnail_path, size)
        elif file_ext == '.psd':
            return generate_psd_thumbnail(file_path, thumbnail_path, size)
        else:
            return False
    except Exception as e:
        print(f"Error generating thumbnail: {e}")
    return False

def generate_pdf_thumbnail(pdf_path, thumbnail_path, size=(200, 200)):
    """Generate a thumbnail from the first page of a PDF file."""
    try:
        # Convert first page of PDF to image
        images = convert_from_path(pdf_path, first_page=1, last_page=1, dpi=150)
        if images:
            # Get the first page
            first_page = images[0]
            # Create thumbnail
            first_page.thumbnail(size, Image.Resampling.LANCZOS)
            # Save thumbnail
            first_page.save(thumbnail_path, 'PNG')
            return True
    except Exception as e:
        print(f"Error generating PDF thumbnail: {e}")
    return False

def generate_eps_thumbnail(eps_path, thumbnail_path, size=(200, 200)):
    """Generate a thumbnail from an EPS file using Ghostscript."""
    try:
        # Use Ghostscript to convert EPS to PNG
        cmd = [
            'gs', '-dNOPAUSE', '-dBATCH', '-sDEVICE=png16m',
            f'-dDEVICEWIDTHPOINTS={size[0]}', f'-dDEVICEHEIGHTPOINTS={size[1]}',
            f'-sOutputFile={thumbnail_path}', eps_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 and os.path.exists(thumbnail_path):
            return True
    except Exception as e:
        print(f"Error generating EPS thumbnail: {e}")
    return False

def generate_svg_thumbnail(svg_path, thumbnail_path, size=(200, 200)):
    """Generate a thumbnail from an SVG file using CairoSVG."""
    if cairosvg is None:
        print("CairoSVG not installed, cannot generate SVG thumbnail")
        return False
    
    try:
        # Convert SVG to PNG using CairoSVG
        with open(svg_path, 'rb') as svg_file:
            png_data = cairosvg.svg2png(
                bytestring=svg_file.read(),
                output_width=size[0],
                output_height=size[1]
            )
        
        # Save the PNG data
        with open(thumbnail_path, 'wb') as png_file:
            png_file.write(png_data)
        return True
    except Exception as e:
        print(f"Error generating SVG thumbnail: {e}")
    return False

def generate_ai_thumbnail(ai_path, thumbnail_path, size=(200, 200)):
    """Generate a thumbnail from an AI file using Ghostscript."""
    try:
        # AI files are essentially EPS files, so we can use Ghostscript
        # Use Ghostscript to convert AI to PNG
        cmd = [
            'gs', '-dNOPAUSE', '-dBATCH', '-sDEVICE=png16m',
            f'-dDEVICEWIDTHPOINTS={size[0]}', f'-dDEVICEHEIGHTPOINTS={size[1]}',
            f'-sOutputFile={thumbnail_path}', ai_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 and os.path.exists(thumbnail_path):
            return True
    except Exception as e:
        print(f"Error generating AI thumbnail: {e}")
    return False

def generate_psd_thumbnail(psd_path, thumbnail_path, size=(200, 200)):
    """Generate a thumbnail from a PSD file using psd-tools."""
    if PSDImage is None:
        print("psd-tools not installed, cannot generate PSD thumbnail")
        return False
    
    try:
        # Load PSD file
        psd = PSDImage.open(psd_path)
        
        # Get the composite image (flattened version)
        composite = psd.composite()
        
        # Convert to RGB if necessary
        if composite.mode != 'RGB':
            composite = composite.convert('RGB')
        
        # Create thumbnail
        composite.thumbnail(size, Image.Resampling.LANCZOS)
        
        # Save thumbnail
        composite.save(thumbnail_path, 'PNG')
        return True
    except Exception as e:
        print(f"Error generating PSD thumbnail: {e}")
    return False

def get_thumbnail_path(filename, upload_folder):
    """Get the thumbnail path for a file, generating it if it's a supported format and doesn't exist."""
    if not filename:
        return None
    
    # Image files (jpg, png, gif) don't need thumbnails - return None so template uses original
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    if any(filename.lower().endswith(ext) for ext in image_extensions):
        return None
    
    # Check if file is a supported format for thumbnail generation
    supported_extensions = ['.pdf', '.eps', '.svg', '.ai', '.psd']
    if not any(filename.lower().endswith(ext) for ext in supported_extensions):
        return None
    
    # Create thumbnail filename
    base_name = os.path.splitext(filename)[0]
    thumbnail_filename = f"{base_name}_thumb.png"
    thumbnail_path = os.path.join(upload_folder, thumbnail_filename)
    
    # If thumbnail doesn't exist, try to generate it
    if not os.path.exists(thumbnail_path):
        file_path = os.path.join(upload_folder, filename)
        if os.path.exists(file_path):
            if generate_thumbnail(file_path, thumbnail_path):
                return thumbnail_filename
            else:
                return None
        else:
            return None
    
    return thumbnail_filename
