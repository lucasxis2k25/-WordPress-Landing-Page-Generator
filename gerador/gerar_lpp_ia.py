# -*- coding: utf-8 -*-
"""
Demo Store — AUTOMATED LPP GENERATION VIA GEMINI API
Generates the validated technical copy directly using the official product datasheet PDF.
"""
import os
import sys
import json
import time

# Adiciona o diretório atual e subdiretórios ao sys.path
GERADOR_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(GERADOR_DIR)
AUTOMACAO_DIR = os.path.join(GERADOR_DIR, "automacao")
sys.path.insert(0, GERADOR_DIR)
sys.path.insert(0, AUTOMACAO_DIR)

from config import get_gemini_api_key, DB_PATH
from regras import validar_produto_completo, sanitizar_produto
from scraper import scrape_DemoStore_product

try:
    import google.generativeai as genai
except ImportError:
    print("Biblioteca google-generativeai não encontrada. Instale com: pip install google-generativeai")
    sys.exit(1)


def generate_lpp_via_gemini(slug):
    # 1. Carrega banco de dados de produtos para checar configurações
    if not os.path.exists(DB_PATH):
        print(f"[!] Banco de dados local não encontrado em: {DB_PATH}")
        sys.exit(1)

    with open(DB_PATH, "r", encoding="utf-8") as f:
        db = json.load(f)

    if slug not in db:
        print(f"[!] Produto com slug '{slug}' não encontrado no banco de dados.")
        sys.exit(1)

    entry = db[slug]
    nome_prod = entry.get("nome", slug)
    sku_prod = entry.get("sku", "")
    pdf_file = entry.get("datasheet_file", "")
    mercado_db = entry.get("mercado", "")
    aplicacoes_db = entry.get("aplicacoes", [])

    print(f"[*] Iniciando geração automática para: {nome_prod}")
    print(f"[*] SKU: {sku_prod} | PDF: {pdf_file or 'Nenhum'}")

    # 2. Garante raspagem inicial das informações atuais da página (se existirem)
    scraped_json_path = os.path.join(AUTOMACAO_DIR, "scraped_data", f"{slug}_raw.json")
    if not os.path.exists(scraped_json_path):
        url = f"https://DemoStore.com.br/produto/{slug}/"
        print(f"[*] Dados brutos não encontrados localmente. Raspando página atual: {url}...")
        scrape_DemoStore_product(url)

    raw_scraped_data = {}
    if os.path.exists(scraped_json_path):
        with open(scraped_json_path, "r", encoding="utf-8") as f:
            raw_scraped_data = json.load(f)

    # 3. Configura a API do Gemini
    api_key = get_gemini_api_key()
    if not api_key or api_key == "sua_chave_gemini" or not api_key.startswith("AIzaSy"):
        print("[!] Chave API do Gemini inválida ou ausente no arquivo .env (deve começar com 'AIzaSy').")
        sys.exit(3)

    genai.configure(api_key=api_key)

    # 4. Upload de datasheet PDF (se disponível)
    uploaded_file = None
    if pdf_file:
        pdf_path = os.path.join(GERADOR_DIR, "datasheets", pdf_file)
        if os.path.exists(pdf_path):
            print(f"[*] Enviando datasheet PDF para processamento: {pdf_file}...")
            try:
                uploaded_file = genai.upload_file(pdf_path)
                print(f"[*] Upload concluído. URI: {uploaded_file.uri}")
                # Espera processamento básico
                while uploaded_file.state.name == "PROCESSING":
                    print("[*] Processando arquivo no Gemini...")
                    time.sleep(1)
                    uploaded_file = genai.get_file(uploaded_file.name)
                print("[*] Arquivo processado com sucesso!")
            except Exception as e:
                print(f"[!] Erro ao subir PDF para o Gemini: {e}. Prosseguindo sem PDF...")
                uploaded_file = None
        else:
            print(f"[!] Arquivo PDF {pdf_file} não encontrado na pasta gerador/datasheets/. Prosseguindo sem PDF...")

    # 5. Constrói o Super-Prompt de geração técnica de LPP
    system_instruction = """
Você é o Engenheiro Sênior de Aplicação e Copywriter B2B da Sell-Parts Brasil.
Sua missão é gerar os dados estruturados de uma landing page técnica de alta conversão para o produto especificado.

Você deve respeitar RIGOROSAMENTE as seguintes regras:
1. TOM REALISTA E SEM EXAGEROS: Nunca use jargões hiperbólicos como "resfriamento de missão crítica", "perdas incalculáveis", "tornou-se o padrão da indústria", "garantir máxima proteção", "alto rendimento", "excelente desempenho" ou "alta performance". Foque em fatos técnicos comprovados e aplicações reais.
2. ZERO INFERÊNCIA: Não invente dados técnicos (tensão, corrente, potência, rotação, vazão, ruído, IP, temperatura de operação). Use estritamente o que estiver contido no documento PDF (datasheet) anexado ou nas especificações raspadas do site. Se faltar, deixe o valor em branco ou omitido.
3. PADRONIZAÇÃO TIPOGRÁFICA DE UNIDADES: Números devem ser separados da unidade por um espaço obrigatório.
   Exemplos corretos: "250 mm", "70 W", "220 V", "68 dBA", "240 m³/h", "3200 RPM".
   *ATENÇÃO*: O nível de ruído acústico DEVE ser grafado como "dBA" (com 'A' maiúsculo).
4. ESTRUTURA OBRIGATÓRIA DE QUANTIDADES (REGRA DE FERRO):
   - 'resumo_tecnico': Exatamente 2 parágrafos curtos.
     *Formato de Abertura*: A primeira frase do primeiro parágrafo deve começar exatamente citando o produto usando a estrutura:
     "O [Nome do Produto] – [Modelo] é um..." (usando travessão en-dash '–', e NUNCA incluir texto explícito '(SKU ...)').
     O resumo deve focar em aplicação, benefício operacional e construção mecânica, SEM repetir valores numéricos detalhados que já aparecem na tabela de Especificações.
   - 'hero_checklist': Exatamente 3 itens no topo destacando diferenciais B2B rápidos (ex: "Regime S1 – Operação Contínua", "Bi-Tensão 110/220 V (Facilidade de Integração)", "Suporte Técnico Especializado Sell-Parts"). Não repita valores numéricos exatos de especificações.
   - 'beneficios': Exatamente 4 cards. Mínimo de 80 caracteres cada. Cada benefício deve terminar com uma conclusão ÚNICA (proibido ter sufixos ou conclusões idênticas em múltiplos cards).
   - 'diferenciais': Exatamente 4 itens de texto. Mínimo de 50 caracteres cada. OBRIGATÓRIO incluir pelo menos 1 item contendo prova de marca e confiança citando explicitamente a Sell-Parts e seu suporte técnico especializado de engenharia. Não repita frases dos benefícios.
   - 'mercados': Exatamente 6 setores/indústrias que demandam o produto (ex: "Siderurgia, Metalurgia, Usinagem e Indústria pesada", "Fabricantes OEM...", "Painéis elétricos..."). NUNCA listar equipamentos físicos nesta seção.
   - 'aplicacoes_categoria': Objeto contendo 'titulo', 'intro' e 'cards' (lista de exatamente 4 cards contendo 'titulo' e 'descricao'). Títulos devem focar no uso técnico / equipamentos reais (evaporadores, inversores, etc.) e descrições secas e diretas. SEM marketing ou verbos de marketing genéricos ("Atua na...", "Garante...", "Proporciona...").
   - 'aplicacoes_equipamento': Objeto contendo 'titulo', 'intro' e 'cards' (lista de exatamente 4 cards contendo 'titulo' e 'descricao') detalhando onde se instala o equipamento.
   - 'faq': Exatamente 3 perguntas. Mínimo de 120 caracteres por resposta. Devem cobrir dúvidas B2B reais (substituição/manutenção, mancais/vida útil, comparação elétrica/voltagens, cuidados de instalação). Não ecoar apenas os dados numéricos brutos na resposta de forma superficial.
5. PALAVRAS E FRASES ESTRITAMENTE PROIBIDAS (NÃO PODEM CONTER EM NENHUM CAMPO PÚBLICO):
   "Faturamento", "Faturamos", "CNPJ", "Revendas", "Nota Fiscal", "transportadora parceira com rastreamento", "o envio é realizado via transportadora".
6. MARCAS CONCORRENTES: Não cite nomes de concorrentes em campos públicos (como ebm-papst, ziehl-abegg, sunon, metaltex, weiguang, adda, asten, elgin, danfoss, brahex).
7. EMOJIS: É estritamente proibido o uso de qualquer emoji nos blocos de texto gerados.
"""

    prompt = f"""
Gere o JSON completo para o produto com os seguintes metadados básicos:
- Slug: {slug}
- Nome: {nome_prod}
- SKU: {sku_prod}
- Categoria original do painel: {entry.get("categoria", "")}

Informações raspadas da página atual:
{json.dumps(raw_scraped_data, ensure_ascii=False, indent=2)}

Foco de Mercado Adicional (se disponível):
{mercado_db if mercado_db else "Usar mercado-padrão de fabricantes OEM, painéis elétricos, sistemas de potência, refrigeração comercial e automação."}

Aplicações sugeridas (se disponível):
{", ".join(aplicacoes_db) if aplicacoes_db else "Detectar do datasheet ou usar aplicações correspondentes à família técnica."}

Use o documento PDF anexado como a fonte primária e infalível para as especificações técnicas (especificacoes). Todos os dados técnicos elétricos e mecânicos (vazão, corrente, potência, rotação, IP, ruído, etc.) confirmados no PDF devem ser gerados com confiança '100%' e fonte 'Datasheet Oficial Sell-Parts'.

Gere a resposta EXATAMENTE no formato JSON com a estrutura mostrada no exemplo abaixo. Não inclua comentários nem tags markdown adicionais fora da estrutura JSON esperada:

{{
  "slug": "{slug}",
  "nome": "{nome_prod}",
  "sku": "{sku_prod}",
  "categoria": "Nome da Categoria",
  "familia": "Familia tecnica do produto (ex: ventilador_axial, ventilador_centrifugo, micro_ventilador, radial, inline, gabinete_ventilacao, soprador_axial)",
  "resumo_tecnico": "Parágrafo 1\\n\\nParágrafo 2",
  "hero_checklist": [
    "Item 1",
    "Item 2",
    "Item 3"
  ],
  "meta_description": "Meta descrição contendo especificação técnica separada por espaço da unidade e terminada com ponto final.",
  "especificacoes": [
    {{
      "atributo": "Nome do atributo",
      "valor": "Valor formatado com espaço e unidade (ex: 220 V)",
      "campo": "nome_do_campo",
      "confianca": "100%",
      "fonte": "Datasheet Oficial Sell-Parts"
    }}
  ],
  "beneficios": [
    {{
      "titulo": "Benefício 1",
      "descricao": "Descrição detalhada (mínimo 80 caracteres)."
    }},
    {{
      "titulo": "Benefício 2",
      "descricao": "Descrição detalhada (mínimo 80 caracteres)."
    }},
    {{
      "titulo": "Benefício 3",
      "descricao": "Descrição detalhada (mínimo 80 caracteres)."
    }},
    {{
      "titulo": "Benefício 4",
      "descricao": "Descrição detalhada (mínimo 80 caracteres)."
    }}
  ],
  "diferenciais": [
    "Diferencial 1 (mínimo 50 caracteres)",
    "Diferencial 2 (mínimo 50 caracteres)",
    "Diferencial 3 (mínimo 50 caracteres)",
    "Diferencial 4 (mínimo 50 caracteres, citando Sell-Parts e seu suporte técnico especializado de engenharia)"
  ],
  "mercados": [
    "Setor 1",
    "Setor 2",
    "Setor 3",
    "Setor 4",
    "Setor 5",
    "Setor 6"
  ],
  "aplicacoes_categoria": {{
    "titulo": "Aplicações do [Nome do Produto]",
    "intro": "Introdução curta.",
    "cards": [
      {{
        "titulo": "Equipamento 1",
        "descricao": "Uso técnico seco e direto."
      }},
      {{
        "titulo": "Equipamento 2",
        "descricao": "Uso técnico seco e direto."
      }},
      {{
        "titulo": "Equipamento 3",
        "descricao": "Uso técnico seco e direto."
      }},
      {{
        "titulo": "Equipamento 4",
        "descricao": "Uso técnico seco e direto."
      }}
    ]
  }},
  "aplicacoes_equipamento": {{
    "titulo": "Onde usar o [Nome/SKU do Produto]",
    "intro": "Introdução curta.",
    "cards": [
      {{
        "titulo": "Equipamento A",
        "descricao": "Detalhes de instalação ou uso real."
      }},
      {{
        "titulo": "Equipamento B",
        "descricao": "Detalhes de instalação ou uso real."
      }},
      {{
        "titulo": "Equipamento C",
        "descricao": "Detalhes de instalação ou uso real."
      }},
      {{
        "titulo": "Equipamento D",
        "descricao": "Detalhes de instalação ou uso real."
      }}
    ]
  }},
  "faq": [
    {{
      "pergunta": "Pergunta 1?",
      "resposta": "Resposta longa e explicativa (mínimo 120 caracteres)."
    }},
    {{
      "pergunta": "Pergunta 2?",
      "resposta": "Resposta longa e explicativa (mínimo 120 caracteres)."
    }},
    {{
      "pergunta": "Pergunta 3?",
      "resposta": "Resposta longa e explicativa (mínimo 120 caracteres)."
    }}
  ],
  "is_similar_to": [
    "Termo similar 1",
    "Termo similar 2"
  ],
  "alerta_tecnico": "Texto explicativo para orientação de instalação elétrica (obrigatório aviso sobre ligação estrela/triângulo para trifásicos e aviso geral para monofásicos).",
  "alerta_tabela": "Nota sobre conformidade dos dados na tabela.",
  "pdf_fonte": "{pdf_file if pdf_file else slug + '.pdf'}"
}}
"""

    print("[*] Chamando API do Gemini...")
    try:
        model_name = "gemini-1.5-pro"
        try:
            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system_instruction
            )
            content_parts = []
            if uploaded_file:
                content_parts.append(uploaded_file)
            content_parts.append(prompt)

            response = model.generate_content(
                content_parts,
                generation_config={"response_mime_type": "application/json"}
            )
        except Exception as e_pro:
            msg = str(e_pro).lower()
            if "api key not valid" in msg or "api_key_invalid" in msg or "invalid api key" in msg:
                raise e_pro
            print(f"[*] Falha ao usar {model_name} ({e_pro}). Tentando fallback para gemini-1.5-flash...")
            model_name = "gemini-1.5-flash"
            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system_instruction
            )
            content_parts = []
            if uploaded_file:
                content_parts.append(uploaded_file)
            content_parts.append(prompt)

            response = model.generate_content(
                content_parts,
                generation_config={"response_mime_type": "application/json"}
            )

        # Deleta o arquivo temporário da nuvem para segurança
        if uploaded_file:
            try:
                genai.delete_file(uploaded_file.name)
                print("[*] Arquivo temporário removido da nuvem com sucesso.")
            except Exception as ex:
                print(f"[!] Aviso: erro ao apagar arquivo temporário: {ex}")

        # 6. Processa resposta do Gemini
        raw_json_str = response.text.strip()
        data = json.loads(raw_json_str)

        # 7. Sanitização local prévia
        sanitizar_produto(data)

        # 8. Executa as validações da Regra de Ferro
        is_valid, validation_errors = validar_produto_completo(data, sanitizar=True)

        # Salva o arquivo em gerador/dados/
        out_path = os.path.join(DADOS_DIR, f"{slug}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"[OK] JSON gerado com sucesso e salvo em: {out_path}")

        if not is_valid:
            print("\n[!] AVISO: O conteúdo foi gerado, mas falhou em algumas regras de validação:")
            for err in validation_errors:
                print(f"  - {err}")
            # Retorna False indicando pendências
            return False, validation_errors
        else:
            print("\n[OK] 100% VALIDADO! Produto passou em todos os gates de qualidade.")
            # Atualiza o status no DB para revisão se estiver pendente
            if entry.get("status") in ["pendente", "pesquisa_pendente", "em_producao", ""]:
                db[slug]["status"] = "em_revisao"
                with open(DB_PATH, "w", encoding="utf-8") as f:
                    json.dump(db, f, ensure_ascii=False, indent=2)
            return True, []

    except Exception as e:
        msg = str(e).lower()
        if "api key not valid" in msg or "api_key_invalid" in msg or "invalid api key" in msg or "keynotfound" in msg:
            print("[!] Erro de Chave API: A chave API do Gemini configurada é inválida ou expirou.")
            if uploaded_file:
                try:
                    genai.delete_file(uploaded_file.name)
                except:
                    pass
            sys.exit(3)

        print(f"[!] Falha catastrófica durante a geração: {e}")
        # Limpa arquivo temporário em caso de falha
        if uploaded_file:
            try:
                genai.delete_file(uploaded_file.name)
            except:
                pass
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python gerar_lpp_ia.py <slug-do-produto>")
        sys.exit(1)

    target_slug = sys.argv[1]
    ok, errors = generate_lpp_via_gemini(target_slug)
    if not ok:
        sys.exit(2)  # Código de saída 2 indica falha na validação das regras
    sys.exit(0)
