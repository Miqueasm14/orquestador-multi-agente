"""Configuración compartida: modelo de lenguaje y conexión al Vector DB de la pre-entrega 4."""

import os

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

load_dotenv()

# --- Vector DB de la pre-entrega 4 (Pinecone) ---
# El investigador busca en el índice que se creó y cargó en la pre-entrega 4:
# documentación de módulos de la librería estándar de Python.
INDEX_NAME = os.environ.get("INDEX_NAME", "rag-hibrido-python-docs")
NAMESPACE = "python-stdlib-docs"


def get_llm() -> ChatGoogleGenerativeAI:
    """Modelo usado por el supervisor, los especialistas y la síntesis.

    Versión "lite" de Gemini: en el plan gratuito tiene más pedidos diarios
    disponibles que gemini-flash-latest, y cada consulta al orquestador hace ~8.
    """
    return ChatGoogleGenerativeAI(model="gemini-flash-lite-latest", temperature=0)


def get_embeddings() -> GoogleGenerativeAIEmbeddings:
    """Mismo modelo y dimensión con los que se indexó el Vector DB en la pre-entrega 4."""
    return GoogleGenerativeAIEmbeddings(model="gemini-embedding-001", output_dimensionality=1536)
