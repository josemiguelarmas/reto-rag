"""Almacén vectorial (ChromaDB) y modelo de embeddings compartidos por el RAG y la memoria.

Se usa el mismo modelo del tutorial de Memoria RAG (paraphrase-multilingual-MiniLM-L12-v2),
pero en su exportación ONNX oficial y ejecutado con onnxruntime: produce los mismos vectores
que sentence-transformers sin instalar PyTorch (cientos de MB y bloqueado en algunos equipos
con Control de aplicaciones de Windows).
"""
from functools import lru_cache
from pathlib import Path

import chromadb
import numpy as np
from chromadb.config import Settings
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings

RAIZ = Path(__file__).resolve().parent
RUTA_ALMACEN = RAIZ / "almacen"
MODELO_EMB = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


@lru_cache(maxsize=1)
def _cargar_modelo():
    """Descarga (solo la primera vez) y carga el modelo ONNX y su tokenizador."""
    import onnxruntime as ort
    from huggingface_hub import hf_hub_download
    from tokenizers import Tokenizer

    tokenizador = Tokenizer.from_file(hf_hub_download(MODELO_EMB, "tokenizer.json"))
    tokenizador.enable_truncation(max_length=256)
    tokenizador.enable_padding()
    sesion = ort.InferenceSession(hf_hub_download(MODELO_EMB, "onnx/model.onnx"),
                                  providers=["CPUExecutionProvider"])
    return tokenizador, sesion


class EmbeddingsMultilingues(EmbeddingFunction[Documents]):
    """Embeddings normalizados: mean pooling sobre los tokens, como sentence-transformers."""

    def __init__(self) -> None:
        pass

    def __call__(self, input: Documents) -> Embeddings:
        tokenizador, sesion = _cargar_modelo()
        vectores = []
        for inicio in range(0, len(input), 32):
            lote = tokenizador.encode_batch(list(input[inicio:inicio + 32]))
            ids = np.array([e.ids for e in lote], dtype=np.int64)
            mascara = np.array([e.attention_mask for e in lote], dtype=np.int64)
            entradas = {"input_ids": ids, "attention_mask": mascara}
            if "token_type_ids" in {i.name for i in sesion.get_inputs()}:
                entradas["token_type_ids"] = np.zeros_like(ids)
            tokens = sesion.run(None, entradas)[0]                    # (lote, tokens, 384)
            m = mascara[..., None].astype(np.float32)
            medias = (tokens * m).sum(axis=1) / np.clip(m.sum(axis=1), 1e-9, None)
            medias /= np.linalg.norm(medias, axis=1, keepdims=True)
            vectores.extend(medias.astype(np.float32))
        return vectores

    @staticmethod
    def name() -> str:
        return "onnx-paraphrase-multilingual-minilm-l12-v2"

    def get_config(self) -> dict:
        return {}

    @staticmethod
    def build_from_config(config: dict) -> "EmbeddingsMultilingues":
        return EmbeddingsMultilingues()


def crear_cliente(ruta: Path | str) -> chromadb.ClientAPI:
    """Crea (o abre) una base vectorial persistente en disco."""
    Path(ruta).mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(ruta), settings=Settings(anonymized_telemetry=False))


def obtener_coleccion(cliente, nombre: str, funcion_emb=None):
    """Colección con distancia coseno (0 = mismo significado, 2 = opuesto)."""
    return cliente.get_or_create_collection(
        name=nombre,
        embedding_function=funcion_emb or EmbeddingsMultilingues(),
        metadata={"hnsw:space": "cosine"},
    )
