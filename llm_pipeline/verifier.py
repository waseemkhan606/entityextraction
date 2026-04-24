from neo4j import GraphDatabase

def verify_graph(uri: str, user: str, password: str):
    print("\n" + "="*40)
    print(" VERIFYING GRAPH INTEGRITY ")
    print("="*40)

    driver = GraphDatabase.driver(uri, auth=(user, password))
    test_query = """
    MATCH (c1:Company)-[:COMPETES_WITH]->(c2:Company)<-[:ACQUIRED]-(:Company {id: 'Microsoft'})
    RETURN c1.id AS Competitor, c2.id AS Acquired_Startup
    """
    with driver.session() as session:
        results = session.run(test_query)
        for record in results:
            print(f"Graph Intelligence: {record['Competitor']} competes directly with "
                  f"{record['Acquired_Startup']}, which is owned by Microsoft.")
    driver.close()
