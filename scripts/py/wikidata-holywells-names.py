from SPARQLWrapper import SPARQLWrapper, JSON
import pandas as pd
import plotly.express as px

def querySparql(query):
    sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.queryAndConvert()
    return results['results']['bindings']

# SPARQL Query for Holy Wells and Their Etymologies
holyWellsQuery = """
SELECT ?etymology ?etymologyLabel (COUNT(?HW) AS ?count)
WHERE
{
  ?HW wdt:P31 wd:Q126443332.
  ?HW wdt:P131 wd:Q180231.
  ?HW wdt:P138 ?etymology.
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
GROUP BY ?etymology ?etymologyLabel
ORDER BY DESC(?count)
"""

# Fetch data using the SPARQL query
sparql_results = querySparql(holyWellsQuery)

# Convert SPARQL JSON results into a DataFrame
data = []
for result in sparql_results:
    data.append({
        "etymology": result['etymology']['value'],
        "etymologyLabel": result['etymologyLabel']['value'],
        "count": int(result['count']['value']),
    })

df = pd.DataFrame(data)

# Check if DataFrame is populated
if df.empty:
    print("No data retrieved from the query.")
else:
    # Interactive Bubble Chart using Plotly
    fig = px.scatter(
        df,
        x="etymologyLabel",
        y="count",
        size="count",
        text="etymologyLabel",
        title="Holy Wells Named After Entities",
        labels={"etymologyLabel": "Namesake", "count": "Count of Holy Wells"},
        template="plotly_white"
    )
    fig.update_traces(marker=dict(opacity=0.7, line=dict(width=2, color="DarkSlateGrey")), textposition="top center")
    fig.update_layout(title_x=0.5, xaxis_title="Namesake (Etymology)", yaxis_title="Count of Holy Wells")
    fig.show()
