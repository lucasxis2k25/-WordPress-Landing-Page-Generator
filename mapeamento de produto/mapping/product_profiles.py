"""Perfil fechado por produto — cada SKU com mercados, aplicações e equipamentos próprios.

Evita reutilizar aplicações de um produto (ex.: A12038) em ventiladores de outra família.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any


# Mercados canônicos (vocabulário golden A12038 / VENT FS4-400)
MARKET_REFRIGERATION = "Refrigeração comercial e cadeia do frio"
MARKET_REFRIGERATION_IND = "Refrigeração comercial e industrial"
MARKET_FOOD = "Food service, varejo alimentar e bebidas"
MARKET_MED_LAB = "Saúde, farmacêutico e laboratórios"
MARKET_TRANSFORM = "Indústrias de transformação, agronegócio e bens de capital"
MARKET_AUTOMATION = "Automação, energia e infraestrutura digital"
MARKET_HVAC = "HVAC, ventilação e qualidade do ar"
MARKET_REVIEW = "Não comprovado — revisar"


@dataclass(frozen=True)
class ProductProfile:
    profile_id: str
    match_patterns: tuple[str, ...]
    technical_family: str
    product_role: str
    allowed_applications: tuple[str, ...]
    default_application: str
    default_equipment: str
    market_map: dict[str, tuple[str, str]]


def _profile(
    profile_id: str,
    patterns: tuple[str, ...],
    family: str,
    role: str,
    allowed_apps: tuple[str, ...],
    default_app: str,
    default_equip: str,
    market_map: dict[str, tuple[str, str]],
) -> ProductProfile:
    return ProductProfile(
        profile_id=profile_id,
        match_patterns=patterns,
        technical_family=family,
        product_role=role,
        allowed_applications=allowed_apps,
        default_application=default_app,
        default_equipment=default_equip,
        market_map=market_map,
    )


# --- Perfis por produto (aplicações fechadas, sem herança cruzada) ---

PROFILE_A12038 = _profile(
    "A12038",
    ("A12038",),
    "A12038",
    "Ventilador axial compacto para circulação forçada em evaporadores, expositores e equipamentos térmicos.",
    (
        "Circulação de ar e troca térmica em refrigeração",
        "Conservação e exposição refrigerada de produtos",
        "Controle térmico e conservação médico-científica",
        "Ventilação, exaustão e qualidade do ar",
        "Aquecimento, secagem e processamento térmico",
        "Controle térmico de painéis, gabinetes e compartimentos",
        "Resfriamento de alimentos e bebidas",
        "Resfriamento e troca térmica de processos industriais",
        "Não comprovado — revisar aplicação",
    ),
    "Circulação de ar e troca térmica em refrigeração",
    "Evaporadores, forçadores e unidades frigoríficas",
    {
        MARKET_REFRIGERATION: (
            "Circulação de ar e troca térmica em refrigeração",
            "Evaporadores, forçadores e unidades frigoríficas",
        ),
        MARKET_FOOD: (
            "Conservação e exposição refrigerada de produtos",
            "Armários, balcões e expositores refrigerados",
        ),
        MARKET_MED_LAB: (
            "Controle térmico e conservação médico-científica",
            "Câmaras, freezers e incubadoras médico-científicas",
        ),
        MARKET_HVAC: (
            "Ventilação, exaustão e qualidade do ar",
            "Sistemas de ventilação, exaustão e tratamento de ar",
        ),
        MARKET_TRANSFORM: (
            "Aquecimento, secagem e processamento térmico",
            "Fornos, estufas e secadores",
        ),
        MARKET_AUTOMATION: (
            "Controle térmico de painéis, gabinetes e compartimentos",
            "Painéis elétricos, racks e eletrônica de potência",
        ),
    },
)

PROFILE_VENT_FS4_400 = _profile(
    "VENT_FS4_400_ET",
    ("FS/4-400 ET", "FS 4-400 ET"),
    "AXIAL",
    "Ventilador axial FS/4-400 ET para circulação de ar em evaporadores, condensadores e unidades frigoríficas.",
    (
        "Circulação de ar e troca térmica em sistemas frigoríficos",
        "Ventilação, exaustão e qualidade do ar",
        "Rejeição e transferência de calor em processos industriais",
        "Não comprovado — revisar aplicação",
    ),
    "Circulação de ar e troca térmica em sistemas frigoríficos",
    "Evaporadores, condensadores e unidades frigoríficas",
    {
        MARKET_REFRIGERATION_IND: (
            "Circulação de ar e troca térmica em sistemas frigoríficos",
            "Evaporadores, condensadores e unidades frigoríficas",
        ),
        MARKET_HVAC: (
            "Ventilação, exaustão e qualidade do ar",
            "Sistemas de ventilação, exaustão e tratamento de ar",
        ),
        MARKET_TRANSFORM: (
            "Rejeição e transferência de calor em processos industriais",
            "Chillers, trocadores e resfriadores de processo",
        ),
    },
)

PROFILE_VENT_FS_AXIAL = _profile(
    "VENT_FS_AXIAL",
    ("VENT. FS/", "FS/2-300", "FS/4-400 EMBT"),
    "AXIAL",
    "Ventilador axial médio/grande para circulação de ar em sistemas frigoríficos, ventilação industrial e resfriamento de processos.",
    (
        "Circulação de ar e troca térmica em refrigeração",
        "Ventilação, exaustão e qualidade do ar",
        "Controle térmico de painéis, gabinetes e compartimentos",
        "Resfriamento e troca térmica de processos industriais",
        "Não comprovado — revisar aplicação",
    ),
    "Circulação de ar e troca térmica em refrigeração",
    "Evaporadores, forçadores e unidades frigoríficas",
    {
        MARKET_REFRIGERATION: (
            "Circulação de ar e troca térmica em refrigeração",
            "Evaporadores, forçadores e unidades frigoríficas",
        ),
        MARKET_HVAC: (
            "Ventilação, exaustão e qualidade do ar",
            "Sistemas de ventilação, exaustão e tratamento de ar",
        ),
        MARKET_AUTOMATION: (
            "Controle térmico de painéis, gabinetes e compartimentos",
            "Painéis elétricos, racks e eletrônica de potência",
        ),
        MARKET_TRANSFORM: (
            "Resfriamento e troca térmica de processos industriais",
            "Máquinas industriais com ventilação ou resfriamento",
        ),
        MARKET_FOOD: (
            "Conservação e exposição refrigerada de produtos",
            "Armários, balcões e expositores refrigerados",
        ),
    },
)

PROFILE_VENT_FF_CENTRIFUGO = _profile(
    "VENT_FF_CENTRIFUGO",
    ("VENT. FF/", "VENT.FB/", "CENTRIFUGO/GABINETE", "CENTRIFUGO/TURBINA", "CENTRIFUGO"),
    "CENTRIFUGO/GABINETE",
    "Ventilador centrífugo de gabinete para dutos, UTAs, coifas e evaporadores com alta pressão estática.",
    (
        "Ventilação, exaustão e qualidade do ar",
        "Circulação de ar e troca térmica em refrigeração",
        "Controle térmico de painéis, gabinetes e compartimentos",
        "Não comprovado — revisar aplicação",
    ),
    "Ventilação, exaustão e qualidade do ar",
    "Sistemas de ventilação, exaustão e tratamento de ar",
    {
        MARKET_HVAC: (
            "Ventilação, exaustão e qualidade do ar",
            "Sistemas de ventilação, exaustão e tratamento de ar",
        ),
        MARKET_FOOD: (
            "Ventilação, exaustão e qualidade do ar",
            "Sistemas de ventilação, exaustão e tratamento de ar",
        ),
        MARKET_MED_LAB: (
            "Ventilação, exaustão e qualidade do ar",
            "Sistemas de ventilação, exaustão e tratamento de ar",
        ),
        MARKET_REFRIGERATION: (
            "Circulação de ar e troca térmica em refrigeração",
            "Evaporadores, forçadores e unidades frigoríficas",
        ),
        MARKET_AUTOMATION: (
            "Controle térmico de painéis, gabinetes e compartimentos",
            "Painéis elétricos, racks e eletrônica de potência",
        ),
    },
)

PROFILE_MICROVENTILADOR = _profile(
    "MICROVENTILADOR",
    ("MICROVENTILADOR", "A17251"),
    "MICROVENTILADOR",
    "Microventilador 172 mm — ventilação forçada em painéis, gabinetes, estufas/laboratório e tanques de leite.",
    (
        "Controle térmico de painéis, gabinetes e compartimentos",
        "Controle térmico e conservação médico-científica",
        "Resfriamento de alimentos e bebidas",
        "Ventilação, exaustão e qualidade do ar",
        "Circulação de ar e troca térmica em refrigeração",
        "Não comprovado — revisar aplicação",
    ),
    "Controle térmico de painéis, gabinetes e compartimentos",
    "Painéis elétricos, racks e eletrônica de potência",
    {
        MARKET_AUTOMATION: (
            "Controle térmico de painéis, gabinetes e compartimentos",
            "Painéis elétricos, racks e eletrônica de potência",
        ),
        MARKET_MED_LAB: (
            "Controle térmico e conservação médico-científica",
            "Câmaras, freezers e incubadoras médico-científicas",
        ),
        MARKET_TRANSFORM: (
            "Controle térmico de painéis, gabinetes e compartimentos",
            "Máquinas industriais com ventilação ou resfriamento",
        ),
        MARKET_FOOD: (
            "Ventilação, exaustão e qualidade do ar",
            "Fornos, estufas e secadores",
        ),
        MARKET_REFRIGERATION: (
            "Circulação de ar e troca térmica em refrigeração",
            "Evaporadores, forçadores e unidades frigoríficas",
        ),
        MARKET_HVAC: (
            "Ventilação, exaustão e qualidade do ar",
            "Sistemas de ventilação, exaustão e tratamento de ar",
        ),
    },
)

PROFILE_TANGENCIAL = _profile(
    "TANGENCIAL",
    ("TGH", "TANGENCIAL"),
    "TANGENCIAL",
    "Ventilador tangencial para cortinas de ar, climatizadores lineares e fluxo laminar.",
    (
        "Ventilação, exaustão e qualidade do ar",
        "Conservação e exposição refrigerada de produtos",
        "Não comprovado — revisar aplicação",
    ),
    "Ventilação, exaustão e qualidade do ar",
    "Sistemas de ventilação, exaustão e tratamento de ar",
    {
        MARKET_FOOD: (
            "Ventilação, exaustão e qualidade do ar",
            "Sistemas de ventilação, exaustão e tratamento de ar",
        ),
        MARKET_HVAC: (
            "Ventilação, exaustão e qualidade do ar",
            "Sistemas de ventilação, exaustão e tratamento de ar",
        ),
        MARKET_REFRIGERATION: (
            "Conservação e exposição refrigerada de produtos",
            "Armários, balcões e expositores refrigerados",
        ),
    },
)

PROFILE_CONECTO = _profile(
    "CONECTO",
    ("CONECTO",),
    "ACESSORIOS",
    "Conector elétrico para interligação de ventiladores centrífugos da linha FF.",
    (
        "Interligação elétrica de ventiladores centrífugos",
        "Não comprovado — revisar aplicação",
    ),
    "Interligação elétrica de ventiladores centrífugos",
    "Chicotes e conectores para ventiladores centrífugos",
    {
        MARKET_FOOD: (
            "Interligação elétrica de ventiladores centrífugos",
            "Chicotes e conectores para ventiladores centrífugos",
        ),
        MARKET_HVAC: (
            "Interligação elétrica de ventiladores centrífugos",
            "Chicotes e conectores para ventiladores centrífugos",
        ),
    },
)

PROFILE_ECM = _profile(
    "ECM",
    ("ECM",),
    "MOTORES",
    "Motor ECM de alta eficiência para acionamento de ventiladores em expositores e evaporadores comerciais.",
    (
        "Acionamento de alta eficiência em sistemas frigoríficos",
        "Não comprovado — revisar aplicação",
    ),
    "Acionamento de alta eficiência em sistemas frigoríficos",
    "Armários, balcões e expositores refrigerados",
    {
        MARKET_REFRIGERATION: (
            "Acionamento de alta eficiência em sistemas frigoríficos",
            "Armários, balcões e expositores refrigerados",
        ),
        MARKET_FOOD: (
            "Acionamento de alta eficiência em sistemas frigoríficos",
            "Armários, balcões e expositores refrigerados",
        ),
    },
)

PROFILE_PECAS = _profile(
    "PECAS",
    ("PLUS UNIC",),
    "PECAS",
    "Peça/componente de reposição — classificação depende do equipamento destino comprovado.",
    (
        "Reposição e manutenção de ventiladores",
        "Não comprovado — revisar aplicação",
    ),
    "Reposição e manutenção de ventiladores",
    "Componentes e peças de ventiladores",
    {
        MARKET_REVIEW: (
            "Reposição e manutenção de ventiladores",
            "Componentes e peças de ventiladores",
        ),
    },
)


# Ordem importa: perfis mais específicos primeiro
ALL_PROFILES: tuple[ProductProfile, ...] = (
    PROFILE_A12038,
    PROFILE_VENT_FS4_400,
    PROFILE_CONECTO,
    PROFILE_ECM,
    PROFILE_PECAS,
    PROFILE_MICROVENTILADOR,
    PROFILE_TANGENCIAL,
    PROFILE_VENT_FF_CENTRIFUGO,
    PROFILE_VENT_FS_AXIAL,
)


def resolve_product_profile(product_code: str, tech_family: str = "") -> ProductProfile | None:
    norm_prod = (product_code or "").upper()
    norm_fam = (tech_family or "").upper()
    for profile in ALL_PROFILES:
        for pattern in profile.match_patterns:
            if pattern.upper() in norm_prod or pattern.upper() in norm_fam:
                return profile
    return None


def profile_for_product(product_code: str, tech_family: str = "") -> ProductProfile:
    profile = resolve_product_profile(product_code, tech_family)
    if profile:
        return profile
    return PROFILE_VENT_FF_CENTRIFUGO
