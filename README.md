# 🚀 WordPress Landing Page Generator

> Geração automática de landing pages de produto com IA (Gemini ou Claude) + publicação direta no WooCommerce via REST API.

---

## 📋 O que é este projeto

Ferramenta Python para automatizar a criação de landing pages de produto com conteúdo técnico e SEO otimizado para lojas WooCommerce. O pipeline:

1. **Raspa** os dados atuais do produto na loja
2. **Gera** textos, schemas JSON-LD e campos ACF via IA
3. **Valida** o conteúdo com regras de negócio configuráveis
4. **Publica** diretamente na API REST do WooCommerce

Compatível com **Google Gemini** e **Anthropic Claude** — você escolhe qual usar no `.env`.

---

## 🗂️ Estrutura do Projeto

```
.
├── dashboard.py              # Painel Streamlit de gestão
├── gerador/
│   ├── config.py             # Configuração central (IA + WooCommerce)
│   ├── auth.py               # Autenticação de usuários do painel
│   ├── regras.py             # Regras de validação de produto
│   ├── normalizadores.py     # Normalização de dados
│   ├── renderizador.py       # Geração de HTML/Schema dos blocos
│   ├── gerar_lpp_ia.py       # ⭐ Script principal: gera conteúdo via IA
│   ├── gerar_conteudo_acf.py # Geração de campos ACF
│   ├── processar.py          # Pipeline interativo de processamento
│   ├── catalogo.py           # Catálogo de produtos de exemplo
│   ├── texto_pt.py           # Utilitários de texto em PT-BR
│   ├── automacao/
│   │   ├── builder.py        # Constrói JSON limpo do produto
│   │   ├── scraper.py        # Scraping de dados do produto
│   │   └── publicar_wordpress.py  # Publicação via REST API
│   └── revisao/              # Módulo de revisão e aprovação
├── ecommerce-core/           # Plugin WordPress customizado
├── mapeamento de produto/    # Pipeline de mapeamento de catálogo
├── requirements.txt
├── .env.example              # Template de configuração
└── iniciar_dashboard.bat     # Atalho Windows para o painel
```

---

## ⚙️ Configuração

### 1. Clone e instale dependências

```bash
git clone https://github.com/seu-usuario/seu-repositorio.git
cd seu-repositorio
pip install -r requirements.txt
```

### 2. Crie o arquivo `.env`

```bash
cp .env.example .env
```

---

## 🤖 Configurando a IA

Edite o `.env` e escolha **uma** das opções:

### Opção A — Google Gemini (padrão)

1. Acesse [aistudio.google.com](https://aistudio.google.com) e crie uma API Key gratuita
2. No `.env`:

```env
GEMINI_API_KEY=AIzaSy...sua_chave_aqui
```

### Opção B — Anthropic Claude

1. Acesse [console.anthropic.com](https://console.anthropic.com) e crie uma API Key
2. Instale a biblioteca extra:

```bash
pip install anthropic
```

3. No `.env`:

```env
ANTHROPIC_API_KEY=sk-ant-...sua_chave_aqui
AI_PROVIDER=claude
```

> **Como o projeto decide qual IA usar:**
> - Se `AI_PROVIDER=claude` → usa Claude
> - Se `AI_PROVIDER=gemini` → usa Gemini
> - Se `AI_PROVIDER` não estiver definido → usa Gemini se tiver `GEMINI_API_KEY`, senão tenta Claude
> - Se ambas as chaves estiverem presentes → `AI_PROVIDER` decide (padrão: gemini)

---

## 🔌 Configurando o WooCommerce

No painel WordPress:

1. Vá em **Usuários → Seu perfil → Application Passwords**
2. Crie uma nova senha de aplicação (ex: `"Content Bot"`)
3. No `.env`:

```env
WP_USERNAME=seu_usuario
WP_APP_PASSWORD=xxxx xxxx xxxx xxxx xxxx xxxx
WP_BASE_URL=https://seu-site.com
```

---

## 🚀 Como usar

### Painel interativo (recomendado)

```bash
streamlit run dashboard.py
# ou no Windows:
iniciar_dashboard.bat
```

Acesse `http://localhost:8501` no navegador.

**Usuários de demonstração:**

| Login | Senha | Perfil |
|-------|-------|--------|
| `admin` | `admin123` | Administrador |
| `editor` | `editor123` | Editor |
| `viewer` | `viewer123` | Visualizador |

> ⚠️ Altere as senhas em `gerador/auth.py` antes de usar em produção.

---

### Geração via linha de comando

```bash
# Gera conteúdo para um produto pelo slug
python gerador/gerar_lpp_ia.py nome-do-produto

# Pipeline interativo (mostra catálogo e permite escolher)
python gerador/processar.py

# Geração de campos ACF
python gerador/gerar_conteudo_acf.py nome-do-produto
```

---

## 🔄 Trocando de Gemini para Claude (ou vice-versa)

Basta alterar o `.env` — não precisa mudar nenhum código:

```env
# Para usar Claude:
AI_PROVIDER=claude
ANTHROPIC_API_KEY=sk-ant-...

# Para voltar ao Gemini:
AI_PROVIDER=gemini
GEMINI_API_KEY=AIzaSy...
```

O `config.py` detecta automaticamente e inicializa o cliente correto.

---

## 🔌 Plugin WordPress

A pasta `ecommerce-core/` contém um plugin WordPress. Para instalar:

1. Copie a pasta para `wp-content/plugins/ecommerce-core/`
2. Ative em **Plugins → Plugins instalados**

---

## 📦 Dependências

| Pacote | Uso |
|--------|-----|
| `streamlit` | Painel interativo |
| `google-generativeai` | Geração com Gemini |
| `anthropic` | Geração com Claude *(instalar separado se usar Claude)* |
| `requests` | Integração REST API WooCommerce |
| `openpyxl` | Leitura/escrita de planilhas |

```bash
pip install -r requirements.txt
# Se usar Claude:
pip install anthropic
```

---

## 📄 Licença

MIT — use, adapte e contribua livremente.
