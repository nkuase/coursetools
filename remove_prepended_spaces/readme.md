Remove Prepended Spaces (RPS) - PyQt6 Application
A practical desktop application that demonstrates GUI programming concepts while solving a real-world text formatting problem.
📚 Educational Purpose
This application serves as an excellent example for teaching students about:
	•	PyQt6 GUI Development: Window creation, layouts, widgets, and event handling
	•	Text Processing Algorithms: String manipulation and algorithmic thinking
	•	Clipboard Operations: System integration and user experience design
	•	Object-Oriented Programming: Class design and method organization
	•	Error Handling: Robust application development practices
🎯 Problem It Solves
When copying code or text from various sources (IDEs, web pages, documents), the indentation often becomes inconsistent. This tool automatically removes the same amount of leading spaces from all lines, ensuring the first non-empty line starts at column 1.
Example Transformation
Before (inconsistent indentation):
  abc
    def
      ghi
After (consistent relative indentation):
abc
  def
    ghi
🚀 Setup Instructions
1. Create Directory Structure
mkdir -p nkuase/coursetools/remove_trail_spaces
cd nkuase/coursetools/remove_trail_spaces
2. Install Dependencies
pip install PyQt6

or

pip install -r requirements.txt
3. Run the Application
python rts.py
🔧 How It Works
Core Algorithm
The application implements a simple but effective algorithm:
	1	Split text into lines: Break the input into individual lines
	2	Find minimum indentation: Calculate the smallest number of leading spaces among all non-empty lines
	3	Remove consistent amount: Subtract that minimum from each line
	4	Preserve relative indentation: Maintain the relative spacing between lines
Code Structure
def remove_leading_spaces(self, text):
    """
    Algorithm walkthrough:
    1. Split text → ['  abc', '    def', '      ghi']
    2. Find min spaces → 2 (from '  abc')
    3. Remove 2 spaces from each → ['abc', '  def', '    ghi']
    4. Join back → 'abc\n  def\n    ghi'
    """
🎮 Usage Instructions
	1	Copy text with inconsistent indentation to your clipboard
	2	Click "Read Clipboard & Process" to load and process the text
	3	Review the results in the side-by-side text areas
	4	Click "Copy Result to Clipboard" to copy the formatted text
	5	Paste the clean text wherever needed
🏗️ GUI Components Explained
Layout Structure
	•	QMainWindow: Main application window
	•	QVBoxLayout: Vertical arrangement of components
	•	QSplitter: Resizable side-by-side text areas
	•	QTextEdit: Text display and editing areas
	•	QPushButton: Interactive buttons for actions
Key Features
	•	Real-time processing: Immediate feedback on text transformation
	•	Monospace font: Proper alignment visualization
	•	Status updates: Clear feedback on operations
	•	Error handling: Graceful handling of edge cases
🎓 Learning Opportunities
For Beginning Students
	•	Understanding event-driven programming
	•	Learning about GUI layout management
	•	Practicing string manipulation
For Intermediate Students
	•	Implementing algorithms for text processing
	•	Understanding clipboard operations
	•	Exploring user experience design
For Advanced Students
	•	Extending the application with additional features
	•	Adding configuration options
	•	Implementing file I/O operations
🔧 Possible Extensions
Students can enhance this application by adding:
	1	File Operations: Load/save text files
	2	Configuration: Customizable space removal options
	3	History: Undo/redo functionality
	4	Batch Processing: Process multiple clipboard entries
	5	Regex Support: Advanced pattern-based formatting
🐛 Common Issues & Solutions
Issue: Application won't start
Solution: Ensure PyQt6 is properly installed: pip install PyQt6
Issue: Clipboard operations fail
Solution: Check system permissions for clipboard access
Issue: Text formatting looks wrong
Solution: Verify the text uses spaces (not tabs) for indentation
📝 Code Analysis Questions
Use these questions to help students understand the code:
	1	What happens if the clipboard is empty?
	2	How does the algorithm handle empty lines?
	3	Why is a monospace font important for this application?
	4	What would happen if we processed tabs instead of spaces?
	5	How could we modify the algorithm to handle mixed indentation?
🎯 Assignment Ideas
	1	Add a preview mode that shows changes before applying them
	2	Implement tab-to-space conversion as a preprocessing step
	3	Create a command-line version of the same functionality
	4	Add support for different indentation styles (2 spaces, 4 spaces, tabs)
	5	Implement a "smart" mode that detects the most common indentation
This application demonstrates how simple algorithms can solve everyday problems while teaching fundamental programming concepts in an engaging, practical way.
