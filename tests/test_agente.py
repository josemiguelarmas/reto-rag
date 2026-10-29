"""Integración agente + servidor MCP + memoria con un modelo simulado (sin API).

El modelo simulado decide llamar a buscar_en_pliegos; la herramienta se ejecuta de verdad en el
servidor MCP por stdio y su resultado vuelve al agente. Valida el cableado, no la calidad del LLM
(esa se mide con evaluar.py y el modelo real).
"""
import asyncio

from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, ToolMessage

from agente import Analista


class ModeloFalso(GenericFakeChatModel):
    def bind_tools(self, tools, **kwargs):
        return self


def test_agente_usa_herramienta_mcp_y_recuerda(tmp_path):
    respuestas = iter([
        AIMessage(content="", tool_calls=[{"name": "buscar_en_pliegos", "id": "c1", "args": {
            "consulta": "índice de liquidez", "referencia": "FLO-INFRA-SA-MC-007-2025"}}]),
        AIMessage(content="Exige liquidez ≥ 1.8.\nFuentes: 14_FLO_INFRA_SA_MC_007_2025.pdf, p. 2"),
        AIMessage(content="Resumen: se consultó la liquidez de FLO-INFRA-SA-MC-007-2025."),   # resumen
        AIMessage(content="[]"),                                                              # hechos
    ])

    async def flujo():
        async with Analista(modelo=ModeloFalso(messages=respuestas), ruta_memoria=tmp_path) as a:
            nombres = {t.name for t in a.herramientas}
            r = await a.preguntar("¿Qué liquidez exige FLO-INFRA-SA-MC-007-2025?")
            a.cerrar_sesion()
            return nombres, r, a.memoria.medio.recientes(1)

    nombres, r, resumenes = asyncio.run(flujo())
    assert {"buscar_procesos", "consultar_empresa", "calcular_indicadores",
            "buscar_en_pliegos", "listar_documentos"} <= nombres
    assert r["herramientas"] == ["buscar_en_pliegos"]
    assert "Fuentes: 14_FLO" in r["respuesta"]
    assert resumenes and "FLO-INFRA-SA-MC-007-2025" in resumenes[0]


def test_resultado_mcp_llega_al_modelo(tmp_path):
    """El segundo turno del modelo recibe el ToolMessage con el fragmento real del pliego."""
    vistos = []

    class Espia(ModeloFalso):
        def _generate(self, messages, *args, **kwargs):
            vistos.extend(m for m in messages if isinstance(m, ToolMessage))
            return super()._generate(messages, *args, **kwargs)

    respuestas = iter([
        AIMessage(content="", tool_calls=[{"name": "buscar_en_pliegos", "id": "c1", "args": {
            "consulta": "garantía de seriedad", "referencia": "FLO-INFRA-SA-MC-007-2025"}}]),
        AIMessage(content="ok"),
    ])

    async def flujo():
        async with Analista(modelo=Espia(messages=respuestas), memoria=False) as a:
            return await a.preguntar("garantía")

    asyncio.run(flujo())
    assert vistos and "14_FLO_INFRA_SA_MC_007_2025.pdf" in str(vistos[0].content)
    assert "10 % del presupuesto oficial" in str(vistos[0].content)
