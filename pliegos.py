"""RAG sobre los 20 documentos del curso (estudios previos, invitaciones y pliegos en PDF).

Indexación: cada PDF se divide por sus secciones numeradas («5. Capacidad financiera...»),
de modo que un requisito y su tabla quedan en el mismo fragmento. Cada fragmento guarda
archivo, páginas y sección para poder citar la fuente exacta.

Uso:  python pliegos.py                      # indexa (si hace falta) y muestra un resumen
      python pliegos.py --reindexar
      python pliegos.py "liquidez exigida" --referencia FLO-INFRA-SA-MC-007-2025
"""
import argparse
import hashlib
import logging
import math
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

from pypdf import PdfReader

from almacen import RAIZ, RUTA_ALMACEN, crear_cliente, obtener_coleccion

logging.getLogger("pypdf").setLevel(logging.ERROR)   # los PDF del curso traen un xref inexacto

CARPETA_PDF = RAIZ / "datos" / "pliegos"
COLECCION = "pliegos"
# Por encima de esta distancia coseno un fragmento se considera no relacionado con la
# consulta. Calibrado con las preguntas de datos/conjunto_taller2.json (ver README).
DISTANCIA_MAX = 0.62
MAX_CARACTERES = 1500

_SECCION = re.compile(r"^(\d{1,2})\.\s+(\S.*)$")
_RUIDO = (
    re.compile(r"^Documento simulado con fines educativos"),
    re.compile(r"^Página \d+$"),
)
_AVISO = "DOCUMENTO SIMULADO CON FINES EDUCATIVOS"


def _clave(ref: str) -> str:
    """Normaliza una referencia de proceso para compararla (sin tildes, símbolos ni mayúsculas)."""
    ref = unicodedata.normalize("NFKD", str(ref or ""))
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in ref if not unicodedata.combining(c)).lower())


def extraer_documento(pdf: Path) -> dict:
    """Lee un PDF y devuelve sus metadatos y sus secciones con las páginas que abarcan."""
    lineas = []                                      # (página, texto)
    for num, pagina in enumerate(PdfReader(pdf).pages, start=1):
        for linea in (pagina.extract_text() or "").splitlines():
            linea = linea.strip()
            if linea and not any(r.match(linea) for r in _RUIDO):
                lineas.append((num, linea))
    texto = "\n".join(t for _, t in lineas)
    m = re.search(r"Proceso (\S+) · (CO1\.\S+)", texto)
    if not m:
        raise ValueError(f"{pdf.name}: no se encontró la referencia del proceso")
    referencia, id_proceso = m.group(1), m.group(2)
    entidad = next((t for _, t in lineas if not t.startswith(_AVISO) and t.isupper() and len(t) > 5), "")

    secciones, actual = [], {"numero": 0, "titulo": "Encabezado", "lineas": []}
    for pagina, linea in lineas:
        s = _SECCION.match(linea)
        if s:
            secciones.append(actual)
            actual = {"numero": int(s.group(1)), "titulo": s.group(2), "lineas": []}
        actual["lineas"].append((pagina, linea))
    secciones.append(actual)

    resultado = []
    for s in secciones:
        cuerpo = [t for _, t in s["lineas"] if not t.startswith(_AVISO) and "ejercicio académico" not in t
                  and not t.startswith("ficticios.")]
        if not cuerpo:
            continue
        paginas = [p for p, _ in s["lineas"]]
        resultado.append({"numero": s["numero"], "titulo": s["titulo"], "texto": "\n".join(cuerpo),
                          "pagina_inicio": min(paginas), "pagina_fin": max(paginas)})
    tipo = next((t for _, t in lineas if t.startswith(("Estudio previo", "Pliego", "Invitación", "Aviso",
                                                       "Documento de"))), "Documento del proceso")
    return {"archivo": pdf.name, "referencia": referencia, "id_proceso": id_proceso,
            "entidad": entidad, "tipo_documento": tipo, "secciones": resultado}


def _trocear(texto: str) -> list[str]:
    """Divide una sección demasiado larga por líneas, sin cortar ninguna."""
    trozos, actual = [], ""
    for linea in texto.splitlines():
        if actual and len(actual) + len(linea) > MAX_CARACTERES:
            trozos.append(actual)
            actual = ""
        actual += ("\n" if actual else "") + linea
    return trozos + ([actual] if actual else [])


