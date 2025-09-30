# Personal Geodatabase to CSV Converter

A Python script to extract feature data from ESRI Personal Geodatabase (.mdb) files and convert geometry to Well-Known Text (WKT) format for use in QGIS and other GIS applications.

## Overview

This script reads feature classes from Personal Geodatabase files and exports them as CSV files with geometry converted to WKT format. It uses reverse-engineered Shapefile geometry format parsing (as documented in the ESRI Shapefile Technical Description, July 1998) since Personal Geodatabases store geometry as "essentially Shapefile geometry fragments."

### Key Features

- **Automatic geometry column detection** - Queries GDB_GeomColumns metadata table
- **WKT geometry conversion** - Converts binary geometry BLOBs to readable WKT format
- **All geometry types supported** - Point, LineString, Polygon, MultiPoint, MultiLineString, MultiPolygon, and Z/M variants
- **UTF-8 output** - Ensures compatibility with modern GIS applications like QGIS
- **Stream processing** - Handles large datasets efficiently without loading all data into memory
- **Progress indicators** - Shows progress for large tables (every 1000 rows)

## Requirements

- Python 3.6+
- `pyodbc` library
- **Windows**: Microsoft Access Database Engine (ODBC driver)
- **Linux/Mac**: `mdbtools` and `unixodbc`

### Installation

```bash
# Install Python dependencies
pip install pyodbc

# Windows: Install Microsoft Access Database Engine
# Download from: https://www.microsoft.com/en-us/download/details.aspx?id=54920

# Linux (Debian/Ubuntu):
sudo apt-get install mdbtools unixodbc unixodbc-dev

# Mac (with Homebrew):
brew install mdbtools unixodbc
```

## Usage

### Basic Syntax

```bash
python pgdb.py <mdb_file> <table_name> [-o OUTPUT_FILE]
```

### Arguments

- `mdb_file` - Path to the Personal Geodatabase (.mdb) file
- `table_name` - Name of the feature class/table to extract
- `-o, --output` - (Optional) Output CSV file path

### Recommended Usage (Cross-Platform)

**Use the `-o` flag to ensure UTF-8 encoding:**

```bash
python pgdb.py data.mdb Buildings -o buildings.csv
```

This method guarantees UTF-8 encoding regardless of your operating system or shell.

## Platform-Specific CLI Options

### Windows

**❌ AVOID using `>` redirection in PowerShell:**
```powershell
# DON'T DO THIS - Creates UTF-16 LE BOM encoding
python pgdb.py data.mdb Buildings > output.csv
```

**✅ RECOMMENDED options:**

**Use PowerShell `Out-File` with UTF8:**
```powershell
python pgdb.py data.mdb Buildings | Out-File -Encoding UTF8 buildings.csv
```

**Use Command Prompt instead of PowerShell:**
```cmd
python pgdb.py data.mdb Buildings > buildings.csv
```
*Note: CMD output may still use system codepage (CP1252), so `-o` is still preferred*

### Linux/Mac

**✅ Standard redirection works fine:**
```bash
# This works perfectly on Unix-like systems
python pgdb.py data.mdb Buildings > buildings.csv
```

**✅ Or use the `-o` flag for consistency:**
```bash
python pgdb.py data.mdb Buildings -o buildings.csv
```

## Output Format

### CSV Structure

The script outputs a CSV file with:
- **Header row**: Column names in lowercase, unquoted
- **Data rows**: Values with `QUOTE_NONNUMERIC` quoting (strings quoted, numbers unquoted)
- **Geometry column**: Binary geometry converted to WKT format
- **Encoding**: UTF-8
- **Line endings**: Unix-style (`\n`)

### Example Output

```csv
objectid,name,type,shape
1,"Building A","Residential","POLYGON ((100 200, 150 200, 150 250, 100 250, 100 200))"
2,"Building B","Commercial","POLYGON ((200 300, 250 300, 250 350, 200 350, 200 300))"
```

## Supported Geometry Types

| Shapefile Type | WKT Output | Description |
|----------------|-----------|-------------|
| Point (1) | POINT | Single point |
| Polyline (3) | LINESTRING / MULTILINESTRING | Single or multi-part line |
| Polygon (5) | POLYGON / MULTIPOLYGON | Single or multi-part polygon (with hole support) |
| MultiPoint (8) | MULTIPOINT | Collection of points |
| PointZ (11) | POINT Z | 3D point |
| PolyLineZ (13) | LINESTRING Z / MULTILINESTRING Z | 3D line |
| PolygonZ (15) | POLYGON Z / MULTIPOLYGON Z | 3D polygon |
| MultiPointZ (18) | MULTIPOINT Z | 3D point collection |
| PointM (21) | POINT M | Point with measure |

