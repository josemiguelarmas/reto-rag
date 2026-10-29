"""RAG sobre los documentos: extracción, fragmentación con fuente y recuperación."""
import json

import pytest

import pliegos
from almacen import RAIZ


@pytest.fixture(scope="module", autouse=True)
def indice():
    pliegos.indexar()


def test_cada_pdf_corresponde_a_un_proceso_de_la_muestra():
    muestra = {p["referencia_del_proceso"] for p in
               json.loads((RAIZ / "datos" / "secop_muestra.json").read_text(encoding="utf-8"))}
    refs = {pliegos.extraer_documento(p)["referencia"] for p in pliegos.CARPETA_PDF.glob("*.pdf")}
    assert refs == muestra and len(refs) == 20


def test_los_fragmentos_llevan_fuente_citable():
    doc = pliegos.extraer_documento(pliegos.CARPETA_PDF / "14_FLO_INFRA_SA_MC_007_2025.pdf")
    frag = next(f for f in pliegos.fragmentar(doc) if "Capacidad financiera" in f["metadatos"]["seccion"])
    assert "Mayor o igual a 1.8" in frag["texto"]
    assert frag["metadatos"]["fuente"].startswith("14_FLO_INFRA_SA_MC_007_2025.pdf, p. 2, sección «5.")
    assert "DOCUMENTO SIMULADO" not in frag["texto"]


def test_seccion_que_cruza_paginas_cita_ambas():
    doc = pliegos.extraer_documento(pliegos.CARPETA_PDF / "03_RE_CGBM_049_2024.pdf")
    habilitantes = next(s for s in doc["secciones"] if s["titulo"].startswith("Requisitos habilitantes"))
    assert (habilitantes["pagina_inicio"], habilitantes["pagina_fin"]) == (1, 2)


def test_no_reindexa_si_los_pdf_no_cambian():
    assert pliegos.indexar()["reindexado"] is False


@pytest.mark.parametrize("consulta, referencia, archivo, seccion", [
    ("índice de liquidez exigido", "FLO-INFRA-SA-MC-007-2025", "14_FLO", "5. Capacidad financiera"),
    ("requisitos de experiencia de la licitación de INVIAS en Cauca", None, "13_LP_DT_CAU", "7. Experiencia"),
    ("formación del nutricionista de la Gobernación del Chocó", None, "16_CD_PS_GDCH", "4. Perfil"),
    ("garantía de seriedad de la Alcaldía de Floridablanca", None, "14_FLO", "8. Garantías"),
])
def test_recupera_el_fragmento_correcto(consulta, referencia, archivo, seccion):
    r = pliegos.buscar(consulta, referencia, k=3)
    assert r["encontrado"]
    assert any(f["fuente"].startswith(archivo) and seccion in f["fuente"] for f in r["fragmentos"])


def test_referencia_tolerante_a_formato():
    r = pliegos.buscar("liquidez", "flo infra sa mc 007 2025", k=2)
    assert r["encontrado"] and all(f["referencia"] == "FLO-INFRA-SA-MC-007-2025" for f in r["fragmentos"])


@pytest.mark.parametrize("consulta", ["¿Quién ganó el mundial de fútbol de 2022?",
                                      "receta de arepas de choclo", "¿Cuál es la capital de Francia?"])
def test_fuera_de_los_documentos_no_encuentra(consulta):
    r = pliegos.buscar(consulta)
    assert r == {"encontrado": False, "fragmentos": [], "mensaje": r["mensaje"]}


def test_referencia_inexistente_y_consulta_vacia():
    assert not pliegos.buscar("requisitos", "XYZ-999-2030")["encontrado"]
    assert not pliegos.buscar("   ")["encontrado"]


def test_listar_documentos():
    docs = pliegos.documentos()
    assert len(docs) == 20 and {"referencia", "entidad", "archivo"} <= set(docs[0])
