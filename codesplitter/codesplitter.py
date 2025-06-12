import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                            QWidget, QPushButton, QTextEdit, QLabel, QSpinBox,
                            QMessageBox, QSplitter, QGroupBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import re

class CodeSplitterApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('Code Column Splitter for Teaching')
        self.setGeometry(100, 100, 900, 600)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout(central_widget)
        
        # Control panel
        control_panel = self.create_control_panel()
        layout.addWidget(control_panel)
        
        # Preview area
        preview_area = self.create_preview_area()
        layout.addWidget(preview_area)
        
        # Action buttons
        button_layout = self.create_button_layout()
        layout.addLayout(button_layout)
        
        # Status
        self.status_label = QLabel("Ready - Copy code to clipboard and click 'Read & Split' or 'Join Columns Back'")
        self.status_label.setStyleSheet("color: blue; padding: 5px;")
        layout.addWidget(self.status_label)
        
    def create_control_panel(self):
        group = QGroupBox("Settings")
        layout = QHBoxLayout(group)
        
        layout.addWidget(QLabel("Number of columns:"))
        self.columns_spinbox = QSpinBox()
        self.columns_spinbox.setRange(2, 4)
        self.columns_spinbox.setValue(2)
        layout.addWidget(self.columns_spinbox)
        
        layout.addStretch()
        
        return group
        
    def create_preview_area(self):
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Original code
        original_group = QGroupBox("Original Code")
        original_layout = QVBoxLayout(original_group)
        self.original_text = QTextEdit()
        # Use platform-appropriate monospace font
        monospace_font = QFont()
        monospace_font.setFamily("monospace")  # Generic monospace
        monospace_font.setPointSize(10)
        monospace_font.setStyleHint(QFont.StyleHint.Monospace)
        
        self.original_text.setFont(monospace_font)
        self.original_text.setPlaceholderText("Original code will appear here...")
        original_layout.addWidget(self.original_text)
        
        # Split code
        split_group = QGroupBox("Split Result")
        split_layout = QVBoxLayout(split_group)
        self.split_text = QTextEdit()
        # Use platform-appropriate monospace font
        monospace_font = QFont()
        monospace_font.setFamily("monospace")  # Generic monospace
        monospace_font.setPointSize(10)
        monospace_font.setStyleHint(QFont.StyleHint.Monospace)
        
        self.split_text.setFont(monospace_font)
        self.split_text.setPlaceholderText("Split code will appear here...")
        split_layout.addWidget(self.split_text)
        
        splitter.addWidget(original_group)
        splitter.addWidget(split_group)
        splitter.setSizes([450, 450])
        
        return splitter
        
    def create_button_layout(self):
        layout = QHBoxLayout()
        
        self.read_split_btn = QPushButton("📋 Read & Split from Clipboard")
        self.read_split_btn.clicked.connect(self.read_and_split)
        self.read_split_btn.setStyleSheet("QPushButton { padding: 10px; font-weight: bold; }")
        
        self.copy_result_btn = QPushButton("📋 Copy Result to Clipboard")
        self.copy_result_btn.clicked.connect(self.copy_result)
        self.copy_result_btn.setEnabled(False)
        self.copy_result_btn.setStyleSheet("QPushButton { padding: 10px; font-weight: bold; }")
        
        self.join_columns_btn = QPushButton("🔄 Join Columns Back")
        self.join_columns_btn.clicked.connect(self.join_columns)
        self.join_columns_btn.setEnabled(False)
        self.join_columns_btn.setStyleSheet("QPushButton { padding: 10px; font-weight: bold; }")
        
        layout.addWidget(self.read_split_btn)
        layout.addWidget(self.copy_result_btn)
        layout.addWidget(self.join_columns_btn)
        
        return layout
        
    def read_and_split(self):
        """Read code from clipboard and split it"""
        try:
            clipboard = QApplication.clipboard()
            code = clipboard.text()
            
            if not code.strip():
                self.show_message("Clipboard is empty or contains no text!")
                return
                
            # Display original code
            self.original_text.setPlainText(code)
            
            # Split the code
            split_result = self.split_code_into_columns(code, self.columns_spinbox.value())
            
            # Display split result
            self.split_text.setPlainText(split_result)
            
            # Enable copy button
            self.copy_result_btn.setEnabled(True)
            self.join_columns_btn.setEnabled(False)  # Disable join since we just split
            
            self.status_label.setText(f"✅ Code split into {self.columns_spinbox.value()} columns successfully!")
            self.status_label.setStyleSheet("color: green; padding: 5px;")
            
        except Exception as e:
            self.show_message(f"Error processing clipboard: {str(e)}")
            
    def join_columns(self):
        """Read split code from clipboard and join it back to original"""
        try:
            clipboard = QApplication.clipboard()
            code = clipboard.text()
            
            if not code.strip():
                self.show_message("Clipboard is empty or contains no text!")
                return
                
            # Check if code contains | separators
            if '|' not in code:
                self.show_message("No column separators (|) found in clipboard text!")
                return
                
            # Display original split code
            self.split_text.setPlainText(code)
            
            # Join the columns
            joined_result = self.join_code_columns(code)
            
            # Display joined result
            self.original_text.setPlainText(joined_result)
            
            # Enable copy button, disable join
            self.copy_result_btn.setEnabled(True)
            self.join_columns_btn.setEnabled(False)
            
            self.status_label.setText("✅ Columns joined back to original code successfully!")
            self.status_label.setStyleSheet("color: green; padding: 5px;")
            
        except Exception as e:
            self.show_message(f"Error joining columns: {str(e)}")
            
    def join_code_columns(self, split_code):
        """Join split code back into original format"""
        lines = split_code.replace('\r\n', '\n').replace('\r', '\n').split('\n')
        
        # Remove empty lines at the end
        while lines and not lines[-1].strip():
            lines.pop()
            
        if not lines:
            return "No code to join"
            
        # Split each line by | and collect columns
        all_columns = []
        for line in lines:
            if '|' in line:
                parts = line.split('|')
                # Remove trailing/leading whitespace from each part
                parts = [part.rstrip() for part in parts]
                all_columns.append(parts)
            else:
                # Line without separator, treat as single column
                all_columns.append([line.rstrip()])
                
        if not all_columns:
            return "No valid columns found"
            
        # Determine number of columns
        max_columns = max(len(row) for row in all_columns)
        
        # Reconstruct original code by reading columns from left to right, top to bottom
        result_lines = []
        
        for col_idx in range(max_columns):
            for row in all_columns:
                if col_idx < len(row) and row[col_idx].strip():
                    result_lines.append(row[col_idx])
                    
        return "\n".join(result_lines)
            
    def split_code_into_columns(self, code, num_columns):
        """Split code into specified number of columns"""
        # Clean and split into lines
        lines = code.replace('\r\n', '\n').replace('\r', '\n').split('\n')
        
        # Remove trailing empty lines
        while lines and not lines[-1].strip():
            lines.pop()
            
        if not lines:
            return "No code to split"
            
        # Calculate lines per column
        total_lines = len(lines)
        lines_per_column = total_lines // num_columns
        remainder = total_lines % num_columns
        
        # Distribute lines across columns
        columns = []
        start_idx = 0
        
        for col in range(num_columns):
            # Add one extra line to first 'remainder' columns
            column_size = lines_per_column + (1 if col < remainder else 0)
            end_idx = start_idx + column_size
            
            column_lines = lines[start_idx:end_idx]
            columns.append(column_lines)
            start_idx = end_idx
            
        # Find the maximum width needed for formatting
        max_line_length = max(len(line) for line in lines) if lines else 0
        column_width = max(max_line_length + 2, 40)  # Minimum width of 40
        
        # Create side-by-side output with | separator
        result_lines = []
        max_column_height = max(len(col) for col in columns) if columns else 0
        
        # Add the code lines side by side with | separator
        for row in range(max_column_height):
            line_parts = []
            for col_idx, column in enumerate(columns):
                if row < len(column):
                    # Preserve original line, but ensure minimum width
                    code_line = column[row].ljust(column_width)
                else:
                    # Empty space for shorter columns
                    code_line = " " * column_width
                line_parts.append(code_line)
            
            # Join with | separator
            result_lines.append("|".join(line_parts).rstrip())
            
        return "\n".join(result_lines)
        
    def copy_result(self):
        """Copy the current result back to clipboard"""
        try:
            # Determine which text to copy based on current state
            split_text = self.split_text.toPlainText()
            original_text = self.original_text.toPlainText()
            
            # If split_text contains | separators and original_text doesn't, copy split_text
            # If original_text is the result of joining, copy original_text
            # Default to split_text for backward compatibility
            if ('|' in split_text and '|' not in original_text and 
                len(original_text.strip()) > len(split_text.strip())):
                # We just joined columns, copy the joined result
                result_text = original_text
                message = "✅ Joined result copied to clipboard!"
            else:
                # We split code, copy the split result
                result_text = split_text
                message = "✅ Split result copied to clipboard!"
                
            if not result_text.strip():
                self.show_message("No result to copy!")
                return
                
            clipboard = QApplication.clipboard()
            clipboard.setText(result_text)
            
            # Enable join button only if result contains | separators
            if '|' in result_text:
                self.join_columns_btn.setEnabled(True)
            else:
                self.join_columns_btn.setEnabled(False)
            
            self.status_label.setText(message)
            self.status_label.setStyleSheet("color: green; padding: 5px;")
            
        except Exception as e:
            self.show_message(f"Error copying to clipboard: {str(e)}")
            
    def show_message(self, message):
        """Show message box"""
        msg_box = QMessageBox()
        msg_box.setWindowTitle("Code Splitter")
        msg_box.setText(message)
        msg_box.exec_()
        
        self.status_label.setText(message)
        self.status_label.setStyleSheet("color: red; padding: 5px;")

def main():
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    window = CodeSplitterApp()
    window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()