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
    data.append({
        "item": result['item']['value'],
        "itemLabel": result['itemLabel']['value'],
        "geo": result['geo']['value'] if 'geo' in result else None,
        "site": result['site']['value'],
        "siteLabel": result['siteLabel']['value'],
        "county": result['county']['value'],
        "countyLabel": result['countyLabel']['value'],
    })

df = pd.DataFrame(data)

# Check if DataFrame is populated
if df.empty:
    print("No data retrieved from the query.")
else:
    # Define a color palette for counties
    unique_counties = df['countyLabel'].unique()
    county_colors = {county: color for county, color in zip(unique_counties, plt.cm.tab20.colors)}

    # Group by county and site to count stones
    site_counts = df.groupby(['countyLabel', 'siteLabel']).size().reset_index(name='count')

    # Identify the top 3 sites per county
    top_sites = site_counts.groupby('countyLabel').apply(lambda x: x.nlargest(3, 'count')).reset_index(drop=True)

    # Create a bar plot for the top 3 sites per county
    plt.figure(figsize=(12, 8))
    for county, group in top_sites.groupby('countyLabel'):
        plt.bar(group['siteLabel'], group['count'], color=county_colors[county], label=county)
    
    plt.title("Top 3 Sites per County with the Most Ogham Stones")
    plt.xlabel("Sites")
    plt.ylabel("Number of Ogham Stones")
    plt.xticks(rotation=45, ha="right")
    plt.legend(title="County", bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.show()

    # Bar plot: Distribution by counties
    county_counts = df['countyLabel'].value_counts()
    plt.figure(figsize=(10, 6))
    county_counts.plot(kind='bar', color=[county_colors[county] for county in county_counts.index])
    plt.title("Distribution of Ogham Stones by Counties")
    plt.xlabel("Counties")
    plt.ylabel("Number of Ogham Stones")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()
