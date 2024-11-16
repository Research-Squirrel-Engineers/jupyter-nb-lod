from SPARQLWrapper import SPARQLWrapper, TURTLE
import pandas as pd
from rdflib import Graph, Namespace
from rdflib.namespace import RDF, RDFS
import matplotlib.pyplot as plt

# Function to query Solid Pod and retrieve data in TURTLE format
def querySolidPod(sparql_endpoint, query):
    sparql = SPARQLWrapper(sparql_endpoint)
    sparql.setQuery(query)
    sparql.setReturnFormat(TURTLE)  # Request Turtle format
    results = sparql.query().convert()
    return results

# SPARQL Query
solid_pod_query = """
SELECT ?item ?geo ?label ?ref ?spatialType {
 ?item a <http://fuzzy-sl.squirrel.link/ontology/Site> .
 ?item rdfs:label ?label.
 ?item <http://fuzzy-sl.squirrel.link/ontology/hasReference> ?ref .
 ?item <http://fuzzy-sl.squirrel.link/ontology/spatialType> ?spatialType .
 ?item <http://www.opengis.net/ont/geosparql#hasGeometry> ?item_geom .
 ?item_geom <http://www.opengis.net/ont/geosparql#asWKT> ?geo .
}
"""
sparql_endpoint = "https://fuzzy-sl.solidweb.org/campanian-ignimbrite-geo/ci_full.ttl"

# Query the endpoint
turtle_data = querySolidPod(sparql_endpoint, solid_pod_query)

# Parse Turtle data with rdflib
g = Graph()
g.parse(data=turtle_data, format="turtle")

# Extract namespaces
site_ns = Namespace("http://fuzzy-sl.squirrel.link/ontology/")

# Process RDF data into a DataFrame
data = []
for s, p, o in g:
    if (p == RDF.type) and (o == site_ns.Site):
        # Extract related properties
        spatial_type = g.value(s, site_ns.spatialType)
        data.append({
            "spatialType": str(spatial_type).replace("http://fuzzy-sl.squirrel.link/ontology/", "") if spatial_type else "Unknown"
        })

df = pd.DataFrame(data)

# Check if DataFrame is populated
if not df.empty and 'spatialType' in df:
    # Plot 1: Number of Sites by Spatial Type
    plt.figure(figsize=(12, 8))
    df['spatialType'].value_counts().plot(kind='bar', color='skyblue', edgecolor='black')
    plt.title("Number of Sites by Spatial Type", fontsize=16)
    plt.xlabel("Spatial Type", fontsize=14)
    plt.ylabel("Number of Sites", fontsize=14)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.show()
else:
    print("No data retrieved or 'spatialType' column is missing.")
