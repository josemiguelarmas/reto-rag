"""Evaluadores deterministas de evaluar.py (el juez LLM se prueba con el modelo real)."""
from evaluar import abstencion, cargar_casos, cita_fuente, uso_herramientas

REF_RAG = {"fuente": "14_FLO_INFRA_SA_MC_007_2025.pdf", "pagina": 2, "tipo": "rag", "herramientas": ["buscar_en_pliegos"]}
REF_NLS = {"fuente": None, "pagina": None, "tipo": "no_lo_se", "herramientas": ["buscar_en_pliegos"]}


def _out(texto, herramientas=()):
    return {"respuesta": texto, "herramientas": list(herramientas)}


def test_cita_fuente_exige_archivo_y_pagina():
    ok = _out("Liquidez ≥ 1.8.\nFuentes: 14_FLO_INFRA_SA_MC_007_2025.pdf, p. 2, sección «5. ...»")
    sin_pagina = _out("Fuentes: 14_FLO_INFRA_SA_MC_007_2025.pdf")
    otra_pagina = _out("Fuentes: 14_FLO_INFRA_SA_MC_007_2025.pdf, p. 1")
    assert cita_fuente({}, ok, REF_RAG)["score"] == 1
    assert cita_fuente({}, sin_pagina, REF_RAG)["score"] == 0
    assert cita_fuente({}, otra_pagina, REF_RAG)["score"] == 0
    assert cita_fuente({}, _out("Fuentes: 14_FLO_INFRA_SA_MC_007_2025.pdf, pp. 1-2"), REF_RAG)["score"] == 1


def test_abstencion_en_ambos_sentidos():
    assert abstencion({}, _out("No lo sé: no aparece en los documentos."), REF_NLS)["score"] == 1
    assert abstencion({}, _out("El plazo es de 30 días."), REF_NLS)["score"] == 0
    assert abstencion({}, _out("No lo sé."), REF_RAG)["score"] == 0          # abstención indebida


def test_uso_herramientas():
    assert uso_herramientas({}, _out("x", ["buscar_en_pliegos", "listar_documentos"]), REF_RAG)["score"] == 1
    assert uso_herramientas({}, _out("x", []), {"herramientas": []})["score"] == 1
    assert uso_herramientas({}, _out("x", ["buscar_procesos"]), {"herramientas": []})["score"] == 0


def test_conjuntos_bien_formados():
    casos = cargar_casos("ambos")
    assert len(casos) == 36 and len({c["id"] for c in casos}) == 36
    t2 = [c for c in casos if c["id"].startswith("T")]
    assert 15 <= len(t2) <= 20 and sum(c["tipo"] == "no_lo_se" for c in t2) >= 5
