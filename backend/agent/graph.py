import os
from langgraph.graph import StateGraph, START, END
from .state import AgentState
from .nodes import (
    node_normalize, node_research, node_split, 
    node_complete, node_merge, node_reply, node_save
)
from config import settings

# Setup LangSmith Tracing if enabled
if settings.LANGCHAIN_TRACING_V2.lower() == "true":
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY or ""
    os.environ["LANGCHAIN_PROJECT"] = settings.LANGCHAIN_PROJECT
    os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"

def create_research_graph():
    """Builds and compiles the research workflow graph using StateGraph."""
    workflow = StateGraph(AgentState)
    
    # Add Nodes
    workflow.add_node("normalize", node_normalize)
    workflow.add_node("research", node_research)
    workflow.add_node("split", node_split)
    workflow.add_node("complete", node_complete)
    workflow.add_node("merge", node_merge)
    workflow.add_node("reply", node_reply)
    workflow.add_node("save", node_save)
    
    # Define Edges as per request:
    # START → node_normalize
    workflow.add_edge(START, "normalize")
    # node_normalize → node_research
    workflow.add_edge("normalize", "research")
    
    # Parallel start: node_research → node_split AND node_research → node_complete
    workflow.add_edge("research", "split")
    workflow.add_edge("research", "complete")
    
    # Merging back: node_split → node_merge AND node_complete → node_merge
    workflow.add_edge("split", "merge")
    workflow.add_edge("complete", "merge")
    
    # Continue chain: node_merge → node_reply
    workflow.add_edge("merge", "reply")
    # node_reply → node_save
    workflow.add_edge("reply", "save")
    # node_save → END
    workflow.add_edge("save", END)
    
    return workflow.compile()

# Single compiled instance
research_graph = create_research_graph()
