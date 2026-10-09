"""Grafo del orquestador: Supervisor -> especialistas -> Supervisor -> ... -> síntesis.

Ejecutarlo directo exporta el diagrama del grafo: python graph.py
"""

from typing import Literal

from langchain_core.messages import AIMessage
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

from agents import nodo_analista, nodo_investigador
from config import get_llm
from state import AgentState

# Condición de parada dura: después de esta cantidad de intervenciones de especialistas,
# el supervisor pasa a la síntesis aunque el LLM quiera seguir delegando.
MAX_PASOS = 6


class DecisionSupervisor(BaseModel):
    next: Literal["investigador", "analista", "FINISH"] = Field(
        description="Agente que debe intervenir ahora, o FINISH si es momento de finalizar"
    )
    instruccion: str = Field(
        description="Instrucción concreta para el agente elegido (vacía si next es FINISH)"
    )
    razon: str = Field(description="Breve justificación de la decisión")


SUPERVISOR_PROMPT = """Sos el Supervisor de un equipo de dos especialistas:
- investigador: busca datos concretos en la documentación técnica de Python (Vector DB).
- analista: hace cálculos a partir de los datos que ya obtuvo el investigador.

Dada la conversación actual, ¿quién debe intervenir ahora o es momento de finalizar?
Respondé con "investigador", "analista" o "FINISH", y una instrucción concreta para el agente elegido.

Reglas de delegación:
1. Si falta un dato de la documentación, mandá al investigador.
2. Si ya están los datos pero falta un cálculo, mandá al analista.
3. No repitas un agente que ya cumplió su parte correctamente.

Rúbrica de validación (revisala antes de responder FINISH):
a) Los datos usados vienen de un aporte del investigador que cita su fuente, no son supuestos.
b) Si la tarea pide un cálculo, el analista lo hizo con su herramienta y el resultado es
   consistente con los datos del investigador.
c) Los aportes cubren todo lo que pide la tarea original.
Si algún aporte no cumple la rúbrica, mandá de nuevo al especialista que corresponda con una
instrucción que diga exactamente qué corregir o completar. Solo respondé FINISH cuando se cumplan a), b) y c).

Aportes del equipo hasta ahora:
{contribuciones}
"""

_llm = get_llm()
_llm_supervisor = _llm.with_structured_output(DecisionSupervisor)


def _formatear_contribuciones(state: AgentState) -> str:
    return "\n".join(
        f"- [{c['agente']}] (instrucción: {c['instruccion']})\n  {c['aporte']}" for c in state["contribuciones"]
    ) or "(ninguno todavía)"


def nodo_supervisor(state: AgentState) -> dict:
    """Decide el próximo paso. Corta por MAX_PASOS aunque el LLM quiera seguir."""
    if state["pasos"] >= MAX_PASOS:
        return {"next_agent": "FINISH", "instruccion": "", "task_completed": True}

    decision = _llm_supervisor.invoke([
        ("system", SUPERVISOR_PROMPT.format(contribuciones=_formatear_contribuciones(state))),
        ("human", f"Tarea original: {state['messages'][0].text}"),
    ])
    return {
        "next_agent": decision.next,
        "instruccion": decision.instruccion,
        "task_completed": decision.next == "FINISH",
        "messages": [AIMessage(f"Decisión: {decision.next}. {decision.razon}", name="supervisor")],
    }


def nodo_sintesis(state: AgentState) -> dict:
    """Fase de síntesis final: redacta la respuesta al usuario combinando los aportes."""
    prompt = (
        f"Tarea original: {state['messages'][0].text}\n\n"
        f"Aportes del equipo:\n{_formatear_contribuciones(state)}\n\n"
        "Redactá una respuesta final clara y breve para el usuario combinando estos aportes. "
        "No agregues datos que no estén en los aportes."
    )
    return {"messages": [AIMessage(_llm.invoke(prompt).text, name="sintesis")]}


def enrutar(state: AgentState) -> Literal["investigador", "analista", "sintesis"]:
    """Traduce la decisión del supervisor al nombre del nodo siguiente."""
    if state["next_agent"] == "FINISH":
        return "sintesis"
    return state["next_agent"]


def construir_grafo():
    grafo = StateGraph(AgentState)
    grafo.add_node("supervisor", nodo_supervisor)
    grafo.add_node("investigador", nodo_investigador)
    grafo.add_node("analista", nodo_analista)
    grafo.add_node("sintesis", nodo_sintesis)

    grafo.add_edge(START, "supervisor")
    grafo.add_conditional_edges("supervisor", enrutar, {
        "investigador": "investigador",
        "analista": "analista",
        "sintesis": "sintesis",
    })
    # Topología jerárquica: los especialistas siempre devuelven el control al supervisor.
    grafo.add_edge("investigador", "supervisor")
    grafo.add_edge("analista", "supervisor")
    grafo.add_edge("sintesis", END)
    return grafo.compile()


if __name__ == "__main__":
    app = construir_grafo()
    with open("graph.png", "wb") as f:
        f.write(app.get_graph().draw_mermaid_png())
    print(app.get_graph().draw_mermaid())
    print("✅ Diagrama guardado en graph.png")
