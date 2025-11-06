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
import json


class MapApplication(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PySide6 + Folium Map Viewer (Fixed)")
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
            "CartoDB dark_matter"
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
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        
        main_layout.addWidget(self.web_view)
        
        # Set layout proportions
        main_layout.setStretch(0, 0)  # Controls take minimal space
        main_layout.setStretch(1, 1)  # Map takes remaining space
    
    def get_tile_url(self, style_name):
        """Get the tile URL for the given style"""
        tile_urls = {
            "OpenStreetMap": "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            "CartoDB positron": "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
            "CartoDB dark_matter": "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        }
        return tile_urls.get(style_name, tile_urls["OpenStreetMap"])
    
    def get_tile_attribution(self, style_name):
        """Get the attribution for the given style"""
        attributions = {
            "OpenStreetMap": "&copy; <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a> contributors",
            "CartoDB positron": "&copy; <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a> contributors &copy; <a href='https://carto.com/attributions'>CARTO</a>",
            "CartoDB dark_matter": "&copy; <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a> contributors &copy; <a href='https://carto.com/attributions'>CARTO</a>"
        }
        return attributions.get(style_name, attributions["OpenStreetMap"])
    
    def create_default_map(self):
        """Create the initial map"""
        self.markers = []  # Store markers for clearing
        self.update_map()
    
    def update_map(self):
        """Update the map with current settings using custom HTML"""
        try:
            # Get current values
            lat = float(self.lat_input.text())
            lon = float(self.lon_input.text())
            zoom = self.zoom_input.value()
            style = self.style_combo.currentText()
            
            # Create custom HTML instead of using folium
            self.create_custom_map_html(lat, lon, zoom, style)
            
        except ValueError:
            print("Invalid latitude or longitude values")
    
    def create_custom_map_html(self, lat, lon, zoom, style):
        """Create a custom HTML file with embedded Leaflet"""
        tile_url = self.get_tile_url(style)
        attribution = self.get_tile_attribution(style)
        
        # Prepare markers data - ensure proper JSON escaping
        markers_json = json.dumps(self.markers).replace("'", "\\'")
        
        html_content = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Map</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
          integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="
          crossorigin=""/>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
            integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo="
            crossorigin=""></script>
    <style>
        body {{
            margin: 0;
            padding: 0;
        }}
        #map {{
            width: 100%;
            height: 100vh;
        }}
    </style>
</head>
<body>
    <div id="map"></div>
    <script>
        // Initialize the map
        var map = L.map('map').setView([{lat}, {lon}], {zoom});
        
        // Add tile layer
        L.tileLayer('{tile_url}', {{
            attribution: '{attribution}',
            maxZoom: 18
        }}).addTo(map);
        
        // Add markers
        var markersData = {markers_json};
        markersData.forEach(function(markerData) {{
            var marker = L.marker(markerData.location).addTo(map);
            if (markerData.popup) {{
                marker.bindPopup(markerData.popup);
            }}
            if (markerData.tooltip) {{
                marker.bindTooltip(markerData.tooltip);
            }}
        }});
        
        console.log('Map initialized successfully with', markersData.length, 'markers');
    </script>
</body>
</html>'''
        
        # Save the HTML content
        self.save_custom_html(html_content)
    
    def save_custom_html(self, html_content):
        """Save the custom HTML and load it in the web view"""
        # Clean up previous temp file
        if self.temp_file and os.path.exists(self.temp_file):
            try:
                os.remove(self.temp_file)
            except:
                pass
        
        # Create new temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            self.temp_file = f.name
            f.write(html_content)
        
        # Load in web view with a small delay
        QTimer.singleShot(100, self.load_map_in_view)
    
    def load_map_in_view(self):
        """Load the map file in the web view"""
        if self.temp_file and os.path.exists(self.temp_file):
            file_url = QUrl.fromLocalFile(os.path.abspath(self.temp_file))
            self.web_view.setUrl(file_url)
    
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
            
            # Update the map
            self.update_map()
            
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