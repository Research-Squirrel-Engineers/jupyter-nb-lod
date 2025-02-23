from SPARQLWrapper import SPARQLWrapper, JSON

# Set up the SPARQL endpoint
sparql_endpoint = "https://fuzzy-sl.wikibase.cloud/query/sparql"
sparql = SPARQLWrapper(sparql_endpoint)

# Define your SPARQL query
'''query = """
PREFIX fslwd: <https://fuzzy-sl.wikibase.cloud/entity/>

SELECT ?item ?itemLabel ?geo WHERE { 
  ?item <https://fuzzy-sl.wikibase.cloud/prop/statement/P4> ?geo .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". } 
}
"""'''
query = """
SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 5000
"""

# Set the query
sparql.setQuery(query)
sparql.setReturnFormat(JSON)

# Execute the query and get results
results = sparql.query().convert()

print(results)

# Print the results
for result in results["results"]["bindings"]:
    print(result["s"]["value"], "-", result["p"]["value"], "-", result["o"]["value"])
