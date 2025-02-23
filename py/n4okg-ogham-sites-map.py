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
    sparql = SPARQLWrapper("https://graph.nfdi4objects.net/api/sparql")
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.queryAndConvert()
    return results['results']['bindings']

# Define the GeoJSON file path
geojson_file = os.path.join(os.path.dirname(__file__), "gs_ireland_island.geojson")

# SPARQL Query
oghamQuery = """
PREFIX oghamonto: <http://ontology.ogham.link/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?item ?label ?geo ?county (count(distinct ?stone) as ?count) WHERE {
 ?item <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://ontology.ogham.link/OghamSite> .
 ?item rdfs:label ?label .
 ?item <http://www.opengis.net/ont/geosparql#hasGeometry> ?item_geom .
 ?item_geom <http://www.opengis.net/ont/geosparql#asWKT> ?geo . 
 ?item oghamonto:within ?c .
 ?c a oghamonto:County .
 ?c rdfs:label ?county .
 ?stone oghamonto:disclosedAt ?item .
 ?stone a oghamonto:OghamStone_CIIC .
} GROUP BY ?item ?label ?geo ?county ORDER BY DESC(?count)
"""

# Fetch data using the SPARQL query
sparql_results = querySparql(oghamQuery)

# Convert SPARQL JSON results into a DataFrame
data = []
for result in sparql_results:
    geo = result['geo']['value'] if 'geo' in result else None
    lat, lon = (None, None)
    if geo:
        lon, lat = map(float, geo.replace("POINT(", "").replace(")", "").split())
    data.append({
        "item": result['item']['value'],
        "label": result['label']['value'],
        "county": result['county']['value'],
        "count": int(result.get("count", {}).get("value", 0)),
        "latitude": lat,
        "longitude": lon,
    })

df = pd.DataFrame(data)
print(df)

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

    # Map 1: Plot with points coloured by county
    fig, ax = plt.subplots(figsize=(12, 8))
    unique_counties = gdf['county'].unique()
    # Create a colormap with as many colours as unique counties
    cmap = plt.get_cmap('tab20', len(unique_counties))
    county_colors = {county: cmap(idx) for idx, county in enumerate(unique_counties)}

    patches = []
    for county, color in county_colors.items():
        county_data = gdf_mercator[gdf_mercator['county'] == county]
        county_data.plot(ax=ax, color=color, markersize=50, alpha=0.7)
        patches.append(Patch(color=color, label=county))  # Add patch for legend

    ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik, zoom=8)
    ax.set_axis_off()
    plt.title("Map of Ogham Stone Sites Grouped by Counties")
    plt.legend(handles=patches, title="Counties", bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.show()

    # Map 2: Plot with point colours and sizes grouped/styled by stone count.
    fig, ax = plt.subplots(figsize=(12, 8))
    # Extract x and y coordinates from the GeoDataFrame.
    x = gdf_mercator.geometry.x
    y = gdf_mercator.geometry.y

    # Define a scaling factor for point sizes.
    size_factor = 10
    sizes = gdf_mercator["count"] * size_factor

    # Plot the points using a continuous colormap (e.g. 'viridis') based on the stone count.
    sc = ax.scatter(x, y, s=sizes, c=gdf_mercator["count"], cmap="viridis", alpha=0.7, edgecolor="k")
    ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik, zoom=8)
    ax.set_axis_off()
    plt.title("Map of Ogham Stone Sites: Styled by Stone Count", fontsize=16)

    # Add a colour bar with label.
    cbar = plt.colorbar(sc, ax=ax)
    cbar.set_label("Stone Count", fontsize=12)
    plt.show()