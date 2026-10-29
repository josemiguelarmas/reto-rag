"""Servidor MCP real: se arranca por stdio y se llama con el mismo cliente que usa el agente."""
import asyncio
import json

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools

from agente import conexion_mcp


def _contenido(resultado):
    """El adaptador devuelve el contenido MCP como texto JSON (o lista de bloques)."""
    if isinstance(resultado, tuple):
        resultado = resultado[0]
    if isinstance(resultado, list):
        resultado = "".join(b.get("text", "") if isinstance(b, dict) else str(b) for b in resultado)
    return json.loads(resultado)


def test_servidor_mcp_expone_y_ejecuta_herramientas():
    async def flujo():
        cliente = MultiServerMCPClient(conexion_mcp())
        async with cliente.session("pliegos") as sesion:
            herramientas = {t.name: t for t in await load_mcp_tools(sesion)}
            assert set(herramientas) == {"buscar_en_pliegos", "listar_documentos"}
            assert "FUENTE" in herramientas["buscar_en_pliegos"].description
            r = _contenido(await herramientas["buscar_en_pliegos"].ainvoke(
                {"consulta": "índice de liquidez", "referencia": "FLO-INFRA-SA-MC-007-2025", "k": 2}))
            vacio = _contenido(await herramientas["buscar_en_pliegos"].ainvoke(
                {"consulta": "¿Cuál es la capital de Francia?"}))
            return r, vacio

    r, vacio = asyncio.run(flujo())
    assert r["encontrado"] and "1.8" in r["fragmentos"][0]["texto"]
    assert r["fragmentos"][0]["fuente"].startswith("14_FLO_INFRA_SA_MC_007_2025.pdf, p. 2")
    assert vacio["encontrado"] is False