*Note: M-type geometries (PolyLineM, PolygonM, MultiPointM) are partially implemented*

## Using Output in QGIS

1. **Open QGIS**
2. **Layer → Add Layer → Add Delimited Text Layer**
3. **File name**: Select your CSV file
4. **File Format**: CSV (comma)
5. **Geometry Definition**: Well Known Text (WKT)
6. **Geometry field**: Select your geometry column (usually `shape`, `wkt`, or `geom`)
7. **Geometry CRS**: Specify the appropriate coordinate reference system (e.g., EPSG:4326 for WGS84, EPSG:32639 for UTM)
8. Click **Add**

## How It Works

### Geometry Parsing

Personal Geodatabases store geometry in a proprietary binary format that is essentially identical to the Shapefile geometry format. The script:

1. Connects to the .mdb file via ODBC
2. Queries the `GDB_GeomColumns` metadata table to find the geometry column
3. Reads each feature's geometry BLOB
4. Parses the binary data according to the ESRI Shapefile specification
5. Converts to WKT format
6. Outputs as CSV with proper quoting

### Polygon and MultiPolygon Detection

The script uses ring orientation (clockwise vs counter-clockwise) to distinguish between:
- **Polygons with holes**: Outer ring (clockwise) + inner rings (counter-clockwise)
- **MultiPolygons**: Multiple outer rings, each potentially with holes

This follows the Shapefile specification where ring winding order determines topology.

## Diagnostic Output

The script provides diagnostic information to stderr (separate from CSV output):

```
# Geometry column: Shape
# Shape type from metadata: Polygon
# Processed 1000 rows...
# Processed 2000 rows...
# Complete: Processed 2547 rows total
```

To suppress diagnostic output:
```bash
# Linux/Mac
python pgdb.py data.mdb Buildings -o output.csv 2>/dev/null

# Windows (PowerShell)
python pgdb.py data.mdb Buildings -o output.csv 2>$null
```

## Troubleshooting

### "Table not found in GDB_GeomColumns"

The specified table is not a valid feature class. Use a GIS tool to inspect the geodatabase and verify the table name.

### "Microsoft Access Driver not found" (Windows)

Install the Microsoft Access Database Engine:
https://www.microsoft.com/en-us/download/details.aspx?id=54920

### "No suitable driver found" (Linux/Mac)

Install mdbtools and unixodbc:
```bash
# Ubuntu/Debian
sudo apt-get install mdbtools unixodbc unixodbc-dev

# Mac
brew install mdbtools unixodbc
```

### QGIS says "data source needs to be repaired"

Common causes:
- **Wrong encoding**: File is UTF-16 instead of UTF-8 (use `-o` flag)
- **Wrong CRS**: Make sure to specify the correct coordinate reference system
- **Invalid WKT**: Check diagnostic output for geometry parsing errors

Verify file encoding:
```bash
file output.csv  # Should show "UTF-8 Unicode text"
```

### Geometry parsing errors

Some geometries may fail to parse if they use unsupported Shapefile extensions or are corrupted. The script will output empty geometry for failed records and report errors to stderr.

## Technical Details

### Based On

- **ESRI Shapefile Technical Description** (July 1998)
- GDAL/OGR PGeo driver implementation
- Personal Geodatabase stores geometry as "essentially Shapefile geometry fragments"

### Binary Format

- **Shape type**: 4-byte little-endian integer
- **Bounding box**: 4 doubles (Xmin, Ymin, Xmax, Ymax)
- **Parts and points**: Integer counts followed by coordinate arrays
- **Byte order**: Little-endian for geometry data (Intel byte order)

### Limitations

- Read-only (no write support)
- Does not support topology, networks, or other advanced geodatabase features
- M-coordinate geometries are partially implemented
- MultiPatch geometries are recognized but not fully implemented
- Does not process annotation, dimensions, or relationship classes
- Does not write out CRS information. Examine the GDB_SpatialRefs table in the MDB to determine the CRS for the exported table.

## License

This script is provided as-is for educational and research purposes. The ESRI Shapefile format specification is publicly available, and this implementation is based on publicly documented specifications.

## Contributing

Contributions are welcome! Please submit pull requests or open issues for:
- Additional geometry type support
- Performance improvements
- Bug fixes
- Documentation improvements

## References

- [ESRI Shapefile Technical Description (PDF)](https://www.esri.com/content/dam/esrisites/sitecore-archive/Files/Pdfs/library/whitepapers/pdfs/shapefile.pdf)
- [GDAL PGeo Driver Documentation](https://gdal.org/drivers/vector/pgeo.html)
- [OGC Well-Known Text Specification](https://www.ogc.org/standards/sfa)
