from SPARQLWrapper import SPARQLWrapper, JSON
import pandas as pd
import matplotlib.pyplot as plt

def querySparql(query):
    sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.queryAndConvert()
    return results['results']['bindings']

# Updated SPARQL Query
pokemonQuery = """
SELECT DISTINCT ?pokemon ?pokemonLabel ?pokedexNumber ?color ?colorLabel ?mass
WHERE
{
    ?pokemon wdt:P31/wdt:P279* wd:Q3966183 .
    ?pokemon p:P1685 ?statement.
    ?pokemon wdt:P462 ?color.
    ?pokemon wdt:P2067 ?mass. 
    ?statement ps:P1685 ?pokedexNumber;
              pq:P972 wd:Q20005020.
    FILTER ( !isBLANK(?pokedexNumber) ) .
    SERVICE wikibase:label { bd:serviceParam wikibase:language "en" }
}
ORDER BY (?pokedexNumber)
"""

# Fetch data using the SPARQL query
sparql_results = querySparql(pokemonQuery)

# Convert SPARQL JSON results into a DataFrame
data = []
for result in sparql_results:
    data.append({
        "pokemon": result['pokemon']['value'],
        "pokemonLabel": result['pokemonLabel']['value'],
        "pokedexNumber": int(result['pokedexNumber']['value']),
        "color": result['color']['value'],
        "colorLabel": result['colorLabel']['value'],
        "mass": float(result['mass']['value']),
    })

# Create a DataFrame
df = pd.DataFrame(data)

# Check if DataFrame is populated
if df.empty:
    print("No data retrieved from the query.")
else:
    # Scatter plot: Yellow Pokémon Mass vs. Pokémon Labels
    yellow_pokemon = df[df['colorLabel'].str.lower() == "yellow"]  # Filter yellow Pokémon
    plt.figure(figsize=(12, 8))
    plt.scatter(yellow_pokemon['mass'], yellow_pokemon['pokemonLabel'], color="yellow", alpha=0.8, edgecolors="black")
    plt.title("Scatter Plot: Yellow Pokémon Mass vs. Pokémon")
    plt.xlabel("Mass (kg)")
    plt.ylabel("Pokémon")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()
    plt.show()