import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_cytoscape as cyto
from dash.dependencies import Input, Output
import plotly.express as px
from api_clients import SparqlClient
import networkx as nx
import json

client = SparqlClient()
def generate_politician_party_relation():
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
    rows_to_take = (df["party"].value_counts() > 10) #& (df["party"].value_counts() < 20)
    relevant_orgs = set(rows_to_take[rows_to_take].index)
    df = df[df['party'].isin(relevant_orgs)]

    elements = []
    for iterator, group in zip([set(df["party"]), df["politician"]], ["party", "politician"]):
        for node in iterator:
            item = {
                "data" : {
                    "id": node,
                    "label": node
                    },
                "classes": group
            }
            elements.append(item)

    for source, target in zip(df["party"], df["politician"]):
        item = {
            "data": {
                "source": source,
                "target": target
            }
        }
        elements.append(item)

    return elements

def generate_politician_org_relation():
    query = """
        PREFIX schema: <http://schema.org/>
        PREFIX dbo: <http://dbpedia.org/ontology/>
        PREFIX lw: <https://lod.lobbywatch.ch/>
        PREFIX org: <http://www.w3.org/ns/org#>

        SELECT ?politician ?org WHERE {

        ?politicianUri schema:memberOf ?partyUri .
        ?partyUri a dbo:PoliticalParty .
        ?politicianUri schema:givenName ?pGivenName .
        ?politicianUri schema:familyName ?pFamilyName .
        BIND(CONCAT(?pGivenName, " ", ?pFamilyName) AS ?politician) .

        ?interests a lw:MembersInterest .
        ?interests lw:parliamentMember ?politicianUri.
        ?interests org:organization ?orgUri .
        ?orgUri schema:name ?org .

        FILTER(LANG(?org) = "de")
        } ORDER BY ?pFamilyName
    """

    df = client.send_query(query)
    rows_to_take = (df["org"].value_counts() > 10) & (df["org"].value_counts() < 20)
    relevant_orgs = set(rows_to_take[rows_to_take].index)
    df = df[df['org'].isin(relevant_orgs)]

    elements = []
    for iterator, group in zip([set(df["org"]), df["politician"]], ["org", "politician"]):
        for node in iterator:
            item = {
                "data" : {
                    "id": node,
                    "label": node
                    },
                "classes": group
            }
            elements.append(item)

    for source, target in zip(df["org"], df["politician"]):
        item = {
            "data": {
                "source": source,
                "target": target
            }
        }
        elements.append(item)

    return elements


cyto.load_extra_layouts()

elements = []
elements += generate_politician_party_relation()
elements += generate_politician_org_relation()

default_stylesheet = [
    {
        'selector': '.party',
        'style': {
            'background-color': 'blue',
            'label': 'data(label)',
            'z-index': 9998
            }
    },
    {
        'selector': '.politician',
        'style': {
            'background-color': 'grey'}
    },
    {
        'selector': '.org',
        'style': {
            'background-color': 'yellow'}
    }
]
app = dash.Dash(__name__)

app.layout = html.Div([
    html.P("Dash Cytoscape:"),
    cyto.Cytoscape(
        id='cytoscape',
        elements=elements,
        layout={'name': 'cose', 'animate': False}, #cose, klay, cola
        style={'width': '1800px', 'height': '1000px'},
        #stylesheet=default_stylesheet,
    )
])

@app.callback(Output('cytoscape', 'stylesheet'),
              [Input('cytoscape', 'tapNode')])
def generate_stylesheet(node):
    if not node:
        return default_stylesheet

    stylesheet = [
    {
        'selector': '.party',
        'style': {
            'background-color': 'blue',
            'label': 'data(label)',
            'z-index': 9998}
    },{
        'selector': '.politician',
        'style': {
            'background-color': 'grey'}
    },
    {
        'selector': '.org',
        'style': {
            'background-color': 'yellow'}
    },{
        "selector": 'node[id = "{}"]'.format(node['data']['id']),
        'style': {
            'background-color': 'green',
            'label': 'data(label)',
            'z-index': 9999}
    }]

    return stylesheet


app.run_server(debug=True)