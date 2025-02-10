#!/usr/bin/env python3

import argparse
from pathlib import Path
import glob
from PIL import Image
import os
import math
from typing import List, Tuple

def parse_aspect_ratio(ratio_str):
    """Convert aspect ratio string (e.g., '16:9') to float."""
    try:
        width, height = map(float, ratio_str.split(':'))
        return width / height
    except ValueError:
        raise argparse.ArgumentTypeError("Aspect ratio must be in format W:H (e.g., 16:9)")

def resize_with_crop(image, target_ratio):
    """Resize and crop image to match target aspect ratio."""
    width, height = image.size
    current_ratio = width / height

    if current_ratio > target_ratio:
        # Image is too wide, crop width
        new_width = int(height * target_ratio)
        left = (width - new_width) // 2
        return image.crop((left, 0, left + new_width, height))
    elif current_ratio < target_ratio:
        # Image is too tall, crop height
        new_height = int(width / target_ratio)
        top = (height - new_height) // 2
        return image.crop((0, top, width, top + new_height))
    return image

def resize_with_padding(image, target_ratio):
    """Resize image to match target aspect ratio by adding padding."""
    width, height = image.size
    current_ratio = width / height

    if current_ratio > target_ratio:
        # Image is too wide, add vertical padding
        new_height = int(width / target_ratio)
        new_size = (width, new_height)
        new_image = Image.new('RGB', new_size, (0, 0, 0))
        paste_y = (new_height - height) // 2
        new_image.paste(image, (0, paste_y))
        return new_image
    elif current_ratio < target_ratio:
        # Image is too tall, add horizontal padding
        new_width = int(height * target_ratio)
        new_size = (new_width, height)
        new_image = Image.new('RGB', new_size, (0, 0, 0))
        paste_x = (new_width - width) // 2
        new_image.paste(image, (paste_x, 0))
        return new_image
    return image

def calculate_grid_size(n: int) -> Tuple[int, int]:
    """Calculate the optimal grid size for n images."""
    if n <= 1:
        return (1, 1)
    
    # Try to make it as square as possible
    cols = math.ceil(math.sqrt(n))
    rows = math.ceil(n / cols)
    return (rows, cols)

def create_image_mosaic(images: List[Image.Image], target_ratio: float, crop_mode: bool = False) -> Image.Image:
    """Create a mosaic of images that fits the target aspect ratio."""
    if not images:
        raise ValueError("No images provided")
    
    n_images = len(images)
    rows, cols = calculate_grid_size(n_images)
    
    # Calculate the size of each cell to maintain target ratio
    # If we have R rows and C columns, then:
    # (C * cell_width) / (R * cell_height) = target_ratio
    # Therefore: cell_width / cell_height = (target_ratio * R) / C
    cell_ratio = (target_ratio * rows) / cols
    
    # Base size for each cell (can be adjusted for higher/lower resolution)
    BASE_HEIGHT = 300
    cell_height = BASE_HEIGHT
    cell_width = int(cell_height * cell_ratio)
    
    # Create the final image
    final_width = cell_width * cols
    final_height = cell_height * rows
    final_image = Image.new('RGB', (final_width, final_height), (0, 0, 0))
    
    # Place each image in the grid
    for idx, img in enumerate(images):
        if idx >= rows * cols:
            break
            
        # Calculate position in grid
        grid_row = idx // cols
        grid_col = idx % cols
        
        # Resize image to fit cell
        if crop_mode:
            resized = resize_with_crop(img, cell_ratio)
        else:
            resized = resize_with_padding(img, cell_ratio)
        
        # Resize to exact cell size
        resized = resized.resize((cell_width, cell_height), Image.Resampling.LANCZOS)
        
        # Calculate position and paste
        x = grid_col * cell_width
        y = grid_row * cell_height
        final_image.paste(resized, (x, y))
    
    return final_image

def process_image(input_path, output_dir, target_ratio, crop_mode):
    """Process a single image."""
    try:
        with Image.open(input_path) as img:
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize with either cropping or padding
            if crop_mode:
                result = resize_with_crop(img, target_ratio)
            else:
                result = resize_with_padding(img, target_ratio)
            
            # Create output filename
            output_path = Path(output_dir) / f"processed_{Path(input_path).name}"
            result.save(output_path, quality=95)
            print(f"Processed: {input_path} -> {output_path}")
            
    except Exception as e:
        print(f"Error processing {input_path}: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description="Resize images to match a target aspect ratio")
    parser.add_argument("--input", required=True, help="Input image path (supports glob patterns)")
    parser.add_argument("--aspect-ratio", required=True, type=parse_aspect_ratio,
                      help="Target aspect ratio in format W:H (e.g., 16:9)")
    parser.add_argument("--crop", action="store_true",
                      help="Use cropping instead of padding to achieve target ratio")
    parser.add_argument("--output-dir", default="output",
                      help="Output directory for processed images")
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Process all matching input files
    input_files = glob.glob(args.input)
    if not input_files:
        print(f"No files found matching pattern: {args.input}")
        return
    
    for input_file in input_files:
        process_image(input_file, args.output_dir, args.aspect_ratio, args.crop)

if __name__ == "__main__":
    main() 