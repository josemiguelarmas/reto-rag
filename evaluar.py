"""Evalúa el agente del Taller 2 (y, si se pide, el conjunto de referencia del Taller 1).

Métricas por pregunta:
  uso_herramientas   usó las herramientas esperadas (y ninguna cuando no hacía falta)
  respuesta_correcta un modelo juez compara con la respuesta esperada
  cita_fuente        cita el archivo y la página esperados (o, si no hay fuente, dice «No lo sé»)
  abstencion         dice «No lo sé» exactamente cuando la información no está

Uso:  python evaluar.py A-haiku                      # conjunto del Taller 2
      python evaluar.py A-haiku --conjunto ambos     # Taller 2 + referencia del Taller 1
      python evaluar.py B-sonnet --modelo anthropic:claude-sonnet-5-5
      python evaluar.py A-haiku --local              # sin LangSmith aunque haya clave
Con LANGSMITH_API_KEY se sube el dataset y el experimento a LangSmith; sin ella, o con
--local, se ejecuta en local y el resultado queda en reportes/<nombre>.json.
"""
import argparse
import asyncio
import json
import os
import re
import sys
import time
import unicodedata

from agente import RAIZ, Analista, _texto
from langchain.chat_models import init_chat_model

CONJUNTOS = {"taller2": RAIZ / "datos" / "conjunto_taller2.json",
             "taller1": RAIZ / "datos" / "conjunto_referencia.json"}
JUEZ = os.getenv("MODELO_JUEZ", "anthropic:claude-haiku-4-5")


def _norm(t: str) -> str:
    t = unicodedata.normalize("NFKD", str(t or "").lower())
    return "".join(c for c in t if not unicodedata.combining(c))


def cargar_casos(conjunto: str) -> list[dict]:
    nombres = ["taller2", "taller1"] if conjunto == "ambos" else [conjunto]
    casos = []
    for n in nombres:
        for c in json.loads(CONJUNTOS[n].read_text(encoding="utf-8")):
            c.setdefault("tipo", "sin_herramientas" if not c["herramientas_esperadas"] else "taller1")
            c.setdefault("fuente_esperada", None)
            c.setdefault("pagina_esperada", None)
            casos.append(c)
    return casos


def _dice_no_lo_se(respuesta: str) -> bool:
    return "no lo se" in _norm(respuesta)[:200]


# ---------- Evaluadores (misma firma que espera LangSmith) ----------
def uso_herramientas(inputs: dict, outputs: dict, reference_outputs: dict) -> dict:
    esperadas, usadas = set(reference_outputs["herramientas"]), set(outputs["herramientas"])
    ok = usadas == set() if not esperadas else esperadas.issubset(usadas)
    return {"key": "uso_herramientas", "score": int(ok)}


def cita_fuente(inputs: dict, outputs: dict, reference_outputs: dict) -> dict:
    r = _norm(outputs["respuesta"])
    fuente, pagina = reference_outputs.get("fuente"), reference_outputs.get("pagina")
    if fuente:
        archivo = _norm(fuente).replace(".pdf", "")
        ok = archivo in r and (pagina is None or re.search(rf"\bpp?\.\s*(\d+-)?{pagina}\b", r) is not None)
    elif reference_outputs.get("tipo") == "no_lo_se":
        ok = _dice_no_lo_se(outputs["respuesta"])
    else:
        ok = "fuente" in r
    return {"key": "cita_fuente", "score": int(ok)}


def abstencion(inputs: dict, outputs: dict, reference_outputs: dict) -> dict:
    debe = reference_outputs.get("tipo") == "no_lo_se"
    return {"key": "abstencion", "score": int(_dice_no_lo_se(outputs["respuesta"]) == debe)}


_juez = None


def respuesta_correcta(inputs: dict, outputs: dict, reference_outputs: dict) -> dict:
    global _juez
    _juez = _juez or init_chat_model(JUEZ)
    veredicto = _texto(_juez.invoke(
        "Eres un evaluador estricto. Compara la RESPUESTA con la RESPUESTA ESPERADA a la PREGUNTA. "
        "Las cifras y condiciones deben coincidir (se aceptan diferencias de formato, redondeo y "
        "redacción, y que la respuesta agregue contexto o fuentes). Si la respuesta esperada dice "
        "«No lo sé», la RESPUESTA es correcta solo si reconoce que no tiene el dato o que no está en "
        "los documentos, sin inventarlo. Responde solo CORRECTA o INCORRECTA.\n\n"
        f"PREGUNTA: {inputs['pregunta']}\nRESPUESTA ESPERADA: {reference_outputs['respuesta']}\n"
        f"RESPUESTA: {outputs['respuesta']}"))
    return {"key": "respuesta_correcta", "score": int("INCORRECTA" not in veredicto.upper())}


EVALUADORES = [uso_herramientas, respuesta_correcta, cita_fuente, abstencion]


