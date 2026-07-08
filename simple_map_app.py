import sys
import os
import tempfile
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, 
                              QHBoxLayout, QWidget, QPushButton, QLineEdit, 
                              QLabel, QComboBox, QSpinBox, QGroupBox,
                              QCheckBox, QSlider)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineSettings
from PySide6.QtCore import QUrl, QTimer, QObject, QThread, Signal, Slot, Qt

from weather.radar import RadarTimeIndexService
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


class RadarTimelineWorker(QObject):
    timeline_ready = Signal(object)
    timeline_failed = Signal(str)
    finished = Signal()

    def __init__(self, user_agent, limit=60):
        super().__init__()
        self.user_agent = user_agent
        self.limit = limit

    @Slot()
    def run(self):
        try:
            service = RadarTimeIndexService(self.user_agent)
            frames = service.get_recent_frames(limit=self.limit)
            self.timeline_ready.emit([f.__dict__ for f in frames])
        except Exception as exc:
            self.timeline_failed.emit(str(exc))
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
        self.radar_service = RadarTimeIndexService(self.weather_service.user_agent)
        self.radar_enabled = False
        self.radar_live_mode = True
        self.radar_frames = []
        self.radar_selected_time_ms = None
        self.radar_thread = None
        self.radar_worker = None
        self.radar_refresh_timer = QTimer(self)
        self.radar_refresh_timer.setInterval(60000)
        self.radar_refresh_timer.timeout.connect(self._refresh_radar_timeline)
        
        self.setup_ui()
        self.web_view.loadFinished.connect(self._on_map_load_finished)
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

        radar_group = QGroupBox("Radar")
        radar_layout = QVBoxLayout(radar_group)

        radar_toggle_layout = QHBoxLayout()
        self.radar_enable_check = QCheckBox("Enable Radar Overlay")
        self.radar_enable_check.toggled.connect(self._on_radar_enabled_toggled)
        radar_toggle_layout.addWidget(self.radar_enable_check)

        self.radar_live_check = QCheckBox("Latest")
        self.radar_live_check.setChecked(True)
        self.radar_live_check.setEnabled(False)
        self.radar_live_check.toggled.connect(self._on_radar_live_toggled)
        radar_toggle_layout.addWidget(self.radar_live_check)
        radar_layout.addLayout(radar_toggle_layout)

        self.radar_time_slider = QSlider(Qt.Orientation.Horizontal)
        self.radar_time_slider.setRange(0, 0)
        self.radar_time_slider.setEnabled(False)
        self.radar_time_slider.valueChanged.connect(self._on_radar_slider_changed)
        radar_layout.addWidget(self.radar_time_slider)

        self.radar_time_label = QLabel("Radar time: latest")
        radar_layout.addWidget(self.radar_time_label)

        self.radar_status_label = QLabel("Radar: disabled")
        radar_layout.addWidget(self.radar_status_label)

        controls_layout.addWidget(radar_group)
        
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

    def _start_radar_timeline_fetch(self, force=False):
        """Fetch recent radar frame timestamps without blocking UI."""
        if self.radar_thread and self.radar_thread.isRunning():
            return
        if self.radar_frames and not force:
            return

        self.radar_status_label.setText("Radar: loading timeline...")
        self.radar_thread = QThread(self)
        self.radar_worker = RadarTimelineWorker(self.weather_service.user_agent, limit=60)
        self.radar_worker.moveToThread(self.radar_thread)

        self.radar_thread.started.connect(self.radar_worker.run)
        self.radar_worker.timeline_ready.connect(self._on_radar_timeline_ready)
        self.radar_worker.timeline_failed.connect(self._on_radar_timeline_failed)
        self.radar_worker.finished.connect(self._cleanup_radar_thread)
        self.radar_worker.finished.connect(self.radar_thread.quit)

        self.radar_thread.start()

    @Slot(object)
    def _on_radar_timeline_ready(self, frames_payload):
        """Store timeline and update slider state."""
        self.radar_frames = frames_payload or []
        if not self.radar_frames:
            self.radar_time_slider.setEnabled(False)
            self.radar_live_check.setEnabled(False)
            self.radar_status_label.setText("Radar: no frames available")
            return

        self.radar_time_slider.blockSignals(True)
        self.radar_time_slider.setRange(0, len(self.radar_frames) - 1)
        self.radar_time_slider.setEnabled(not self.radar_live_mode)
        self.radar_live_check.setEnabled(True)

        if self.radar_live_mode or self.radar_selected_time_ms is None:
            self.radar_time_slider.setValue(0)
            self.radar_selected_time_ms = int(self.radar_frames[0]["valid_time_ms"])
        else:
            selected_index = 0
            for i, frame in enumerate(self.radar_frames):
                if int(frame["valid_time_ms"]) == int(self.radar_selected_time_ms):
                    selected_index = i
                    break
            self.radar_time_slider.setValue(selected_index)
        self.radar_time_slider.blockSignals(False)

        self._update_radar_time_label()
        self.radar_status_label.setText("Radar: timeline ready")
        self._apply_radar_state_to_map()

    @Slot(str)
    def _on_radar_timeline_failed(self, error_text):
        """Handle timeline loading failures gracefully."""
        self.radar_status_label.setText("Radar: timeline unavailable")
        print(f"Radar timeline fetch failed: {error_text}")

    @Slot()
    def _cleanup_radar_thread(self):
        """Tear down radar worker thread objects."""
        if self.radar_worker:
            self.radar_worker.deleteLater()
            self.radar_worker = None
        if self.radar_thread:
            self.radar_thread.deleteLater()
            self.radar_thread = None

    @Slot(bool)
    def _on_radar_enabled_toggled(self, enabled):
        """Enable/disable radar overlay and timeline controls."""
        self.radar_enabled = bool(enabled)
        if self.radar_enabled:
            self.radar_status_label.setText("Radar: enabled")
            self._start_radar_timeline_fetch(force=not self.radar_frames)
            self.radar_time_slider.setEnabled(bool(self.radar_frames) and not self.radar_live_mode)
            self.radar_live_check.setEnabled(bool(self.radar_frames))
            if not self.radar_refresh_timer.isActive():
                self.radar_refresh_timer.start()
        else:
            self.radar_refresh_timer.stop()
            self.radar_time_slider.setEnabled(False)
            self.radar_live_check.setEnabled(False)
            self.radar_status_label.setText("Radar: disabled")
        self._apply_radar_state_to_map()

    @Slot(bool)
    def _on_radar_live_toggled(self, enabled):
        """Switch between latest and manual slider mode."""
        self.radar_live_mode = bool(enabled)
        self.radar_time_slider.setEnabled(self.radar_enabled and (not self.radar_live_mode) and bool(self.radar_frames))
        if self.radar_live_mode and self.radar_frames:
            self.radar_time_slider.blockSignals(True)
            self.radar_time_slider.setValue(0)
            self.radar_time_slider.blockSignals(False)
            self.radar_selected_time_ms = int(self.radar_frames[0]["valid_time_ms"])
        self._update_radar_time_label()
        self._apply_radar_state_to_map()

    @Slot(int)
    def _on_radar_slider_changed(self, index):
        """Update selected radar time frame from slider."""
        if not self.radar_frames or index < 0 or index >= len(self.radar_frames):
            return
        self.radar_selected_time_ms = int(self.radar_frames[index]["valid_time_ms"])
        if not self.radar_live_mode:
            self._update_radar_time_label()
            self._apply_radar_state_to_map()

    def _refresh_radar_timeline(self):
        """Periodic timeline refresh in live mode."""
        if not self.radar_enabled:
            return
        self._start_radar_timeline_fetch(force=True)

    def _update_radar_time_label(self):
        """Refresh user-facing radar time text."""
        if not self.radar_frames:
            self.radar_time_label.setText("Radar time: latest")
            return

        if self.radar_live_mode:
            frame = self.radar_frames[0]
            self.radar_time_label.setText(f"Radar time: {frame['label_utc']} (live)")
            return

        for frame in self.radar_frames:
            if int(frame["valid_time_ms"]) == int(self.radar_selected_time_ms or 0):
                self.radar_time_label.setText(f"Radar time: {frame['label_utc']}")
                return
        self.radar_time_label.setText("Radar time: custom")

    @Slot(bool)
    def _on_map_load_finished(self, _ok):
        """Reapply radar state after each HTML map load."""
        self._apply_radar_state_to_map()

    def _apply_radar_state_to_map(self):
        """Push radar enabled/time state into the in-page Leaflet controller."""
        page = self.web_view.page()
        enabled_js = "true" if self.radar_enabled else "false"
        page.runJavaScript(f"window.setRadarEnabled && window.setRadarEnabled({enabled_js});")

        if not self.radar_enabled:
            return

        selected_time = self.radar_selected_time_ms
        if self.radar_live_mode and self.radar_frames:
            selected_time = int(self.radar_frames[0]["valid_time_ms"])

        if selected_time is not None:
            page.runJavaScript(f"window.setRadarTime && window.setRadarTime({int(selected_time)});")
    
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

        initial_radar_enabled = "true" if self.radar_enabled else "false"
        initial_radar_time = "null"
        if self.radar_selected_time_ms is not None:
            initial_radar_time = str(int(self.radar_selected_time_ms))
        
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

        var radarImageServerBase = "https://mapservices.weather.noaa.gov/eventdriven/rest/services/radar/radar_base_reflectivity_time/ImageServer";
        var radarEnabled = {initial_radar_enabled};
        var radarTimeMs = {initial_radar_time};
        var radarOverlay = null;
        
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            attribution: '© OpenStreetMap contributors'
        }}).addTo(map);

        function buildRadarExportUrl(timeMs) {{
            var bounds = map.getBounds();
            var sw = map.options.crs.project(bounds.getSouthWest());
            var ne = map.options.crs.project(bounds.getNorthEast());
            var bbox = [sw.x, sw.y, ne.x, ne.y].join(',');
            var size = map.getSize().x + ',' + map.getSize().y;

            var url = radarImageServerBase
                + '/exportImage?f=image'
                + '&bbox=' + encodeURIComponent(bbox)
                + '&bboxSR=3857'
                + '&imageSR=3857'
                + '&size=' + encodeURIComponent(size)
                + '&format=png32'
                + '&transparent=true';

            if (timeMs !== null && timeMs !== undefined) {{
                url += '&time=' + encodeURIComponent(String(timeMs));
            }}
            return url;
        }}

        function clearRadarOverlay() {{
            if (radarOverlay) {{
                map.removeLayer(radarOverlay);
                radarOverlay = null;
            }}
        }}

        function updateRadarOverlayFromMapState() {{
            if (!radarEnabled) {{
                clearRadarOverlay();
                return;
            }}

            var imageBounds = map.getBounds();
            var imageUrl = buildRadarExportUrl(radarTimeMs);
            clearRadarOverlay();
            radarOverlay = L.imageOverlay(imageUrl, imageBounds, {{ opacity: 0.6 }});
            radarOverlay.addTo(map);
        }}

        window.setRadarEnabled = function(enabled) {{
            radarEnabled = !!enabled;
            updateRadarOverlayFromMapState();
        }};

        window.setRadarTime = function(timeMs) {{
            radarTimeMs = timeMs;
            updateRadarOverlayFromMapState();
        }};

        window.updateRadarOverlayFromMapState = updateRadarOverlayFromMapState;

        map.on('moveend zoomend resize', function() {{
            if (radarEnabled) {{
                updateRadarOverlayFromMapState();
            }}
        }});
        
        {markers_html}

        updateRadarOverlayFromMapState();
        
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
        self.radar_refresh_timer.stop()
        if self.radar_thread and self.radar_thread.isRunning():
            self.radar_thread.quit()
            self.radar_thread.wait(2000)

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