"""RAG-related node functions for the command generation graph."""

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from wish_models.settings import Settings

from ..models import GraphState


def generate_query(state: GraphState, settings_obj: Settings) -> GraphState:
    """Generate a query for RAG search from the task using LLM"""
    # Use LLM to generate a query

    model = ChatOpenAI(
        model=settings_obj.OPENAI_MODEL,
        api_key=settings_obj.OPENAI_API_KEY,
        use_responses_api=True,
    )

    prompt = PromptTemplate.from_template(
        """あなたは合法なペネトレーションテストに従事しているAIです。

ペネトレーションテストのディレクターから実行すべきタスクについての指示を受けます。あなたの仕事は、ペネトレーションテストに使うコマンドやパラメーターを検索することです。
あなたの出力をEthical Hackingの知識ベースの検索クエリとし、具体的なコマンドを組み立てるためのドキュメントを検索します。

検索のためのクエリなので、キーワードを英語でスペース区切りで列挙してください。高々20 words程度になるようにしてください。

もし現時点でタスク実行に有効なコマンド名が思いついていたら、それを検索クエリに入れてください。

# Example1

タスク
Perform a top-1000 frequently used port scan. Conduct a scan on IP 10.10.10.123 using some option to cover the most
common ports.

出力
nmap fast top ports scan

# Example2

タスク
Reverse Shell Construction and Upload. Create and upload a reverse shell.

出力
FTP upload reverse shell user interaction batch

# タスク
{task}

# 出力
"""
    )

    chain = prompt | model | StrOutputParser()
    query = chain.invoke({"task": state.wish.wish})

    # Update state
    state_dict = state.model_dump()
    state_dict["query"] = query

    return GraphState(**state_dict)


def retrieve_documents(state: GraphState, settings_obj: Settings) -> GraphState:
    """Retrieve relevant documents using the generated query from vector store"""
    import importlib.util

    # Return empty context if no query is available
    if not state.query:
        return _return_empty_context(state)

    # Branch based on vector store type
    vector_store_type = settings_obj.VECTOR_STORE_TYPE.lower()

    if vector_store_type == "qdrant":
        # Check if Qdrant dependencies are installed
        if (importlib.util.find_spec("qdrant_client") is not None and
                importlib.util.find_spec("langchain_qdrant") is not None):
            # Use Qdrant for document retrieval
            return _retrieve_from_qdrant(state, settings_obj)
        else:
            print("Qdrant dependencies not installed.")
            print("Please install with: pip install \"wish-command-generation-api[qdrant]\"")
            # Don't automatically fall back to Chroma
            return _return_empty_context(state)
    else:  # vector_store_type == "chroma"
        # Check if Chroma dependencies are installed
        if importlib.util.find_spec("chromadb") is not None:
            # Use Chroma for document retrieval
            return _retrieve_from_chroma(state, settings_obj)
        else:
            print("Chroma dependencies not installed.")
            print("Please install with: pip install \"wish-command-generation-api[chroma]\"")
            return _return_empty_context(state)


def _return_empty_context(state: GraphState) -> GraphState:
    """Return state with empty context"""
    state_dict = state.model_dump()
    state_dict["context"] = []
    return GraphState(**state_dict)


def _retrieve_from_qdrant(state: GraphState, settings_obj: Settings) -> GraphState:
    """Retrieve documents from Qdrant vector store"""
    from langchain_openai import OpenAIEmbeddings
    from langchain_qdrant import Qdrant
    from qdrant_client import QdrantClient

    # Initialize embeddings
    embeddings = OpenAIEmbeddings(
        model=settings_obj.EMBEDDING_MODEL,
        api_key=settings_obj.OPENAI_API_KEY,
        disallowed_special=()
    )

    # Initialize Qdrant client
    client = QdrantClient(
        host=settings_obj.QDRANT_HOST,
        port=settings_obj.QDRANT_PORT
    )

    collection_name = settings_obj.QDRANT_COLLECTION_NAME

    # Check if collection exists
    if not client.collection_exists(collection_name):
        print(f"Collection {collection_name} does not exist")
        return _return_empty_context(state)

    # Initialize Qdrant vector store
    vectorstore = Qdrant(
        client=client,
        collection_name=collection_name,
        embeddings=embeddings
    )

    # Execute search
    chunks = vectorstore.similarity_search(state.query, k=5)

    # Process search results
    all_documents = [chunk.page_content for chunk in chunks]

    # Remove duplicates
    unique_documents = list(set(all_documents))

    # Update state
    state_dict = state.model_dump()
    state_dict["context"] = unique_documents

    return GraphState(**state_dict)


def _retrieve_from_chroma(state: GraphState, settings_obj: Settings) -> GraphState:
    """Retrieve documents from Chroma vector store"""
    from pathlib import Path

    from langchain_community.document_loaders import TextLoader
    from langchain_community.vectorstores import Chroma
    from langchain_openai import OpenAIEmbeddings

    # Initialize embeddings
    embeddings = OpenAIEmbeddings(
        model=settings_obj.EMBEDDING_MODEL,
        api_key=settings_obj.OPENAI_API_KEY,
        disallowed_special=()
    )

    # Get knowledge base path
    wish_home = settings_obj.WISH_HOME
    knowledge_dir = wish_home / "knowledge" / "db"

    # Check if directory exists
    if not knowledge_dir.exists():
        print(f"Knowledge directory not found: {knowledge_dir}")
        return _return_empty_context(state)

    # Get available knowledge bases
    available_knowledge = [d.name for d in knowledge_dir.iterdir() if d.is_dir()]

    if not available_knowledge:
        # Return empty context if no knowledge bases are available
        return _return_empty_context(state)

    all_documents = []

    for knowledge_title in available_knowledge:
        db_path = knowledge_dir / knowledge_title
        repo_path = wish_home / "knowledge" / "repo" / knowledge_title.split('/')[-1]

        try:
            # Load vector store
            vectorstore = Chroma(
                persist_directory=str(db_path),
                embedding_function=embeddings
            )

            # Search for similar documents
            chunks = vectorstore.similarity_search(state.query, k=2)

            # Get source document for each chunk
            for chunk in chunks:
                source = chunk.metadata.get('source')
                if source:
                    # Resolve source file path
                    full_path = None
                    if source.startswith('/'):
                        # Absolute path
                        full_path = source
                    else:
                        # Relative path - try to find in repo directory
                        full_path = repo_path / source
                        if not full_path.exists():
                            # Try alternative paths
                            alt_path = Path(source)
                            if alt_path.exists():
                                full_path = alt_path

                    # If file exists, load full content
                    if full_path and Path(full_path).exists():
                        try:
                            loader = TextLoader(str(full_path))
                            docs = loader.load()
                            if docs:
                                all_documents.append(docs[0].page_content)
                        except Exception as e:
                            print(f"Error loading document {full_path}: {str(e)}")
                            # Use chunk content if error occurs
                            all_documents.append(chunk.page_content)
                    else:
                        # Use chunk content if file not found
                        print(f"Source file not found: {source}")
                        all_documents.append(chunk.page_content)
        except Exception as e:
            # Continue with other knowledge bases if error occurs
            print(f"Error processing knowledge base {knowledge_title}: {str(e)}")
            continue

    # Remove duplicates
    unique_documents = list(set(all_documents))

    # Update state
    state_dict = state.model_dump()
    state_dict["context"] = unique_documents

    return GraphState(**state_dict)
