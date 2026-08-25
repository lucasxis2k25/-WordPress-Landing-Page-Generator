"""Quality Gate — mapeamento por produto, sem misturar aplicações entre SKUs."""

from __future__ import annotations

import re
import unicodedata
from typing import Any

from .product_profiles import (
    MARKET_AUTOMATION,
    MARKET_FOOD,
    MARKET_HVAC,
    MARKET_MED_LAB,
    MARKET_REVIEW,
    MARKET_REFRIGERATION,
    MARKET_REFRIGERATION_IND,
    MARKET_TRANSFORM,
    profile_for_product,
)


def normalize_str(val: Any) -> str:
    if val is None:
        return ""
    text = unicodedata.normalize("NFKD", str(val)).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", text).strip().upper()


# Override determinístico: cliente + produto (evita QUIMIS=UTA no microventilador)
CLIENT_PRODUCT_OVERRIDES: list[dict[str, Any]] = [
    {
        "client_keys": ("QUIMIS",),
        "product_keys": ("MICROVENTILADOR", "A17251"),
        "market": MARKET_MED_LAB,
        "application": "Controle térmico e conservação médico-científica",
        "equipment": "Câmaras, freezers e incubadoras médico-científicas",
        "evidence": "Fabricante de estufas, incubadoras e equipamentos científicos — microventilador em câmara térmica.",
    },
    {
        "client_keys": ("HORT",),
        "product_keys": ("MICROVENTILADOR", "A17251"),
        "market": MARKET_TRANSFORM,
        "application": "Resfriamento de alimentos e bebidas",
        "equipment": "Resfriadores e equipamentos de processo alimentício",
        "evidence": "Fabricante de tanques resfriadores de leite — microventilador no tanque.",
    },
    {
        "client_keys": ("SEMPEL",),
        "product_keys": ("MICROVENTILADOR", "A17251"),
        "market": MARKET_AUTOMATION,
        "application": "Controle térmico de painéis, gabinetes e compartimentos",
        "equipment": "Painéis elétricos, racks e eletrônica de potência",
        "evidence": "Fabricante de painéis elétricos e quadros de comando.",
    },
    {
        "client_keys": ("TRINEVA",),
        "product_keys": ("A12038",),
        "market": MARKET_REFRIGERATION,
        "application": "Circulação de ar e troca térmica em refrigeração",
        "equipment": "Evaporadores, forçadores e unidades frigoríficas",
        "evidence": "Fabricante de evaporadores e forçadores para refrigeração comercial.",
    },
    {
        "client_keys": ("TRINEVA",),
        "product_keys": ("VENT. FS", "AXIAL"),
        "market": MARKET_REFRIGERATION,
        "application": "Circulação de ar e troca térmica em refrigeração",
        "equipment": "Evaporadores, forçadores e unidades frigoríficas",
        "evidence": "Fabricante de evaporadores — ventilador axial em unidade frigorífica.",
    },
    {
        "client_keys": ("BERLINERLUFT", "MGE", "PREMIUM AR", "FILTERFLUX", "LINTER", "HENGST"),
        "product_keys": ("VENT. FF", "VENT.FB", "CENTRIFUGO"),
        "market": MARKET_HVAC,
        "application": "Ventilação, exaustão e qualidade do ar",
        "equipment": "Sistemas de ventilação, exaustão e tratamento de ar",
        "evidence": "Fabricante de UTAs, filtragem e tratamento de ar.",
    },
    {
        "client_keys": ("COPLAN", "COIFART", "MUCHERONE", "PROJINOX", "CASITECH", "OURO GRILL", "SULFISA", "TOPEMA"),
        "product_keys": ("VENT. FF", "VENT.FB", "TGH", "CONECTO"),
        "market": MARKET_FOOD,
        "application": "Ventilação, exaustão e qualidade do ar",
        "equipment": "Sistemas de ventilação, exaustão e tratamento de ar",
        "evidence": "Fabricante de coifas e equipamentos gastronômicos.",
    },
    {
        "client_keys": ("OURIFRIO", "GRESOCOL", "ELETROFRIO", "MAXFREEZER", "FRIOTECH"),
        "product_keys": ("VENT. FS", "VENT. FF", "AXIAL"),
        "market": MARKET_REFRIGERATION,
        "application": "Circulação de ar e troca térmica em refrigeração",
        "equipment": "Evaporadores, forçadores e unidades frigoríficas",
        "evidence": "Fabricante ou integrador de refrigeração comercial/industrial.",
    },
    {
        "client_keys": ("MUCHERONE",),
        "product_keys": ("CONECTO",),
        "market": MARKET_FOOD,
        "application": "Interligação elétrica de ventiladores centrífugos",
        "equipment": "Chicotes e conectores para ventiladores centrífugos",
        "evidence": "Fabricante de coifas — conector FF em ventilador centrífugo de exaustão.",
    },
    {
        "client_keys": ("TUPER",),
        "product_keys": ("MICROVENTILADOR", "A17251"),
        "market": MARKET_TRANSFORM,
        "application": "Controle térmico de painéis, gabinetes e compartimentos",
        "equipment": "Painéis elétricos, racks e eletrônica de potência",
        "evidence": "Indústria metalúrgica — ventilação de painéis e CCM.",
    },
    {
        "client_keys": ("HB SOLUCOES", "AR COMPRIMIDO"),
        "product_keys": ("VENT. FS",),
        "market": MARKET_HVAC,
        "application": "Ventilação, exaustão e qualidade do ar",
        "equipment": "Sistemas de ventilação, exaustão e tratamento de ar",
        "evidence": "Fabricante de sistemas de ar comprimido — ventilador axial em resfriamento/ventilação de pacote.",
    },
    {
        "client_keys": ("TRANSFORMADOR", "TRANSFOR", "ENERGYA"),
        "product_keys": ("VENT. FS",),
        "market": MARKET_AUTOMATION,
        "application": "Controle térmico de painéis, gabinetes e compartimentos",
        "equipment": "Painéis elétricos, racks e eletrônica de potência",
        "evidence": "Fabricante de transformadores — ventilação forçada em cubículo/painel.",
    },
]


