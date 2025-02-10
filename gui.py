#!/usr/bin/env python3

import sys
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QFileDialog, 
                            QComboBox, QScrollArea, QFrame, QGridLayout, 
                            QMessageBox, QSpacerItem, QSizePolicy, QCheckBox)
from PyQt6.QtCore import Qt, QSize, QMimeData
from PyQt6.QtGui import (QPixmap, QImage, QPalette, QColor, QDragEnterEvent, 
                        QDropEvent, QKeySequence)
import img_boxer
from PIL import Image
from PIL.ImageQt import ImageQt
import io
import mimetypes
import tempfile

class DropArea(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setText("\n\nDrop images here\nor\nPress Ctrl+V to paste\n\n")
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #aaa;
                border-radius: 8px;
                background-color: #f8f8f8;
                color: #666;
                font-size: 14px;
            }
        """)
        self.setMinimumHeight(120)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls() or event.mimeData().hasImage():
            event.acceptProposedAction()
            self.setStyleSheet("""
                QLabel {
                    border: 2px dashed #2196F3;
                    border-radius: 8px;
                    background-color: #E3F2FD;
                    color: #1976D2;
                    font-size: 14px;
                }
            """)

    def dragLeaveEvent(self, event):
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #aaa;
                border-radius: 8px;
                background-color: #f8f8f8;
                color: #666;
                font-size: 14px;
            }
        """)

    def dropEvent(self, event: QDropEvent):
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #aaa;
                border-radius: 8px;
                background-color: #f8f8f8;
                color: #666;
                font-size: 14px;
            }
        """)
        
        mime_data = event.mimeData()
        if mime_data.hasUrls():
            # Handle file drops
            file_paths = []
            for url in mime_data.urls():
                path = url.toLocalFile()
                if self.is_valid_image(path):
                    file_paths.append(path)
            
            if file_paths:
                self.parent().add_files(file_paths)
        
        elif mime_data.hasImage():
            # Handle image data drops
            image = QImage(mime_data.imageData())
            if not image.isNull():
                # Save the image to a temporary file
                temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                image.save(temp_file.name, 'PNG')
                self.parent().add_files([temp_file.name])

    def is_valid_image(self, file_path):
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type and mime_type.startswith('image/')

class ImageBoxerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Boxer")
        self.setMinimumSize(1000, 600)
        
        # Initialize variables
        self.selected_files = []
        self.processed_images = []
        self.final_mosaic = None
        self.aspect_ratios = {
            "16:9 (Widescreen)": "16:9",
            "4:3 (Standard)": "4:3",
            "1:1 (Square)": "1:1",
            "2:1 (Ultrawide)": "2:1",
            "3:2 (Classic Photo)": "3:2"
        }
        
        # Set up the main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Create and style the control panel
        control_panel = self.create_control_panel()
        control_panel.setStyleSheet("""
            QFrame {
                background-color: #f0f0f0;
                border-radius: 10px;
                padding: 10px;
            }
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton.success {
                background-color: #4CAF50;
            }
            QPushButton.success:hover {
                background-color: #388E3C;
            }
            QComboBox {
                padding: 6px;
                border: 1px solid #ccc;
                border-radius: 4px;
                min-width: 150px;
            }
            QCheckBox {
                spacing: 8px;
            }
        """)
        layout.addWidget(control_panel)

        # Create drop area
        self.drop_area = DropArea(self)
        layout.addWidget(self.drop_area)
        
        # Create the image preview area
        self.preview_area = self.create_preview_area()
        layout.addWidget(self.preview_area)
        
        # Set the window style
        self.setStyleSheet("""
            QMainWindow {
                background-color: white;
            }
        """)

        # Install event filter for keyboard shortcuts
        self.installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == event.Type.KeyPress:
            modifiers = QApplication.keyboardModifiers()
            key = event.key()
            
            # Check for Ctrl+V (Cmd+V on Mac)
            if modifiers == Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_V:
                self.handle_paste()
                return True
        return super().eventFilter(obj, event)

    def handle_paste(self):
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        
        if mime_data.hasImage():
            image = QImage(mime_data.imageData())
            if not image.isNull():
                # Save the image to a temporary file
                temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                image.save(temp_file.name, 'PNG')
                self.add_files([temp_file.name])
        elif mime_data.hasUrls():
            file_paths = []
            for url in mime_data.urls():
                path = url.toLocalFile()
                if self.is_valid_image(path):
                    file_paths.append(path)
            if file_paths:
                self.add_files(file_paths)

    def is_valid_image(self, file_path):
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type and mime_type.startswith('image/')

    def add_files(self, file_paths):
        """Add new files to the selection and update preview."""
        # Add new files to the existing selection
        self.selected_files.extend(file_paths)
        # Remove duplicates while preserving order
        self.selected_files = list(dict.fromkeys(self.selected_files))
        self.update_preview()
        # Hide drop area if we have files
        self.drop_area.setVisible(not self.selected_files)

    def create_control_panel(self):
        control_frame = QFrame()
        control_frame.setFrameStyle(QFrame.Shape.Box)
        
        layout = QHBoxLayout(control_frame)
        
        # File selection button
        self.file_btn = QPushButton("Select Images")
        self.file_btn.clicked.connect(self.select_files)
        layout.addWidget(self.file_btn)
        
        # Clear button
        self.clear_btn = QPushButton("Clear All")
        self.clear_btn.clicked.connect(self.clear_files)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        layout.addWidget(self.clear_btn)
        
        # Aspect ratio dropdown
        self.aspect_combo = QComboBox()
        self.aspect_combo.addItems(self.aspect_ratios.keys())
        layout.addWidget(QLabel("Aspect Ratio:"))
        layout.addWidget(self.aspect_combo)
        
        # Crop mode toggle
        self.crop_checkbox = QCheckBox("Enable Crop Mode")
        layout.addWidget(self.crop_checkbox)
        
        # Process button
        self.process_btn = QPushButton("Create Mosaic")
        self.process_btn.clicked.connect(self.process_images)
        layout.addWidget(self.process_btn)
        
        # Save button
        self.save_btn = QPushButton("Save Mosaic")
        self.save_btn.clicked.connect(self.save_mosaic)
        self.save_btn.setProperty('class', 'success')
        self.save_btn.setEnabled(False)
        layout.addWidget(self.save_btn)
        
        # Add stretching space
        layout.addStretch()
        
        return control_frame

    def clear_files(self):
        """Clear all selected files and reset the interface."""
        self.selected_files = []
        self.processed_images = []
        self.final_mosaic = None
        self.update_preview()
        self.drop_area.setVisible(True)
        self.save_btn.setEnabled(False)

    def create_preview_area(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #fafafa;
            }
        """)
        
        self.preview_widget = QWidget()
        self.preview_layout = QGridLayout(self.preview_widget)
        scroll.setWidget(self.preview_widget)
        
        return scroll

    def select_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Images",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if files:
            self.add_files(files)

    def update_preview(self):
        # Clear existing preview
        for i in reversed(range(self.preview_layout.count())): 
            self.preview_layout.itemAt(i).widget().setParent(None)
        
        # Add images to preview grid
        for idx, file_path in enumerate(self.selected_files):
            try:
                pixmap = QPixmap(file_path)
                label = QLabel()
                scaled_pixmap = pixmap.scaled(
                    200, 200,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                label.setPixmap(scaled_pixmap)
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                
                row = idx // 4
                col = idx % 4
                self.preview_layout.addWidget(label, row, col)
                
            except Exception as e:
                print(f"Error loading preview for {file_path}: {str(e)}")

    def process_images(self):
        if not self.selected_files:
            QMessageBox.warning(self, "Warning", "Please select images first!")
            return
        
        try:
            # Get selected aspect ratio
            ratio_text = self.aspect_ratios[self.aspect_combo.currentText()]
            target_ratio = img_boxer.parse_aspect_ratio(ratio_text)
            
            # Load all images
            images = []
            for file_path in self.selected_files:
                with Image.open(file_path) as img:
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    images.append(img.copy())
            
            # Create the mosaic
            self.final_mosaic = img_boxer.create_image_mosaic(
                images, 
                target_ratio, 
                self.crop_checkbox.isChecked()
            )
            
            # Show the mosaic preview
            self.show_mosaic_preview()
            
            # Enable save button
            self.save_btn.setEnabled(True)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error processing images: {str(e)}")

    def show_mosaic_preview(self):
        """Show the final mosaic in the preview area."""
        if not self.final_mosaic:
            return
            
        # Clear existing preview
        for i in reversed(range(self.preview_layout.count())): 
            self.preview_layout.itemAt(i).widget().setParent(None)
        
        # Convert PIL image to QPixmap
        qimg = ImageQt(self.final_mosaic)
        pixmap = QPixmap.fromImage(qimg)
        
        # Create label and scale the preview
        label = QLabel()
        scaled_pixmap = pixmap.scaled(
            800, 600,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        label.setPixmap(scaled_pixmap)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Add to layout
        self.preview_layout.addWidget(label, 0, 0)

    def save_mosaic(self):
        """Save the final mosaic image."""
        if not self.final_mosaic:
            QMessageBox.warning(self, "Warning", "No mosaic to save!")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Mosaic",
            "",
            "PNG Image (*.png);;JPEG Image (*.jpg);;All Files (*.*)"
        )
        
        if file_path:
            try:
                self.final_mosaic.save(file_path, quality=95)
                QMessageBox.information(self, "Success", "Mosaic saved successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error saving mosaic: {str(e)}")

def main():
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    window = ImageBoxerGUI()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 