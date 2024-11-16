import os
from SPARQLWrapper import SPARQLWrapper, JSON
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Point
import contextily as ctx  # For adding OpenStreetMap basemaps
from matplotlib.patches import Patch
from scipy.stats import gaussian_kde
import numpy as np

def querySparql(query):
    sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.queryAndConvert()
    return results['results']['bindings']

# Define the GeoJSON file path
geojson_file = os.path.join(os.path.dirname(__file__), "gs_ireland_island.geojson")

# SPARQL Query
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

    # Convert to Web Mercator for OSM basemap
    gdf_mercator = gdf.to_crs(epsg=3857)

    # Load Ireland boundary from GeoJSON
    ireland_boundary = gpd.read_file(geojson_file)
    ireland_boundary = ireland_boundary.to_crs(epsg=3857)

    # Map 1: Plot points without text decorations
    fig, ax = plt.subplots(figsize=(12, 8))
    gdf_mercator.plot(ax=ax, color='red', markersize=50, alpha=0.7, label="Ogham Stones")
    ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik, zoom=8)
    ax.set_axis_off()
    plt.title("Map of Ogham Stone Sites (OSM)")
    plt.legend()
    plt.show()

    # Map 2: Plot with points colored by county and fix legend
    fig, ax = plt.subplots(figsize=(12, 8))
    unique_counties = gdf['countyLabel'].unique()
    colors = plt.cm.tab20.colors[:len(unique_counties)]  # Generate unique colors
    county_colors = {county: colors[idx] for idx, county in enumerate(unique_counties)}

    patches = []
    for county, color in county_colors.items():
        county_data = gdf_mercator[gdf_mercator['countyLabel'] == county]
        county_data.plot(ax=ax, color=color, markersize=50, alpha=0.7)
        patches.append(Patch(color=color, label=county))  # Add patch for legend

    ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik, zoom=8)
    ax.set_axis_off()
    plt.title("Map of Ogham Stone Sites Grouped by Counties")
    plt.legend(handles=patches, title="Counties", bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.show()

    # Map 3: Density map with normalized values
    x = gdf_mercator.geometry.x
    y = gdf_mercator.geometry.y

    # Calculate kernel density
    xy = np.vstack([x, y])
    kde = gaussian_kde(xy)
    density = kde(xy)

    # Normalize density to range [0, 1]
    density_normalized = (density - density.min()) / (density.max() - density.min())
    gdf_mercator['density'] = density_normalized

    fig, ax = plt.subplots(figsize=(12, 8))
    ireland_boundary.plot(ax=ax, color="white", edgecolor="black")
    gdf_mercator.plot(ax=ax, column='density', cmap="Reds", markersize=50, alpha=0.7, legend=True)
    ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik, zoom=8)
    ax.set_axis_off()
    plt.title("Density Map of Ogham Stone Sites (Normalized)")
    plt.show()