def _match_override(client_name: str, product_code: str, tech_family: str) -> dict[str, str] | None:
    norm_cli = normalize_str(client_name)
    norm_ctx = f"{normalize_str(product_code)} {normalize_str(tech_family)}"
    for item in CLIENT_PRODUCT_OVERRIDES:
        if not any(key in norm_cli for key in item["client_keys"]):
            continue
        if not any(key in norm_ctx for key in item["product_keys"]):
            continue
        return {
            "market": item["market"],
            "application": item["application"],
            "equipment": item["equipment"],
            "evidence": item["evidence"],
        }
    return None


def map_canonical_market(client_name: str, segment: str, market_base: str, channel: str) -> str:
    """Classifica o cliente em um único mercado macro (vocabulário golden)."""
    norm_cli = normalize_str(client_name)
    norm_seg = normalize_str(segment)
    norm_base = normalize_str(market_base)
    full_text = f"{norm_cli} {norm_seg} {norm_base}"

    # Clientes conhecidos (prioridade máxima — evita HORT→food service por cache legado)
    if any(k in norm_cli for k in ("HORT", "TECNOSUL", "TANQUE", "LEITE", "LACTIC")):
        return MARKET_TRANSFORM
    if "QUIMIS" in norm_cli or any(k in norm_cli for k in ("CIENTIFIC", "LABORAT", "APARELHOS CIENT")):
        return MARKET_MED_LAB
    if any(k in norm_cli for k in ("SEMPEL", "PAINEL", "PAINEIS", "QGBT", "TRANSFORMADOR", "TRANSFOR", "ENERGYA")):
        return MARKET_AUTOMATION
    if any(k in norm_cli for k in ("TRINEVA", "SERRAFF", "OURIFRIO", "GRESOCOL", "ELETROFRIO", "MAXFREEZER", "FRIOTECH")):
        return MARKET_REFRIGERATION
    if any(k in norm_cli for k in ("BERLINERLUFT", "MGE", "PREMIUM AR", "FILTERFLUX", "LINTER", "HENGST", "HB SOLUCOES", "AR COMPRIMIDO")):
        return MARKET_HVAC
    if any(k in norm_cli for k in ("COPLAN", "COIFART", "MUCHERONE", "PROJINOX", "CASITECH", "OURO GRILL", "SULFISA", "TOPEMA", "COIFA", "COIF")):
        return MARKET_FOOD

    if any(k in full_text for k in ["CIENTIFIC", "LABORAT", "HOSPIT", "FARMACEUT", "BIOLOGIC", "ODONTO", "CLINIC"]):
        return MARKET_MED_LAB

    if any(k in full_text for k in ["COIFA", "GRILL", "GOURMET", "CHURRASQ", "COZINHA", "FOOD SERVICE", "GASTRONOM", "RESTAURANT", "SORVET", "LANCHE"]):
        return MARKET_FOOD

    if any(k in full_text for k in ["AR COMPRIMIDO", "COMPRESSOR"]):
        return MARKET_HVAC

    if any(k in full_text for k in ["FILTRO", "FILTRAGEM", "SALA LIMPA", "AR CONDICIONADO", "HVAC", "VENTILACAO", "EXAUSTAO", "TRATAMENTO DE AR", "FANCOIL", "UTA"]):
        return MARKET_HVAC

    if any(k in full_text for k in ["REFRIGERACAO", "CAMARA FRIGOR", "CONGELAMENTO", "EVAPORADOR", "CONDENSADOR", "FRIO", "GELADEIRA", "FREEZER"]):
        return MARKET_REFRIGERATION

    if any(k in full_text for k in ["TRANSFORMADOR", "PAINEL", "PAINEIS", "ELETRIC", "QGBT", "CCM", "QUADRO", "NOBREAK", "DATA CENTER", "SUBESTACAO", "AUTOMACAO", "RACK"]):
        return MARKET_AUTOMATION

    if any(k in full_text for k in ["LEITE", "AGRO", "GRANJA", "AVIARIO", "USINA", "ETANOL", "ACUCAR"]):
        return MARKET_TRANSFORM

    if any(k in full_text for k in ["SIDERURG", "METALURG", "MINERACAO", "FUNDICAO", "TUBOS", "USINAGEM", "ACO", "EMBALAGEM", "PLASTIC", "TEXTIL", "MAQUINA", "EXTRUSORA", "PRENSA", "SOLDA"]):
        return MARKET_TRANSFORM

    if "REFRIG" in norm_seg:
        return MARKET_REFRIGERATION
    if "VENTIL" in norm_seg or "AR" in norm_seg:
        return MARKET_HVAC
    if "PAINEL" in norm_seg or "ELETR" in norm_seg:
        return MARKET_AUTOMATION

    return MARKET_REVIEW


