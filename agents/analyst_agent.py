"""Agente de Análisis/Cómputo: hace cálculos con los datos que obtuvo el investigador."""

import ast
import operator as op

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

from config import get_llm
from state import AgentState

# Operaciones aritméticas permitidas. Se evalúa la expresión con ast en lugar de eval():
# el texto lo genera un LLM, y eval() permitiría ejecutar código arbitrario.
_OPERADORES = {
    ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
    ast.Div: op.truediv, ast.Pow: op.pow, ast.USub: op.neg,
}


def _evaluar(nodo: ast.AST) -> float:
    if isinstance(nodo, ast.Constant) and isinstance(nodo.value, (int, float)):
        return nodo.value
    if isinstance(nodo, ast.BinOp):
        return _OPERADORES[type(nodo.op)](_evaluar(nodo.left), _evaluar(nodo.right))
    if isinstance(nodo, ast.UnaryOp):
        return _OPERADORES[type(nodo.op)](_evaluar(nodo.operand))
    raise ValueError("Expresión no permitida: solo números y + - * / ** ( )")


@tool
def calculadora(expresion: str) -> str:
    """Evalúa una expresión aritmética con números, +, -, *, /, ** y paréntesis.
    Ejemplo: '1_000_000 * (3 + 1)'. Usar para cualquier cálculo numérico."""
    try:
        return f"Resultado: {_evaluar(ast.parse(expresion, mode='eval').body)}"
    except Exception as e:
        return f"Error al calcular '{expresion}': {e}"


agente_analista = create_react_agent(
    model=get_llm(),
    tools=[calculadora],
    prompt=(
        "Sos un agente de análisis y cómputo. Tu única función es hacer cálculos con tu "
        "herramienta a partir de los datos que te dan. NO busques información nueva ni "
        "inventes datos que no estén en el contexto. Mostrá la operación y el resultado."
    ),
)


def nodo_analista(state: AgentState) -> dict:
    """Ejecuta al analista con contexto acotado: la instrucción del supervisor más los
    datos que aportó el investigador, sin el resto del historial."""
    instruccion = state["instruccion"]
    datos = "\n\n".join(c["aporte"] for c in state["contribuciones"] if c["agente"] == "investigador")
    tarea = f"{instruccion}\n\nDatos disponibles (aportados por el investigador):\n{datos or '(ninguno)'}"

    resultado = agente_analista.invoke({"messages": [HumanMessage(tarea)]})
    aporte = resultado["messages"][-1].text

    return {
        "messages": [AIMessage(aporte, name="analista")],
        "contribuciones": [{"agente": "analista", "instruccion": instruccion, "aporte": aporte}],
        "pasos": state["pasos"] + 1,
    }
