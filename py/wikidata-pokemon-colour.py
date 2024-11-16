from SPARQLWrapper import SPARQLWrapper, JSON
import pandas as pd
import matplotlib.pyplot as plt

def querySparql(query):
    sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.queryAndConvert()
    return results['results']['bindings']

# Define the SPARQL query
pokemonQuery = """
SELECT DISTINCT ?pokemon ?pokemonLabel ?pokedexNumber ?color ?colorLabel
WHERE
{
    ?pokemon wdt:P31/wdt:P279* wd:Q3966183 .
    ?pokemon p:P1685 ?statement.
    ?pokemon wdt:P462 ?color.
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
    })

# Create a DataFrame
df = pd.DataFrame(data)

# Check if DataFrame is populated
if df.empty:
    print("No data retrieved from the query.")
else:
    # Bar chart: Count Pokémon by color
    color_counts = df['colorLabel'].value_counts()

    # Map color labels to actual colors
    color_mapping = {
        "red": "red",
        "blue": "blue",
        "green": "green",
        "yellow": "yellow",
        "purple": "purple",
        "pink": "pink",
        "brown": "brown",
        "white": "white",
        "black": "black",
        "gray": "gray",
    }

    # Create a list of bar colors based on the color labels
    bar_colors = [color_mapping.get(color.lower(), "gray") for color in color_counts.index]

    # Plot the bar chart with black edges
    plt.figure(figsize=(10, 6))
    bars = plt.bar(
        color_counts.index, 
        color_counts.values, 
        color=bar_colors, 
        edgecolor="black",  # Add black border
        linewidth=1.5      # Adjust border thickness
    )
    
    # Customize the white bar to ensure visibility
    for bar, color in zip(bars, bar_colors):
        if color == "white":
            bar.set_edgecolor("black")
            bar.set_linewidth(2)

    plt.title("Distribution of Pokémon by Color")
    plt.xlabel("Color")
    plt.ylabel("Number of Pokémon")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()
