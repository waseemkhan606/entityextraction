# knowledge-graph-primitives

An autonomous knowledge graph extraction pipeline that ingests raw, unstructured text and builds a structured graph database using **Gemini 2.5 Flash**, **LangChain**, and **Neo4j**.

The pipeline reads plain text (e.g. financial transcripts, compliance reports), uses an LLM to extract named entities and their relationships into a validated schema, and commits the result to a Neo4j graph database — making multi-hop relational queries possible over unstructured data.

---

## How It Works

```
Raw Text Chunks
      │
      ▼
┌─────────────────────────────────┐
│  Gemini 2.5 Flash (temp=0.0)    │  ← LangChain extraction chain
│  + Pydantic structured output   │  ← constrains output to KnowledgeGraph schema
└─────────────┬───────────────────┘
              │  KnowledgeGraph { nodes: [...], edges: [...] }
              ▼
┌─────────────────────────────────┐
│  Neo4j Graph Database           │  ← idempotent MERGE Cypher queries
│  (Docker, bolt://localhost:7687)│
└─────────────┬───────────────────┘
              │
              ▼
       Verification Query
  (multi-hop Cypher traversal)
```

### Step-by-step

1. **Load** — 4 raw text chunks (mock financial transcripts) are fed into the pipeline.
2. **Extract** — Each chunk is sent to Gemini 2.5 Flash via LangChain with `temperature=0.0` for deterministic output. The LLM is forced to return a `KnowledgeGraph` Pydantic object — no free-form text, no hallucinated schema.
3. **Validate** — The Pydantic schema constrains nodes to typed labels (`Person`, `Company`, `Document`) and edges to an explicit allowed vocabulary: `ACQUIRED`, `INVESTED_IN`, `COMPETES_WITH`, `WORKS_FOR`, `WROTE`, `MENTIONS`.
4. **Ingest** — Nodes and edges are written to Neo4j using `MERGE` (idempotent — safe to re-run without creating duplicates).
5. **Verify** — A multi-hop Cypher query traverses the graph to confirm the extracted relationships are correct.

### Example

Given this input text:
```
"Tim Cook mentioned that NeuralNet Labs directly competes with Alpha AI in the generative space."
```

The LLM extracts:
```json
{
  "nodes": [
    { "id": "Tim Cook",       "label": "Person",  "original_text": "Tim Cook" },
    { "id": "NeuralNet Labs", "label": "Company", "original_text": "NeuralNet Labs" },
    { "id": "Alpha AI",       "label": "Company", "original_text": "Alpha AI" }
  ],
  "edges": [
    { "source_node_id": "NeuralNet Labs", "target_node_id": "Alpha AI", "relationship_type": "COMPETES_WITH" }
  ]
}
```

After all 4 chunks are processed, this verification query:
```cypher
MATCH (c1:Company)-[:COMPETES_WITH]->(c2:Company)<-[:ACQUIRED]-(:Company {id: 'Microsoft'})
RETURN c1.id AS Competitor, c2.id AS Acquired_Startup
```
Returns:
```
Graph Intelligence: NeuralNet Labs competes directly with Alpha AI, which is owned by Microsoft.
```

---

## Project Structure

```
.
├── alphafund-graph/
│   └── docker-compose.yml      # Neo4j 5.18.0 service (with APOC plugin)
├── llm_pipeline/
│   ├── __init__.py
│   ├── models.py               # Pydantic schemas: Node, Edge, KnowledgeGraph
│   ├── extractor.py            # LangChain + Gemini extraction chain
│   ├── neo4j_writer.py         # push_graph_to_neo4j() — Cypher MERGE logic
│   └── verifier.py             # Post-ingestion graph verification query
├── main.py                     # Entry point — runs the full pipeline
├── requirements.txt
├── .env                        # Secret credentials (never committed)
└── .env.example                # Safe-to-commit template
```

---

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- Python 3.10+
- A [Gemini API key](https://aistudio.google.com/app/apikey)

---

## Setup

### 1. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:
```
GOOGLE_API_KEY=your_actual_gemini_api_key
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASS=AlphaFund2026!
```

### 2. Start Neo4j

```bash
cd alphafund-graph
docker compose up -d
```

Neo4j starts on two ports:

| Port | Purpose |
|------|---------|
| `7474` | Neo4j Browser (web UI) |
| `7687` | Bolt protocol (Python driver) |

Wait ~15–20 seconds on first launch, then verify at [http://localhost:7474](http://localhost:7474).

To stop: `docker compose down`

### 3. Install Python dependencies

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Run the pipeline

```bash
python main.py
```

---

## Schema Reference

| Class | Fields |
|-------|--------|
| `Node` | `id` (canonical name, pronouns resolved), `label` (Person / Company / Document), `original_text` |
| `Edge` | `source_node_id`, `target_node_id`, `relationship_type` |
| `KnowledgeGraph` | `nodes: list[Node]`, `edges: list[Edge]` |

**Allowed relationship types:** `ACQUIRED` · `INVESTED_IN` · `COMPETES_WITH` · `WORKS_FOR` · `WROTE` · `MENTIONS`

---

## Key Design Decisions

- **`temperature=0.0`** — deterministic extraction; same input always yields the same graph.
- **Pydantic `Literal` for relationship types** — the LLM cannot invent edge types outside the allowed vocabulary.
- **`MERGE` over `CREATE`** — ingestion is idempotent; re-running the pipeline will not create duplicate nodes or edges.
- **`python-dotenv`** — secrets never touch source code; loaded from `.env` at runtime.
- **Pinned Neo4j image** (`neo4j:5.18.0`) — avoids silent breaking changes from `latest`.
- **APOC plugin enabled** — required for advanced graph operations and future LLM-integrated export/import.