def _apply_profile_mapping(profile, market: str) -> tuple[str, str, str]:
    """Retorna (equipamento, aplicação, evidência) apenas do vocabulário fechado do produto."""
    if market in profile.market_map:
        app, equip = profile.market_map[market]
        return equip, app, f"Mapeamento determinístico — perfil {profile.profile_id}"

    if market == MARKET_TRANSFORM and MARKET_TRANSFORM not in profile.market_map:
        if MARKET_AUTOMATION in profile.market_map:
            app, equip = profile.market_map[MARKET_AUTOMATION]
            return equip, app, f"Mapeamento determinístico — perfil {profile.profile_id}"
        if MARKET_HVAC in profile.market_map:
            app, equip = profile.market_map[MARKET_HVAC]
            return equip, app, f"Mapeamento determinístico — perfil {profile.profile_id}"

    if market == MARKET_REVIEW:
        return (
            "Não comprovado — revisar equipamento",
            "Não comprovado — revisar aplicação",
            "Segmento ou ativo físico sem evidência suficiente",
        )

    return (
        profile.default_equipment,
        profile.default_application,
        f"Mapeamento padrão — perfil {profile.profile_id}",
    )


def map_canonical_equipment_and_app(
    product_code: str,
    tech_family: str,
    market: str,
    client_name: str,
    raw_equipment: str = "",
) -> tuple[str, str, str]:
    """Retorna (equipamento, aplicação, evidência) coerentes com o produto específico."""
    profile = profile_for_product(product_code, tech_family)

    if profile.profile_id == "VENT_FS4_400_ET" and market == MARKET_REFRIGERATION:
        market = MARKET_REFRIGERATION_IND

    override = _match_override(client_name, product_code, tech_family)
    if override:
        app = override["application"]
        equip = override["equipment"]
        if app in profile.allowed_applications:
            return equip, app, override["evidence"]

    equip, app, evidence = _apply_profile_mapping(profile, market)

    if app not in profile.allowed_applications:
        app = profile.default_application
        equip = profile.default_equipment

    return equip, app, evidence


def sanitize_client_record(
    product_code: str,
    tech_family: str,
    client_name: str,
    quantity: float,
    client_type: str,
    segment: str = "",
    market_base: str = "",
    channel: str = "",
) -> dict[str, Any]:
    """Normaliza um cliente para o mapeamento exclusivo do produto."""
    override = _match_override(client_name, product_code, tech_family)
    if override:
        market = override["market"]
        application = override["application"]
        equipment = override["equipment"]
        evidence = override["evidence"]
    else:
        market = map_canonical_market(client_name, segment, market_base, channel)
        equipment, application, evidence = map_canonical_equipment_and_app(
            product_code=product_code,
            tech_family=tech_family,
            market=market,
            client_name=client_name,
        )

    profile = profile_for_product(product_code, tech_family)
    if application not in profile.allowed_applications:
        equipment, application, evidence = _apply_profile_mapping(profile, market)

    has_proof = "Fabricante" in evidence or "oficial" in evidence.lower()
    return {
        "client": client_name,
        "quantity": quantity,
        "type": client_type,
        "market": market,
        "application": application,
        "equipment": equipment,
        "evidence": evidence,
        "confidence": "Alta" if has_proof else "Média",
        "status": (
            "Comprovado — site oficial + base interna"
            if has_proof
            else "Validado por perfil do produto"
        ),
        "product_profile": profile.profile_id,
    }
