import os
from SPARQLWrapper import SPARQLWrapper, JSON
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Point
import contextily as ctx  # For adding OpenStreetMap basemaps
from scipy.stats import gaussian_kde
import numpy as np

def querySparql(query):
    sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.queryAndConvert()
    return results['results']['bindings']

def decimal_to_dms(decimal, is_latitude):
    """Convert a decimal coordinate to degrees, minutes, and seconds."""
    degrees = int(decimal)
    minutes = int(abs(decimal - degrees) * 60)
    seconds = (abs(decimal - degrees) * 60 - minutes) * 60
    direction = ''
    if is_latitude:
        direction = 'N' if decimal >= 0 else 'S'
    else:
        direction = 'E' if decimal >= 0 else 'W'
    return f"{abs(degrees)}°{minutes}'{seconds:.3f}\"{direction}"

# Define the GeoJSON file path
geojson_file = os.path.join(os.path.dirname(__file__), "gs_ireland_island.geojson")

# Updated SPARQL Query
oghamQuery = """
SELECT ?item ?itemLabel ?geo ?site ?siteLabel ?county ?countyLabel WHERE { 
  ?item wdt:P31 wd:Q2016147.
  ?item wdt:P189 ?site.
  ?site wdt:P31 wd:Q72617071.
  ?item wdt:P189 ?county.
  ?county wdt:P31 wd:Q179872.
  ?item wdt:P625 ?geo.
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
"""

# Fetch data using the SPARQL query
sparql_results = querySparql(oghamQuery)

# Convert SPARQL JSON results into a DataFrame
data = []
for result in sparql_results:
    geo = result['geo']['value'] if 'geo' in result else None
    lat, lon = (None, None)
    if geo:
        lon, lat = map(float, geo.replace("Point(", "").replace(")", "").split())
    data.append({
        "item": result['item']['value'],
        "itemLabel": result['itemLabel']['value'],
        "site": result['site']['value'],
        "siteLabel": result['siteLabel']['value'],
        "county": result['county']['value'],
        "countyLabel": result['countyLabel']['value'],
        "latitude": lat,
        "longitude": lon,
    })

df = pd.DataFrame(data)

# Check if DataFrame is populated
if df.empty:
    print("No data retrieved from the query.")
else:
    # Filter rows with valid coordinates
    df_with_coords = df.dropna(subset=['latitude', 'longitude'])

    # Create a GeoDataFrame
    gdf = gpd.GeoDataFrame(
        df_with_coords,
        geometry=[Point(xy) for xy in zip(df_with_coords['longitude'], df_with_coords['latitude'])],
        crs="EPSG:4326"
    )

    # Add DMS columns
    gdf['latitude_dms'] = gdf['geometry'].y.apply(lambda x: decimal_to_dms(x, is_latitude=True))
    gdf['longitude_dms'] = gdf['geometry'].x.apply(lambda x: decimal_to_dms(x, is_latitude=False))

    # Convert to Web Mercator for OSM basemap
    gdf_mercator = gdf.to_crs(epsg=3857)

    # Load Ireland boundary from GeoJSON
    ireland_boundary = gpd.read_file(geojson_file)
    ireland_boundary = ireland_boundary.to_crs(epsg=3857)

    # Map 1: Plot with DMS coordinates
    fig, ax = plt.subplots(figsize=(12, 8))
    gdf_mercator.plot(ax=ax, color='red', markersize=50, alpha=0.7, label="Ogham Stones")
    ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik, zoom=8)
    ax.set_axis_off()
    for idx, row in gdf.iterrows():
        x, y = row['geometry'].x, row['geometry'].y
        ax.text(x, y, f"{row['latitude_dms']}, {row['longitude_dms']}", fontsize=8, ha='right', va='bottom', color='blue')
    plt.title("Map of Ogham Stone Sites (OSM) with DMS Coordinates")
    plt.legend()
    plt.tight_layout()
    plt.show()

    # Map 2: Plot with points colored by county
    fig, ax = plt.subplots(figsize=(12, 8))
    unique_counties = gdf['countyLabel'].unique()
    colors = plt.cm.tab20.colors[:len(unique_counties)]  # Generate unique colors
    county_colors = {county: colors[idx] for idx, county in enumerate(unique_counties)}
    for county, color in county_colors.items():
        county_data = gdf_mercator[gdf_mercator['countyLabel'] == county]
        county_data.plot(ax=ax, color=color, markersize=50, label=county, alpha=0.7)
    ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik, zoom=8)
    ax.set_axis_off()
    plt.title("Map of Ogham Stone Sites Grouped by Counties")
    plt.legend(title="Counties", bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.show()

    # Map 3: Density map with Ireland's boundary and points > latitude 50
    gdf_high_latitude = gdf[gdf['geometry'].y > 50]  # Filter points with latitude > 50
    gdf_high_latitude_mercator = gdf_high_latitude.to_crs(epsg=3857)
    fig, ax = plt.subplots(figsize=(12, 8))
    ireland_boundary.plot(ax=ax, facecolor="none", edgecolor="black", linewidth=2, alpha=0.7, label="Ireland Border")
    x, y = gdf_high_latitude_mercator['geometry'].x, gdf_high_latitude_mercator['geometry'].y
    xy = np.vstack([x, y])
    kde = gaussian_kde(xy)(xy)  # Kernel density estimate
    ax.scatter(x, y, c=kde, cmap='viridis', s=50, alpha=0.7, label="Ogham Stones Density")
    ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik, zoom=8)
    ax.set_axis_off()
    plt.title("Density Map of Ogham Stone Sites (Latitude > 50°)")
    plt.colorbar(ax.collections[0], ax=ax, label='Density')
    plt.legend()
    plt.tight_layout()
    plt.show()