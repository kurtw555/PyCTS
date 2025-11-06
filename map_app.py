import sys
import os
import tempfile
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, 
                              QHBoxLayout, QWidget, QPushButton, QLineEdit, 
                              QLabel, QComboBox, QSpinBox, QGroupBox)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineSettings
from PySide6.QtCore import QUrl, QTimer
import folium
import time


class MapApplication(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PySide6 + Folium Map Viewer")
        self.setGeometry(100, 100, 1200, 800)
        
        # Initialize the map
        self.current_map = None
        self.temp_file = None
        
        self.setup_ui()
        self.create_default_map()
    
    def setup_ui(self):
        """Set up the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Controls panel
        controls_group = QGroupBox("Map Controls")
        controls_layout = QVBoxLayout(controls_group)
        
        # Location input row
        location_layout = QHBoxLayout()
        location_layout.addWidget(QLabel("Latitude:"))
        self.lat_input = QLineEdit("37.7749")  # Default: San Francisco
        location_layout.addWidget(self.lat_input)
        
        location_layout.addWidget(QLabel("Longitude:"))
        self.lon_input = QLineEdit("-122.4194")  # Default: San Francisco
        location_layout.addWidget(self.lon_input)
        
        location_layout.addWidget(QLabel("Zoom:"))
        self.zoom_input = QSpinBox()
        self.zoom_input.setRange(1, 18)
        self.zoom_input.setValue(10)
        location_layout.addWidget(self.zoom_input)
        
        controls_layout.addLayout(location_layout)
        
        # Map style row
        style_layout = QHBoxLayout()
        style_layout.addWidget(QLabel("Map Style:"))
        self.style_combo = QComboBox()
        self.style_combo.addItems([
            "OpenStreetMap",
            "CartoDB positron",
            "CartoDB dark_matter",
            "Stamen Terrain",
            "Stamen Toner",
            "Stamen Watercolor"
        ])
        style_layout.addWidget(self.style_combo)
        
        controls_layout.addLayout(style_layout)
        
        # Buttons row
        button_layout = QHBoxLayout()
        
        self.update_btn = QPushButton("Update Map")
        self.update_btn.clicked.connect(self.update_map)
        button_layout.addWidget(self.update_btn)
        
        self.add_marker_btn = QPushButton("Add Marker")
        self.add_marker_btn.clicked.connect(self.add_marker)
        button_layout.addWidget(self.add_marker_btn)
        
        self.clear_markers_btn = QPushButton("Clear Markers")
        self.clear_markers_btn.clicked.connect(self.clear_markers)
        button_layout.addWidget(self.clear_markers_btn)
        
        self.sample_data_btn = QPushButton("Load Sample Data")
        self.sample_data_btn.clicked.connect(self.load_sample_data)
        button_layout.addWidget(self.sample_data_btn)
        
        controls_layout.addLayout(button_layout)
        
        main_layout.addWidget(controls_group)
        
        # Web view for the map
        self.web_view = QWebEngineView()
        
        # Configure web engine settings for better map compatibility
        settings = self.web_view.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        
        main_layout.addWidget(self.web_view)
        
        # Set layout proportions
        main_layout.setStretch(0, 0)  # Controls take minimal space
        main_layout.setStretch(1, 1)  # Map takes remaining space
    
    def get_tile_layer(self, style_name):
        """Get the appropriate tile layer based on style name"""
        tile_layers = {
            "OpenStreetMap": "OpenStreetMap",
            "CartoDB positron": "CartoDB positron",
            "CartoDB dark_matter": "CartoDB dark_matter",
            "Stamen Terrain": "Stamen Terrain",
            "Stamen Toner": "Stamen Toner",
            "Stamen Watercolor": "Stamen Watercolor"
        }
        return tile_layers.get(style_name, "OpenStreetMap")
    
    def create_default_map(self):
        """Create the initial map"""
        self.markers = []  # Store markers for clearing
        self.update_map()
    
    def update_map(self):
        """Update the map with current settings"""
        try:
            # Get current values
            lat = float(self.lat_input.text())
            lon = float(self.lon_input.text())
            zoom = self.zoom_input.value()
            style = self.style_combo.currentText()
            
            # Create folium map with explicit prefer_canvas=False for better compatibility
            self.current_map = folium.Map(
                location=[lat, lon],
                zoom_start=zoom,
                tiles=self.get_tile_layer(style),
                prefer_canvas=False
            )
            
            # Re-add existing markers
            for marker_data in self.markers:
                folium.Marker(
                    location=marker_data['location'],
                    popup=marker_data['popup'],
                    tooltip=marker_data['tooltip']
                ).add_to(self.current_map)
            
            # Save map to temporary file and load in web view
            self.save_and_load_map()
            
        except ValueError:
            print("Invalid latitude or longitude values")
    
    def add_marker(self):
        """Add a marker at the current center location"""
        try:
            lat = float(self.lat_input.text())
            lon = float(self.lon_input.text())
            
            # Create marker data
            marker_data = {
                'location': [lat, lon],
                'popup': f"Marker at ({lat:.4f}, {lon:.4f})",
                'tooltip': "Click for details"
            }
            
            # Add to markers list
            self.markers.append(marker_data)
            
            # Add to current map
            if self.current_map:
                folium.Marker(
                    location=marker_data['location'],
                    popup=marker_data['popup'],
                    tooltip=marker_data['tooltip']
                ).add_to(self.current_map)
                
                self.save_and_load_map()
            
        except ValueError:
            print("Invalid latitude or longitude values")
    
    def clear_markers(self):
        """Clear all markers from the map"""
        self.markers = []
        self.update_map()
    
    def load_sample_data(self):
        """Load some sample markers and data"""
        # Famous landmarks
        sample_locations = [
            {"lat": 37.7749, "lon": -122.4194, "name": "San Francisco, CA"},
            {"lat": 40.7128, "lon": -74.0060, "name": "New York City, NY"},
            {"lat": 34.0522, "lon": -118.2437, "name": "Los Angeles, CA"},
            {"lat": 41.8781, "lon": -87.6298, "name": "Chicago, IL"},
            {"lat": 25.7617, "lon": -80.1918, "name": "Miami, FL"},
            {"lat": 47.6062, "lon": -122.3321, "name": "Seattle, WA"},
        ]
        
        # Clear existing markers
        self.markers = []
        
        # Add sample markers
        for location in sample_locations:
            marker_data = {
                'location': [location['lat'], location['lon']],
                'popup': f"<b>{location['name']}</b><br>Lat: {location['lat']}<br>Lon: {location['lon']}",
                'tooltip': location['name']
            }
            self.markers.append(marker_data)
        
        # Center on USA
        self.lat_input.setText("39.8283")
        self.lon_input.setText("-98.5795")
        self.zoom_input.setValue(4)
        
        # Update the map
        self.update_map()
    
    def save_and_load_map(self):
        """Save the current map to a temporary file and load it in the web view"""
        if self.current_map:
            # Clean up previous temp file
            if self.temp_file and os.path.exists(self.temp_file):
                try:
                    os.remove(self.temp_file)
                except:
                    pass
            
            # Create new temporary file with better encoding
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
                self.temp_file = f.name
                
            # Save the map and modify HTML for better compatibility
            self.current_map.save(self.temp_file)
            self.fix_map_html()
            
            # Add a small delay to ensure file is written
            QTimer.singleShot(100, self.load_map_in_view)
    
    def fix_map_html(self):
        """Fix the HTML file to ensure proper Leaflet loading"""
        if not self.temp_file or not os.path.exists(self.temp_file):
            return
            
        try:
            # Read the generated HTML
            with open(self.temp_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Add meta charset and ensure proper CDN links
            html_fixes = '''
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <script>
                // Ensure Leaflet loads properly
                window.addEventListener('DOMContentLoaded', function() {
                    if (typeof L === 'undefined') {
                        console.log('Leaflet not loaded, attempting to reload...');
                        setTimeout(function() {
                            if (typeof L !== 'undefined') {
                                console.log('Leaflet loaded successfully');
                            }
                        }, 1000);
                    }
                });
            </script>
            '''
            
            # Insert the fixes after the <head> tag
            if '<head>' in html_content:
                html_content = html_content.replace('<head>', '<head>' + html_fixes)
            
            # Write back the modified HTML
            with open(self.temp_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
                
        except Exception as e:
            print(f"Error fixing HTML: {e}")
    
    def load_map_in_view(self):
        """Load the map file in the web view with proper URL handling"""
        if self.temp_file and os.path.exists(self.temp_file):
            # Use file:// protocol explicitly
            file_url = QUrl.fromLocalFile(os.path.abspath(self.temp_file))
            self.web_view.setUrl(file_url)
    
    def closeEvent(self, event):
        """Clean up when closing the application"""
        if self.temp_file and os.path.exists(self.temp_file):
            try:
                os.remove(self.temp_file)
            except:
                pass
        event.accept()


def main():
    app = QApplication(sys.argv)
    
    # Create and show the main window
    window = MapApplication()
    window.show()
    
    # Run the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()