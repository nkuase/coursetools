#!/usr/bin/env python3
"""
Remove Prepended Spaces (RPS2) - PyQt6 Application
A reliable utility for removing leading spaces from text with verification.

Requirements implemented:
1. PyQt6 interface
2. Copy clipboard, remove prepended spaces, copy back
3. Two text windows showing before/after
4. Process button for left->right processing  
5. Auto-copy with manual copy option
6. Pre-check for prepended spaces
7. Post-verification of space removal

Author: Course Tools
File: nkuase/coursetools/remove_prepended_spaces/rps2.py
"""

import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, 
                             QHBoxLayout, QWidget, QTextEdit, QPushButton, 
                             QLabel, QMessageBox, QSplitter)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class RemovePrependedSpacesApp(QMainWindow):
    """Remove Prepended Spaces application with verification and auto-copy."""
    
    def __init__(self):
        super().__init__()
        self.clipboard = QApplication.clipboard()
        self.init_ui()
        self.load_clipboard()
        
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Remove Prepended Spaces v2")
        self.setGeometry(100, 100, 1000, 600)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Title
        title = QLabel("Remove Prepended Spaces Tool v2")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        main_layout.addWidget(title)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.load_button = QPushButton("📋 Load from Clipboard")
        self.load_button.clicked.connect(self.load_clipboard)
        self.load_button.setStyleSheet("padding: 8px; font-size: 14px;")
        
        self.process_button = QPushButton("⚡ Process")
        self.process_button.clicked.connect(self.process_text)
        self.process_button.setStyleSheet("padding: 8px; font-size: 14px; font-weight: bold;")
        
        self.copy_button = QPushButton("📄 Copy Result")
        self.copy_button.clicked.connect(self.copy_result)
        self.copy_button.setStyleSheet("padding: 8px; font-size: 14px;")
        self.copy_button.setEnabled(False)
        
        button_layout.addWidget(self.load_button)
        button_layout.addWidget(self.process_button)
        button_layout.addWidget(self.copy_button)
        button_layout.addStretch()
        
        main_layout.addLayout(button_layout)
        
        # Text areas
        text_layout = QHBoxLayout()
        
        # Left side - Input
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_label = QLabel("📝 Input Text (Original):")
        left_label.setStyleSheet("font-weight: bold;")
        self.input_text = QTextEdit()
        self.input_text.setFont(QFont("Courier", 11))
        self.input_text.setPlaceholderText("Paste your text here or click 'Load from Clipboard'...")
        left_layout.addWidget(left_label)
        left_layout.addWidget(self.input_text)
        
        # Right side - Output
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_label = QLabel("✨ Output Text (Processed):")
        right_label.setStyleSheet("font-weight: bold;")
        self.output_text = QTextEdit()
        self.output_text.setFont(QFont("Courier", 11))
        self.output_text.setPlaceholderText("Processed text will appear here...")
        self.output_text.setReadOnly(True)
        right_layout.addWidget(right_label)
        right_layout.addWidget(self.output_text)
        
        # Add to splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([500, 500])
        
        text_layout.addWidget(splitter)
        main_layout.addLayout(text_layout)
        
        # Status bar
        self.statusBar().showMessage("Ready - Load text and click Process")
        
    def load_clipboard(self):
        """Load text from clipboard into input area."""
        try:
            clipboard_text = self.clipboard.text()
            if not clipboard_text.strip():
                QMessageBox.information(self, "Info", "Clipboard is empty!")
                self.statusBar().showMessage("❌ Clipboard is empty")
                return
                
            self.input_text.setPlainText(clipboard_text)
            self.statusBar().showMessage(f"✅ Loaded {len(clipboard_text)} characters from clipboard")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load clipboard:\n{str(e)}")
            self.statusBar().showMessage("❌ Failed to load clipboard")
    
    def has_prepended_spaces(self, text):
        """Check if line 1 has prepended spaces that can be removed."""
        if not text.strip():
            return False, 0
            
        lines = text.split('\n')
        
        # Check first line for leading spaces
        if not lines or not lines[0].strip():
            # First line is empty, check for first non-empty line
            for i, line in enumerate(lines):
                if line.strip():
                    leading_spaces = len(line) - len(line.lstrip(' '))
                    return leading_spaces > 0, leading_spaces
            return False, 0
        
        # Count leading spaces in first line
        first_line = lines[0]
        leading_spaces = len(first_line) - len(first_line.lstrip(' '))
        
        return leading_spaces > 0, leading_spaces
    
    def remove_prepended_spaces(self, text):
        """Remove prepended spaces based on first line's leading spaces.
        
        Algorithm:
        1. Count leading spaces in line 1 (N)
        2. Remove N spaces from all lines
        3. If a line has fewer than N spaces, remove as many as possible
        """
        if not text.strip():
            return text
            
        lines = text.split('\n')
        
        if not lines:
            return text
        
        # Find the first non-empty line to determine N
        spaces_to_remove = 0
        first_non_empty_idx = -1
        
        for i, line in enumerate(lines):
            if line.strip():  # Found first non-empty line
                spaces_to_remove = len(line) - len(line.lstrip(' '))
                first_non_empty_idx = i
                break
        
        # If no non-empty lines found or no leading spaces
        if first_non_empty_idx == -1 or spaces_to_remove == 0:
            return text
            
        # Remove N spaces from all lines (or as many as possible)
        processed_lines = []
        for line in lines:
            if line.strip():  # Non-empty line
                # Count current leading spaces
                current_spaces = len(line) - len(line.lstrip(' '))
                # Remove min(N, current_spaces) spaces
                spaces_to_actually_remove = min(spaces_to_remove, current_spaces)
                processed_line = line[spaces_to_actually_remove:]
                processed_lines.append(processed_line)
            else:  # Empty line - keep as is
                processed_lines.append(line)
                
        return '\n'.join(processed_lines)
    
    def verify_processing(self, original, processed):
        """Verify that prepended spaces were removed based on first line."""
        # Check original first line had prepended spaces
        orig_has_spaces, orig_spaces = self.has_prepended_spaces(original)
        
        if not orig_has_spaces:
            return False, "First line had no prepended spaces to remove"
            
        if original == processed:
            return False, "No changes were made to the text"
        
        # Verify first line now has fewer or no leading spaces
        proc_has_spaces, proc_spaces = self.has_prepended_spaces(processed)
        
        if proc_has_spaces and proc_spaces >= orig_spaces:
            return False, f"Processing failed - first line still has {proc_spaces} leading spaces"
            
        return True, f"Successfully removed {orig_spaces} leading spaces from first line (and others as possible)"
    
    def process_text(self):
        """Process the input text and handle all requirements."""
        try:
            # Get input text
            input_text = self.input_text.toPlainText()
            
            if not input_text.strip():
                QMessageBox.warning(self, "Warning", "No input text to process!")
                self.statusBar().showMessage("❌ No input text")
                return
            
            # Requirement 6: Check if prepended spaces exist
            has_spaces, min_spaces = self.has_prepended_spaces(input_text)
            
            if not has_spaces:
                QMessageBox.information(
                    self, 
                    "No Work Needed", 
                    "The text doesn't have prepended spaces that need to be removed."
                )
                self.statusBar().showMessage("ℹ️ No prepended spaces found - no work needed")
                return
            
            # Process the text
            processed_text = self.remove_prepended_spaces(input_text)
            
            # Show in output area
            self.output_text.setPlainText(processed_text)
            
            # Requirement 7: Verify the processing worked
            success, message = self.verify_processing(input_text, processed_text)
            
            if not success:
                QMessageBox.warning(self, "Processing Issue", f"Verification failed:\n{message}")
                self.statusBar().showMessage(f"⚠️ {message}")
                return
            
            # Requirement 5: Auto-copy the result
            self.clipboard.setText(processed_text)
            
            # Enable manual copy button
            self.copy_button.setEnabled(True)
            
            # Success message
            lines_count = len(processed_text.split('\n'))
            self.statusBar().showMessage(f"✅ {message} | {lines_count} lines processed & auto-copied!")
            
            #QMessageBox.information(
            #    self, 
            #    "Success", 
            #    f"{message}\n\nResult has been automatically copied to clipboard!\n"
            #    f"You can now paste it anywhere."
            #)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Processing failed:\n{str(e)}")
            self.statusBar().showMessage("❌ Processing failed")
    
    def copy_result(self):
        """Manual copy of the result text."""
        try:
            result_text = self.output_text.toPlainText()
            
            if not result_text.strip():
                QMessageBox.warning(self, "Warning", "No result text to copy!")
                return
                
            self.clipboard.setText(result_text)
            self.statusBar().showMessage("📋 Result manually copied to clipboard!")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Copy failed:\n{str(e)}")


def main():
    """Main application entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName("Remove Prepended Spaces v2")
    app.setApplicationVersion("2.0")
    
    window = RemovePrependedSpacesApp()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
