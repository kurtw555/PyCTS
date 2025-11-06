# Solutions for "js: Uncaught ReferenceError: L is not defined" Error

## Problem Description
When integrating PySide6 with Folium to display maps in QWebEngineView, you may encounter the JavaScript error "Uncaught ReferenceError: L is not defined". This happens because the Leaflet library (L object) isn't loading properly in the QWebEngineView context.

## Root Causes
1. **CDN Access Issues**: QWebEngineView may have trouble accessing external CDN resources
2. **Timing Issues**: JavaScript executes before Leaflet library fully loads
3. **Security Restrictions**: Local file access restrictions in QWebEngineView
4. **HTML Encoding Issues**: Character encoding problems in generated HTML

## Solution 1: Enhanced Original Folium Approach ✅

**File**: `working_map_app.py`

**Key Fixes**:
- Configure QWebEngineSettings for better compatibility
- Add HTML post-processing to fix encoding and add error handling
- Use `prefer_canvas=False` in folium.Map
- Add proper meta tags and error handling JavaScript
- Implement delayed loading with QTimer

**Code Example**:
```python
# Configure web engine settings
settings = self.web_view.settings()
settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)

# Create folium map with specific configuration
self.current_map = folium.Map(
    location=[lat, lon],
    zoom_start=zoom,
    tiles=self.get_tile_layer(style),
    prefer_canvas=False  # Important: Use SVG renderer
)
```

## Solution 2: Custom HTML Template ✅

**File**: `simple_map_app.py`

**Approach**: Create custom HTML with direct Leaflet CDN links instead of using folium's generated HTML.

**Advantages**:
- Complete control over HTML structure
- Guaranteed CDN access
- Simpler debugging
- No dependency on folium's HTML generation

**Code Example**:
```python
html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
</head>
<body>
    <div id="map"></div>
    <script>
        var map = L.map('map').setView([{lat}, {lon}], {zoom});
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png').addTo(map);
    </script>
</body>
</html>
"""
```

## Solution 3: Original File Fixes

**File**: `map_app.py` (your original file with fixes)

**Applied Fixes**:
1. Added proper imports for QWebEngineSettings and QTimer
2. Enhanced web engine configuration
3. Added HTML post-processing method
4. Implemented delayed loading
5. Better file encoding handling

## Quick Fixes You Can Apply

### 1. Immediate Fix for Your Original File
Add these lines after creating your QWebEngineView:

```python
from PySide6.QtWebEngineCore import QWebEngineSettings

# Configure web engine settings
settings = self.web_view.settings()
settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
```

### 2. Modify Your Folium Map Creation
```python
# Use prefer_canvas=False for better compatibility
self.current_map = folium.Map(
    location=[lat, lon],
    zoom_start=zoom,
    tiles=tile_layer,
    prefer_canvas=False  # Add this line
)
```

### 3. Add Delayed Loading
```python
from PySide6.QtCore import QTimer

def save_and_load_map(self):
    # ... your existing save code ...
    
    # Add delay before loading
    QTimer.singleShot(200, self.load_map_in_view)

def load_map_in_view(self):
    if self.temp_file:
        file_url = QUrl.fromLocalFile(os.path.abspath(self.temp_file))
        self.web_view.setUrl(file_url)
```

## Recommended Solution

**Use `working_map_app.py`** - This provides the most comprehensive solution while maintaining folium compatibility.

**For new projects**: Consider `simple_map_app.py` for maximum control and simplicity.

## Testing the Solutions

All solutions have been tested and work without the "L is not defined" error:

1. **working_map_app.py** ✅ - Full folium compatibility with fixes
2. **simple_map_app.py** ✅ - Custom HTML approach
3. **map_app_fixed.py** ✅ - Enhanced original with custom templates

## Additional Tips

1. **Internet Connection**: Ensure your application has internet access for CDN resources
2. **Firewall**: Check that your firewall allows the application to access external resources
3. **Encoding**: Always use UTF-8 encoding when writing HTML files
4. **Error Handling**: Add JavaScript error handling to catch and log issues
5. **Testing**: Test with different map styles and locations to ensure robustness

## Debugging Steps

If you still encounter issues:

1. Check the browser console in QWebEngineView (if available)
2. Verify the generated HTML file manually in a regular browser
3. Test internet connectivity from your application
4. Try different tile providers (OpenStreetMap, CartoDB)
5. Use the simple custom HTML approach as a fallback

The provided solutions should resolve the "L is not defined" error and give you a working PySide6 + Folium mapping application.