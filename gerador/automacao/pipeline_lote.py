import os
import sys
import csv

# Adiciona o diretório pai ao sys.path para importar módulos do gerador
sys.path.append(os.path.dirname(__file__))

from scraper import scrape_DemoStore_product
from builder import build_clean_json

PAGINAS_CSV = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..', 'Dados GA4', 'Páginas.csv'))

def process_batch(limit=5):
    """
    Lê o arquivo de Páginas.csv e executa o pipeline completo (Scraper + Builder) para as N primeiras URLs de produtos.
    """
    print(f"[*] Iniciando processamento em lote (Limite: {limit} produtos)...")
    
    if not os.path.exists(PAGINAS_CSV):
        print(f"[!] Arquivo CSV de páginas não encontrado em: {PAGINAS_CSV}")
        return

    processed_count = 0
    with open(PAGINAS_CSV, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader, None)
        
        for row in reader:
            if not row:
                continue
            url = row[0].strip()
            
            # Filtra apenas URLs de produtos
            if '/produto/' in url:
                print(f"\n--------------------------------------------------")
                print(f"[{processed_count + 1}/{limit}] Processando: {url}")
                
                # Step 1: Scraping do site oficial
                raw_data = scrape_DemoStore_product(url)
                if raw_data:
                    # Step 2: Geração do JSON limpo formatado
                    clean_data = build_clean_json(raw_data['slug'])
                    if clean_data:
                        processed_count += 1
                        
                if processed_count >= limit:
                    break

    print(f"\n[OK] Processamento concluído! Total de produtos processados: {processed_count}")

if __name__ == '__main__':
    limit_arg = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    process_batch(limit=limit_arg)
