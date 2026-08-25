import os
import json
import re
import urllib.request

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'scraped_data')

def clean_text(text):
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text).strip()

def strip_tags(html):
    return clean_text(re.sub(r'<[^>]+>', ' ', html))

def scrape_DemoStore_product(url):
    """
    Raspa uma página de produto no site da Demo Store e extrai especificações técnicas e dados brutos usando biblioteca padrão do Python.
    """
    print(f"[*] Raspando: {url}")
    
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as resp:
            html_content = resp.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"[!] Erro ao acessar a URL {url}: {e}")
        return None

    # Slug a partir da URL
    slug = url.strip('/').split('/')[-1]
    
    # 1. Título do produto
    title_match = re.search(r'<h1[^>]*class="[^"]*product_title[^"]*"[^>]*>(.*?)</h1>', html_content, re.IGNORECASE | re.DOTALL)
    if not title_match:
        title_match = re.search(r'<h1[^>]*>(.*?)</h1>', html_content, re.IGNORECASE | re.DOTALL)
    nome = strip_tags(title_match.group(1)) if title_match else slug

    # 2. SKU
    sku_match = re.search(r'class="[^"]*sku[^"]*"[^>]*>(.*?)</span>', html_content, re.IGNORECASE | re.DOTALL)
    sku = strip_tags(sku_match.group(1)) if sku_match else ""

    # 3. Categorias
    categories = []
    cat_matches = re.findall(r'<a[^>]*rel="tag"[^>]*>(.*?)</a>', html_content, re.IGNORECASE)
    for cat in cat_matches:
        cleaned_cat = strip_tags(cat)
        if cleaned_cat and cleaned_cat not in categories:
            categories.append(cleaned_cat)
            
    # 4. Descrição Curta / Resumo
    short_desc_match = re.search(r'<div[^>]*class="[^"]*woocommerce-product-details__short-description[^"]*"[^>]*>(.*?)</div>', html_content, re.IGNORECASE | re.DOTALL)
    resumo_bruto = strip_tags(short_desc_match.group(1)) if short_desc_match else ""

    # 5. Descrição Longa / Detalhes
    full_desc_match = re.search(r'<div[^>]*id="tab-description"[^>]*>(.*?)</div>', html_content, re.IGNORECASE | re.DOTALL)
    descricao_bruta = strip_tags(full_desc_match.group(1)) if full_desc_match else ""

    # 6. Tabela de Especificações Técnicas (extração de <tr> e <td>/<th>)
    specs_raw = []
    tr_matches = re.findall(r'<tr[^>]*>(.*?)</tr>', html_content, re.IGNORECASE | re.DOTALL)
    for tr in tr_matches:
        cell_matches = re.findall(r'<(?:td|th)[^>]*>(.*?)</(?:td|th)>', tr, re.IGNORECASE | re.DOTALL)
        if len(cell_matches) >= 2:
            attr = strip_tags(cell_matches[0])
            val = strip_tags(cell_matches[1])
            if attr and val and len(attr) < 100:
                specs_raw.append({"atributo": attr, "valor": val})

    # 7. Imagens (unicidade por basename; ignora logos/selos)
    images = []
    seen_basenames = set()
    skip_tokens = ("logo", "conformite", "europeenne", "selo", "favicon", "sprite")
    img_matches = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', html_content, re.IGNORECASE)
    for src in img_matches:
        if 'wp-content/uploads' not in src:
            continue
        clean_src = src.split('?')[0]
        basename = clean_src.rsplit('/', 1)[-1].lower()
        if any(t in basename for t in skip_tokens):
            continue
        if basename in seen_basenames:
            continue
        seen_basenames.add(basename)
        images.append(clean_src)

    raw_data = {
        "slug": slug,
        "url": url,
        "nome": nome,
        "sku": sku,
        "categorias": categories,
        "resumo_bruto": resumo_bruto,
        "descricao_bruta": descricao_bruta,
        "especificacoes_brutas": specs_raw,
        "imagens": images
    }

    # Salva o arquivo de saída
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, f"{slug}_raw.json")
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(raw_data, f, ensure_ascii=False, indent=2)

    print(f"[OK] Dados brutos salvos com sucesso em: {out_path}")
    return raw_data

if __name__ == '__main__':
    # Teste com o produto #3 da lista (fs-2-250-em)
    test_url = "https://DemoStore.com.br/produto/ventilador-exaustor-axial-250mm-fs-2-250-em/"
    scrape_DemoStore_product(test_url)
