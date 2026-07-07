import sys
import os
import tempfile
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, 
                              QHBoxLayout, QWidget, QPushButton, QLineEdit, 
                              QLabel, QComboBox, QSpinBox, QGroupBox)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineSettings
from PySide6.QtCore import QUrl, QTimer, QObject, QThread, Signal, Slot

from weather.service import WeatherService


class WeatherFetchWorker(QObject):
    weather_ready = Signal(object, float, float, int)
    weather_failed = Signal(str, float, float, int)
    finished = Signal()

    def __init__(self, user_agent, cache_path, lat, lon, zoom, query):
        super().__init__()
        self.user_agent = user_agent
        self.cache_path = cache_path
        self.lat = lat
        self.lon = lon
        self.zoom = zoom
        self.query = query

    @Slot()
    def run(self):
        try:
            service = WeatherService(user_agent=self.user_agent, cache_path=self.cache_path)
            bundle = None
            if self.query:
                try:
                    bundle = service.get_weather_for_place(self.query)
                except Exception:
                    bundle = service.get_weather_for_coordinates(self.lat, self.lon)
            else:
                bundle = service.get_weather_for_coordinates(self.lat, self.lon)

            self.weather_ready.emit(bundle, bundle.latitude, bundle.longitude, self.zoom)
        except Exception as exc:
            self.weather_failed.emit(str(exc), self.lat, self.lon, self.zoom)
        finally:
            self.finished.emit()


class SimpleMapApplication(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simple Leaflet Map Viewer")
        self.setGeometry(100, 100, 1200, 800)
        
        # Initialize the map
        self.temp_file = None
        self.weather_service = WeatherService()
        self.weather_bundle = None
        self.weather_status = "Weather unavailable"
        self.weather_thread = None
        self.weather_worker = None
        
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
        self.lat_input = QLineEdit("33.95")
        location_layout.addWidget(self.lat_input)
        
        location_layout.addWidget(QLabel("Longitude:"))
        self.lon_input = QLineEdit("-83.383333")
        location_layout.addWidget(self.lon_input)
        
        location_layout.addWidget(QLabel("Zoom:"))
        self.zoom_input = QSpinBox()
        self.zoom_input.setRange(1, 18)
        self.zoom_input.setValue(10)
        location_layout.addWidget(self.zoom_input)

        location_layout.addWidget(QLabel("Place/ZIP:"))
        self.place_input = QLineEdit()
        self.place_input.setPlaceholderText("Optional (e.g. Seattle or 98101)")
        location_layout.addWidget(self.place_input)
        
        controls_layout.addLayout(location_layout)
        
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
        
        controls_layout.addLayout(button_layout)

        self.weather_status_label = QLabel("Weather: not loaded")
        controls_layout.addWidget(self.weather_status_label)
        
        main_layout.addWidget(controls_group)
        
        # Web view for the map
        self.web_view = QWebEngineView()
        
        # Configure web engine settings
        settings = self.web_view.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        
        main_layout.addWidget(self.web_view)
        
        # Set layout proportions
        main_layout.setStretch(0, 0)
        main_layout.setStretch(1, 1)
        
        # Initialize markers list
        self.markers = []
    
    def create_default_map(self):
        """Create the initial map"""
        self.update_map()
    
    def update_map(self):
        """Update the map with current settings"""
        try:
            lat = float(self.lat_input.text())
            lon = float(self.lon_input.text())
            zoom = self.zoom_input.value()
            query = self.place_input.text().strip()

            self.weather_bundle = None
            self.weather_status_label.setText("Weather: loading...")
            self.create_map_html(lat, lon, zoom)
            self._start_weather_fetch(lat, lon, zoom, query)
            
        except ValueError:
            print("Invalid latitude or longitude values")

    def _start_weather_fetch(self, lat, lon, zoom, query):
        """Fetch weather in a worker thread to keep UI responsive."""
        if self.weather_thread and self.weather_thread.isRunning():
            self.weather_status_label.setText("Weather: refresh already in progress")
            return

        self.update_btn.setEnabled(False)
        self.weather_thread = QThread(self)
        self.weather_worker = WeatherFetchWorker(
            self.weather_service.user_agent,
            self.weather_service.cache_path,
            lat,
            lon,
            zoom,
            query,
        )
        self.weather_worker.moveToThread(self.weather_thread)

        self.weather_thread.started.connect(self.weather_worker.run)
        self.weather_worker.weather_ready.connect(self._on_weather_ready)
        self.weather_worker.weather_failed.connect(self._on_weather_failed)
        self.weather_worker.finished.connect(self._cleanup_weather_thread)
        self.weather_worker.finished.connect(self.weather_thread.quit)

        self.weather_thread.start()

    @Slot(object, float, float, int)
    def _on_weather_ready(self, bundle, lat, lon, zoom):
        """Handle successful weather fetch and refresh weather details on map."""
        self.weather_bundle = bundle
        self.lat_input.setText(f"{lat:.4f}")
        self.lon_input.setText(f"{lon:.4f}")
        self.weather_status = self._build_weather_status()
        self.weather_status_label.setText(self.weather_status)
        self.create_map_html(lat, lon, zoom)

    @Slot(str, float, float, int)
    def _on_weather_failed(self, error_text, lat, lon, zoom):
        """Handle weather fetch failure without blocking map usage."""
        print(f"Weather lookup failed: {error_text}")
        self.weather_bundle = None
        self.weather_status_label.setText("Weather: unavailable")
        self.create_map_html(lat, lon, zoom)

    @Slot()
    def _cleanup_weather_thread(self):
        """Tear down worker thread objects after completion."""
        self.update_btn.setEnabled(True)
        if self.weather_worker:
            self.weather_worker.deleteLater()
            self.weather_worker = None
        if self.weather_thread:
            self.weather_thread.deleteLater()
            self.weather_thread = None
    
    def create_map_html(self, lat, lon, zoom):
        """Create HTML with embedded Leaflet map"""
        
        # Create markers HTML
        markers_html = ""
        for i, marker in enumerate(self.markers):
            markers_html += f"""
            var marker{i} = L.marker([{marker['lat']}, {marker['lon']}]).addTo(map);
            marker{i}.bindPopup("{marker['popup']}");
            """

        weather_popup = self._build_weather_popup().replace('"', '&quot;')
        markers_html += f"""
            var weatherMarker = L.marker([{lat}, {lon}]).addTo(map);
            weatherMarker.bindPopup("{weather_popup}");
        """
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Leaflet Map</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        body {{ margin: 0; padding: 0; }}
        #map {{ width: 100%; height: 100vh; }}
    </style>
</head>
<body>
    <div id="map"></div>
    <script>
        var map = L.map('map').setView([{lat}, {lon}], {zoom});
        
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            attribution: '© OpenStreetMap contributors'
        }}).addTo(map);
        
        {markers_html}
        
        console.log('Map loaded successfully');
    </script>
