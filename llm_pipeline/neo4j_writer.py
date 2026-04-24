from neo4j import GraphDatabase
from .models import KnowledgeGraph

def push_graph_to_neo4j(graph_data: KnowledgeGraph, driver):
    with driver.session() as session:
        for node in graph_data.nodes:
            node_query = f"""
            MERGE (n:{node.label} {{id: $id}})
            ON CREATE SET n.original_text = $original_text
            """
            session.run(node_query, id=node.id, original_text=node.original_text)

        for edge in graph_data.edges:
            edge_query = f"""
            MATCH (source {{id: $source_id}})
            MATCH (target {{id: $target_id}})
            MERGE (source)-[r:{edge.relationship_type}]->(target)
            """
            session.run(edge_query,
                        source_id=edge.source_node_id,
                        target_id=edge.target_node_id)
