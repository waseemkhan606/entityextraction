from neo4j import GraphDatabase

class AlphaFundGraphEngine:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        print(f"[System] Connected to Neo4j Engine at {uri}")

    def close(self):
        self.driver.close()
        print("[System] Connection securely closed.")

    def execute_write(self, cypher_query, parameters=None):
        with self.driver.session() as session:
            session.execute_write(lambda tx: tx.run(cypher_query, parameters).consume())

    def execute_read(self, cypher_query, parameters=None):
        with self.driver.session() as session:
            # FIXED: Consuming the result before the transaction closes
            return session.execute_read(
                lambda tx: [record.data() for record in tx.run(cypher_query, parameters)]
            )

# 1. Instantiate
graph_db = AlphaFundGraphEngine("bolt://127.0.0.1:7687", "neo4j", "AlphaFund2026!")

# 2. Constraints
constraint_queries = [
    "CREATE CONSTRAINT unique_company IF NOT EXISTS FOR (c:Company) REQUIRE c.name IS UNIQUE",
    "CREATE CONSTRAINT unique_exec IF NOT EXISTS FOR (e:Executive) REQUIRE e.name IS UNIQUE",
    "CREATE CONSTRAINT unique_doc IF NOT EXISTS FOR (d:Document) REQUIRE d.title IS UNIQUE"
]
for query in constraint_queries:
    graph_db.execute_write(query)

# 3. Inject
graph_payload = {
    "author": "Tony",
    "report_title": "Q3 Compliance Report",
    "startup": "Alpha AI",
    "acquirer": "Microsoft",
    "ceo": "Satya Nadella"
}
ingestion_query = """
MERGE (exec1:Executive {name: $author})
MERGE (doc:Document {title: $report_title})
MERGE (company1:Company {name: $startup})
MERGE (company2:Company {name: $acquirer})
MERGE (exec2:Executive {name: $ceo})
MERGE (exec1)-[:WROTE]->(doc)
MERGE (doc)-[:MENTIONS]->(company1)
MERGE (company2)-[:ACQUIRED]->(company1)
MERGE (exec2)-[:WORKS_FOR {role: 'CEO'}]->(company2)
"""
graph_db.execute_write(ingestion_query, graph_payload)

# 4. Traversal
traversal_query = """
MATCH (start:Executive {name: 'Tony'})
      -[w:WROTE]->(doc:Document)
      -[m:MENTIONS]->(startup:Company)
      <-[a:ACQUIRED]-(parent:Company)
      <-[r:WORKS_FOR {role: 'CEO'}]-(ceo:Executive)
RETURN ceo.name AS Target_CEO, parent.name AS Acquiring_Company
"""
results = graph_db.execute_read(traversal_query)

for row in results:
    print(f"\nTarget Found: {row['Target_CEO']} (CEO of {row['Acquiring_Company']})")

graph_db.close()