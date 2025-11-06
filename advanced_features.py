"""
Advanced Map Features Example

This module demonstrates additional folium features that can be integrated
into the main map application.
"""

import folium
from folium import plugins
import random


def create_advanced_map_example():
    """Create a map with advanced folium features"""
    
    # Create base map centered on San Francisco
    m = folium.Map(
        location=[37.7749, -122.4194],
        zoom_start=12,
        tiles='OpenStreetMap'
    )
    
    # Add different types of markers
    add_marker_examples(m)
    
    # Add circle and polygon overlays
    add_shape_examples(m)
    
    # Add heatmap (if you have data)
    add_heatmap_example(m)
    
    # Add marker cluster
    add_marker_cluster_example(m)
    
    # Add custom popup with HTML
    add_custom_popup_example(m)
    
    return m


def add_marker_examples(map_obj):
    """Add various types of markers"""
    
    # Regular marker with custom icon
    folium.Marker(
        location=[37.7749, -122.4194],
        popup="San Francisco City Hall",
        tooltip="City Hall",
        icon=folium.Icon(color='red', icon='info-sign')
    ).add_to(map_obj)
    
    # Circle marker
    folium.CircleMarker(
        location=[37.7849, -122.4094],
        radius=50,
        popup="Circle Marker",
        color='blue',
        fill=True,
        fillColor='lightblue'
    ).add_to(map_obj)
    
    # Custom icon marker
    folium.Marker(
        location=[37.7649, -122.4294],
        popup="Custom Icon",
        icon=folium.Icon(color='green', prefix='fa', icon='star')
    ).add_to(map_obj)


def add_shape_examples(map_obj):
    """Add circles and polygons"""
    
    # Circle overlay
    folium.Circle(
        location=[37.7749, -122.4394],
        radius=500,  # in meters
        popup="500m radius",
        color='purple',
        fill=True,
        fillOpacity=0.2
    ).add_to(map_obj)
    
    # Polygon
    polygon_coords = [
        [37.7849, -122.4494],
        [37.7949, -122.4394],
        [37.7849, -122.4294],
        [37.7749, -122.4394]
    ]
    
    folium.Polygon(
        locations=polygon_coords,
        popup="Sample Polygon",
        color='orange',
        fill=True,
        fillOpacity=0.3
    ).add_to(map_obj)


def add_heatmap_example(map_obj):
    """Add a heatmap layer"""
    
    # Generate sample heat data points around San Francisco
    heat_data = []
    base_lat, base_lon = 37.7749, -122.4194
    
    for _ in range(100):
        # Generate random points within a small area
        lat = base_lat + random.uniform(-0.02, 0.02)
        lon = base_lon + random.uniform(-0.02, 0.02)
        intensity = random.uniform(0.1, 1.0)
        heat_data.append([lat, lon, intensity])
    
    # Add heatmap
    plugins.HeatMap(heat_data).add_to(map_obj)


def add_marker_cluster_example(map_obj):
    """Add clustered markers"""
    
    # Create marker cluster
    marker_cluster = plugins.MarkerCluster().add_to(map_obj)
    
    # Add multiple markers to the cluster
    locations = [
        [37.7849, -122.4594, "Cluster Point 1"],
        [37.7749, -122.4594, "Cluster Point 2"],
        [37.7649, -122.4594, "Cluster Point 3"],
        [37.7849, -122.4694, "Cluster Point 4"],
        [37.7749, -122.4694, "Cluster Point 5"],
    ]
    
    for lat, lon, name in locations:
        folium.Marker(
            location=[lat, lon],
            popup=name
        ).add_to(marker_cluster)


def add_custom_popup_example(map_obj):
    """Add marker with custom HTML popup"""
    
    html_popup = """
    <div style="font-family: Arial; width: 200px;">
        <h4 style="color: #2E86AB;">Custom Popup</h4>
        <p><strong>Location:</strong> Golden Gate Park</p>
        <p><strong>Area:</strong> 1,017 acres</p>
        <img src="https://via.placeholder.com/150x100" alt="Park Image" style="width: 100%;">
        <p style="font-size: 12px; color: #666;">
            This is a custom HTML popup with styling and an image.
        </p>
    </div>
    """
    
    folium.Marker(
        location=[37.7694, -122.4862],
        popup=folium.Popup(html_popup, max_width=300),
        tooltip="Golden Gate Park",
        icon=folium.Icon(color='green', icon='tree-deciduous', prefix='fa')
    ).add_to(map_obj)


def add_drawing_tools(map_obj):
    """Add drawing tools to the map"""
    
    # Add drawing tools
    draw = plugins.Draw(export=True)
    draw.add_to(map_obj)
    
    # Add measure control
    plugins.MeasureControl().add_to(map_obj)


def add_minimap(map_obj):
    """Add a minimap control"""
    
    minimap = plugins.MiniMap()
    map_obj.add_child(minimap)


def add_fullscreen_control(map_obj):
    """Add fullscreen control"""
    
    plugins.Fullscreen().add_to(map_obj)


if __name__ == "__main__":
    # Create and save example map
    example_map = create_advanced_map_example()
    
    # Add additional controls
    add_drawing_tools(example_map)
    add_minimap(example_map)
    add_fullscreen_control(example_map)
    
    # Save to file
    example_map.save("advanced_map_example.html")
    print("Advanced map example saved to 'advanced_map_example.html'")
    print("Open this file in a web browser to see the advanced features.")