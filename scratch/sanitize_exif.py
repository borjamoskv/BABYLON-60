#!/usr/bin/env python3
import os
import sys
import argparse
from PIL import Image
from pypdf import PdfReader, PdfWriter

def sanitize_image(filepath, dry_run=False):
    """Strips all metadata from JPEG/PNG images."""
    try:
        with Image.open(filepath) as img:
            # Check if there is metadata (info dictionary) or exif
            has_exif = hasattr(img, "_getexif") and img._getexif() is not None
            has_info = bool(img.info)
            
            if not has_exif and not has_info:
                # Already clean
                return False, "No metadata detected"
            
            if dry_run:
                exif_details = "EXIF present" if has_exif else "Info present"
                return True, f"Would sanitize ({exif_details})"
            
            # Recreate image to discard all hidden tags, profiles, and EXIF
            # We copy pixel data to a brand new Image object
            img_format = img.format
            if img_format not in ["JPEG", "PNG"]:
                img_format = "PNG"  # fallback
            
            # Handle palette images (P) or transparency
            if img.mode == "P":
                # Convert palette to RGBA to avoid issues, or keep mode and copy palette
                # Keeping it simple: convert to RGB/RGBA
                mode = "RGBA" if "transparency" in img.info else "RGB"
                clean_img = img.convert(mode)
            else:
                clean_img = Image.new(img.mode, img.size)
                clean_img.putdata(list(img.getdata()))
            
            # Save the clean image back, replacing the old one
            clean_img.save(filepath, format=img_format)
            return True, "Sanitized successfully"
    except Exception as e:
        return False, f"ERROR: {str(e)}"

def sanitize_pdf(filepath, dry_run=False):
    """Strips all document information/metadata from PDF files."""
    try:
        reader = PdfReader(filepath)
        metadata = reader.metadata
        
        # If metadata is empty, check if we need to do anything
        if not metadata or all(not val for val in metadata.values()):
            return False, "No metadata detected"
            
        if dry_run:
            meta_summary = ", ".join(f"{k}={v}" for k, v in metadata.items() if v)
            return True, f"Would sanitize (Metadata: {meta_summary})"
            
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
            
        # Empty dictionary overrides/removes metadata
        writer.add_metadata({})
        
        with open(filepath, "wb") as f:
            writer.write(f)
            
        return True, "Sanitized successfully"
    except Exception as e:
        return False, f"ERROR: {str(e)}"

def main():
    parser = argparse.ArgumentParser(description="Sanitizes EXIF and document metadata from images and PDFs in C5-REAL.")
    parser.add_argument("--dir", default=".", help="Directory to scan recursively")
    parser.add_argument("--dry-run", action="store_true", help="Perform a dry run without modifying files")
    args = parser.parse_args()
    
    target_dir = os.path.abspath(args.dir)
    if not os.path.exists(target_dir):
        print(f"Error: Directory {target_dir} does not exist.")
        sys.exit(1)
        
    print(f"Scanning target directory: {target_dir}")
    if args.dry_run:
        print("--- DRY RUN MODE: No files will be modified ---")
        
    stats = {"scanned": 0, "sanitized": 0, "failed": 0, "skipped": 0}
    
    # Define extensions
    img_exts = {".jpg", ".jpeg", ".png"}
    pdf_exts = {".pdf"}
    
    # Exclude common directories to avoid unnecessary work or virtual env corruption
    exclude_dirs = {".venv", ".git", "node_modules", ".pytest_cache", ".ruff_cache", ".mypy_cache"}
    
    for root, dirs, files in os.walk(target_dir):
        # In-place modification of dirs to skip excluded ones
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            filepath = os.path.join(root, file)
            _, ext = os.path.splitext(file.lower())
            
            if ext in img_exts or ext in pdf_exts:
                stats["scanned"] += 1
                
                if ext in img_exts:
                    modified, msg = sanitize_image(filepath, args.dry_run)
                else:
                    modified, msg = sanitize_pdf(filepath, args.dry_run)
                    
                relative_path = os.path.relpath(filepath, target_dir)
                if modified:
                    stats["sanitized"] += 1
                    status_lbl = "[MODIFIED]" if not args.dry_run else "[WOULD MODIFY]"
                    print(f"{status_lbl} {relative_path} -> {msg}")
                else:
                    if "ERROR" in msg:
                        stats["failed"] += 1
                        print(f"[FAILED] {relative_path} -> {msg}")
                    else:
                        stats["skipped"] += 1
                        # Silent skip to avoid cluttering output unless needed
                        
    print("\n--- Execution Summary ---")
    print(f"Total files scanned: {stats['scanned']}")
    print(f"Total files sanitized: {stats['sanitized']}")
    print(f"Total files skipped (already clean): {stats['skipped']}")
    print(f"Total failures: {stats['failed']}")
    
if __name__ == "__main__":
    main()
