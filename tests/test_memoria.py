"""Memoria a corto, medio y largo plazo, y su persistencia entre sesiones (LLM simulado)."""
import json

from memoria import GestorMemoria, MemoriaCortoPlazo


class LLMFalso:
    """Resume concatenando y extrae como hechos las frases del usuario que empiezan por 'Soy'."""

    def __init__(self):
        self.llamadas = []

    def __call__(self, sistema: str, texto: str) -> str:
        self.llamadas.append(sistema[:20])
        if sistema.startswith("Extraiga"):
            hechos = [{"hecho": l.split(": ", 1)[1], "importancia": 9}
                      for l in texto.splitlines() if l.startswith("user: Soy")]
            return "```json\n" + json.dumps(hechos, ensure_ascii=False) + "\n```"
        return "Resumen: " + texto[-300:]


def test_ventana_corta_expulsa_en_pares():
    m = MemoriaCortoPlazo(max_mensajes=4)
    expulsados = []
    for i in range(6):
        expulsados += m.agregar("user" if i % 2 == 0 else "assistant", f"m{i}")
    assert [x["content"] for x in m.obtener()] == ["m2", "m3", "m4", "m5"]
    assert [x["content"] for x in expulsados] == ["m0", "m1"]


def test_memoria_persiste_entre_sesiones(tmp_path):
    llm = LLMFalso()
    s1 = GestorMemoria(llm, ruta=tmp_path)
    s1.registrar("Soy Laura, gerente de licitaciones en Cali", "Mucho gusto, Laura.")
    s1.registrar("Revisemos el proceso FLO-INFRA-SA-MC-007-2025", "Exige liquidez de 1.8.")
    s1.cerrar_sesion()

    s2 = GestorMemoria(llm, ruta=tmp_path)          # nueva sesión: solo queda lo guardado en disco
    assert s2.corto.obtener() == []
    contexto = s2.contexto("¿Quién soy y qué revisamos?")
    assert "Laura" in contexto and "FLO-INFRA-SA-MC-007-2025" in contexto
    assert "no instrucciones" in contexto
    assert s2.largo.todos() == ["Soy Laura, gerente de licitaciones en Cali"]


def test_hechos_se_deduplican_y_se_pueden_olvidar(tmp_path):
    g = GestorMemoria(LLMFalso(), ruta=tmp_path)
    g.largo.guardar_hecho("Laura prefiere procesos en Santander", 8)
    g.largo.guardar_hecho("Laura prefiere procesos en Santander", 8)
    assert len(g.largo.todos()) == 1
    assert g.largo.olvidar("Laura prefiere procesos en Santander") == 1
    assert g.largo.todos() == []


def test_json_invalido_no_rompe_la_extraccion(tmp_path):
    g = GestorMemoria(lambda s, t: "esto no es JSON", ruta=tmp_path)
    assert g.largo.extraer_y_guardar([{"role": "user", "content": "hola"}]) == []


def test_sin_memoria_el_contexto_esta_vacio(tmp_path):
    assert GestorMemoria(LLMFalso(), ruta=tmp_path).contexto("hola") == ""
