import sys
import re
import json
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTextEdit, QPushButton, QLabel, 
                             QSplitter, QMessageBox, QSpinBox, QGroupBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QClipboard


class MarpToHtmlConverter(QMainWindow):
    """
    A PyQt6 application that converts Marp markdown content to HTML format.
    
    This application demonstrates:
    - GUI design with PyQt6
    - Clipboard operations
    - Text processing with regular expressions
    - Configuration file management
    - Dynamic content updates
    - Real-time content display
    """
    
    def __init__(self):
        super().__init__()
        self.clipboard = QApplication.clipboard()
        self.config_file = "marp_converter_config.json"
        self.left_percentage = self.load_config()
        self.init_ui()
        
    def load_config(self):
        """
        Load configuration from JSON file.
        
        Returns:
            int: The left panel percentage (default: 50)
        """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    percentage = config.get('left_percentage', 50)
                    # Ensure percentage is within valid range
                    return max(10, min(90, percentage))
            else:
                # Create default config file
                self.save_config(50)
                return 50
        except Exception as e:
            print(f"Error loading config: {e}")
            return 50
    
    def save_config(self, percentage):
        """
        Save configuration to JSON file.
        
        Args:
            percentage (int): The left panel percentage to save
        """
        try:
            config = {'left_percentage': percentage}
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
        
    def init_ui(self):
        """Initialize the user interface components."""
        self.setWindowTitle("Marp to HTML Converter")
        self.setGeometry(100, 100, 1200, 700)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Title
        title_label = QLabel("Marp Markdown to HTML Converter")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)
        
        # Configuration section
        config_group = QGroupBox("Layout Configuration")
        config_layout = QHBoxLayout(config_group)
        
        config_layout.addWidget(QLabel("Left Panel Width (%):"))
        
        self.percentage_spinbox = QSpinBox()
        self.percentage_spinbox.setRange(10, 90)  # Reasonable range
        self.percentage_spinbox.setValue(self.left_percentage)
        self.percentage_spinbox.setSuffix("%")
        self.percentage_spinbox.valueChanged.connect(self.on_percentage_changed)
        config_layout.addWidget(self.percentage_spinbox)
        
        self.right_percentage_label = QLabel()
        self.update_right_percentage_label()
        config_layout.addWidget(self.right_percentage_label)
        
        config_layout.addStretch()  # Push elements to the left
        
        main_layout.addWidget(config_group)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.read_button = QPushButton("Read from Clipboard")
        self.read_button.clicked.connect(self.read_from_clipboard)
        button_layout.addWidget(self.read_button)
        
        self.convert_button = QPushButton("Convert to HTML")
        self.convert_button.clicked.connect(self.convert_content)
        button_layout.addWidget(self.convert_button)
        
        self.copy_button = QPushButton("Copy HTML to Clipboard")
        self.copy_button.clicked.connect(self.copy_to_clipboard)
        self.copy_button.setEnabled(False)
        button_layout.addWidget(self.copy_button)
        
        main_layout.addLayout(button_layout)
        
        # Content display area
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Input panel
        input_widget = QWidget()
        input_layout = QVBoxLayout(input_widget)
        input_label = QLabel("Input (Marp Markdown):")
        input_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        input_layout.addWidget(input_label)
        
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("Paste your Marp content here or click 'Read from Clipboard'")
        # Add sample content for testing
        sample_content = """- First feature with some longer text to test wrapping
- Second feature
- Third feature
- Fourth feature for testing

![w:320pt](./pic/draw.webp)"""
        self.input_text.setPlainText(sample_content)
        input_layout.addWidget(self.input_text)
        
        # Output panel
        output_widget = QWidget()
        output_layout = QVBoxLayout(output_widget)
        output_label = QLabel("Output (HTML):")
        output_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        output_layout.addWidget(output_label)
        
        self.output_text = QTextEdit()
        self.output_text.setPlaceholderText("Converted HTML will appear here")
        self.output_text.setReadOnly(True)
        output_layout.addWidget(self.output_text)
        
        splitter.addWidget(input_widget)
        splitter.addWidget(output_widget)
        splitter.setSizes([500, 500])  # Equal split initially
        
        main_layout.addWidget(splitter)
        
        # Status label
        self.status_label = QLabel(f"Ready. Current layout: {self.left_percentage}% / {100-self.left_percentage}%")
        main_layout.addWidget(self.status_label)
        
        # Convert initial content
        self.convert_content()
        
    def update_right_percentage_label(self):
        """Update the label showing the right panel percentage."""
        right_percentage = 100 - self.left_percentage
        self.right_percentage_label.setText(f"Right Panel Width: {right_percentage}%")
        
    def on_percentage_changed(self, value):
        """
        Handle percentage spinbox value changes.
        
        Args:
            value (int): New percentage value
        """
        self.left_percentage = value
        self.update_right_percentage_label()
        self.save_config(value)
        
        # Update status
        right_percentage = 100 - value
        self.status_label.setText(f"Layout updated: {value}% / {right_percentage}%. Click 'Convert' to apply changes.")
        
        # Auto-convert if there's content
        if self.input_text.toPlainText().strip():
            self.convert_content()
        
    def read_from_clipboard(self):
        """Read content from the system clipboard."""
        try:
            clipboard_content = self.clipboard.text()
            if clipboard_content.strip():
                self.input_text.setPlainText(clipboard_content)
                self.status_label.setText("Content loaded from clipboard successfully.")
                # Auto-convert after loading
                self.convert_content()
            else:
                self.status_label.setText("Clipboard is empty or contains no text.")
        except Exception as e:
            self.show_error(f"Error reading from clipboard: {str(e)}")
    
    def convert_content(self):
        """Convert Marp markdown content to HTML format."""
        try:
            input_content = self.input_text.toPlainText().strip()
            if not input_content:
                self.status_label.setText("No input content to convert.")
                return
            
            html_output = self.parse_marp_to_html(input_content)
            self.output_text.setPlainText(html_output)
            self.copy_button.setEnabled(True)
            
            right_percentage = 100 - self.left_percentage
            self.status_label.setText(f"Content converted successfully! Layout: {self.left_percentage}% / {right_percentage}%")
            
        except Exception as e:
            self.show_error(f"Error during conversion: {str(e)}")
    
    def parse_marp_to_html(self, content):
        """
        Parse Marp markdown content and convert to HTML format.
        Uses configurable percentages for flexible layout.
        
        Args:
            content (str): The input Marp markdown content
            
        Returns:
            str: The converted HTML content with configurable layout
        """
        lines = content.split('\n')
        list_items = []
        image_info = None
        
        # Parse content line by line
        for line in lines:
            line = line.strip()
            
            # Check for list items (starting with -)
            if line.startswith('- '):
                # Remove the '- ' prefix and add to list
                list_item = line[2:].strip()
                if list_item:  # Only add non-empty items
                    list_items.append(list_item)
            
            # Check for image markdown pattern: ![w:XXXpt](path)
            elif line.startswith('!['):
                image_match = re.match(r'!\[([^\]]*)\]\(([^)]+)\)', line)
                if image_match:
                    alt_text = image_match.group(1)
                    image_path = image_match.group(2)
                    image_info = {
                        'alt': alt_text if alt_text else 'Demo image',
                        'src': image_path
                    }
        
        # Calculate percentages
        right_percentage = 100 - self.left_percentage
        
        # Generate HTML output with configurable percentages
        html_parts = []
        html_parts.append('<div style="display: flex; gap: 0em; align-items: flex-start;">')
        
        # Left side - List items (configurable percentage)
        html_parts.append(f'    <div style="flex: 0 0 {self.left_percentage}%;">')
        if list_items:
            html_parts.append('    <ul>')
            for item in list_items:
                html_parts.append(f'      <li>{item}</li>')
            html_parts.append('    </ul>')
        html_parts.append('  </div>')
        
        # Right side - Image (complementary percentage)
        html_parts.append(f'  <div style="flex: 0 0 {right_percentage}%;">')
        if image_info:
            html_parts.append(f'    <img src="{image_info["src"]}" alt="{image_info["alt"]}" style="max-width: 100%;">')
        html_parts.append('  </div>')
        
        html_parts.append('</div>')
        
        return '\n'.join(html_parts)
    
    def copy_to_clipboard(self):
        """Copy the converted HTML to the system clipboard."""
        try:
            html_content = self.output_text.toPlainText()
            if html_content.strip():
                self.clipboard.setText(html_content)
                self.status_label.setText("HTML copied to clipboard successfully!")
            else:
                self.status_label.setText("No HTML content to copy.")
        except Exception as e:
            self.show_error(f"Error copying to clipboard: {str(e)}")
    
    def show_error(self, message):
        """Display error message to the user."""
        QMessageBox.critical(self, "Error", message)
        self.status_label.setText(f"Error: {message}")
    
    def closeEvent(self, event):
        """Handle application close event - save current configuration."""
        self.save_config(self.left_percentage)
        event.accept()


def main():
    """
    Main function to run the application.
    
    This demonstrates the standard PyQt6 application pattern:
    1. Create QApplication instance
    2. Create main window
    3. Show the window
    4. Start the event loop
    """
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Marp to HTML Converter")
    app.setOrganizationName("Educational Demo")
    
    # Create and show the main window
    converter = MarpToHtmlConverter()
    converter.show()
    
    # Start the event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()