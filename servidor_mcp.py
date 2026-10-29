"""Servidor MCP «pliegos»: expone el RAG sobre los documentos del curso por stdio.

El agente (agente.py) lo arranca como subproceso y usa sus herramientas mediante
langchain-mcp-adapters. Cualquier otro cliente MCP (VS Code / Copilot en modo Agente,
MCP Inspector) puede usarlo igual: ver .vscode/mcp.json.

Prueba manual:  mcp dev servidor_mcp.py      (abre el MCP Inspector)
Importante: no usar print() aquí; stdout está reservado para el protocolo JSON-RPC.
"""
import logging
import sys

from mcp.server.fastmcp import FastMCP

import pliegos

logging.basicConfig(stream=sys.stderr, level=logging.WARNING)
mcp = FastMCP("pliegos")


@mcp.tool()
def buscar_en_pliegos(consulta: str, referencia: str | None = None, k: int = 4) -> dict:
    """Busca en el TEXTO de los 20 documentos del curso (estudios previos, invitaciones y
    pliegos de condiciones en PDF) y devuelve los fragmentos relevantes con su FUENTE
    (archivo, página y sección), que debe citarse en la respuesta.

    Úsela para requisitos que solo están en los documentos: requisitos habilitantes
    (jurídicos, financieros, de experiencia), indicadores exigidos (liquidez, endeudamiento,
    cobertura, capital de trabajo, rentabilidades), códigos UNSPSC exigidos, perfil e
    idoneidad, obligaciones, cronograma, criterios de evaluación, garantías y forma de pago.

    - consulta: lo que se busca, en lenguaje natural (p. ej. «índice de liquidez exigido»).
    - referencia: referencia del proceso (p. ej. «FLO-INFRA-SA-MC-007-2025») para buscar solo
      en su documento. Úsela siempre que la pregunta se refiera a un proceso concreto.
    - k: número máximo de fragmentos (1 a 10).

    Si devuelve encontrado=false, la información NO está en los documentos.
    """
    return pliegos.buscar(consulta, referencia, k)


@mcp.tool()
def listar_documentos() -> list[dict]:
    """Lista los documentos indexados con la referencia del proceso, la entidad y el archivo.
    Úsela para averiguar la referencia de un proceso cuando solo se conoce la entidad."""
    return pliegos.documentos()


if __name__ == "__main__":
    pliegos.indexar()          # indexa al arrancar (solo la primera vez tarda)
    mcp.run()                  # stdio por defecto
