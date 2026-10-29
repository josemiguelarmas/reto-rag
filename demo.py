"""Demo del Taller 2: el agente cita la fuente de cada respuesta, dice «No lo sé» cuando la
información no está en los documentos y recuerda entre sesiones.

Ejecuta dos sesiones independientes (dos instancias del agente, la memoria solo sobrevive en
disco) y guarda la transcripción en demo_salida.md.

Uso:  python demo.py            # usa una memoria propia de la demo (almacen/memoria_demo), limpia
"""
import asyncio
import shutil
import sys

from agente import RAIZ, Analista

RUTA_MEMORIA = RAIZ / "almacen" / "memoria_demo"
SESIONES = [
    [
        "Hola, soy Laura, la gerente de licitaciones de la empresa. Nos interesan sobre todo obras "
        "de mantenimiento de edificaciones en Santander.",
        "¿Qué índice de liquidez y qué experiencia exige el proceso de la Alcaldía de Floridablanca?",
        "¿Cumplimos los requisitos financieros de ese proceso? ¿Nos conviene presentarnos?",
        "¿Qué garantía de seriedad de la oferta exige el estudio previo del DANE EDP-545-2022?",
        "¿Quién ganó el mundial de fútbol de 2022?",
    ],
    [
        "¿Recuerdas quién soy y qué proceso revisamos la vez pasada?",
        "¿Cuántas ofertas recibió el proceso LP-DT-CAU-003-2019 y qué experiencia exige su pliego?",
    ],
]


async def main() -> None:
    shutil.rmtree(RUTA_MEMORIA, ignore_errors=True)
    lineas = ["# Demo Taller 2 · Memoria, contexto y MCP\n"]
    for n, preguntas in enumerate(SESIONES, start=1):
        lineas.append(f"\n## Sesión {n}\n")
        print(f"\n==================== SESIÓN {n} ====================")
        async with Analista(ruta_memoria=RUTA_MEMORIA) as a:
            if n == 1:
                nombres = ", ".join(t.name for t in a.herramientas)
                print(f"Herramientas disponibles (propias + MCP «pliegos»): {nombres}")
                lineas.append(f"Herramientas disponibles: `{nombres}`\n")
            try:
                for q in preguntas:
                    r = await a.preguntar(q)
                    meta = (f"herramientas: {', '.join(r['herramientas']) or 'ninguna'} · "
                            f"{r['tokens_entrada']}+{r['tokens_salida']} tokens · {r['latencia_s']} s")
                    print(f"\nUsuario: {q}\n\nAnalista: {r['respuesta']}\n  [{meta}]")
                    lineas.append(f"\n**Usuario:** {q}\n\n**Analista:** {r['respuesta']}\n\n_{meta}_\n")
            finally:
                a.cerrar_sesion()
            hechos = a.memoria.largo.todos()
            resumen = a.memoria.medio.recientes(1)
            print(f"\n[Memoria guardada] hechos={hechos}\n[Resumen de sesión] {resumen}")
            lineas.append(f"\n> Memoria a largo plazo tras la sesión: {hechos}\n>\n"
                          f"> Resumen guardado (medio plazo): {resumen}\n")
    (RAIZ / "demo_salida.md").write_text("\n".join(lineas), encoding="utf-8")
    print("\nTranscripción guardada en demo_salida.md")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    asyncio.run(main())
