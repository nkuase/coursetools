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
    - Code block and list detection
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
        self.setWindowTitle("Enhanced Marp to HTML Converter")
        self.setGeometry(100, 100, 1400, 800)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Title
        title_label = QLabel("Enhanced Marp Markdown to HTML Converter")
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
        # Add sample content for testing - both lists and code
        sample_content = """```python
names = ["Vera", "Chuck", "Samantha", 
         "Roberto", "Joe", "Dave", "Tina"]
salaries = [2000, 1800, 1800, 2100, 
            2000, 2200, 2300]

for n in names: print(n)
for s in salaries: print(s)
```

![w:320pt](./pic/proto/v1.webp)"""
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
        splitter.setSizes([700, 700])  # Equal split initially
        
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
    
    def detect_content_type(self, content):
        """
        Analyze the content to determine what type it contains.
        
        This method demonstrates:
        - String parsing and pattern recognition
        - State machine logic (tracking code block state)
        - Regular expressions for pattern matching
        - Data structure organization
        
        Args:
            content (str): The input content to analyze
            
        Returns:
            dict: Information about detected content types
        """
        lines = content.split('\n')
        
        # Initialize detection results
        result = {
            'has_code_block': False,
            'has_list': False,
            'has_image': False,
            'code_blocks': [],
            'list_items': [],
            'images': []
        }
        
        # State tracking for code blocks (finite state machine concept)
        in_code_block = False
        current_code_block = {'language': '', 'lines': []}
        
        for line in lines:
            line_stripped = line.strip()
            
            # Check for code block start/end (``` markers)
            if line_stripped.startswith('```'):
                if not in_code_block:
                    # Starting a code block
                    in_code_block = True
                    result['has_code_block'] = True
                    # Extract language (everything after ```)
                    language = line_stripped[3:].strip()
                    current_code_block = {'language': language, 'lines': []}
                else:
                    # Ending a code block
                    in_code_block = False
                    result['code_blocks'].append(current_code_block.copy())
                    current_code_block = {'language': '', 'lines': []}
            elif in_code_block:
                # Inside a code block - collect the line (preserve original formatting)
                current_code_block['lines'].append(line)
            elif line_stripped.startswith('- '):
                # List item detected
                result['has_list'] = True
                list_item = line_stripped[2:].strip()
                if list_item:
                    result['list_items'].append(list_item)
            elif line_stripped.startswith('!['):
                # Image detected using regex
                image_match = re.match(r'!\[([^\]]*)\]\(([^)]+)\)', line_stripped)
                if image_match:
                    result['has_image'] = True
                    alt_text = image_match.group(1)
                    image_path = image_match.group(2)
                    result['images'].append({
                        'alt': alt_text if alt_text else 'Demo image',
                        'src': image_path
                    })
        
        return result
    
    def parse_marp_to_html(self, content):
        """
        Parse Marp markdown content and convert to HTML format.
        Now handles both code blocks and lists with configurable layout.
        
        This method demonstrates:
        - Content analysis and classification
        - Dynamic HTML generation
        - CSS styling in Python strings
        - Security considerations (HTML escaping)
        - Flexible layout systems
        
        Args:
            content (str): The input Marp markdown content
            
        Returns:
            str: The converted HTML content with configurable layout
        """
        # Analyze the content first
        content_info = self.detect_content_type(content)
        
        # Calculate percentages for flexible layout
        right_percentage = 100 - self.left_percentage
        
        # Generate HTML output with configurable percentages
        html_parts = []
        html_parts.append('<div style="display: flex; gap: 0.5em; align-items: stretch;">')
        
        # Left side - Main content (lists or code blocks)
        html_parts.append(f'  <div style="flex: 0 0 {self.left_percentage}%; font-size: 1em;">')
        
        # Add code blocks if present
        if content_info['has_code_block']:
            for code_block in content_info['code_blocks']:
                language = code_block['language']
                code_lines = code_block['lines']
                
                # Create syntax-highlighted code block with proper styling
                html_parts.append('    <pre style="background-color: #f4f4f4; padding: 1em; border-radius: 5px; overflow-x: auto; margin: 0.5em 0;">')
                if language:
                    html_parts.append(f'      <code class="language-{language}" style="font-family: \'Courier New\', monospace; font-size: 0.9em; line-height: 1.4;">')
                else:
                    html_parts.append('      <code style="font-family: \'Courier New\', monospace; font-size: 0.9em; line-height: 1.4;">')
                
                # Add each line of code with proper HTML escaping
                for code_line in code_lines:
                    # IMPORTANT: Escape HTML characters to prevent XSS and display issues
                    escaped_line = (code_line.replace('&', '&amp;')
                                               .replace('<', '&lt;')
                                               .replace('>', '&gt;')
                                               .replace('"', '&quot;'))
                    html_parts.append(escaped_line)
                
                html_parts.append('      </code>')
                html_parts.append('    </pre>')
        
        # Add lists if present
        if content_info['has_list']:
            html_parts.append('    <ul style="margin: 0.5em 0;">')
            for item in content_info['list_items']:
                html_parts.append(f'      <li>{item}</li>')
            html_parts.append('    </ul>')
        
        # If no content detected, show a helpful message
        if not content_info['has_code_block'] and not content_info['has_list']:
            html_parts.append('    <p style="color: #666; font-style: italic;">No lists or code blocks detected in the input.</p>')
        
        html_parts.append('  </div>')
        
        # Right side - Images (complementary percentage)
        html_parts.append(f'  <div style="flex: 0 0 {right_percentage}%; display: flex; justify-content: center; align-items: center; flex-direction: column; gap: 1em;">')
        
        if content_info['has_image']:
            for image in content_info['images']:
                html_parts.append(f'    <img src="{image["src"]}" alt="{image["alt"]}" style="max-width: 100%; height: auto; border-radius: 5px;">')
        else:
            html_parts.append('    <div style="color: #ccc; font-style: italic; text-align: center;">No images detected</div>')
        
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
    
    This is a common pattern in GUI applications and shows
    the separation of concerns between setup and execution.
    """
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Enhanced Marp to HTML Converter")
    app.setOrganizationName("Educational Demo")
    
    # Create and show the main window
    converter = MarpToHtmlConverter()
    converter.show()
    
    # Start the event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
