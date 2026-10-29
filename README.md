# Taller 2 · Memoria, contexto y MCP — Agente analista del SECOP

Solución del Taller 02 del reto «Agente analista de contratación pública» (IA 2026-2, Icesi;
enunciado en `Reto_IA_2026.pdf` de [armandoordonez/taller_agente](https://github.com/armandoordonez/taller_agente)).

**Reto:** agregar al agente del Taller 1 **RAG sobre los documentos del curso**, **una herramienta vía
servidor MCP** y **memoria entre sesiones**. **Entregable:** una demo en la que el agente cita la fuente
de cada respuesta. **Criterio clave:** que responda «no lo sé» cuando la información no está.

## Arquitectura

```
usuario ─► agente.py (LangChain create_agent, Claude)
             ├─ herramientas propias (Taller 1): buscar_procesos · consultar_empresa · calcular_indicadores
             ├─ cliente MCP (langchain-mcp-adapters) ══stdio══► servidor_mcp.py «pliegos»
             │                                                    buscar_en_pliegos · listar_documentos
             │                                                    └─ pliegos.py: RAG híbrido sobre 20 PDF
             └─ memoria.py: corto (ventana) · medio (resúmenes de sesión) · largo (hechos)
                almacen.py: ChromaDB persistente + embeddings multilingües (ONNX)
```

| Archivo | Función |
|---|---|
| `agente.py` | Agente, prompt (citas + «No lo sé»), sesión MCP persistente, chat CLI |
| `servidor_mcp.py` | Servidor MCP (FastMCP) que expone el RAG; también usable desde VS Code (`.vscode/mcp.json`) |
| `pliegos.py` | Extracción por página, fragmentación por sección numerada, búsqueda híbrida (embeddings + BM25, RRF) con compuerta de relevancia |
| `memoria.py` | Tres niveles de memoria del tutorial, con el LLM inyectado |
| `almacen.py` | Chroma + `paraphrase-multilingual-MiniLM-L12-v2` (mismo modelo del tutorial) en ONNX |
| `herramientas.py` | Herramientas del Taller 1 (filtro `texto` ampliado a la referencia) |
| `evaluar.py` | Evaluación: uso de herramientas, respuesta correcta (juez LLM), cita de fuente, abstención |
| `demo.py` | Demo de dos sesiones → `demo_salida.md` |
| `datos/conjunto_taller2.json` | 18 preguntas (9 RAG, 3 combinadas, 6 «no lo sé») con fuente y página esperadas |
| `tests/` | 26 pruebas sin LLM (RAG, MCP real por stdio, memoria, agente con modelo simulado, evaluadores) |

Decisiones principales:
- **Citas exactas:** cada fragmento guarda `archivo, página(s), sección`; el agente debe copiar ese campo en «Fuentes:».
- **«No lo sé» en dos capas:** la herramienta devuelve `encontrado=false` si nada supera la compuerta
  (distancia coseno ≤ 0.62 o todos los términos presentes); el prompt obliga a buscar antes de abstenerse.
  Con `referencia`, no hay compuerta y el LLM juzga si el documento trae el dato.
- **Búsqueda híbrida:** solo embeddings fallaba con nombres propios («INVIAS Cauca»); BM25 lo corrige (mejora propuesta por el propio tutorial).
- **Embeddings ONNX en vez de sentence-transformers:** mismos vectores sin PyTorch (en este equipo el Control de aplicaciones de Windows bloquea las DLL de torch).
- **Memoria del tutorial RAG** (no el servidor `server-memory` de Node del tutorial MCP): evita depender de Node y cubre corto/medio/largo plazo.
- Conocimiento general solo para conceptos de contratación (compatibilidad con R17/R18 del Taller 1), marcado como tal.

## Instalación y ejecución (Windows, Python 3.12)

```bash
uv venv --python 3.12 .venv          # o: py -3.12 -m venv .venv
.venv\Scripts\activate
uv pip install -r requirements.txt    # o: pip install -r requirements.txt
copy .env.example .env                # y complete ANTHROPIC_API_KEY
python pliegos.py                     # indexa los 20 PDF (descarga el modelo de embeddings la 1.ª vez)
python agente.py "¿Qué índice de liquidez exige el proceso FLO-INFRA-SA-MC-007-2025 y lo cumplimos?"
python agente.py                      # chat con memoria: salir · /memoria · /olvidar <texto>
python demo.py                        # demo del entregable (dos sesiones)
python evaluar.py A-haiku --conjunto ambos   # Taller 2 + referencia del Taller 1
python -m pytest -q                   # pruebas sin API
mcp dev servidor_mcp.py               # MCP Inspector (opcional)
```

## Resultados medidos (claude-haiku-4-5, 36 casos, en local)

Dos corridas de la versión final (`reportes/A-haiku-4-5-corrida{1,2}.json`):

| Métrica | Corrida 1 | Corrida 2 |
|---|---|---|
| Uso de herramientas | 100 % | 100 % |
| Respuesta correcta (juez LLM) | 91,7 % | 94,4 % |
| Cita de la fuente | 94,4 % | 100 % |
| Abstención correcta (todas) | 97,2 % | 100 % |
| Abstención en los 6 casos «no lo sé» | 83,3 % | 100 % |
| Costo por pregunta | US$0,0099 | US$0,0101 |
| Latencia media | 5,4 s | 32,4 s (picos de la API) |

Ambas corridas superan el 85 % de precisión. T14 sale marcada como incorrecta en las dos, aunque la respuesta dice «No lo sé: no exige índice de liquidez» (el juez la penaliza).

## Limitaciones conocidas

- Sin `LANGSMITH_API_KEY` no se verificaron trazas en LangSmith; el código las soporta (`evaluar.py` y `LANGSMITH_TRACING`).
- Variabilidad del LLM: a veces responde bien pero sin la frase literal «No lo sé»; el juez Haiku también varía.
- En conversaciones largas el agente puede apoyarse en el historial en vez de reconsultar el pliego.
- Los resúmenes de memoria los genera el LLM y pueden contener imprecisiones; se presentan como referencia, no como fuente.
- La API usada rechaza `temperature`, por eso no se fija.
- Fijaciones: `mcp<2` (incompatible con langchain-mcp-adapters 0.3.1) y, en este equipo, `uuid-utils==0.12.0` (la DLL de versiones nuevas fue bloqueada por Control de aplicaciones).
