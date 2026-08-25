import os
import json
import re

RAW_DIR = os.path.join(os.path.dirname(__file__), 'scraped_data')
DADOS_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'dados'))
OUTPUT_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'output'))

def build_clean_json(slug_or_raw_path):
    if os.path.exists(slug_or_raw_path):
        raw_path = slug_or_raw_path
    else:
        raw_path = os.path.join(RAW_DIR, f"{slug_or_raw_path}_raw.json")
        
    if not os.path.exists(raw_path):
        print(f"[!] Arquivo bruto não encontrado: {raw_path}")
        return None

    with open(raw_path, 'r', encoding='utf-8') as f:
        raw = json.load(f)

    slug = raw['slug']
    nome_bruto = raw['nome'].replace('&#8211;', '-').replace('&amp;', '&').strip()
    
    # 1. Extração de especificações
    especificacoes = []
    specs_dict = {}
    for item in raw.get('especificacoes_brutas', []):
        attr = item['atributo'].strip()
        val = item['valor'].strip()
        specs_dict[attr.lower()] = val
        especificacoes.append({
            "atributo": attr,
            "valor": val,
            "confianca": "100%",
            "fonte": "Descrição Oficial Demo Store"
        })

    # Detecta se é motor trifásico
    alimentacao = specs_dict.get('alimentação', '') or specs_dict.get('voltagem', '')
    is_trifasico = 'trifásic' in alimentacao.lower() or '380v' in alimentacao.lower() or '440v' in alimentacao.lower()

    # 2. Hero Checklist
    hero_checklist = []
    if 'voltagem' in specs_dict or 'alimentação' in specs_dict:
        tensao = specs_dict.get('voltagem') or specs_dict.get('alimentação')
        hero_checklist.append(f"<strong>Alimentação:</strong> {tensao} com alta eficiência operacional.")
    if 'volume de ar' in specs_dict:
        hero_checklist.append(f"<strong>Vazão de Ar:</strong> {specs_dict['volume de ar']} para refrigeração otimizada.")
    if 'diâmetro da hélice' in specs_dict or 'diâmetro' in specs_dict:
        diam = specs_dict.get('diâmetro da hélice') or specs_dict.get('diâmetro')
        hero_checklist.append(f"<strong>Dimensão Nominal:</strong> Diâmetro de {diam}.")
    if 'nível de ruído db(a)' in specs_dict:
        hero_checklist.append(f"<strong>Acústica:</strong> Nível de ruído de {specs_dict['nível de ruído db(a)']}.")
    
    if not hero_checklist:
        hero_checklist = []

    # 3. Aplicações
    aplicacoes = []
    desc_text = raw.get('descricao_bruta', '')
    if 'aplicações são:' in desc_text or 'aplicações:' in desc_text:
        match = re.search(r'aplicações[^:]*:(.*?)(?:Consulte|$)', desc_text, re.IGNORECASE)
        if match:
            app_str = match.group(1)
            aplicacoes = [a.strip().capitalize() for a in app_str.split(',') if a.strip()]

    if not aplicacoes:
        aplicacoes = []

    # 4. Benefícios
    beneficios = []

    # 5. Diferenciais
    diferenciais = []

    # 6. FAQ Dinâmica
    codigo_modelo = raw.get('sku') or slug.upper()
    faq = []

    if is_trifasico:
        faq.append({
            "pergunta": "Como deve ser feita a ligação do motor trifásico?",
            "resposta": "Motores trifásicos aceitam esquemas de ligação (Estrela/Triângulo ou Delta). Consulte sempre o diagrama na placa do motor ou no manual do fabricante."
        })

    # 7. SEO
    seo_keywords = [
        nome_bruto.lower(),
        f"ventilador {slug}",
        f"exaustor {slug}",
        "Demo Store b2b refrigeração"
    ]
    meta_desc = f"{nome_bruto}. Equipamento industrial com suporte técnico especializado na Demo Store."
    if len(meta_desc) > 160:
        meta_desc = meta_desc[:157] + "..."

    clean_data = {
        "slug": slug,
        "nome": nome_bruto,
        "sku": raw.get('sku') or slug.upper(),
        "categoria": raw.get('categorias')[0] if raw.get('categorias') else "Ventiladores e Exaustores Industriais",
        "resumo_tecnico": desc_text[:250] + "..." if len(desc_text) > 250 else desc_text,
        "hero_checklist": hero_checklist,
        "especificacoes": especificacoes,
        "aplicacoes": aplicacoes,
        "categoria_link": "https://DemoStore.com.br/produtos/",
        "beneficios": beneficios,
        "diferenciais": diferenciais,
        "faq": faq,
        "alerta_tecnico": "Antes de efetuar qualquer substituição de ventiladores, valide os seguintes parâmetros no datasheet ou etiqueta do produto: Vazão (m³/h), Rotação (RPM), Potência (W), Corrente (A), Pressão estática, Furação de fixação, Tensão (V) e Frequência (Hz). Conecte conforme indicação na etiqueta do produto.",
        "motor_trifasico": is_trifasico,
        "seo": {
            "keywords": seo_keywords,
            "meta_description": meta_desc
        }
    }

    # Salva em gerador/dados/
    os.makedirs(DADOS_DIR, exist_ok=True)
    out_dados_path = os.path.join(DADOS_DIR, f"{slug}.json")
    with open(out_dados_path, 'w', encoding='utf-8') as f:
        json.dump(clean_data, f, ensure_ascii=False, indent=2)

    print(f"[OK] JSON limpo gerado em: {out_dados_path}")
    return clean_data

if __name__ == '__main__':
    # Teste de conversão do produto raspado
    test_slug = "ventilador-exaustor-axial-250mm-fs-2-250-em"
    build_clean_json(test_slug)
