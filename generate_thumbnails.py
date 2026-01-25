#!/usr/bin/env python3
"""Script to generate thumbnails for all uploaded files."""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.utils.thumbnails import generate_thumbnail

def main():
    """Generate thumbnails for all files in the uploads directory."""
    uploads_dir = project_root / 'static' / 'uploads'
    
    if not uploads_dir.exists():
        print(f"Uploads directory not found: {uploads_dir}")
        return
    
    # Supported extensions
    supported_extensions = ['.pdf', '.eps', '.ai', '.psd', '.svg']
    
    # Find all supported files
    files_to_process = []
    for ext in supported_extensions:
        files_to_process.extend(uploads_dir.glob(f'*{ext}'))
    
    print(f"Found {len(files_to_process)} files to process")
    
    success_count = 0
    error_count = 0
    
    for file_path in files_to_process:
        # Skip if thumbnail already exists
        thumbnail_name = f"{file_path.stem}_thumb.png"
        thumbnail_path = uploads_dir / thumbnail_name
        
        if thumbnail_path.exists():
            print(f"✓ Thumbnail already exists: {thumbnail_name}")
            success_count += 1
            continue
        
        # Generate thumbnail
        print(f"Generating thumbnail for: {file_path.name}...")
        try:
            result = generate_thumbnail(str(file_path), str(thumbnail_path))
            if result:
                print(f"✓ Successfully generated: {thumbnail_name}")
                success_count += 1
            else:
                print(f"✗ Failed to generate thumbnail for: {file_path.name}")
                error_count += 1
        except Exception as e:
            print(f"✗ Error processing {file_path.name}: {e}")
            error_count += 1
    
    print(f"\nSummary:")
    print(f"  Success: {success_count}")
    print(f"  Errors: {error_count}")
    print(f"  Total: {len(files_to_process)}")

if __name__ == '__main__':
    main()
