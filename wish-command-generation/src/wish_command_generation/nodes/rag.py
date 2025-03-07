"""RAG-related node functions for the command generation graph."""

from ..models import GraphState


def generate_query(state: GraphState) -> GraphState:
    """Generate a query for RAG search from the task"""
    # Mock implementation for testing
    # In the actual implementation, LangChain will be used to generate queries

    # Generate a simple query based on the task
    task = state.wish.wish.lower()

    if "port scan" in task:
        query = "nmap port scan techniques"
    elif "vulnerability" in task:
        query = "vulnerability assessment tools kali linux"
    else:
        query = "penetration testing commands kali linux"

    # Save the query to the state
    state_dict = state.model_dump()
    state_dict["query"] = query

    return GraphState(**state_dict)


def retrieve_documents(state: GraphState) -> GraphState:
    """Retrieve relevant documents using the generated query"""
    # Here we are using a placeholder for the actual RAG implementation
    # In the actual implementation, you need to set up a vector store or retriever

    # Placeholder results
    context = [
        "# nmap command\nnmap is a network scanning tool.\nBasic usage: nmap [options] [target]\n\n"
        "Main options:\n-p: Port specification\n-sV: Version detection\n"
        "-A: OS detection, version detection, script scanning, traceroute\n"
        "-T4: Scan speed setting (0-5, higher is faster)",
        "# rustscan\nrustscan is a fast port scanner.\n"
        "Basic usage: rustscan -a [target IP] -- [nmap options]\n\n"
        "Main options:\n-r: Port range specification (e.g., -r 1-1000)\n"
        "-b: Batch size (number of simultaneous connections)\n"
        "--scripts: Execute nmap scripts"
    ]

    # Update the state
    state_dict = state.model_dump()
    state_dict["context"] = context

    return GraphState(**state_dict)
