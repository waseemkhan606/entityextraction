import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
from llm_pipeline.extractor import build_extraction_chain
from llm_pipeline.neo4j_writer import push_graph_to_neo4j
from llm_pipeline.verifier import verify_graph

load_dotenv()

print("="*60)
print(" INITIATING AUTONOMOUS GRAPH EXTRACTION PIPELINE ")
print("="*60)

NEO4J_URI  = os.getenv("NEO4J_URI",  "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASS = os.getenv("NEO4J_PASS", "AlphaFund2026!")

raw_document_chunks = [
    "Tony's Q3 Compliance Report detailed the massive Alpha AI buyout by Microsoft.",
    "Satya Nadella, its CEO, approved the $2B deal yesterday morning.",
    "Meanwhile, Apple announced they have heavily invested in a new startup called NeuralNet Labs.",
    "Tim Cook mentioned that NeuralNet Labs directly competes with Alpha AI in the generative space."
]
print(f"[System] Loaded {len(raw_document_chunks)} unstructured text chunks.")

print("[System] Initializing Gemini 2.5 Flash with Constrained Decoding...")
extraction_chain = build_extraction_chain()

print("\n[System] Commencing Extraction & Ingestion Loop...")
neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))

try:
    for i, chunk in enumerate(raw_document_chunks):
        print(f"\n--- Processing Chunk {i+1}/{len(raw_document_chunks)} ---")
        print(f"Text: '{chunk}'")

        extracted_graph = extraction_chain.invoke({"text": chunk})

        node_count = len(extracted_graph.nodes)
        edge_count = len(extracted_graph.edges)
        print(f"Extraction Success: Found {node_count} Nodes and {edge_count} Edges.")

        push_graph_to_neo4j(extracted_graph, neo4j_driver)
        print("Ingestion Success: Committed to Neo4j.")

except Exception as e:
    print(f"\n[FATAL ERROR] Pipeline halted: {str(e)}")

finally:
    neo4j_driver.close()
    print("\n[System] Pipeline execution complete. Driver connection closed.")

verify_graph(NEO4J_URI, NEO4J_USER, NEO4J_PASS)
