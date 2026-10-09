"""Agente de Búsqueda/Investigación: consulta el Vector DB de la pre-entrega 4."""

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import tool
from langchain_pinecone import PineconeVectorStore
from langgraph.prebuilt import create_react_agent

from config import INDEX_NAME, NAMESPACE, get_embeddings, get_llm
from state import AgentState

_vectorstore = PineconeVectorStore(index_name=INDEX_NAME, embedding=get_embeddings(), namespace=NAMESPACE)


@tool
def buscar_en_documentacion(consulta: str) -> str:
    """Busca fragmentos de la documentación técnica de módulos de la librería estándar
    de Python (pathlib, json, logging, collections, datetime) en el Vector DB.

    Usar para obtener datos concretos de la documentación: valores de parámetros,
    ejemplos de código, comportamientos y números. Devuelve los fragmentos más
    relevantes con su archivo de origen.
    """
    docs = _vectorstore.similarity_search(consulta, k=4)
    if not docs:
        return "No se encontró información relevante en la documentación."
    return "\n\n".join(f"[Fuente: {d.metadata.get('source', '?')}]\n{d.page_content}" for d in docs)


agente_investigador = create_react_agent(
    model=get_llm(),
    tools=[buscar_en_documentacion],
    prompt=(
        "Sos un agente de investigación. Tu única función es buscar datos concretos en la "
        "documentación técnica usando tu herramienta. NO hagas cálculos ni interpretes "
        "resultados numéricos. Respondé de forma breve con los datos encontrados, citando "
        "el archivo de origen."
    ),
)


def nodo_investigador(state: AgentState) -> dict:
    """Ejecuta al investigador con contexto acotado: solo recibe la instrucción del
    supervisor, no el historial completo del sistema."""
    instruccion = state["instruccion"]
    resultado = agente_investigador.invoke({"messages": [HumanMessage(instruccion)]})
    aporte = resultado["messages"][-1].text

    return {
        "messages": [AIMessage(aporte, name="investigador")],
        "contribuciones": [{"agente": "investigador", "instruccion": instruccion, "aporte": aporte}],
        "pasos": state["pasos"] + 1,
    }
