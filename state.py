"""Esquema de datos compartido por todos los nodos del grafo."""

import operator
from typing import Annotated, Literal, Optional, TypedDict

from langgraph.graph import MessagesState


class Contribucion(TypedDict):
    """Registro de un aporte: qué agente lo hizo, qué se le pidió y qué respondió."""
    agente: str
    instruccion: str
    aporte: str


class AgentState(MessagesState):
    """Estado compartido. MessagesState es un TypedDict: hereda de él la lista "messages"
    (con el reducer add_messages) y suma campos propios del orquestador."""

    # Próximo nodo elegido por el supervisor, o FINISH para pasar a la síntesis.
    next_agent: Optional[Literal["investigador", "analista", "FINISH"]]
    # Instrucción puntual que el supervisor le deja al especialista elegido.
    instruccion: str
    # Reducer operator.add: cada aporte se suma a la lista en lugar de reemplazarla,
    # así queda el registro completo de qué agente contribuyó con qué información.
    contribuciones: Annotated[list[Contribucion], operator.add]
    # Cantidad de veces que se invocó a un especialista (corte de seguridad).
    pasos: int
    task_completed: bool
