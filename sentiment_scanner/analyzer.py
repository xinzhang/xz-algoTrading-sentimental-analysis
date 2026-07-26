"""FinBERT-based sentiment analysis."""

import logging
from dataclasses import dataclass
from functools import lru_cache

import numpy as np
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

logger = logging.getLogger(__name__)

MODEL_NAME = "yiyanghkust/finbert-tone"
MAX_TOKEN_LENGTH = 512


@dataclass
class SentimentResult:
    label: str
    confidence: float


@lru_cache(maxsize=1)
def load_finbert() -> tuple:
    """Load and cache the FinBERT tokenizer/model so repeated calls reuse one instance."""
    logger.info("Loading FinBERT model: %s", MODEL_NAME)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
    model.eval()
    return tokenizer, model


def analyze_sentiment(text: str) -> SentimentResult:
    """Classify text as Positive/Negative/Neutral using FinBERT."""
    if not text or not text.strip():
        return SentimentResult(label="Neutral", confidence=0.0)

    tokenizer, model = load_finbert()
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=MAX_TOKEN_LENGTH)

    with torch.no_grad():
        outputs = model(**inputs)

    probabilities = torch.softmax(outputs.logits, dim=1).numpy()[0]
    top_index = int(np.argmax(probabilities))
    label = model.config.id2label[top_index]
    return SentimentResult(label=label, confidence=float(probabilities[top_index]))
