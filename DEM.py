import rasterio
import numpy as np
import matplotlib.pyplot as plt
import geopandas as gpd
from matplotlib.ticker import FuncFormatter
from rasterio.warp import calculate_default_transform, reproject, Resampling

# Define file paths for DEM and shapefile
dem_path = "your_dem_file.tif"
shapefile_path = "your_shapefile_path.shp"

# Convert DEM coordinate system to WGS84 (EPSG:4326)
dst_crs = "EPSG:4326"
with rasterio.open(dem_path) as src:
    transform, width, height = calculate_default_transform(
        src.crs, dst_crs, src.width, src.height, *src.bounds
    )
    kwargs = src.meta.copy()
    kwargs.update({
        "crs": dst_crs,
        "transform": transform,
        "width": width,
        "height": height
    })

    with rasterio.open("temp_dem.tif", "w", **kwargs) as dst:
        reproject(
            source=rasterio.band(src, 1),
            destination=rasterio.band(dst, 1),
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=transform,
            dst_crs=dst_crs,
            resampling=Resampling.cubic  # Higher accuracy using cubic resampling
        )

# Load the transformed DEM file
with rasterio.open("temp_dem.tif") as dem:
    dem_data = dem.read(1)  # Read the first band (elevation data)
    dem_extent = (dem.bounds.left, dem.bounds.right, dem.bounds.bottom, dem.bounds.top)  
    dem_data = np.where(dem_data <= 0, np.nan, dem_data)  # Replace invalid values (e.g., water, NoData) with NaN

# Load the shapefile using Geopandas and convert it to WGS84
boundary = gpd.read_file(shapefile_path)
if not boundary.crs.to_string() == dst_crs:
    boundary = boundary.to_crs(dst_crs)  # Convert shapefile to WGS84

# Format coordinates with degree symbols
def format_coord(value, is_longitude):
    direction = "E" if is_longitude else "N"
    return f"{abs(value):.1f}° {direction}"

# Create and display the map
fig, ax = plt.subplots(figsize=(14, 12))  
im = ax.imshow(dem_data, cmap="terrain", extent=dem_extent)

# Add colorbar
cbar = plt.colorbar(im, ax=ax, orientation='horizontal', pad=0.1, extend='max', shrink=0.9, aspect=15)
cbar.set_label("Elevation (m)")
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")

# Overlay the shapefile boundary in black
boundary.plot(ax=ax, edgecolor="black", linewidth=1.5, facecolor="none", label="Boundary")

# Format axes labels
ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: format_coord(x, is_longitude=True)))
ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: format_coord(y, is_longitude=False)))
plt.xticks(fontsize=10)
plt.yticks(fontsize=10)
plt.grid(True, linestyle="--", alpha=0.5)

# Set longitude and latitude bounds
ax.set_xlim(dem_extent[0], dem_extent[1])
ax.set_ylim(dem_extent[2], dem_extent[3])

# Add scale bar
scalebar_length_km = 50  
scalebar_x = dem_extent[0] + (dem_extent[1] - dem_extent[0]) * 0.25  
scalebar_y = dem_extent[2] + (dem_extent[3] - dem_extent[2]) * 0.1  
scalebar_width = (scalebar_length_km / 111)  # Convert km to degrees (approximate)

ax.plot([scalebar_x, scalebar_x + scalebar_width], [scalebar_y, scalebar_y], color="black", linewidth=3)
ax.text(scalebar_x + scalebar_width / 2, scalebar_y - 0.05, f"{scalebar_length_km} km",
        ha="center", va="center", fontsize=10, color="black")

# Add north arrow
x, y, arrow_length = 0.92, 0.95, 0.1  
ax.annotate('N', xy=(x, y), xytext=(x, y - arrow_length),
            arrowprops=dict(facecolor='black', width=4, headwidth=15),
            ha='center', va='center', fontsize=20,
            xycoords=ax.transAxes)

# Save the output map as a high-quality image
output_path = "dem_map.png"
plt.savefig(output_path, dpi=600, bbox_inches="tight", pad_inches=0.1)

# Optimize layout
plt.tight_layout()

# Display the map
plt.show()
