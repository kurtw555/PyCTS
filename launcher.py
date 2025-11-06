"""
Map Application Launcher

Simple launcher to choose between basic and enhanced map applications.
"""

import sys
from PySide6.QtWidgets import QApplication, QDialog, QVBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt
import subprocess
import os


class LauncherDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Map Application Launcher")
        self.setFixedSize(300, 200)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Choose Map Application")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 20px;")
        layout.addWidget(title)
        
        # Basic app button
        basic_btn = QPushButton("Basic Map Application")
        basic_btn.setToolTip("Simple map viewer with basic features")
        basic_btn.clicked.connect(self.launch_basic)
        layout.addWidget(basic_btn)
        
        # Enhanced app button
        enhanced_btn = QPushButton("Enhanced Map Application")
        enhanced_btn.setToolTip("Advanced map viewer with multiple features and tabs")
        enhanced_btn.clicked.connect(self.launch_enhanced)
        layout.addWidget(enhanced_btn)
        
        # Example generator button
        example_btn = QPushButton("Generate Advanced Example")
        example_btn.setToolTip("Create an HTML file with advanced folium features")
        example_btn.clicked.connect(self.generate_example)
        layout.addWidget(example_btn)
        
        layout.addStretch()
    
    def launch_basic(self):
        """Launch the basic map application"""
        python_exe = "D:/python/PyCTS/.venv/Scripts/python.exe"
        script_path = os.path.join(os.path.dirname(__file__), "map_app.py")
        subprocess.Popen([python_exe, script_path])
        self.accept()
    
    def launch_enhanced(self):
        """Launch the enhanced map application"""
        python_exe = "D:/python/PyCTS/.venv/Scripts/python.exe"
        script_path = os.path.join(os.path.dirname(__file__), "enhanced_map_app.py")
        subprocess.Popen([python_exe, script_path])
        self.accept()
    
    def generate_example(self):
        """Generate the advanced example HTML file"""
        python_exe = "D:/python/PyCTS/.venv/Scripts/python.exe"
        script_path = os.path.join(os.path.dirname(__file__), "advanced_features.py")
        subprocess.Popen([python_exe, script_path])
        self.accept()


def main():
    app = QApplication(sys.argv)
    
    launcher = LauncherDialog()
    launcher.exec()


if __name__ == "__main__":
    main()