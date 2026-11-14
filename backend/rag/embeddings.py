"""
backend/rag/embeddings.py
==========================
Generates vector embeddings using Sentence Transformers.

WHAT ARE EMBEDDINGS?
  An embedding converts text into a list of numbers (a vector).
  Similar texts produce similar vectors.

  Example:
    "Machine Learning" → [0.12, -0.34, 0.56, ...]  (384 numbers)
    "ML algorithms"    → [0.11, -0.33, 0.55, ...]  (very similar!)
    "French cooking"   → [-0.45, 0.78, -0.12, ...]  (very different)

  By comparing these vectors with cosine similarity, we can find
  which framework skills are most relevant to syllabus topics.

WHY SENTENCE TRANSFORMERS?
  - Runs completely offline (no API key needed).
  - Small model (all-MiniLM-L6-v2 is ~80MB).
  - Fast on CPU (no GPU required).
  - Good quality for semantic similarity.
  - Well-tested and widely used.

FIRST RUN:
  The first time you use this module, it downloads the model
  (~80MB) from Hugging Face. After that, it's cached and
  works fully offline.
"""

import logging
from typing import Optional

from backend.config import settings

logger = logging.getLogger(__name__)

# ── Module-level cache for the model ──
# We load the model once and reuse it for all embeddings.
# This avoids reloading the model for every query.
_model = None


def get_model():
    """
    Load and cache the Sentence Transformer model.

    Returns the model instance. On first call, downloads/loads
    the model from cache. Subsequent calls return the cached instance.
    """
    global _model

    if _model is None:
        import os
        from sentence_transformers import SentenceTransformer

        model_name = settings.EMBEDDING_MODEL
        logger.info(f"[Embeddings] Loading model: {model_name}")

        try:
            # First attempt loading from local cache for instant offline startup
            _model = SentenceTransformer(model_name, local_files_only=True)
        except Exception:
            # If not yet downloaded, load normally (downloads once and caches)
            _model = SentenceTransformer(model_name)

        logger.info(
            f"[Embeddings] Model loaded: {model_name} "
            f"(dimension={_model.get_embedding_dimension()})"
        )

    return _model


def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings for a list of texts.

    Args:
        texts: List of text strings to embed.

    Returns:
        List of embedding vectors (each is a list of floats).
        The number of floats per vector depends on the model
        (384 for all-MiniLM-L6-v2).

    Example:
        >>> embeddings = generate_embeddings(["Machine Learning", "Data Science"])
        >>> len(embeddings)       # 2 texts → 2 vectors
        2
        >>> len(embeddings[0])    # 384-dimensional vector
        384
    """
    if not texts:
        return []

    model = get_model()

    # SentenceTransformer.encode() returns numpy arrays
    # We convert to plain Python lists for JSON serialisation
    vectors = model.encode(texts, show_progress_bar=False)

    # Convert numpy arrays to plain lists
    embeddings = [vec.tolist() for vec in vectors]

    logger.info(f"[Embeddings] Generated {len(embeddings)} embeddings")
    return embeddings


def generate_single_embedding(text: str) -> list[float]:
    """
    Generate an embedding for a single text.

    Convenience wrapper around generate_embeddings() for single queries.
    """
    embeddings = generate_embeddings([text])
    return embeddings[0] if embeddings else []


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    Cosine similarity measures the angle between two vectors:
    - 1.0 = identical direction (very similar meaning)
    - 0.0 = perpendicular (unrelated)
    - -1.0 = opposite direction (opposite meaning, rare in practice)

    For text embeddings, typical ranges:
    - > 0.75: Very similar / same topic
    - 0.45 - 0.75: Related / partially overlapping
    - < 0.45: Different topics

    Formula:
      similarity = (A · B) / (||A|| × ||B||)

    Where:
      A · B    = dot product (sum of element-wise multiplication)
      ||A||    = magnitude (square root of sum of squares)
    """
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0

    # Dot product: sum of (a_i * b_i) for all elements
    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))

    # Magnitudes: sqrt(sum of squares)
    magnitude_a = sum(a * a for a in vec_a) ** 0.5
    magnitude_b = sum(b * b for b in vec_b) ** 0.5

    # Avoid division by zero
    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0

    similarity = dot_product / (magnitude_a * magnitude_b)

    # Clamp to [-1, 1] to handle floating point errors
    return max(-1.0, min(1.0, similarity))
