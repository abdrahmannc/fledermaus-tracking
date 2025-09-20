"""
3D Stereo Visualization Module

Creates 3D visualizations and exports for stereo bat tracking data.
Supports multiple output formats for GIS compatibility.
"""

import numpy as np
import matplotlib.pyplot as plt
import os
from datetime import datetime
import json
from typing import List, Dict, Optional
import logging

# Optional dependencies for advanced 3D visualization
try:
    import plotly.graph_objects as go
    import plotly.offline as pyo
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

try:
    import open3d as o3d
    OPEN3D_AVAILABLE = True
except ImportError:
    OPEN3D_AVAILABLE = False

logger = logging.getLogger(__name__)


class Stereo3DVisualizer:
    """3D visualization system for stereo bat tracking data"""
    
    def __init__(self, trajectory_data: List[Dict], video_info: Optional[Dict] = None):
        self.trajectory_data = trajectory_data
        self.video_info = video_info or {}
        self.output_dir = None
        
    def create_3d_flight_visualization(self, output_path: str, visualization_type: str = "matplotlib") -> str:
        """Create 3D flight path visualization"""
        
        if not self.trajectory_data:
            raise ValueError("No 3D trajectory data available")
        
        # Prepare output directory
        self.output_dir = os.path.dirname(output_path)
        os.makedirs(self.output_dir, exist_ok=True)
        
        if visualization_type == "matplotlib":
            return self._create_matplotlib_3d(output_path)
        elif visualization_type == "plotly" and PLOTLY_AVAILABLE:
            return self._create_plotly_3d(output_path)
        elif visualization_type == "open3d" and OPEN3D_AVAILABLE:
            return self._create_open3d_visualization(output_path)
        else:
            # Fallback to matplotlib
            return self._create_matplotlib_3d(output_path)
    
    def _create_matplotlib_3d(self, output_path: str) -> str:
        """Create 3D visualization using matplotlib"""
        fig = plt.figure(figsize=(12, 9))
        ax = fig.add_subplot(111, projection='3d')
        
        # Extract coordinates
        x_coords = [point['x'] for point in self.trajectory_data]
        y_coords = [point['y'] for point in self.trajectory_data]
        z_coords = [point['z'] for point in self.trajectory_data]
        timestamps = [point['timestamp'] for point in self.trajectory_data]
        confidences = [point.get('confidence', 1.0) for point in self.trajectory_data]
        
        # Create color map based on time or confidence
        plt.cm.viridis(np.linspace(0, 1, len(x_coords)))
        
        # Plot trajectory
        ax.plot(x_coords, y_coords, z_coords, 'b-', linewidth=2, alpha=0.7, label='Flight Path')
        
        # Plot points with confidence-based sizing
        sizes = [50 * conf for conf in confidences]
        scatter = ax.scatter(x_coords, y_coords, z_coords, 
                           c=timestamps, s=sizes, cmap='plasma', alpha=0.8)
        
        # Mark start and end points
        if len(x_coords) > 0:
            ax.scatter([x_coords[0]], [y_coords[0]], [z_coords[0]], 
                      c='green', s=100, marker='o', label='Start')
            ax.scatter([x_coords[-1]], [y_coords[-1]], [z_coords[-1]], 
                      c='red', s=100, marker='s', label='End')
        
        # Customize plot
        ax.set_xlabel('X Position (mm)', fontsize=12)
        ax.set_ylabel('Y Position (mm)', fontsize=12)
        ax.set_zlabel('Z Position (mm)', fontsize=12)
        ax.set_title('3D Bat Flight Path Analysis', fontsize=16, fontweight='bold')
        
        # Add colorbar for timestamps
        cbar = plt.colorbar(scatter, ax=ax, shrink=0.5, aspect=20)
        cbar.set_label('Time (seconds)', fontsize=10)
        
        # Add legend
        ax.legend(fontsize=10)
        
        # Add grid and improve visibility
        ax.grid(True, alpha=0.3)
        
        # Add statistics text box
        stats_text = self._generate_statistics_text()
        ax.text2D(0.02, 0.98, stats_text, transform=ax.transAxes, fontsize=8,
                 verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        # Save plot
        plt.tight_layout()
        if not output_path.endswith('.png'):
            output_path += '.png'
        
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return output_path
    
    def _create_plotly_3d(self, output_path: str) -> str:
        """Create interactive 3D visualization using plotly"""
        if not PLOTLY_AVAILABLE:
            raise ImportError("Plotly not available. Install with: pip install plotly")
        
        # Extract coordinates
        x_coords = [point['x'] for point in self.trajectory_data]
        y_coords = [point['y'] for point in self.trajectory_data]
        z_coords = [point['z'] for point in self.trajectory_data]
        timestamps = [point['timestamp'] for point in self.trajectory_data]
        confidences = [point.get('confidence', 1.0) for point in self.trajectory_data]
        frame_indices = [point.get('frame_idx', i) for i, point in enumerate(self.trajectory_data)]
        
        # Create traces
        traces = []
        
        # Flight path line
        traces.append(go.Scatter3d(
            x=x_coords, y=y_coords, z=z_coords,
            mode='lines',
            name='Flight Path',
            line=dict(color='blue', width=4),
            hovertemplate='<b>Flight Path</b><br>' +
                         'X: %{x:.1f} mm<br>' +
                         'Y: %{y:.1f} mm<br>' +
                         'Z: %{z:.1f} mm<extra></extra>'
        ))
        
        # Detection points
        traces.append(go.Scatter3d(
            x=x_coords, y=y_coords, z=z_coords,
            mode='markers',
            name='Detections',
            marker=dict(
                size=[8 * conf for conf in confidences],
                color=timestamps,
                colorscale='Viridis',
                colorbar=dict(title="Time (s)"),
                opacity=0.8
            ),
            text=[f'Frame: {frame}<br>Time: {time:.2f}s<br>Confidence: {conf:.2f}' 
                  for frame, time, conf in zip(frame_indices, timestamps, confidences)],
            hovertemplate='<b>Detection</b><br>' +
                         'X: %{x:.1f} mm<br>' +
                         'Y: %{y:.1f} mm<br>' +
                         'Z: %{z:.1f} mm<br>' +
                         '%{text}<extra></extra>'
        ))
        
        # Start and end markers
        if len(x_coords) > 0:
            traces.append(go.Scatter3d(
                x=[x_coords[0]], y=[y_coords[0]], z=[z_coords[0]],
                mode='markers',
                name='Start',
                marker=dict(size=15, color='green', symbol='circle')
            ))
            
            traces.append(go.Scatter3d(
                x=[x_coords[-1]], y=[y_coords[-1]], z=[z_coords[-1]],
                mode='markers',
                name='End',
                marker=dict(size=15, color='red', symbol='square')
            ))
        
        # Create layout
        layout = go.Layout(
            title=dict(
                text='3D Bat Flight Path Analysis - Interactive View',
                x=0.5,
                font=dict(size=16)
            ),
            scene=dict(
                xaxis_title='X Position (mm)',
                yaxis_title='Y Position (mm)',
                zaxis_title='Z Position (mm)',
                bgcolor='rgba(0,0,0,0)',
                xaxis=dict(gridcolor='lightgray'),
                yaxis=dict(gridcolor='lightgray'),
                zaxis=dict(gridcolor='lightgray')
            ),
            margin=dict(l=0, r=0, b=0, t=40),
            font=dict(family="Arial, sans-serif", size=12)
        )
        
        # Create figure
        fig = go.Figure(data=traces, layout=layout)
        
        # Save as HTML
        if not output_path.endswith('.html'):
            output_path += '.html'
        
        pyo.plot(fig, filename=output_path, auto_open=False)
        
        return output_path
    
    def _create_open3d_visualization(self, output_path: str) -> str:
        """Create 3D visualization using Open3D"""
        if not OPEN3D_AVAILABLE:
            raise ImportError("Open3D not available. Install with: pip install open3d")
        
        # Extract coordinates
        points = np.array([[point['x'], point['y'], point['z']] for point in self.trajectory_data])
        
        # Create point cloud
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(points)
        
        # Color points based on timestamps
        timestamps = np.array([point['timestamp'] for point in self.trajectory_data])
        normalized_times = (timestamps - timestamps.min()) / (timestamps.max() - timestamps.min())
        colors = plt.cm.viridis(normalized_times)[:, :3]  # Remove alpha channel
        pcd.colors = o3d.utility.Vector3dVector(colors)
        
        # Create line set for trajectory
        if len(points) > 1:
            lines = [[i, i + 1] for i in range(len(points) - 1)]
            line_set = o3d.geometry.LineSet()
            line_set.points = o3d.utility.Vector3dVector(points)
            line_set.lines = o3d.utility.Vector2iVector(lines)
            line_colors = [[0, 0, 1] for _ in range(len(lines))]  # Blue lines
            line_set.colors = o3d.utility.Vector3dVector(line_colors)
        
        # Save point cloud
        if not output_path.endswith('.ply'):
            output_path += '.ply'
        
        o3d.io.write_point_cloud(output_path, pcd)
        
        # Also save trajectory as line set
        if len(points) > 1:
            trajectory_path = output_path.replace('.ply', '_trajectory.ply')
            o3d.io.write_line_set(trajectory_path, line_set)
        
        return output_path
    
    def _generate_statistics_text(self) -> str:
        """Generate statistics text for visualization"""
        if not self.trajectory_data:
            return "No data available"
        
        x_coords = [point['x'] for point in self.trajectory_data]
        y_coords = [point['y'] for point in self.trajectory_data]
        z_coords = [point['z'] for point in self.trajectory_data]
        timestamps = [point['timestamp'] for point in self.trajectory_data]
        
        # Calculate statistics
        total_distance = 0
        if len(x_coords) > 1:
            for i in range(1, len(x_coords)):
                dx = x_coords[i] - x_coords[i-1]
                dy = y_coords[i] - y_coords[i-1]
                dz = z_coords[i] - z_coords[i-1]
                total_distance += np.sqrt(dx**2 + dy**2 + dz**2)
        
        duration = max(timestamps) - min(timestamps) if timestamps else 0
        avg_speed = total_distance / duration if duration > 0 else 0
        
        stats = [
            f"3D Flight Statistics:",
            f"Total Points: {len(self.trajectory_data)}",
            f"Duration: {duration:.2f} s",
            f"Total Distance: {total_distance:.1f} mm",
            f"Average Speed: {avg_speed:.1f} mm/s",
            f"X Range: {min(x_coords):.1f} to {max(x_coords):.1f} mm",
            f"Y Range: {min(y_coords):.1f} to {max(y_coords):.1f} mm",
            f"Z Range: {min(z_coords):.1f} to {max(z_coords):.1f} mm"
        ]
        
        return '\n'.join(stats)
    
    def export_gis_compatible_data(self, output_dir: str) -> List[str]:
        """Export 3D data in GIS-compatible formats"""
        exported_files = []
        
        # Export as GeoJSON (with Z coordinates)
        geojson_path = os.path.join(output_dir, "bat_flight_3d.geojson")
        self._export_geojson(geojson_path)
        exported_files.append(geojson_path)
        
        # Export as KML for Google Earth
        kml_path = os.path.join(output_dir, "bat_flight_3d.kml")
        self._export_kml(kml_path)
        exported_files.append(kml_path)
        
        # Export as Shapefile (requires pyshp)
        try:
            shp_path = os.path.join(output_dir, "bat_flight_3d.shp")
            self._export_shapefile(shp_path)
            exported_files.append(shp_path)
        except ImportError:
            logger.warning("Shapefile export requires pyshp package")
        
        return exported_files
    
    def _export_geojson(self, output_path: str):
        """Export trajectory as GeoJSON with Z coordinates"""
        features = []
        
        # Create point features
        for i, point in enumerate(self.trajectory_data):
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [point['x'], point['y'], point['z']]
                },
                "properties": {
                    "point_id": i,
                    "timestamp": point['timestamp'],
                    "frame_idx": point.get('frame_idx', i),
                    "confidence": point.get('confidence', 1.0)
                }
            }
            features.append(feature)
        
        # Create LineString for trajectory
        if len(self.trajectory_data) > 1:
            coordinates = [[point['x'], point['y'], point['z']] for point in self.trajectory_data]
            trajectory_feature = {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": coordinates
                },
                "properties": {
                    "feature_type": "trajectory",
                    "total_points": len(coordinates),
                    "duration": max([p['timestamp'] for p in self.trajectory_data]) - 
                               min([p['timestamp'] for p in self.trajectory_data])
                }
            }
            features.append(trajectory_feature)
        
        geojson = {
            "type": "FeatureCollection",
            "features": features,
            "crs": {
                "type": "name",
                "properties": {
                    "name": "urn:ogc:def:crs:EPSG::4326"
                }
            }
        }
        
        with open(output_path, 'w') as f:
            json.dump(geojson, f, indent=2)
    
    def _export_kml(self, output_path: str):
        """Export trajectory as KML for Google Earth"""
        kml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Bat Flight Path 3D</name>
    <description>3D bat flight trajectory from stereo analysis</description>
    
    <!-- Style for flight path -->
    <Style id="flightPath">
      <LineStyle>
        <color>ff0000ff</color>
        <width>3</width>
      </LineStyle>
    </Style>
    
    <!-- Style for detection points -->
    <Style id="detectionPoint">
      <IconStyle>
        <Icon>
          <href>http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png</href>
        </Icon>
        <scale>0.8</scale>
      </IconStyle>
    </Style>
    
    <!-- Flight path -->
    <Placemark>
      <name>3D Flight Trajectory</name>
      <description>Complete bat flight path</description>
      <styleUrl>#flightPath</styleUrl>
      <LineString>
        <extrude>1</extrude>
        <altitudeMode>absolute</altitudeMode>
        <coordinates>
