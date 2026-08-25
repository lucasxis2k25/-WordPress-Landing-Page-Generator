import os
import json
import shutil
import difflib

def main():
    PROJ_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    GERADOR_DIR = os.path.join(PROJ_DIR, "gerador")
    DB_PATH = os.path.join(GERADOR_DIR, "produtos_db.json")
    DATASHEETS_DIR = os.path.join(GERADOR_DIR, "datasheets")

    if not os.path.exists(DB_PATH) or not os.path.exists(DATASHEETS_DIR):
        print("Erro: Diretório de datasheets ou banco de dados não encontrado.")
        return

    with open(DB_PATH, "r", encoding="utf-8") as f:
        db = json.load(f)

    # Pegar todos os slugs e nomes para facilitar o match
    slugs = []
    nomes = []
    slug_map = {}
    for prod in db.values():
        s = prod.get("slug")
        n = prod.get("nome")
        if s and n:
            slugs.append(s)
            nomes.append(n)
            slug_map[s] = prod
            slug_map[n] = prod

    pdfs = [f for f in os.listdir(DATASHEETS_DIR) if f.lower().endswith(".pdf")]
    renamed_count = 0

    print("Iniciando padronização de Datasheets...\n")

    for pdf in pdfs:
        # Se o PDF já é exatamente o nome de um slug, ignorar
        pdf_name_no_ext = pdf[:-4]
        if pdf_name_no_ext in slugs:
            continue
        
        # Estratégia 1: 'Contains' - Se o slug estiver contido no nome do pdf ou vice-versa
        match_found = False
        for s in slugs:
            # limpar hifens para facilitar
            s_clean = s.replace("-", "").lower()
            p_clean = pdf_name_no_ext.replace("-", "").replace(" ", "").lower()
            if s_clean in p_clean or p_clean in s_clean:
                novo_nome = s + ".pdf"
                os.rename(os.path.join(DATASHEETS_DIR, pdf), os.path.join(DATASHEETS_DIR, novo_nome))
                print(f"RENOMEADO (Contains): '{pdf}' -> '{novo_nome}'")
                renamed_count += 1
                match_found = True
                break
        
        if match_found:
            continue
            
        # Estratégia 2: Fuzzy Matching (Similaridade Alta)
        # Comparar com os slugs
        matches = difflib.get_close_matches(pdf_name_no_ext.lower().replace(" ", "-"), slugs, n=1, cutoff=0.7)
        if matches:
            novo_nome = matches[0] + ".pdf"
            os.rename(os.path.join(DATASHEETS_DIR, pdf), os.path.join(DATASHEETS_DIR, novo_nome))
            print(f"RENOMEADO (Fuzzy): '{pdf}' -> '{novo_nome}'")
            renamed_count += 1
            continue

    print(f"\nConcluído! {renamed_count} arquivos renomeados com sucesso para o padrão de slugs do site.")

if __name__ == "__main__":
    main()
