"""Garante mapeamento fechado por produto — sem mistura de aplicações."""

from mapping.product_profiles import profile_for_product
from mapping.quality_gate import sanitize_client_record


def test_microventilador_hort_tanque_leite():
    row = sanitize_client_record(
        product_code="MICROVENTILADOR A17251VBHBL - 110/220V",
        tech_family="MICROVENTILADOR",
        client_name="HORT INDUSTRIA E COMERCIO LTDA.",
        quantity=744,
        client_type="FABRICANTE",
    )
    assert row["market"] == "Indústrias de transformação, agronegócio e bens de capital"
    assert row["application"] == "Resfriamento de alimentos e bebidas"
    assert "Resfriador" in row["equipment"]


def test_microventilador_quimis_laboratorio():
    row = sanitize_client_record(
        product_code="MICROVENTILADOR A17251VBHBL - 110/220V",
        tech_family="MICROVENTILADOR",
        client_name="QUIMIS APARELHOS CIENTIFICOS LTDA",
        quantity=201,
        client_type="FABRICANTE",
    )
    assert row["market"] == "Saúde, farmacêutico e laboratórios"
    assert row["application"] == "Controle térmico e conservação médico-científica"


def test_conecto_apenas_interligacao():
    profile = profile_for_product("CONECTO FF", "ACESSORIOS")
    assert profile.profile_id == "CONECTO"
    row = sanitize_client_record(
        product_code="CONECTO FF",
        tech_family="ACESSORIOS",
        client_name="MUCHERONE & VOLPE LTDA",
        quantity=678,
        client_type="FABRICANTE",
    )
    assert row["application"] == "Interligação elétrica de ventiladores centrífugos"
    assert "Circulação de ar" not in row["application"]


def test_fs_axial_nao_usa_aplicacao_a12038_generica():
    profile = profile_for_product("VENT. FS/2-300 EM -  230 V", "AXIAL")
    assert profile.profile_id == "VENT_FS_AXIAL"
    assert "Circulação de ar e troca térmica em sistemas frigoríficos" not in profile.allowed_applications


def test_ff_centrifugo_equipamento_consolidado():
    row = sanitize_client_record(
        product_code="VENT. FF/2-146 P 220V",
        tech_family="CENTRIFUGO/GABINETE",
        client_name="BERLINERLUFT DO BRASIL IND E COM LTDA",
        quantity=362,
        client_type="FABRICANTE",
    )
    assert row["application"] == "Ventilação, exaustão e qualidade do ar"
    assert row["equipment"] == "Sistemas de ventilação, exaustão e tratamento de ar"
