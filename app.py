import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_cytoscape as cyto
from dash.dependencies import Input, Output
import plotly.express as px
from api_clients import SparqlClient
import networkx as nx

client = SparqlClient()
query = """
    PREFIX schema: <http://schema.org/>
    PREFIX dbo: <http://dbpedia.org/ontology/>

    SELECT ?politician ?party WHERE {

    ?politicianUri schema:memberOf ?partyUri .
    ?partyUri <http://www.w3.org/2004/02/skos/core#altLabel> ?party .
    ?partyUri a dbo:PoliticalParty .

    ?politicianUri schema:givenName ?pGivenName .
    ?politicianUri schema:familyName ?pFamilyName .
    BIND(CONCAT(?pGivenName, " ", ?pFamilyName) AS ?politician) .

    FILTER(LANG(?party) = "de")
    }
"""

df = client.send_query(query)
parties = set(df["party"])

graph = nx.Graph()
graph.add_nodes_from(df["politician"])
graph.add_nodes_from(df["party"])
graph.add_edges_from(zip(df["politician"], df["party"]))

elements = []
for node in graph.nodes:
    if node in parties:
        group = "party"
    else:
        group = "politician"

    item = {
        "data" : {
            "id": node,
            "label": node
            },
        "classes": group
    }
    elements.append(item)

for edge in graph.edges:
    item = {
        "data": {
            "source": edge[0],
            "target": edge[1]
        }
    }
    elements.append(item)

cyto.load_extra_layouts()

stylesheet = [
    {
        'selector': '.party',
        'style': {
            'background-color': 'blue',
            'label': 'data(label)'}
    }
]
app = dash.Dash(__name__)

app.layout = html.Div([
    html.P("Dash Cytoscape:"),
    cyto.Cytoscape(
        id='cytoscape',
        elements=elements,
        layout={'name': 'cose', 'animate': True}, #klay, cola
        style={'width': '1800px', 'height': '1000px'},
        stylesheet=stylesheet

    )
])

app.run_server(debug=True)