def fragmentar(doc: dict) -> list[dict]:
    """Convierte un documento en fragmentos listos para indexar.

    El texto indexado lleva un encabezado con proceso, entidad y sección (recuperación
    contextual): así una pregunta como «¿qué liquidez pide Floridablanca?» encuentra el
    fragmento aunque la tabla no mencione la entidad.
    """
    fragmentos = []
    for s in doc["secciones"]:
        for n, trozo in enumerate(_trocear(s["texto"]), start=1):
            encabezado = (f"Proceso {doc['referencia']} · {doc['entidad']} · {doc['tipo_documento']} · "
                          f"Sección {s['numero']}. {s['titulo']}")
            paginas = (f"p. {s['pagina_inicio']}" if s["pagina_inicio"] == s["pagina_fin"]
                       else f"pp. {s['pagina_inicio']}-{s['pagina_fin']}")
            fragmentos.append({
                "id": f"{doc['archivo']}#s{s['numero']}.{n}",
                "texto": f"{encabezado}\n{trozo}",
                "metadatos": {
                    "archivo": doc["archivo"], "referencia": doc["referencia"],
                    "clave_referencia": _clave(doc["referencia"]), "entidad": doc["entidad"],
                    "seccion": f"{s['numero']}. {s['titulo']}", "pagina_inicio": s["pagina_inicio"],
                    "pagina_fin": s["pagina_fin"],
                    "fuente": f"{doc['archivo']}, {paginas}, sección «{s['numero']}. {s['titulo']}»",
                },
            })
    return fragmentos


def _huella(pdfs: list[Path]) -> str:
    sha = hashlib.sha256()
    for pdf in pdfs:
        sha.update(pdf.name.encode() + pdf.read_bytes())
    return sha.hexdigest()[:16]


@lru_cache(maxsize=1)
def coleccion():
    return obtener_coleccion(crear_cliente(RUTA_ALMACEN / "pliegos"), COLECCION)


def indexar(forzar: bool = False) -> dict:
    """Indexa todos los PDF de datos/pliegos. No repite el trabajo si los PDF no cambiaron.

    Los PDF con contenido idéntico se indexan una sola vez.
    """
    col = coleccion()
    pdfs = sorted(CARPETA_PDF.glob("*.pdf"))
    if not pdfs:
        raise FileNotFoundError(f"No hay PDF en {CARPETA_PDF}")
    huella = _huella(pdfs)
    archivo_huella = RUTA_ALMACEN / "pliegos" / "huella.txt"
    if not forzar and col.count() and archivo_huella.exists() and archivo_huella.read_text() == huella:
        return {"documentos": len(pdfs), "fragmentos": col.count(), "reindexado": False}

    vistos, fragmentos = set(), []
    for pdf in pdfs:
        contenido = hashlib.sha256(pdf.read_bytes()).hexdigest()
        if contenido in vistos:
            continue
        vistos.add(contenido)
        fragmentos.extend(fragmentar(extraer_documento(pdf)))
    if col.count():
        col.delete(ids=col.get(include=[])["ids"])
    col.upsert(ids=[f["id"] for f in fragmentos], documents=[f["texto"] for f in fragmentos],
               metadatas=[f["metadatos"] for f in fragmentos])
    archivo_huella.write_text(huella)
    return {"documentos": len(vistos), "fragmentos": len(fragmentos), "reindexado": True}


def documentos() -> list[dict]:
    """Lista los documentos indexados (referencia, entidad, archivo)."""
    indexar()
    vistos = {}
    for m in coleccion().get(include=["metadatas"])["metadatas"]:
        vistos.setdefault(m["referencia"], {"referencia": m["referencia"], "entidad": m["entidad"],
                                            "archivo": m["archivo"]})
    return sorted(vistos.values(), key=lambda d: d["archivo"])


_VACIAS = set("""a al ante con de del el en entre es la las lo los o para por que qué se sin su sus
un una uno y cual cuál cuales cuáles cuanto cuánto como cómo hay pide exige proceso nuestra nuestro""".split())


def _tokens(texto: str) -> list[str]:
    texto = unicodedata.normalize("NFKD", texto.lower())
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return [t for t in re.findall(r"[a-z0-9]+", texto) if len(t) > 1 and t not in _VACIAS]


