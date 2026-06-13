import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


try:
    import torch  # type: ignore[import-not-found]
    from torch import nn  # type: ignore[import-not-found]
    from torch.utils.data import DataLoader, TensorDataset  # type: ignore[import-not-found]

    TORCH_AVAILABLE = True
except ImportError:  # pragma: no cover - runtime fallback
    torch = None
    nn = None
    DataLoader = None
    TensorDataset = None
    TORCH_AVAILABLE = False


PAD_TOKEN = "__PAD__"
UNK_TOKEN = "__UNK__"


@dataclass
class LSTMArtifacts:
    model_path: Path
    vocab_path: Path
    config_path: Path


class _NextItemLSTM(nn.Module):
    def __init__(self, vocab_size: int, embed_dim: int, hidden_dim: int, pad_idx: int):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=pad_idx)
        self.lstm = nn.LSTM(input_size=embed_dim, hidden_size=hidden_dim, batch_first=True)
        self.output = nn.Linear(hidden_dim, vocab_size)

    def forward(self, x):
        emb = self.embedding(x)
        out, _ = self.lstm(emb)
        last_hidden = out[:, -1, :]
        return self.output(last_hidden)


class LSTMNextItemService:
    def __init__(
        self,
        artifact_dir: str,
        max_seq_len: int = 20,
        embed_dim: int = 64,
        hidden_dim: int = 128,
    ):
        self.artifact_dir = Path(artifact_dir)
        self.artifacts = LSTMArtifacts(
            model_path=self.artifact_dir / "next_item_lstm.pt",
            vocab_path=self.artifact_dir / "vocab.json",
            config_path=self.artifact_dir / "config.json",
        )
        self.max_seq_len = int(max_seq_len)
        self.embed_dim = int(embed_dim)
        self.hidden_dim = int(hidden_dim)
        self.item_to_idx: Dict[str, int] = {}
        self.idx_to_item: Dict[int, str] = {}
        self.model = None

    @property
    def enabled(self) -> bool:
        return TORCH_AVAILABLE

    def _ensure_artifact_dir(self) -> None:
        self.artifact_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def build_sequences(activities: Iterable[Dict], min_user_events: int = 3) -> Dict[int, List[str]]:
        grouped: Dict[int, List[Tuple[str, int]]] = {}
        for act in activities:
            customer_id = act.get("customer_id")
            item_id = act.get("product_id") if act.get("product_id") is not None else act.get("item_id")
            if customer_id is None or item_id is None:
                continue

            try:
                cid = int(customer_id)
                iid = int(item_id)
            except (TypeError, ValueError):
                continue

            action = str(act.get("action") or "VIEW_PRODUCT").upper()
            action_weight = {
                "VIEW_PRODUCT": 1,
                "ADD_TO_CART": 2,
                "RATE_PRODUCT": 1,
                "PURCHASE": 3,
            }.get(action, 1)
            token = f"product:{iid}"
            grouped.setdefault(cid, []).append((token, action_weight))

        sequences: Dict[int, List[str]] = {}
        for cid, rows in grouped.items():
            sequence: List[str] = []
            for token, weight in rows:
                sequence.extend([token] * max(1, min(weight, 3)))
            if len(sequence) >= int(min_user_events):
                sequences[cid] = sequence
        return sequences

    @staticmethod
    def _left_pad(values: List[int], pad_value: int, max_len: int) -> List[int]:
        cropped = values[-max_len:]
        if len(cropped) >= max_len:
            return cropped
        return [pad_value] * (max_len - len(cropped)) + cropped

    def _build_vocab(self, sequences: Dict[int, List[str]]) -> None:
        vocab = {PAD_TOKEN: 0, UNK_TOKEN: 1}
        for seq in sequences.values():
            for token in seq:
                if token not in vocab:
                    vocab[token] = len(vocab)
        self.item_to_idx = vocab
        self.idx_to_item = {idx: token for token, idx in vocab.items()}

    def _encode_pairs(self, sequences: Dict[int, List[str]]) -> Tuple[List[List[int]], List[int]]:
        pad_idx = self.item_to_idx[PAD_TOKEN]
        unk_idx = self.item_to_idx[UNK_TOKEN]
        X: List[List[int]] = []
        y: List[int] = []

        for seq in sequences.values():
            idx_seq = [self.item_to_idx.get(token, unk_idx) for token in seq]
            for cut in range(1, len(idx_seq)):
                history = idx_seq[:cut]
                target = idx_seq[cut]
                X.append(self._left_pad(history, pad_value=pad_idx, max_len=self.max_seq_len))
                y.append(target)
        return X, y

    def train(
        self,
        activities: Iterable[Dict],
        epochs: int = 8,
        batch_size: int = 64,
        learning_rate: float = 1e-3,
        min_user_events: int = 3,
    ) -> Dict:
        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch is not installed. Install torch before training LSTM recommender.")

        sequences = self.build_sequences(activities, min_user_events=min_user_events)
        if not sequences:
            raise RuntimeError("Not enough activity data to train LSTM model.")

        self._build_vocab(sequences)
        X, y = self._encode_pairs(sequences)
        if not X or not y:
            raise RuntimeError("Unable to generate training pairs from activity sequences.")

        x_tensor = torch.tensor(X, dtype=torch.long)
        y_tensor = torch.tensor(y, dtype=torch.long)
        dataset = TensorDataset(x_tensor, y_tensor)
        loader = DataLoader(dataset, batch_size=max(1, int(batch_size)), shuffle=True)

        pad_idx = self.item_to_idx[PAD_TOKEN]
        model = _NextItemLSTM(
            vocab_size=len(self.item_to_idx),
            embed_dim=self.embed_dim,
            hidden_dim=self.hidden_dim,
            pad_idx=pad_idx,
        )
        optimizer = torch.optim.Adam(model.parameters(), lr=float(learning_rate))
        criterion = nn.CrossEntropyLoss(ignore_index=pad_idx)

        model.train()
        final_loss = 0.0
        for _ in range(max(1, int(epochs))):
            epoch_loss = 0.0
            sample_count = 0
            for batch_x, batch_y in loader:
                optimizer.zero_grad()
                logits = model(batch_x)
                loss = criterion(logits, batch_y)
                loss.backward()
                optimizer.step()

                epoch_loss += float(loss.item()) * int(batch_x.size(0))
                sample_count += int(batch_x.size(0))
            final_loss = epoch_loss / max(1, sample_count)

        self.model = model
        self._save()

        return {
            "status": "trained",
            "users": len(sequences),
            "samples": len(X),
            "vocab_size": len(self.item_to_idx),
            "final_loss": round(final_loss, 6),
        }

    def _save(self) -> None:
        if self.model is None:
            raise RuntimeError("Model is empty. Train or load model before saving.")

        self._ensure_artifact_dir()
        torch.save(self.model.state_dict(), self.artifacts.model_path)

        with self.artifacts.vocab_path.open("w", encoding="utf-8") as f:
            json.dump(self.item_to_idx, f, ensure_ascii=True, indent=2)

        with self.artifacts.config_path.open("w", encoding="utf-8") as f:
            json.dump(
                {
                    "max_seq_len": self.max_seq_len,
                    "embed_dim": self.embed_dim,
                    "hidden_dim": self.hidden_dim,
                },
                f,
                ensure_ascii=True,
                indent=2,
            )

    def load(self) -> bool:
        if not TORCH_AVAILABLE:
            return False
        if not (self.artifacts.model_path.exists() and self.artifacts.vocab_path.exists()):
            return False

        with self.artifacts.vocab_path.open("r", encoding="utf-8") as f:
            self.item_to_idx = json.load(f)
        self.idx_to_item = {idx: token for token, idx in self.item_to_idx.items()}

        if self.artifacts.config_path.exists():
            with self.artifacts.config_path.open("r", encoding="utf-8") as f:
                cfg = json.load(f)
            self.max_seq_len = int(cfg.get("max_seq_len", self.max_seq_len))
            self.embed_dim = int(cfg.get("embed_dim", self.embed_dim))
            self.hidden_dim = int(cfg.get("hidden_dim", self.hidden_dim))

        pad_idx = self.item_to_idx.get(PAD_TOKEN, 0)
        model = _NextItemLSTM(
            vocab_size=len(self.item_to_idx),
            embed_dim=self.embed_dim,
            hidden_dim=self.hidden_dim,
            pad_idx=pad_idx,
        )
        state = torch.load(self.artifacts.model_path, map_location="cpu")
        model.load_state_dict(state)
        model.eval()
        self.model = model
        return True

    def predict_top_k(self, sequence_tokens: List[str], top_k: int = 20) -> List[Dict]:
        if not TORCH_AVAILABLE:
            return []
        if self.model is None and not self.load():
            return []

        pad_idx = self.item_to_idx.get(PAD_TOKEN, 0)
        unk_idx = self.item_to_idx.get(UNK_TOKEN, 1)

        idx_seq = [self.item_to_idx.get(token, unk_idx) for token in sequence_tokens if token]
        if not idx_seq:
            return []

        x = torch.tensor([self._left_pad(idx_seq, pad_value=pad_idx, max_len=self.max_seq_len)], dtype=torch.long)
        with torch.no_grad():
            logits = self.model(x)
            probs = torch.softmax(logits, dim=-1)[0]

        k = min(max(1, int(top_k)), int(probs.numel()))
        values, indices = torch.topk(probs, k=k)

        seen = set(sequence_tokens)
        output: List[Dict] = []
        for score, idx in zip(values.tolist(), indices.tolist()):
            token = self.idx_to_item.get(int(idx), "")
            if not token or token in {PAD_TOKEN, UNK_TOKEN}:
                continue
            if token in seen:
                continue
            output.append({"token": token, "score": float(score)})
        return output