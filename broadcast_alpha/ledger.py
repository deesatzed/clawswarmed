import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


GENESIS_HASH = "0" * 64


def _canonical(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


@dataclass
class Receipt:
    id: str
    kind: str
    body: dict[str, Any]
    evaluator_id: str = "eval_0"
    epoch_id: str = "epoch_0"
    parent_hash: str = GENESIS_HASH
    ts: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    hash: str = ""

    def signing_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        payload.pop("hash", None)
        return payload

    def compute_hash(self) -> str:
        return hashlib.sha256(_canonical(self.signing_payload()).encode("utf-8")).hexdigest()

    def seal(self) -> "Receipt":
        self.hash = self.compute_hash()
        return self

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Receipt":
        return cls(**data)


class Ledger:
    def __init__(self, receipts: list[Receipt] | None = None) -> None:
        self.receipts = receipts or []

    def append(
        self,
        kind: str,
        body: dict[str, Any],
        evaluator_id: str = "eval_0",
        epoch_id: str = "epoch_0",
    ) -> Receipt:
        parent_hash = self.receipts[-1].hash if self.receipts else GENESIS_HASH
        receipt = Receipt(
            id=f"receipt_{len(self.receipts) + 1:06d}",
            kind=kind,
            body=body,
            evaluator_id=evaluator_id,
            epoch_id=epoch_id,
            parent_hash=parent_hash,
        ).seal()
        self.receipts.append(receipt)
        return receipt

    def verify_chain(self) -> bool:
        expected_parent = GENESIS_HASH
        for receipt in self.receipts:
            if receipt.parent_hash != expected_parent:
                return False
            if receipt.hash != receipt.compute_hash():
                return False
            expected_parent = receipt.hash
        return True

    def export_jsonl(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "".join(json.dumps(receipt.to_dict(), sort_keys=True) + "\n" for receipt in self.receipts)
        )
        return path

    @classmethod
    def from_jsonl(cls, path: Path) -> "Ledger":
        receipts = [
            Receipt.from_dict(json.loads(line))
            for line in path.read_text().splitlines()
            if line.strip()
        ]
        return cls(receipts)

