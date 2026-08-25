from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata
from typing import Any


PIPELINE_VERSION = "0.1.0"
RULES_VERSION = "method-escalavel-2026-08-14"
TAXONOMY_VERSION = "golden-seed-2026-08-14"


@dataclass(frozen=True)
class FamilyRule:
    family_id: str
    display_name: str
    match_pattern: str
    default_market: str
    default_application: str
    default_equipment: str

    def matches(self, product: str) -> bool:
        return re.search(self.match_pattern, product or "", flags=re.IGNORECASE) is not None


FAMILY_RULES = (
    FamilyRule(
        "A12038",
        "A12038",
        r"A\s*12038",
        "Refrigeração comercial e cadeia do frio",
        "Circulação de ar e troca térmica em refrigeração",
        "Evaporadores, forçadores e unidades frigoríficas",
    ),
    FamilyRule(
        "VENT_FS4_400_ET",
        "VENT. FS/4-400 ET",
        r"FS\s*/?\s*4\s*[-/]\s*400\s+ET",
        "Refrigeração comercial e industrial",
        "Circulação de ar e troca térmica em sistemas frigoríficos",
        "Evaporadores, condensadores e unidades frigoríficas",
    ),
)


def normalize_text(value: Any) -> str:
    text = "" if value is None else str(value)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^A-Za-z0-9]+", " ", text).strip().upper()
    return re.sub(r"\s+", " ", text)


def family_for_product(product: str) -> FamilyRule | None:
    for rule in FAMILY_RULES:
        if rule.matches(product):
            return rule
    return None


def eligible_client(channel: Any, profile: Any = "", segment: Any = "") -> bool:
    text = " ".join(normalize_text(value) for value in (channel, profile, segment))
    if "REVENDA" in text or "MANUTENCAO" in text:
        return False
    channel_norm = normalize_text(channel)
    return channel_norm in {"FABRICANTE", "CONSUMIDOR"}


def client_type(channel: Any) -> str:
    value = normalize_text(channel)
    if value == "FABRICANTE":
        return "FABRICANTE"
    if value == "CONSUMIDOR":
        return "CONSUMIDOR"
    if "REVENDA" in value:
        return "REVENDA"
    if "MANUTENCAO" in value:
        return "MANUTENÇÃO"
    return value or "DESCONHECIDO"


def split_terms(value: Any) -> list[str]:
    if value is None:
        return []
    return [item.strip() for item in str(value).split(";") if item.strip()][:5]
