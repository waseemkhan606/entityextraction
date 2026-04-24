from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from .models import KnowledgeGraph

def build_extraction_chain():
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.0)
    graph_extractor = llm.with_structured_output(KnowledgeGraph)

    extraction_prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are an elite Information Extraction AI. Extract entities and relationships. "
         "Resolve all pronouns to canonical names. Use ONLY allowed relationship types. "
         "Output MUST strictly adhere to the JSON schema."),
        ("human", "Extract the graph from this text:\n\n{text}")
    ])

    return extraction_prompt | graph_extractor