def _bm25(consulta: list[str], textos: list[list[str]], k1: float = 1.5, b: float = 0.75) -> list[float]:
    """Puntuación léxica BM25: favorece nombres propios y códigos que los embeddings diluyen."""
    n = len(textos)
    media = sum(map(len, textos)) / max(n, 1)
    df = {t: sum(t in set(d) for d in textos) for t in set(consulta)}
    puntos = []
    for d in textos:
        tf = {t: d.count(t) for t in df}
        puntos.append(sum(
            math.log(1 + (n - df[t] + 0.5) / (df[t] + 0.5)) * tf[t] * (k1 + 1)
            / (tf[t] + k1 * (1 - b + b * len(d) / media))
            for t in df if tf[t]))
    return puntos


def buscar(consulta: str, referencia: str | None = None, k: int = 4,
           distancia_max: float = DISTANCIA_MAX) -> dict:
    """Recupera los fragmentos más relevantes para la consulta, con su fuente citable.

    Búsqueda híbrida: ordena combinando (RRF) la similitud de embeddings y BM25. Compuerta de
    relevancia: un fragmento pasa si su distancia coseno es menor o igual a `distancia_max` o si
    contiene todos los términos de la consulta (las consultas de una sola palabra, como
    «liquidez», quedan semánticamente lejos aunque el término esté literalmente). Si no pasa
    ninguno, encontrado=False para que el agente diga «no lo sé» en lugar de inventar.
    Con `referencia` la búsqueda se limita a ese documento y no se aplica la compuerta: el
    documento existe y se devuelven sus k fragmentos mejor ordenados (el agente decide si
    contienen el dato; si no, responde «no lo sé»).
    """
    if not (consulta or "").strip():
        return {"encontrado": False, "mensaje": "La consulta está vacía.", "fragmentos": []}
    indexar()
    col = coleccion()
    k = max(1, min(int(k or 4), 10))
    filtro = None
    if referencia:
        clave = _clave(referencia)
        if not any(_clave(d["referencia"]) == clave for d in documentos()):
            return {"encontrado": False, "fragmentos": [],
                    "mensaje": f"No hay ningún documento para la referencia «{referencia}». "
                               "Use listar_documentos para ver las referencias disponibles."}
        filtro = {"clave_referencia": clave}
    r = col.query(query_texts=[consulta], n_results=col.count(), where=filtro,
                  include=["documents", "metadatas", "distances"])
    docs, metas, dists = r["documents"][0], r["metadatas"][0], r["distances"][0]
    terminos = _tokens(consulta)
    tokens_docs = [_tokens(d) for d in docs]
    lexico = _bm25(terminos, tokens_docs)
    completo = [bool(terminos) and set(terminos) <= set(t) for t in tokens_docs]
    rango_lex = {i: n for n, i in enumerate(sorted(range(len(docs)), key=lambda i: -lexico[i]))}
    fusion = [1 / (60 + i) + (1 / (60 + rango_lex[i]) if lexico[i] > 0 else 0) for i in range(len(docs))]
    orden = sorted(range(len(docs)), key=lambda i: -fusion[i])
    fragmentos = [
        {"fuente": metas[i]["fuente"], "referencia": metas[i]["referencia"],
         "entidad": metas[i]["entidad"], "distancia": round(dists[i], 3), "texto": docs[i]}
        for i in orden if referencia or dists[i] <= distancia_max or completo[i]
    ][:k]
    if not fragmentos:
        return {"encontrado": False, "fragmentos": [],
                "mensaje": "Ningún fragmento de los documentos es relevante para la consulta: "
                           "la información no está en los documentos."}
    return {"encontrado": True, "fragmentos": fragmentos}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Indexa y consulta los pliegos del curso")
    ap.add_argument("consulta", nargs="?")
    ap.add_argument("--referencia")
    ap.add_argument("--reindexar", action="store_true")
    a = ap.parse_args()
    print(indexar(forzar=a.reindexar))
    if a.consulta:
        res = buscar(a.consulta, a.referencia)
        print(res.get("mensaje", ""))
        for f in res["fragmentos"]:
            print(f"\n[{f['distancia']}] {f['fuente']}\n{f['texto'][:400]}")
