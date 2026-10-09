"""Prueba de la interacción: una consulta que obliga al supervisor a enviar la tarea al
investigador, recibir el dato, enviarlo al analista y finalmente cerrar la conversación.

Uso: python main.py
"""

from langchain_core.messages import HumanMessage

from graph import construir_grafo

PREGUNTA = (
    "Según la documentación de logging, ¿qué valores de maxBytes y backupCount usa el ejemplo "
    "de RotatingFileHandler? Con esa configuración, ¿cuánto espacio en disco pueden ocupar como "
    "máximo los logs (el archivo actual más sus copias), en bytes y en megabytes?"
)


def estado_inicial(pregunta: str) -> dict:
    return {
        "messages": [HumanMessage(pregunta)],
        "next_agent": None,
        "instruccion": "",
        "contribuciones": [],
        "pasos": 0,
        "task_completed": False,
    }


def main() -> None:
    app = construir_grafo()
    print(f"🧑 Consulta: {PREGUNTA}\n")
    print("🎬 Flujo de delegación:\n")

    # recursion_limit: techo adicional de pasos del grafo, además de MAX_PASOS del supervisor.
    for evento in app.stream(estado_inicial(PREGUNTA), {"recursion_limit": 20}, stream_mode="updates"):
        for nodo, cambios in evento.items():
            print(f"🔹 {nodo}")
            if nodo == "supervisor" and cambios.get("instruccion"):
                print(f"   → instrucción para {cambios['next_agent']}: {cambios['instruccion']}")
            for m in cambios.get("messages", []):
                print(f"   [{m.name}] {m.text}")
            print()


if __name__ == "__main__":
    main()
