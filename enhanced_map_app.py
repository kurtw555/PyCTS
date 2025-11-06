import sys
import os
import tempfile
import random
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, 
                              QHBoxLayout, QWidget, QPushButton, QLineEdit, 
                              QLabel, QComboBox, QSpinBox, QGroupBox, 
                              QCheckBox, QTabWidget, QTextEdit, QSlider,
                              QColorDialog, QMessageBox)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl, Qt
from PySide6.QtGui import QColor
import folium
from folium import plugins


class EnhancedMapApplication(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Enhanced PySide6 + Folium Map Viewer")
        self.setGeometry(100, 100, 1400, 900)
        
        # Initialize the map and data
        self.current_map = None
        self.temp_file = None
        self.markers = []
        self.shapes = []
        self.heat_data = []
        
        self.setup_ui()
        self.create_default_map()
    
    def setup_ui(self):
        """Set up the enhanced user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Left panel with controls
        left_panel = QWidget()
        left_panel.setMaximumWidth(350)
        left_layout = QVBoxLayout(left_panel)
        
        # Create tabbed interface for controls
        tabs = QTabWidget()
        
        # Basic controls tab
        basic_tab = self.create_basic_controls_tab()
        tabs.addTab(basic_tab, "Basic")
        
        # Advanced features tab
        advanced_tab = self.create_advanced_features_tab()
        tabs.addTab(advanced_tab, "Features")
        
        # Data tab
        data_tab = self.create_data_tab()
        tabs.addTab(data_tab, "Data")
        
        left_layout.addWidget(tabs)
        
        # Web view for the map
        self.web_view = QWebEngineView()
        
        # Add to main layout
        main_layout.addWidget(left_panel)
        main_layout.addWidget(self.web_view)
        
        # Set layout proportions
        main_layout.setStretch(0, 0)  # Controls take minimal space
        main_layout.setStretch(1, 1)  # Map takes remaining space
    
    def create_basic_controls_tab(self):
        """Create the basic controls tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Location controls
        location_group = QGroupBox("Location")
        location_layout = QVBoxLayout(location_group)
        
        # Coordinate inputs
        coord_layout = QHBoxLayout()
        coord_layout.addWidget(QLabel("Lat:"))
        self.lat_input = QLineEdit("37.7749")
        coord_layout.addWidget(self.lat_input)
        
        coord_layout.addWidget(QLabel("Lon:"))
        self.lon_input = QLineEdit("-122.4194")
        coord_layout.addWidget(self.lon_input)
        
        location_layout.addLayout(coord_layout)
        
        # Zoom control
        zoom_layout = QHBoxLayout()
        zoom_layout.addWidget(QLabel("Zoom:"))
        self.zoom_input = QSpinBox()
        self.zoom_input.setRange(1, 18)
        self.zoom_input.setValue(10)
        zoom_layout.addWidget(self.zoom_input)
        location_layout.addLayout(zoom_layout)
        
        layout.addWidget(location_group)
        
        # Map style controls
        style_group = QGroupBox("Map Style")
        style_layout = QVBoxLayout(style_group)
        
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
        
        layout.addWidget(style_group)
        
        # Basic action buttons
        button_group = QGroupBox("Actions")
        button_layout = QVBoxLayout(button_group)
        
        self.update_btn = QPushButton("Update Map")
        self.update_btn.clicked.connect(self.update_map)
        button_layout.addWidget(self.update_btn)
        
        self.add_marker_btn = QPushButton("Add Marker")
        self.add_marker_btn.clicked.connect(self.add_marker)
        button_layout.addWidget(self.add_marker_btn)
        
        self.clear_all_btn = QPushButton("Clear All")
        self.clear_all_btn.clicked.connect(self.clear_all)
        button_layout.addWidget(self.clear_all_btn)
        
        layout.addWidget(button_group)
        
        layout.addStretch()
        return tab
    
    def create_advanced_features_tab(self):
        """Create the advanced features tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Layer controls
        layers_group = QGroupBox("Map Layers")
        layers_layout = QVBoxLayout(layers_group)
        
        self.minimap_check = QCheckBox("Show Minimap")
        layers_layout.addWidget(self.minimap_check)
        
        self.fullscreen_check = QCheckBox("Fullscreen Control")
        layers_layout.addWidget(self.fullscreen_check)
        
        self.measure_check = QCheckBox("Measure Tool")
        layers_layout.addWidget(self.measure_check)
        
        self.draw_check = QCheckBox("Drawing Tools")
        layers_layout.addWidget(self.draw_check)
        
        layout.addWidget(layers_group)
        
        # Shape controls
        shapes_group = QGroupBox("Shapes")
        shapes_layout = QVBoxLayout(shapes_group)
        
        self.add_circle_btn = QPushButton("Add Circle")
        self.add_circle_btn.clicked.connect(self.add_circle)
        shapes_layout.addWidget(self.add_circle_btn)
        
        self.add_polygon_btn = QPushButton("Add Polygon")
        self.add_polygon_btn.clicked.connect(self.add_polygon)
        shapes_layout.addWidget(self.add_polygon_btn)
        
        # Circle radius
        radius_layout = QHBoxLayout()
        radius_layout.addWidget(QLabel("Radius (m):"))
        self.radius_input = QSpinBox()
        self.radius_input.setRange(100, 10000)
        self.radius_input.setValue(500)
        self.radius_input.setSingleStep(100)
        radius_layout.addWidget(self.radius_input)
        shapes_layout.addLayout(radius_layout)
        
        # Shape color
        self.color_btn = QPushButton("Choose Color")
        self.color_btn.clicked.connect(self.choose_color)
        self.current_color = "#FF0000"
        self.color_btn.setStyleSheet(f"background-color: {self.current_color}")
        shapes_layout.addWidget(self.color_btn)
        
        layout.addWidget(shapes_group)
        
        # Clustering
        cluster_group = QGroupBox("Clustering")
        cluster_layout = QVBoxLayout(cluster_group)
        
        self.cluster_check = QCheckBox("Enable Marker Clustering")
        cluster_layout.addWidget(self.cluster_check)
        
        layout.addWidget(cluster_group)
        
        layout.addStretch()
        return tab
    
    def create_data_tab(self):
        """Create the data management tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Sample data
        sample_group = QGroupBox("Sample Data")
        sample_layout = QVBoxLayout(sample_group)
        
        self.sample_cities_btn = QPushButton("Load US Cities")
        self.sample_cities_btn.clicked.connect(self.load_sample_cities)
        sample_layout.addWidget(self.sample_cities_btn)
        
        self.sample_world_btn = QPushButton("Load World Capitals")
        self.sample_world_btn.clicked.connect(self.load_world_capitals)
        sample_layout.addWidget(self.sample_world_btn)
        
        layout.addWidget(sample_group)
        
        # Heatmap
        heatmap_group = QGroupBox("Heatmap")
        heatmap_layout = QVBoxLayout(heatmap_group)
        
        self.generate_heat_btn = QPushButton("Generate Random Heat Data")
        self.generate_heat_btn.clicked.connect(self.generate_heat_data)
        heatmap_layout.addWidget(self.generate_heat_btn)
        
        self.show_heatmap_check = QCheckBox("Show Heatmap")
        self.show_heatmap_check.stateChanged.connect(self.update_map)
        heatmap_layout.addWidget(self.show_heatmap_check)
        
        # Heat intensity
        intensity_layout = QHBoxLayout()
        intensity_layout.addWidget(QLabel("Intensity:"))
        self.heat_intensity = QSlider(Qt.Horizontal)
        self.heat_intensity.setRange(1, 10)
        self.heat_intensity.setValue(5)
        self.heat_intensity.valueChanged.connect(self.update_map)
        intensity_layout.addWidget(self.heat_intensity)
        heatmap_layout.addLayout(intensity_layout)
        
        layout.addWidget(heatmap_group)
        
        # Statistics
        stats_group = QGroupBox("Statistics")
        stats_layout = QVBoxLayout(stats_group)
        
        self.stats_text = QTextEdit()
        self.stats_text.setMaximumHeight(100)
        self.stats_text.setReadOnly(True)
        stats_layout.addWidget(self.stats_text)
        
        layout.addWidget(stats_group)
        
        layout.addStretch()
        return tab
    
    def update_map(self):
        """Update the map with all current settings"""
        try:
            # Get current values
            lat = float(self.lat_input.text())
            lon = float(self.lon_input.text())
            zoom = self.zoom_input.value()
            style = self.style_combo.currentText()
            
            # Create folium map
            self.current_map = folium.Map(
                location=[lat, lon],
                zoom_start=zoom,
                tiles=self.get_tile_layer(style)
            )
            
            # Add features based on checkboxes
            if hasattr(self, 'minimap_check') and self.minimap_check.isChecked():
                minimap = plugins.MiniMap()
                self.current_map.add_child(minimap)
            
            if hasattr(self, 'fullscreen_check') and self.fullscreen_check.isChecked():
                plugins.Fullscreen().add_to(self.current_map)
            
            if hasattr(self, 'measure_check') and self.measure_check.isChecked():
                plugins.MeasureControl().add_to(self.current_map)
            
            if hasattr(self, 'draw_check') and self.draw_check.isChecked():
                draw = plugins.Draw(export=True)
                draw.add_to(self.current_map)
            
            # Add markers
            if hasattr(self, 'cluster_check') and self.cluster_check.isChecked():
                # Use marker clustering
                marker_cluster = plugins.MarkerCluster().add_to(self.current_map)
                for marker_data in self.markers:
                    folium.Marker(
                        location=marker_data['location'],
                        popup=marker_data['popup'],
                        tooltip=marker_data['tooltip']
                    ).add_to(marker_cluster)
            else:
                # Regular markers
                for marker_data in self.markers:
                    folium.Marker(
                        location=marker_data['location'],
                        popup=marker_data['popup'],
                        tooltip=marker_data['tooltip']
                    ).add_to(self.current_map)
            
            # Add shapes
            for shape_data in self.shapes:
                if shape_data['type'] == 'circle':
                    folium.Circle(
                        location=shape_data['location'],
                        radius=shape_data['radius'],
                        popup=shape_data['popup'],
                        color=shape_data['color'],
                        fill=True,
                        fillOpacity=0.3
                    ).add_to(self.current_map)
                elif shape_data['type'] == 'polygon':
                    folium.Polygon(
                        locations=shape_data['locations'],
                        popup=shape_data['popup'],
                        color=shape_data['color'],
                        fill=True,
                        fillOpacity=0.3
                    ).add_to(self.current_map)
            
            # Add heatmap if enabled
            if (hasattr(self, 'show_heatmap_check') and 
                self.show_heatmap_check.isChecked() and 
                self.heat_data):
                
                # Adjust intensity
                intensity = self.heat_intensity.value() / 5.0
                adjusted_heat_data = [
                    [point[0], point[1], point[2] * intensity] 
                    for point in self.heat_data
                ]
                plugins.HeatMap(adjusted_heat_data).add_to(self.current_map)
            
            # Update statistics
            self.update_statistics()
            
            # Save and load map
            self.save_and_load_map()
            
        except ValueError as e:
            QMessageBox.warning(self, "Error", f"Invalid input: {str(e)}")
    
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
        self.update_map()
    
    def add_marker(self):
        """Add a marker at the current center location"""
        try:
            lat = float(self.lat_input.text())
            lon = float(self.lon_input.text())
            
            marker_data = {
                'location': [lat, lon],
                'popup': f"Marker #{len(self.markers) + 1}<br>({lat:.4f}, {lon:.4f})",
                'tooltip': f"Marker {len(self.markers) + 1}"
            }
            
            self.markers.append(marker_data)
            self.update_map()
            
        except ValueError:
            QMessageBox.warning(self, "Error", "Invalid latitude or longitude values")
    
    def add_circle(self):
        """Add a circle at the current center location"""
        try:
            lat = float(self.lat_input.text())
            lon = float(self.lon_input.text())
            radius = self.radius_input.value()
            
            shape_data = {
                'type': 'circle',
                'location': [lat, lon],
                'radius': radius,
                'popup': f"Circle {len(self.shapes) + 1}<br>Radius: {radius}m",
                'color': self.current_color
            }
            
            self.shapes.append(shape_data)
            self.update_map()
            
        except ValueError:
            QMessageBox.warning(self, "Error", "Invalid coordinates")
    
    def add_polygon(self):
        """Add a sample polygon around the current center"""
        try:
            lat = float(self.lat_input.text())
            lon = float(self.lon_input.text())
            
            # Create a simple square polygon
            offset = 0.01
            polygon_coords = [
                [lat + offset, lon + offset],
                [lat + offset, lon - offset],
                [lat - offset, lon - offset],
                [lat - offset, lon + offset]
            ]
            
            shape_data = {
                'type': 'polygon',
                'locations': polygon_coords,
                'popup': f"Polygon {len(self.shapes) + 1}",
                'color': self.current_color
            }
            
            self.shapes.append(shape_data)
            self.update_map()
            
        except ValueError:
            QMessageBox.warning(self, "Error", "Invalid coordinates")
    
    def choose_color(self):
        """Open color picker dialog"""
        color = QColorDialog.getColor(QColor(self.current_color), self)
        if color.isValid():
            self.current_color = color.name()
            self.color_btn.setStyleSheet(f"background-color: {self.current_color}")
    
    def clear_all(self):
        """Clear all markers, shapes, and heat data"""
        self.markers = []
        self.shapes = []
        self.heat_data = []
        self.show_heatmap_check.setChecked(False)
        self.update_map()
    
    def load_sample_cities(self):
        """Load sample US city markers"""
        cities = [
            {"lat": 37.7749, "lon": -122.4194, "name": "San Francisco, CA"},
            {"lat": 40.7128, "lon": -74.0060, "name": "New York City, NY"},
            {"lat": 34.0522, "lon": -118.2437, "name": "Los Angeles, CA"},
            {"lat": 41.8781, "lon": -87.6298, "name": "Chicago, IL"},
            {"lat": 25.7617, "lon": -80.1918, "name": "Miami, FL"},
            {"lat": 47.6062, "lon": -122.3321, "name": "Seattle, WA"},
            {"lat": 39.2904, "lon": -76.6122, "name": "Baltimore, MD"},
            {"lat": 32.7767, "lon": -96.7970, "name": "Dallas, TX"},
        ]
        
        self.markers = []
        for city in cities:
            marker_data = {
                'location': [city['lat'], city['lon']],
                'popup': f"<b>{city['name']}</b><br>Lat: {city['lat']}<br>Lon: {city['lon']}",
                'tooltip': city['name']
            }
            self.markers.append(marker_data)
        
        # Center on USA
        self.lat_input.setText("39.8283")
        self.lon_input.setText("-98.5795")
        self.zoom_input.setValue(4)
        self.update_map()
    
    def load_world_capitals(self):
        """Load world capital markers"""
        capitals = [
            {"lat": 51.5074, "lon": -0.1278, "name": "London, UK"},
            {"lat": 48.8566, "lon": 2.3522, "name": "Paris, France"},
            {"lat": 35.6762, "lon": 139.6503, "name": "Tokyo, Japan"},
            {"lat": -33.8688, "lon": 151.2093, "name": "Sydney, Australia"},
            {"lat": 55.7558, "lon": 37.6173, "name": "Moscow, Russia"},
            {"lat": 39.9042, "lon": 116.4074, "name": "Beijing, China"},
            {"lat": 28.6139, "lon": 77.2090, "name": "New Delhi, India"},
            {"lat": -23.5505, "lon": -46.6333, "name": "São Paulo, Brazil"},
        ]
        
        self.markers = []
        for capital in capitals:
            marker_data = {
                'location': [capital['lat'], capital['lon']],
                'popup': f"<b>{capital['name']}</b><br>Capital City",
                'tooltip': capital['name']
            }
            self.markers.append(marker_data)
        
        # Center on world view
        self.lat_input.setText("30")
        self.lon_input.setText("0")
        self.zoom_input.setValue(2)
        self.update_map()
    
    def generate_heat_data(self):
        """Generate random heat data points"""
        try:
            lat = float(self.lat_input.text())
            lon = float(self.lon_input.text())
            
            self.heat_data = []
            for _ in range(200):
                # Generate points within a reasonable area
                heat_lat = lat + random.uniform(-0.05, 0.05)
                heat_lon = lon + random.uniform(-0.05, 0.05)
                intensity = random.uniform(0.1, 1.0)
                self.heat_data.append([heat_lat, heat_lon, intensity])
            
            self.show_heatmap_check.setChecked(True)
            self.update_map()
            
        except ValueError:
            QMessageBox.warning(self, "Error", "Invalid coordinates")
    
    def update_statistics(self):
        """Update the statistics display"""
        stats = [
            f"Markers: {len(self.markers)}",
            f"Shapes: {len(self.shapes)}",
            f"Heat Points: {len(self.heat_data)}",
            f"Current Zoom: {self.zoom_input.value()}",
            f"Map Style: {self.style_combo.currentText()}"
        ]
        self.stats_text.setText("\n".join(stats))
    
    def save_and_load_map(self):
        """Save the current map to a temporary file and load it in the web view"""
        if self.current_map:
            # Clean up previous temp file
            if self.temp_file and os.path.exists(self.temp_file):
                try:
                    os.remove(self.temp_file)
                except:
                    pass
            
            # Create new temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
                self.temp_file = f.name
                self.current_map.save(f.name)
            
            # Load in web view
            self.web_view.setUrl(QUrl.fromLocalFile(os.path.abspath(self.temp_file)))
    
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
    window = EnhancedMapApplication()
    window.show()
    
    # Run the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()