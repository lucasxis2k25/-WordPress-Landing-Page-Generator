import os
import json
import base64
import urllib.request
import sys

sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(__file__), '..')))

USERNAME = 'lucas'
PASSWORD = 'XcAZ UbJL NkvT jnBB Kdip ST5S'
BASE_URL = 'https://DemoStore.com.br/wp-json/wc/v3'

AUTH_STRING = base64.b64encode(f"{USERNAME}:{PASSWORD}".encode('utf-8')).decode('utf-8')
HEADERS = {
    'Authorization': f'Basic {AUTH_STRING}',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Content-Type': 'application/json'
}

OUTPUT_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'output'))

def get_product_by_slug(slug):
    url = f"{BASE_URL}/products?slug={slug}"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            products = json.loads(resp.read().decode('utf-8'))
            if products:
                return products[0]
    except Exception as e:
        print(f"[!] Erro ao buscar produto por slug '{slug}': {e}")
    return None

def update_product_acf(slug, skip_validation=False, make_draft=False):
    # Regera sempre o payload ACF a partir do JSON de dados se existir, para garantir 100% de sincronicidade
    dados_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'dados', f'{slug}.json'))
    if os.path.exists(dados_path):
        try:
            from gerar_conteudo_acf import gerar_payload_acf, salvar_output
            with open(dados_path, 'r', encoding='utf-8') as df:
                dados_prod = json.load(df)
            payload_fresco = gerar_payload_acf(dados_prod)
            salvar_output(payload_fresco)
            print(f"[OK] Payload ACF regenerado com sucesso para '{slug}' a partir dos dados do JSON.")
        except Exception as e:
            print(f"[!] Aviso ao regerar payload ACF ({e})")

    acf_file = os.path.join(OUTPUT_DIR, f"{slug}_acf.json")
    if not os.path.exists(acf_file):
        print(f"[!] Arquivo ACF payload não encontrado em: {acf_file}")
        return False

    with open(acf_file, 'r', encoding='utf-8') as f:
        payload = json.load(f)

    acf_fields = payload.get('acf', {})
    
    # 1. Busca o produto no WooCommerce
    print(f"[*] Buscando produto no WooCommerce para o slug: {slug}...")
    product = get_product_by_slug(slug)
    if not product:
        print(f"[!] Produto com slug '{slug}' não foi encontrado no WooCommerce de DemoStore.com.br.")
        return False

    product_id = product['id']
    wp_name = product.get('name', '')
    wp_sku = (product.get('sku') or '').strip().upper()
    expected_sku = (payload.get('sku') or '').strip().upper()
    print(f"[OK] Produto encontrado! ID WooCommerce: {product_id} - Nome: {wp_name}")

    # Bloqueia publish se o SKU do WP não bater com o JSON (ex: VMBT publicado no slug VM)
    if expected_sku and wp_sku and expected_sku != wp_sku:
        print(f"[!] BLOQUEADO: SKU mismatch. JSON={expected_sku} WP={wp_sku} (slug={slug}).")
        return False
    if expected_sku and expected_sku not in wp_name.upper().replace(' ', ''):
        # nome_wp às vezes contém outra variante (VM vs VMBT)
        def _compact(s):
            return (
                (s or "")
                .upper()
                .replace(" ", "")
                .replace("/", "")
                .replace("-", "")
                .replace("_", "")
            )
        sku_compact = _compact(expected_sku)
        name_compact = _compact(wp_name)
        if sku_compact not in name_compact and expected_sku.split()[-1].replace("-", "") not in name_compact:
            print(f"[!] BLOQUEADO: nome WP '{wp_name}' nao corresponde ao SKU '{expected_sku}'.")
            return False

    # Gate pos-geracao: revalida payload textual se JSON de dados existir
    if not skip_validation:
        try:
            from regras import validar_produto_completo
            dados_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'dados', f'{slug}.json'))
            if os.path.exists(dados_path):
                with open(dados_path, 'r', encoding='utf-8') as df:
                    dados = json.load(df)
                ok, erros = validar_produto_completo(dados, sanitizar=False)
                if not ok:
                    print("[!] BLOQUEADO pela validacao pos-geracao:")
                    for e in erros:
                        print(f"    {e}")
                    return False
        except Exception as e:
            print(f"[!] Aviso: nao foi possivel revalidar dados ({e})")

    # 2. Prepara os campos ACF (meta_data)
    meta_data = []
    for field_key, field_value in acf_fields.items():
        meta_data.append({
            "key": field_key,
            "value": field_value
        })

    # Adiciona Schemas JSON-LD
    if 'schema_jsonld' in payload:
        meta_data.append({"key": "sp_schema_product", "value": payload['schema_jsonld'].get('product', '')})
        meta_data.append({"key": "sp_schema_faq", "value": payload['schema_jsonld'].get('faq', '')})

    update_payload = {
        "meta_data": meta_data,
        "description": acf_fields.get("sp_resumo_tecnico", "")
    }

    # 3. Envia atualização via WooCommerce REST API em lotes pequenos para evitar WAF/ModSecurity 403
    update_url = f"{BASE_URL}/products/{product_id}"
    chunk_size = 5
    print(f"[*] Enviando atualização automática para o WordPress (Produto ID #{product_id})...")


    if make_draft:
        print(f"[*] Revertendo produto para Rascunho (Produto ID #{product_id})...")
        try:
            draft_payload = json.dumps({"status": "draft"}, ensure_ascii=False).encode('utf-8')
            req_draft = urllib.request.Request(update_url, data=draft_payload, headers=HEADERS, method='PUT')
            with urllib.request.urlopen(req_draft, timeout=15) as resp:
                print("[OK] Produto revertido para rascunho com sucesso no WordPress!")
                return True
        except Exception as e:
            print(f"[!] Erro ao reverter para rascunho: {e}")
            return False
            
    # Primeiro atualiza a descrição e status do produto
    try:
        desc_payload = json.dumps({"description": acf_fields.get("sp_resumo_tecnico", ""), "status": "publish"}, ensure_ascii=False).encode('utf-8')
        req_desc = urllib.request.Request(update_url, data=desc_payload, headers=HEADERS, method='PUT')
        with urllib.request.urlopen(req_desc, timeout=15) as resp:
            pass
    except Exception as e:
        print(f"[!] Aviso na descrição: {e}")

    # Envia os campos meta_data em lotes
    for i in range(0, len(meta_data), chunk_size):
        chunk = meta_data[i:i + chunk_size]
        update_payload = {"meta_data": chunk}
        json_bytes = json.dumps(update_payload, ensure_ascii=False).encode('utf-8')
        req = urllib.request.Request(update_url, data=json_bytes, headers=HEADERS, method='PUT')
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                res_data = json.loads(resp.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            print(f"[!] Erro HTTP {e.code} ao enviar lote {i//chunk_size + 1}: {e.read().decode('utf-8')}")
            return False
        except Exception as e:
            print(f"[!] Erro ao atualizar lote {i//chunk_size + 1}: {e}")
            return False

    print(f"\n============================================================")
    print(f"[OK] SUCESSO TOTAL! O Produto #{product_id} ('{res_data['name']}') FOI PUBLICADO E ATUALIZADO AUTOMATICAMENTE NO WORDPRESS!")
    print(f"Link do produto: {res_data.get('permalink')}")
    print(f"============================================================\n")
    return True

if __name__ == '__main__':
    import sys
    
    skip_val = '--skip-validation' in sys.argv
    make_draft = '--draft' in sys.argv
    args = [a for a in sys.argv[1:] if a not in ('--skip-validation', '--draft')]
    
    if len(args) > 0:
        arg = args[0]
        # Se passaram o caminho do arquivo JSON, extrai o slug
        if arg.endswith('.json'):
            slug = os.path.basename(arg).replace('.json', '')
            if slug.endswith('_acf'):
                slug = slug.replace('_acf', '')
        else:
            slug = arg
    else:
        slug = "ventilador-exaustor-axial-500mm-fs-4-500-et"
        
    success = update_product_acf(slug, skip_validation=skip_val, make_draft=make_draft)
    if not success:
        sys.exit(1)
