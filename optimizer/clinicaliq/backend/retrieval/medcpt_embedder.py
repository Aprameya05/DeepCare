from __future__ import annotations

from typing import Iterable, List

import torch
import torch.nn.functional as F
from transformers import AutoModel, AutoTokenizer


class MedCPTEmbedder:
    """Embedding wrapper for ncats/MedCPT-Query-Encoder."""

    def __init__(
        self,
        model_name: str = "ncats/MedCPT-Query-Encoder",
        device: str | None = None,
    ) -> None:
        self.model_name = model_name
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModel.from_pretrained(model_name).to(self.device)
        except Exception as exc:  # pragma: no cover - runtime/network dependent
            raise RuntimeError(
                f"Failed to load MedCPT model '{model_name}'. "
                "Stop here and fix model download before proceeding."
            ) from exc

        hidden_size = getattr(self.model.config, "hidden_size", None)
        if hidden_size != 768:
            raise RuntimeError(
                f"Unexpected MedCPT embedding dimension: {hidden_size}. Expected 768."
            )

        self.model.eval()

    @staticmethod
    def _mean_pool_last_hidden_state(
        last_hidden_state: torch.Tensor,
        attention_mask: torch.Tensor,
    ) -> torch.Tensor:
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(last_hidden_state.size()).float()
        sum_embeddings = torch.sum(last_hidden_state * input_mask_expanded, dim=1)
        sum_mask = torch.clamp(input_mask_expanded.sum(dim=1), min=1e-9)
        return sum_embeddings / sum_mask

    @torch.inference_mode()
    def embed_texts(self, texts: Iterable[str]) -> List[List[float]]:
        text_list = list(texts)
        if not text_list:
            return []

        encoded = self.tokenizer(
            text_list,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt",
        ).to(self.device)

        outputs = self.model(**encoded)
        pooled = self._mean_pool_last_hidden_state(
            outputs.last_hidden_state,
            encoded["attention_mask"],
        )
        normalized = F.normalize(pooled, p=2, dim=1)
        return normalized.cpu().tolist()

    def embed_text(self, text: str) -> List[float]:
        embeddings = self.embed_texts([text])
        if not embeddings:
            raise ValueError("Input text cannot be empty.")
        return embeddings[0]
