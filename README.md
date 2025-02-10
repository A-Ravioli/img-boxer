# Image Boxer

A Python utility that resizes images to match a specified aspect ratio, with options for both cropping and non-cropping approaches.

## Features
- Resize multiple images to match a target aspect ratio
- Two modes of operation:
  - Crop mode: Maintains the target aspect ratio by cropping excess image content
  - No-crop mode: Adds letterboxing/pillarboxing to maintain the original image content
- Modern GUI interface for easy image selection and processing
- Command-line interface for batch processing

## Requirements
- Python 3.6+
- Pillow (PIL)
- PyQt6 (for GUI)

## Installation
```bash
pip install -r requirements.txt
```

## Usage

### GUI Application
To use the graphical interface:
```bash
python gui.py
```

The GUI provides an intuitive interface with:
- Image selection button
- Aspect ratio dropdown (16:9, 4:3, 1:1, etc.)
- Crop mode toggle
- Live preview of both original and processed images

### Command Line Interface
For batch processing via command line:
```bash
python img_boxer.py --input "path/to/images/*.jpg" --aspect-ratio 16:9 --crop
```

### Arguments (CLI)
- `--input`: Path to input images (supports glob patterns)
- `--aspect-ratio`: Target aspect ratio in format W:H (e.g., 16:9, 4:3, 1:1)
- `--crop`: Optional flag to enable cropping mode. If not specified, letterboxing/pillarboxing will be used
- `--output-dir`: Optional output directory (defaults to 'output')
