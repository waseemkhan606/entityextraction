from typing import Literal
from pydantic import BaseModel, Field

RelationshipType = Literal[
    "ACQUIRED",
    "INVESTED_IN",
    "COMPETES_WITH",
    "WORKS_FOR",
    "WROTE",
    "MENTIONS",
]

class Node(BaseModel):
    id: str = Field(description="Canonical entity name, with all pronouns resolved")
    label: str = Field(description="Entity type: Person, Company, or Document")
    original_text: str = Field(description="The original text span that mentions this entity")

class Edge(BaseModel):
    source_node_id: str = Field(description="The id of the source node")
    target_node_id: str = Field(description="The id of the target node")
    relationship_type: RelationshipType = Field(description="The type of relationship between the two nodes")

class KnowledgeGraph(BaseModel):
    nodes: list[Node] = Field(description="All entities extracted from the text")
    edges: list[Edge] = Field(description="All relationships between entities")
