import struct

class GeometryParser:
    """
    Parse ESRI Shapefile geometry binary format
    Based on: ESRI Shapefile Technical Description (July 1998)
    Personal Geodatabases store geometry as "essentially Shapefile geometry fragments"
    """
    
    # Shape type constants from ESRI Shapefile spec
    NULL_SHAPE = 0
    POINT = 1
    POLYLINE = 3
    POLYGON = 5
    MULTIPOINT = 8
    POLYLINEX = 10
    POINTZ = 11
    POLYLINEZ = 13
    POLYGONZ = 15
    MULTIPOINTZ = 18
    POINTM = 21
    POLYLINEM = 23
    POLYGONM = 25
    MULTIPOINTM = 28
    MULTIPATCH = 31
    
    def __init__(self, blob):
        self.blob = blob
        self.offset = 0
    
    def read_int32_le(self):
        """Read a 32-bit integer (little endian)"""
        val = struct.unpack('<i', self.blob[self.offset:self.offset+4])[0]
        self.offset += 4
        return val
    
    def read_double_le(self):
        """Read a double (8 bytes, little endian)"""
        val = struct.unpack('<d', self.blob[self.offset:self.offset+8])[0]
        self.offset += 8
        return val
    
    def parse_to_wkt(self):
        """Parse the Shapefile geometry blob and return WKT"""
        if len(self.blob) < 4:
            return None
        
        # Read shape type (first 4 bytes, little endian)
        shape_type = self.read_int32_le()
        print(shape_type)
        
        if shape_type == self.NULL_SHAPE:
            return "GEOMETRYCOLLECTION EMPTY"
        elif shape_type == self.POINT:
            return self.parse_point()
        elif shape_type == self.MULTIPOINT:
            return self.parse_multipoint()
        elif shape_type == self.POLYLINE:
            return self.parse_polyline()
        elif shape_type == self.POLYLINEX:
            return self.parse_polyline()
        elif shape_type == self.POLYGON:
            return self.parse_polygon()
        elif shape_type == self.POINTZ:
            return self.parse_pointz()
        elif shape_type == self.POLYLINEZ:
            return self.parse_polylinez()
        elif shape_type == self.POLYGONZ:
            return self.parse_polygonz()
        elif shape_type == self.MULTIPOINTZ:
            return self.parse_multipointz()
        elif shape_type == self.POINTM:
            return self.parse_pointm()
        elif shape_type == self.POLYLINEM:
            return self.parse_polylinem()
        elif shape_type == self.POLYGONM:
            return self.parse_polygonm()
        elif shape_type == self.MULTIPOINTM:
            return self.parse_multipointm()
        else:
            return f"UNKNOWN GEOMETRY TYPE: {shape_type}"
    
    def parse_point(self):
        """Parse a Point geometry (Type 1)"""
        x = self.read_double_le()
        y = self.read_double_le()
        return f"POINT ({x} {y})"
    
    def parse_multipoint(self):
        """Parse a MultiPoint geometry (Type 8)"""
        # Skip bounding box (4 doubles: Xmin, Ymin, Xmax, Ymax)
        self.offset += 32
        
        num_points = self.read_int32_le()
        
        points = []
        for _ in range(num_points):
            x = self.read_double_le()
            y = self.read_double_le()
            points.append(f"({x} {y})")
        
        return f"MULTIPOINT ({', '.join(points)})"
    
    def parse_polyline(self):
        """Parse a PolyLine geometry (Type 3)"""
        # Skip bounding box
        self.offset += 32
        
        num_parts = self.read_int32_le()
        num_points = self.read_int32_le()
        
        # Read part indices
        parts = []
        for _ in range(num_parts):
            parts.append(self.read_int32_le())
        parts.append(num_points)  # Add end marker
        
        # Read all points
        points = []
        for _ in range(num_points):
            x = self.read_double_le()
            y = self.read_double_le()
            points.append((x, y))
        
        # Build WKT
        if num_parts == 1:
            coords = ', '.join(f"{x} {y}" for x, y in points)
            return f"LINESTRING ({coords})"
        else:
            lines = []
            for i in range(num_parts):
                start = parts[i]
                end = parts[i + 1]
                coords = ', '.join(f"{x} {y}" for x, y in points[start:end])
                lines.append(f"({coords})")
            return f"MULTILINESTRING ({', '.join(lines)})"
    
    def is_clockwise(self, ring_points):
        """
        Determine if a ring is clockwise using the shoelace formula.
        Clockwise = outer ring, Counter-clockwise = hole
        """
        area = 0.0
        n = len(ring_points)
        for i in range(n):
            j = (i + 1) % n
            area += ring_points[i][0] * ring_points[j][1]
            area -= ring_points[j][0] * ring_points[i][1]
        return area < 0  # Negative area = clockwise
    
    def parse_polygon(self):
        """Parse a Polygon geometry (Type 5)"""
        # Skip bounding box
        self.offset += 32
        
        num_parts = self.read_int32_le()
        num_points = self.read_int32_le()
        
        # Read part indices
        parts = []
        for _ in range(num_parts):
            parts.append(self.read_int32_le())
        parts.append(num_points)
        
        # Read all points
        points = []
        for _ in range(num_points):
            x = self.read_double_le()
            y = self.read_double_le()
            points.append((x, y))
        
        if num_parts == 1:
            # Single ring - simple polygon
            coords = ', '.join(f"{x} {y}" for x, y in points)
            return f"POLYGON (({coords}))"
        
        # Multiple rings - need to determine if multipolygon or polygon with holes
        # Group rings by orientation: clockwise = outer, counter-clockwise = holes
        polygons = []
        current_polygon = None
        
        for i in range(num_parts):
            start = parts[i]
            end = parts[i + 1]
            ring_points = points[start:end]
            coords = ', '.join(f"{x} {y}" for x, y in ring_points)
            
            if self.is_clockwise(ring_points):
                # Outer ring - start new polygon
                if current_polygon is not None:
                    polygons.append(current_polygon)
                current_polygon = [f"({coords})"]
            else:
                # Hole - add to current polygon
                if current_polygon is not None:
                    current_polygon.append(f"({coords})")
                else:
                    # No outer ring yet - treat as outer ring anyway
                    current_polygon = [f"({coords})"]
        
        # Add last polygon
        if current_polygon is not None:
            polygons.append(current_polygon)
        
        # Build WKT
        if len(polygons) == 1:
            return f"POLYGON ({', '.join(polygons[0])})"
        else:
            polygon_strings = [f"({', '.join(rings)})" for rings in polygons]
            return f"MULTIPOLYGON ({', '.join(polygon_strings)})"
    
    def parse_pointz(self):
        """Parse a PointZ geometry (Type 11)"""
        x = self.read_double_le()
        y = self.read_double_le()
        z = self.read_double_le()
        # M value follows but we'll ignore it for basic 3D WKT
        return f"POINT Z ({x} {y} {z})"
    
    def parse_polylinez(self):
        """Parse a PolyLineZ geometry (Type 13)"""
        # Skip bounding box
        self.offset += 32
        
        num_parts = self.read_int32_le()
        num_points = self.read_int32_le()
        
        # Read part indices
        parts = []
        for _ in range(num_parts):
            parts.append(self.read_int32_le())
        parts.append(num_points)
        
        # Read XY points
        xy_points = []
        for _ in range(num_points):
            x = self.read_double_le()
            y = self.read_double_le()
            xy_points.append((x, y))
        
        # Read Z range and Z values
        self.offset += 16  # Skip Zmin, Zmax
        z_values = []
        for _ in range(num_points):
            z_values.append(self.read_double_le())
        
        # Combine XY and Z
        points = [(xy[0], xy[1], z) for xy, z in zip(xy_points, z_values)]
        
        # Build WKT
        if num_parts == 1:
            coords = ', '.join(f"{x} {y} {z}" for x, y, z in points)
            return f"LINESTRING Z ({coords})"
        else:
            lines = []
            for i in range(num_parts):
                start = parts[i]
                end = parts[i + 1]
                coords = ', '.join(f"{x} {y} {z}" for x, y, z in points[start:end])
                lines.append(f"({coords})")
            return f"MULTILINESTRING Z ({', '.join(lines)})"
    
    def parse_polygonz(self):
        """Parse a PolygonZ geometry (Type 15)"""
        # Skip bounding box
        self.offset += 32
        
        num_parts = self.read_int32_le()
        num_points = self.read_int32_le()
        
        # Read part indices
        parts = []
        for _ in range(num_parts):
            parts.append(self.read_int32_le())
        parts.append(num_points)
        
        # Read XY points
        xy_points = []
        for _ in range(num_points):
            x = self.read_double_le()
            y = self.read_double_le()
            xy_points.append((x, y))
        
        # Read Z range and Z values
        self.offset += 16  # Skip Zmin, Zmax
        z_values = []
        for _ in range(num_points):
            z_values.append(self.read_double_le())
        
        # Combine XY and Z
        points = [(xy[0], xy[1], z) for xy, z in zip(xy_points, z_values)]
        
        if num_parts == 1:
            # Single ring
            coords = ', '.join(f"{x} {y} {z}" for x, y, z in points)
            return f"POLYGON Z (({coords}))"
        
        # Multiple rings - determine multipolygon or polygon with holes
        polygons = []
        current_polygon = None
        
        for i in range(num_parts):
            start = parts[i]
            end = parts[i + 1]
            ring_xy = xy_points[start:end]
            ring_points = points[start:end]
            coords = ', '.join(f"{x} {y} {z}" for x, y, z in ring_points)
            
            if self.is_clockwise(ring_xy):
                # Outer ring
                if current_polygon is not None:
                    polygons.append(current_polygon)
                current_polygon = [f"({coords})"]
            else:
                # Hole
                if current_polygon is not None:
                    current_polygon.append(f"({coords})")
                else:
                    current_polygon = [f"({coords})"]
        
        if current_polygon is not None:
            polygons.append(current_polygon)
        
        if len(polygons) == 1:
            return f"POLYGON Z ({', '.join(polygons[0])})"
        else:
            polygon_strings = [f"({', '.join(rings)})" for rings in polygons]
            return f"MULTIPOLYGON Z ({', '.join(polygon_strings)})"
    
    def parse_multipointz(self):
        """Parse a MultiPointZ geometry (Type 18)"""
        # Skip bounding box
        self.offset += 32
        
        num_points = self.read_int32_le()
        
        # Read XY points
        xy_points = []
        for _ in range(num_points):
            x = self.read_double_le()
            y = self.read_double_le()
            xy_points.append((x, y))
        
        # Read Z range and Z values
        self.offset += 16  # Skip Zmin, Zmax
        z_values = []
        for _ in range(num_points):
            z_values.append(self.read_double_le())
        
        # Combine
        points = []
        for (x, y), z in zip(xy_points, z_values):
            points.append(f"({x} {y} {z})")
        
        return f"MULTIPOINT Z ({', '.join(points)})"
    
    def parse_pointm(self):
        """Parse a PointM geometry (Type 21)"""
        x = self.read_double_le()
        y = self.read_double_le()
        m = self.read_double_le()
        return f"POINT M ({x} {y} {m})"
    
    def parse_polylinem(self):
        """Parse a PolyLineM geometry (Type 23)"""
        # Implementation similar to PolyLineZ but with M values instead
        # For brevity, providing simplified version
        return "POLYLINE M (not fully implemented)"
    
    def parse_polygonm(self):
        """Parse a PolygonM geometry (Type 25)"""
        return "POLYGON M (not fully implemented)"
    
    def parse_multipointm(self):
        """Parse a MultiPointM geometry (Type 28)"""
        return "MULTIPOINT M (not fully implemented)"

