from api_clients import SparqlClient
import networkx as nx
import json

client = SparqlClient()

def query_politician_party(limit=10):
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
    rows_to_take = (df["party"].value_counts() > limit) #& (df["party"].value_counts() < 20)
    relevant_orgs = set(rows_to_take[rows_to_take].index)
    df = df[df['party'].isin(relevant_orgs)]
    return df

def query_politician_org(min=10, max=20):
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
    rows_to_take = (df["org"].value_counts() > min) & (df["org"].value_counts() < max)
    relevant_orgs = set(rows_to_take[rows_to_take].index)
    df = df[df['org'].isin(relevant_orgs)]

    return df

def generate_politician_org_relation(graph, min=10, max=20):

    df = query_politician_org(min, max)

    graph.add_nodes_from(set(df["org"]), type="organization")
    graph.add_nodes_from(df["politician"], type="politician")
    graph.add_edges_from(list(df[["politician", "org"]].itertuples(index=False)))


def generate_politician_party_relation(graph, limit=10):

    df = query_politician_party(limit)

    graph.add_nodes_from(set(df["party"]), type="party")
    graph.add_nodes_from(df["politician"], type="politician")
    graph.add_edges_from(list(df[["party", "politician"]].itertuples(index=False)))
