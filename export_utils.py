"""
Map Export Utilities

This module provides utilities for exporting maps to different formats
and demonstrates advanced folium capabilities.
"""

import folium
import os
from folium import plugins
import json
import base64
from io import BytesIO


class MapExporter:
    """Utility class for exporting maps in various formats"""
    
    def __init__(self):
        self.map = None
    
    def create_sample_map(self, center_lat=37.7749, center_lon=-122.4194, zoom=10):
        """Create a sample map with various features"""
        
        # Create base map
        self.map = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=zoom,
            tiles='OpenStreetMap'
        )
        
        # Add various markers
        self._add_sample_markers()
        
        # Add shapes
        self._add_sample_shapes()
        
        # Add plugins
        self._add_plugins()
        
        return self.map
    
    def _add_sample_markers(self):
        """Add sample markers to the map"""
        if not self.map:
            return
        
        # Regular marker
        folium.Marker(
            location=[37.7749, -122.4194],
            popup="San Francisco",
            tooltip="Click for details",
            icon=folium.Icon(color='red', icon='info-sign')
        ).add_to(self.map)
        
        # Circle marker
        folium.CircleMarker(
            location=[37.7849, -122.4094],
            radius=30,
            popup="Circle Marker",
            color='blue',
            fill=True,
            fillColor='lightblue'
        ).add_to(self.map)
        
        # Custom HTML popup
        html_popup = """
        <div style="font-family: Arial; width: 200px;">
            <h4 style="color: #2E86AB;">Golden Gate Bridge</h4>
            <p><strong>Type:</strong> Suspension Bridge</p>
            <p><strong>Length:</strong> 2,737 meters</p>
            <p><strong>Opened:</strong> May 27, 1937</p>
        </div>
        """
        
        folium.Marker(
            location=[37.8199, -122.4783],
            popup=folium.Popup(html_popup, max_width=300),
            tooltip="Golden Gate Bridge",
            icon=folium.Icon(color='orange', icon='road', prefix='fa')
        ).add_to(self.map)
    
    def _add_sample_shapes(self):
        """Add sample shapes to the map"""
        if not self.map:
            return
        
        # Circle overlay
        folium.Circle(
            location=[37.7749, -122.4394],
            radius=1000,
            popup="1km radius circle",
            color='purple',
            fill=True,
            fillOpacity=0.2
        ).add_to(self.map)
        
        # Polygon (approximate Golden Gate Park)
        park_coords = [
            [37.7694, -122.5144],
            [37.7694, -122.4544],
            [37.7594, -122.4544],
            [37.7594, -122.5144]
        ]
        
        folium.Polygon(
            locations=park_coords,
            popup="Golden Gate Park Area",
            color='green',
            fill=True,
            fillOpacity=0.3
        ).add_to(self.map)
    
    def _add_plugins(self):
        """Add folium plugins to the map"""
        if not self.map:
            return
        
        # Minimap
        minimap = plugins.MiniMap()
        self.map.add_child(minimap)
        
        # Fullscreen button
        plugins.Fullscreen().add_to(self.map)
        
        # Measure control
        plugins.MeasureControl().add_to(self.map)
        
        # Draw tools
        draw = plugins.Draw(export=True)
        draw.add_to(self.map)
        
        # Add some sample heat data
        heat_data = [
            [37.7749, -122.4194, 0.8],
            [37.7849, -122.4094, 0.6],
            [37.7649, -122.4294, 0.7],
            [37.7549, -122.4394, 0.5],
            [37.7949, -122.4094, 0.9]
        ]
        plugins.HeatMap(heat_data).add_to(self.map)
    
    def export_to_html(self, filename="exported_map.html"):
        """Export map to HTML file"""
        if not self.map:
            print("No map to export. Create a map first.")
            return False
        
        try:
            self.map.save(filename)
            print(f"Map exported to {filename}")
            return True
        except Exception as e:
            print(f"Error exporting to HTML: {e}")
            return False
    
    def get_html_string(self):
        """Get the map as an HTML string"""
        if not self.map:
            return None
        
        try:
            return self.map._repr_html_()
        except Exception as e:
            print(f"Error getting HTML string: {e}")
            return None
    
    def export_bounds_info(self, filename="map_bounds.json"):
        """Export map bounds and center information"""
        if not self.map:
            print("No map to export bounds from.")
            return False
        
        try:
            # Get map bounds (this is approximate since folium doesn't directly expose bounds)
            center = self.map.location
            zoom = getattr(self.map, 'zoom_start', 10)  # Default to 10 if not available
            
            bounds_info = {
                "center": {
                    "lat": center[0],
                    "lon": center[1]
                },
                "zoom": zoom,
                "approximate_bounds": {
                    "north": center[0] + 0.1,
                    "south": center[0] - 0.1,
                    "east": center[1] + 0.1,
                    "west": center[1] - 0.1
                }
            }
            
            with open(filename, 'w') as f:
                json.dump(bounds_info, f, indent=2)
            
            print(f"Map bounds exported to {filename}")
            return True
            
        except Exception as e:
            print(f"Error exporting bounds: {e}")
            return False
    
    def create_thumbnail_map(self, width=300, height=200):
        """Create a smaller thumbnail version of the map"""
        if not self.map:
            return None
        
        # Create a simple version without plugins for thumbnail
        zoom = getattr(self.map, 'zoom_start', 10)  # Default to 10 if not available
        thumbnail = folium.Map(
            location=self.map.location,
            zoom_start=max(zoom - 1, 1),  # Zoom out a bit, minimum 1
            width=width,
            height=height,
            tiles='OpenStreetMap'
        )
        
        # Add just a center marker
        folium.Marker(
            location=self.map.location,
            popup="Map Center",
            icon=folium.Icon(color='red', icon='home')
        ).add_to(thumbnail)
        
        return thumbnail


