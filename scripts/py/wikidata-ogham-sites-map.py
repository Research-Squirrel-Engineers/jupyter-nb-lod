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

# Updated SPARQL Query
oghamQuery = """
SELECT ?item ?itemLabel ?geo ?site ?siteLabel ?county ?countyLabel WHERE { 
  ?item wdt:P31 wd:Q2016147.
  ?item wdt:P189 ?site.
  ?site wdt:P31 wd:Q72617071.
  ?item wdt:P189 ?county.
  ?county wdt:P31 wd:Q179872.
  OPTIONAL { ?item wdt:P625 ?geo. }
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

    # Add DMS columns
    df_with_coords['latitude_dms'] = df_with_coords['latitude'].apply(lambda x: decimal_to_dms(x, is_latitude=True))
    df_with_coords['longitude_dms'] = df_with_coords['longitude'].apply(lambda x: decimal_to_dms(x, is_latitude=False))

    # Create a GeoDataFrame
    gdf = gpd.GeoDataFrame(
        df_with_coords,
        geometry=[Point(xy) for xy in zip(df_with_coords['longitude'], df_with_coords['latitude'])],
        crs="EPSG:4326"
    )

    # Convert to Web Mercator (EPSG:3857) for OSM basemap
    gdf_mercator = gdf.to_crs(epsg=3857)

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
    plt.close(fig)

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
    plt.close(fig)

    # Map 3: Density map
    fig, ax = plt.subplots(figsize=(12, 8))
    x, y = gdf['geometry'].x, gdf['geometry'].y
    xy = np.vstack([x, y])
    kde = gaussian_kde(xy)(xy)  # Kernel density estimate
    ax.scatter(x, y, c=kde, cmap='viridis', s=50, alpha=0.7)  # Scatter plot with density
    ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik, zoom=8)
    ax.set_axis_off()
    plt.title("Density Map of Ogham Stone Sites")
    plt.colorbar(ax.collections[0], ax=ax, label='Density')
    plt.tight_layout()
    plt.show()
    plt.close(fig)