def _referencia(c: dict) -> dict:
    return {"respuesta": c["respuesta_esperada"], "herramientas": c["herramientas_esperadas"],
            "fuente": c["fuente_esperada"], "pagina": c["pagina_esperada"], "tipo": c["tipo"]}


async def evaluar_local(nombre: str, casos: list[dict], modelo: str | None) -> dict:
    filas = []
    async with Analista(modelo=init_chat_model(modelo) if modelo else None, memoria=False) as a:
        for c in casos:
            try:
                out = await a.preguntar(c["pregunta"])
            except Exception as e:   # un fallo puntual de la API no debe abortar la evaluación
                out = {"respuesta": f"ERROR: {e}", "herramientas": [], "tokens_entrada": 0,
                       "tokens_salida": 0, "costo_usd": 0.0, "latencia_s": 0.0}
            inputs, ref = {"pregunta": c["pregunta"]}, _referencia(c)
            notas = {r["key"]: r["score"] for r in (ev(inputs, out, ref) for ev in EVALUADORES)}
            filas.append({"id": c["id"], "tipo": c["tipo"], "pregunta": c["pregunta"], **out, **notas})
            print(f"{c['id']:>4} {c['tipo']:<16} " + " ".join(f"{k[:10]}={v}" for k, v in notas.items())
                  + f"  {out['latencia_s']}s  {out['tokens_entrada']}+{out['tokens_salida']} tok")
    n = len(filas)
    resumen = {k.__name__: round(sum(f[k.__name__] for f in filas) / n, 3) for k in EVALUADORES}
    resumen.update({
        "casos": n,
        "costo_total_usd": round(sum(f["costo_usd"] for f in filas), 4),
        "costo_por_pregunta_usd": round(sum(f["costo_usd"] for f in filas) / n, 5),
        "tokens_promedio": round(sum(f["tokens_entrada"] + f["tokens_salida"] for f in filas) / n),
        "latencia_promedio_s": round(sum(f["latencia_s"] for f in filas) / n, 2),
    })
    no_sabe = [f for f in filas if f["tipo"] == "no_lo_se"]
    if no_sabe:
        resumen["abstencion_en_casos_no_lo_se"] = round(sum(f["abstencion"] for f in no_sabe) / len(no_sabe), 3)
    informe = {"experimento": nombre, "modelo": modelo or os.getenv("MODELO", "anthropic:claude-haiku-4-5"),
               "fecha": time.strftime("%Y-%m-%d %H:%M"), "resumen": resumen, "casos": filas}
    (RAIZ / "reportes").mkdir(exist_ok=True)
    (RAIZ / "reportes" / f"{nombre}.json").write_text(json.dumps(informe, ensure_ascii=False, indent=1),
                                                       encoding="utf-8")
    return informe


async def evaluar_langsmith(nombre: str, casos: list[dict], conjunto: str, modelo: str | None) -> None:
    from langsmith import Client
    client = Client()
    dataset = f"secop-taller2-{conjunto}"
    if not client.has_dataset(dataset_name=dataset):
        ds = client.create_dataset(dataset, description=f"Preguntas de evaluación ({conjunto})")
        client.create_examples(dataset_id=ds.id, examples=[
            {"inputs": {"pregunta": c["pregunta"]}, "outputs": _referencia(c)} for c in casos])
    async with Analista(modelo=init_chat_model(modelo) if modelo else None, memoria=False) as a:
        async def objetivo(inputs: dict) -> dict:
            return await a.preguntar(inputs["pregunta"])
        await client.aevaluate(objetivo, data=dataset, evaluators=EVALUADORES,
                               experiment_prefix=nombre, max_concurrency=1)
    print("Listo. Revise el experimento en LangSmith > Datasets & Experiments.")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Evaluación del agente del Taller 2")
    ap.add_argument("nombre", nargs="?", default="configuracion-A")
    ap.add_argument("--conjunto", choices=["taller2", "taller1", "ambos"], default="taller2")
    ap.add_argument("--modelo", help="proveedor:modelo (por defecto MODELO del .env)")
    ap.add_argument("--local", action="store_true")
    ap.add_argument("--ids", help="solo estos casos, separados por comas (p. ej. T15,R08)")
    a = ap.parse_args()
    casos = cargar_casos(a.conjunto)
    if a.ids:
        casos = [c for c in casos if c["id"] in a.ids.split(",")]
    if os.getenv("LANGSMITH_API_KEY") and not a.local:
        asyncio.run(evaluar_langsmith(a.nombre, casos, a.conjunto, a.modelo))
    else:
        inf = asyncio.run(evaluar_local(a.nombre, casos, a.modelo))
        print("\nResumen:", json.dumps(inf["resumen"], ensure_ascii=False, indent=1))
        print(f"Detalle en reportes/{a.nombre}.json")
