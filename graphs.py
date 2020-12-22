from api_clients import SparqlClient
import networkx as nx
import json

client = SparqlClient()

def query_politician_party(limit=10):
    query = """
        PREFIX schema: <http://schema.org/>
        PREFIX dbo: <http://dbpedia.org/ontology/>

        SELECT ?politicianUri ?politician ?partyUri ?party WHERE {

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
    rows_to_take = (df["partyUri"].value_counts() > limit) #& (df["partyUri"].value_counts() < 20)
    relevant_orgs = set(rows_to_take[rows_to_take].index)
    df = df[df['partyUri'].isin(relevant_orgs)]
    return df

def query_politician_org(min=10, max=20):
    query = """
        PREFIX schema: <http://schema.org/>
        PREFIX dbo: <http://dbpedia.org/ontology/>
        PREFIX lw: <https://lod.lobbywatch.ch/>
        PREFIX org: <http://www.w3.org/ns/org#>

        SELECT ?politicianUri ?politician ?org ?orgUri WHERE {

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
    rows_to_take = (df["orgUri"].value_counts() > min) & (df["orgUri"].value_counts() < max)
    relevant_orgs = set(rows_to_take[rows_to_take].index)
    df = df[df['orgUri'].isin(relevant_orgs)]

    return df

def query_politician_lobbyst():
    query = """
        PREFIX schema: <http://schema.org/>
        PREFIX lw: <https://lod.lobbywatch.ch/>

        SELECT ?politicianUri ?politician ?lobbyistUri ?lobbyist  WHERE {
        ?access lw:issuedBy ?politicianUri .
        ?access lw:issuedTo ?lobbyistUri .
        ?politicianUri schema:givenName ?pGivenName .
        ?politicianUri schema:familyName ?pFamilyName .

        BIND(CONCAT(?pGivenName, " ", ?pFamilyName) AS ?politician) .
        ?lobbyistUri schema:givenName ?viaGivenName .
        ?lobbyistUri schema:familyName ?viaFamilyName .
        BIND(CONCAT(?viaGivenName, " ", ?viaFamilyName) AS ?lobbyist) .

        } ORDER BY ?pFamilyName
    """

    df = client.send_query(query)

    return df

def query_lobbyist_org(min=5, max=100):

    query = """
        PREFIX schema: <http://schema.org/>
        PREFIX lw: <https://lod.lobbywatch.ch/>
        PREFIX org: <http://www.w3.org/ns/org#>

        SELECT ?lobbyistUri ?lobbyist ?orgUri ?org WHERE {
        ?access a lw:AccessRight .
        ?access lw:issuedTo ?lobbyistUri .

        ?lobbyistUri schema:givenName ?pGivenName .
        ?lobbyistUri schema:familyName ?pFamilyName .
        BIND(CONCAT(?pGivenName, " ", ?pFamilyName) AS ?lobbyist) .

        ?lobbyistUri org:hasMembership ?membership .
        ?membership org:organization ?orgUri .
        ?orgUri schema:name ?org .

        FILTER(LANG(?org) = "de")
        } ORDER BY ?lobbyist
    """

    df = client.send_query(query)
    rows_to_take = (df["orgUri"].value_counts() > min) & (df["orgUri"].value_counts() < max)
    relevant_orgs = set(rows_to_take[rows_to_take].index)
    df = df[df['orgUri'].isin(relevant_orgs)]

    return df


def generate_politician_org_relation(graph, min=10, max=20):

    df = query_politician_org(min, max)

    graph.add_nodes_from(set(df["orgUri"]), type="organization")
    graph.add_nodes_from(df["politicianUri"], type="politician")
    graph.add_edges_from(list(df[["politicianUri", "orgUri"]].itertuples(index=False)))

    return graph


def generate_politician_party_relation(graph, limit=10):

    df = query_politician_party(limit)

    graph.add_nodes_from(set(df["partyUri"]), type="party")
    graph.add_nodes_from(df["politicianUri"], type="politician")
    graph.add_edges_from(list(df[["partyUri", "politicianUri"]].itertuples(index=False)))

    return graph


def generate_politician_lobbyist_relation(graph):

    df = query_politician_lobbyst()
    graph.add_nodes_from(df["politicianUri"], type="politician")
    graph.add_nodes_from(df["lobbyistUri"], type="lobbyist")
    graph.add_edges_from(list(df[["politicianUri", "lobbyistUri"]].itertuples(index=False)))

    return graph


def generate_lobbyist_org_relation(graph, min=0, max=200):

    df = query_lobbyist_org(min, max)

    graph.add_nodes_from(set(df["orgUri"]), type="organization")
    graph.add_nodes_from(df["lobbyistUri"], type="lobbyist")
    graph.add_edges_from(list(df[["lobbyistUri", "orgUri"]].itertuples(index=False)))

    return graph