def demonstrate_exports():
    """Demonstrate various export capabilities"""
    print("Creating map exporter...")
    exporter = MapExporter()
    
    print("Creating sample map...")
    exporter.create_sample_map()
    
    print("Exporting to HTML...")
    exporter.export_to_html("sample_export.html")
    
    print("Exporting bounds info...")
    exporter.export_bounds_info("sample_bounds.json")
    
    print("Creating thumbnail...")
    thumbnail = exporter.create_thumbnail_map()
    if thumbnail:
        thumbnail.save("thumbnail_map.html")
        print("Thumbnail saved to thumbnail_map.html")
    
    print("Getting HTML string...")
    html_string = exporter.get_html_string()
    if html_string:
        print(f"HTML string length: {len(html_string)} characters")
    
    print("\nExport demonstration complete!")
    print("Files created:")
    print("- sample_export.html (full featured map)")
    print("- sample_bounds.json (map bounds information)")
    print("- thumbnail_map.html (simplified thumbnail version)")


def create_comparison_maps():
    """Create maps with different styles for comparison"""
    styles = [
        ("OpenStreetMap", "osm_map.html"),
        ("CartoDB positron", "cartodb_light_map.html"),
        ("CartoDB dark_matter", "cartodb_dark_map.html"),
        ("Stamen Terrain", "terrain_map.html")
    ]
    
    print("Creating comparison maps with different styles...")
    
    for style, filename in styles:
        try:
            # Create map with specific style
            m = folium.Map(
                location=[37.7749, -122.4194],
                zoom_start=10,
                tiles=style
            )
            
            # Add a simple marker
            folium.Marker(
                location=[37.7749, -122.4194],
                popup=f"Map Style: {style}",
                tooltip=style
            ).add_to(m)
            
            # Save map
            m.save(filename)
            print(f"Created {filename} with {style} style")
            
        except Exception as e:
            print(f"Error creating {style} map: {e}")
    
    print("Comparison maps created!")


if __name__ == "__main__":
    print("Map Export Utilities Demo")
    print("=" * 40)
    
    # Demonstrate exports
    demonstrate_exports()
    
    print("\n" + "=" * 40)
    
    # Create comparison maps
    create_comparison_maps()
    
    print("\nDemo complete! Check the generated HTML files in your browser.")