'''
        
        # Add coordinates (note: KML uses lon,lat,alt format)
        for point in self.trajectory_data:
            kml_content += f"          {point['x']},{point['y']},{point['z']}\n"
        
        kml_content += '''        </coordinates>
      </LineString>
    </Placemark>
    
    <!-- Detection points -->
'''
        
        # Add individual detection points
        for i, point in enumerate(self.trajectory_data):
            kml_content += f'''    <Placemark>
      <name>Detection {i+1}</name>
      <description>
        Time: {point['timestamp']:.2f}s
        Frame: {point.get('frame_idx', i)}
        Confidence: {point.get('confidence', 1.0):.2f}
      </description>
      <styleUrl>#detectionPoint</styleUrl>
      <Point>
        <altitudeMode>absolute</altitudeMode>
        <coordinates>{point['x']},{point['y']},{point['z']}</coordinates>
      </Point>
    </Placemark>
'''
        
        kml_content += '''  </Document>
</kml>'''
        
        with open(output_path, 'w') as f:
            f.write(kml_content)
    
    def _export_shapefile(self, output_path: str):
        """Export trajectory as ESRI Shapefile"""
        try:
            import shapefile as shp
        except ImportError:
            raise ImportError("Shapefile export requires pyshp package. Install with: pip install pyshp")
        
        # Create shapefile writer
        w = shp.Writer(output_path)
        
        # Define fields
        w.field('POINT_ID', 'N')
        w.field('TIMESTAMP', 'F', 10, 3)
        w.field('FRAME_IDX', 'N')
        w.field('CONFIDENCE', 'F', 5, 3)
        w.field('X_COORD', 'F', 12, 3)
        w.field('Y_COORD', 'F', 12, 3)
        w.field('Z_COORD', 'F', 12, 3)
        
        # Add records
        for i, point in enumerate(self.trajectory_data):
            w.pointz(point['x'], point['y'], point['z'])
            w.record(
                POINT_ID=i,
                TIMESTAMP=point['timestamp'],
                FRAME_IDX=point.get('frame_idx', i),
                CONFIDENCE=point.get('confidence', 1.0),
                X_COORD=point['x'],
                Y_COORD=point['y'],
                Z_COORD=point['z']
            )
        
        w.close()


def create_3d_flight_visualization(trajectory_data: List[Dict], 
                                 video_path: Optional[str] = None,
                                 output_format: str = "matplotlib") -> Optional[str]:
    """
    Main function to create 3D flight visualization
    
    Args:
        trajectory_data: List of 3D trajectory points
        video_path: Optional path to source video for metadata
        output_format: Visualization format ('matplotlib', 'plotly', 'open3d')
    
    Returns:
        Path to created visualization file or None if failed
    """
    try:
        # Prepare video info
        video_info = {}
        if video_path:
            video_info['source_video'] = os.path.basename(video_path)
            video_info['video_dir'] = os.path.dirname(video_path)
        
        # Create visualizer
        visualizer = Stereo3DVisualizer(trajectory_data, video_info)
        
        # Determine output path
        if video_path:
            output_dir = os.path.join(os.path.dirname(video_path), 'results', 'visualizations', '3d_analysis')
        else:
            output_dir = os.path.join(os.getcwd(), 'results', 'visualizations', '3d_analysis')
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"bat_flight_3d_{timestamp}"
        
        if output_format == "plotly":
            output_path = os.path.join(output_dir, f"{base_filename}.html")
        elif output_format == "open3d":
            output_path = os.path.join(output_dir, f"{base_filename}.ply")
        else:  # matplotlib
            output_path = os.path.join(output_dir, f"{base_filename}.png")
        
        # Create visualization
        result_path = visualizer.create_3d_flight_visualization(output_path, output_format)
        
        # Also export GIS-compatible data
        try:
            gis_files = visualizer.export_gis_compatible_data(output_dir)
            logger.info(f"GIS-compatible files exported: {gis_files}")
        except Exception as e:
            logger.warning(f"GIS export failed: {e}")
        
        return result_path
        
    except Exception as e:
        logger.error(f"Failed to create 3D visualization: {e}")
        return None


def create_stereo_calibration_tool():
    """Create stereo calibration tool interface"""
    # This would be a separate calibration tool
    # For now, provide instructions for manual calibration
    
    instructions = """
    Stereo Camera Calibration Instructions:
    
    1. Use OpenCV's stereo calibration functions
    2. Capture chessboard patterns from both cameras simultaneously
    3. Extract calibration parameters and save as JSON
    
    Example calibration data structure:
    {
        "camera_matrix_left": [[fx, 0, cx], [0, fy, cy], [0, 0, 1]],
        "camera_matrix_right": [[fx, 0, cx], [0, fy, cy], [0, 0, 1]],
        "dist_coeffs_left": [k1, k2, p1, p2, k3],
        "dist_coeffs_right": [k1, k2, p1, p2, k3],
        "rotation_matrix": 3x3 rotation matrix,
        "translation_vector": [tx, ty, tz],
        "essential_matrix": 3x3 essential matrix,
        "fundamental_matrix": 3x3 fundamental matrix,
        "rectification_left": 3x3 rectification matrix,
        "rectification_right": 3x3 rectification matrix,
        "projection_left": 3x4 projection matrix,
        "projection_right": 3x4 projection matrix,
        "disparity_to_depth_matrix": 4x4 Q matrix,
        "roi_left": [x, y, width, height],
        "roi_right": [x, y, width, height]
    }
    """
    
    return instructions