</body>
</html>
"""
        
        self.save_and_load_html(html_content)
    
    def save_and_load_html(self, html_content):
        """Save HTML and load in web view"""
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
        
        # Load in web view
        QTimer.singleShot(100, self.load_in_view)
    
    def load_in_view(self):
        """Load the HTML file in the web view"""
        if self.temp_file:
            file_url = QUrl.fromLocalFile(os.path.abspath(self.temp_file))
            self.web_view.setUrl(file_url)
    
    def add_marker(self):
        """Add a marker at current location"""
        try:
            lat = float(self.lat_input.text())
            lon = float(self.lon_input.text())
            
            marker = {
                'lat': lat,
                'lon': lon,
                'popup': f'Marker at ({lat:.4f}, {lon:.4f})'
            }
            
            self.markers.append(marker)
            self.update_map()
            
        except ValueError:
            print("Invalid coordinates")
    
    def clear_markers(self):
        """Clear all markers"""
        self.markers = []
        self.update_map()

    def _build_weather_popup(self):
        """Build a compact weather popup from the latest forecast bundle."""
        if not self.weather_bundle:
            return "Weather data unavailable"

        lines = self.weather_bundle.summary_lines()
        popup_text = "<b>Weather</b><br>" + "<br>".join(lines)
        return popup_text.replace("'", "&#39;")

    def _build_weather_status(self):
        """Build weather status text shown below controls."""
        if not self.weather_bundle:
            return "Weather: unavailable"

        prefix = "Weather: stale cache" if self.weather_bundle.stale else "Weather: live"
        summary = self.weather_bundle.summary_lines()
        if summary:
            return f"{prefix} | {summary[0]}"
        return prefix
    
    def closeEvent(self, event):
        """Clean up on close"""
        if self.weather_thread and self.weather_thread.isRunning():
            self.weather_thread.quit()
            self.weather_thread.wait(2000)

        if self.temp_file and os.path.exists(self.temp_file):
            try:
                os.remove(self.temp_file)
            except:
                pass
        event.accept()


def main():
    app = QApplication(sys.argv)
    window = SimpleMapApplication()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()