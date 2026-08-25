# 🛍️ E-commerce Content & Dashboard Suite

> Pipeline de geração de conteúdo com IA + painel de gestão para lojas WooCommerce.

---

## 📋 Sobre o Projeto

Suite de ferramentas Python para automatizar a criação, enriquecimento e publicação de conteúdo de produtos em lojas WooCommerce, integrada a um painel interativo Streamlit para gestão e monitoramento.

Desenvolvido para cenários reais de e-commerce B2B com catálogos grandes e necessidade de padronização de conteúdo.

---

## 🚀 Funcionalidades

- **Dashboard interativo** (Streamlit) com visão geral do catálogo
- **Gerador de conteúdo com IA** (Google Gemini) para títulos, descrições e campos SEO
- **Integração WooCommerce** via REST API (leitura e publicação)
- **Pipeline de mapeamento de produtos** com validação e auditoria
- **Módulo WordPress plugin** (`ecommerce-core`) com hooks e templates customizados
- **Scripts utilitários**: geração de PDF, limpeza e normalização de dados

---

## 🗂️ Estrutura do Projeto

```
.
├── dashboard.py              # Painel principal (Streamlit)
├── ecommerce-core/           # Plugin WordPress customizado
│   ├── assets/
│   ├── hooks/
│   ├── inc/
│   └── templates/
├── gerador/                  # Scripts de geração de conteúdo
│   ├── automacao/            # Pipeline de publicação automática
│   ├── revisao/              # Módulo de revisão e aprovação
│   ├── tests/                # Testes de integração com WP API
│   ├── auth.py               # Autenticação WooCommerce
│   ├── config.py             # Configurações globais
│   ├── gerar_conteudo_acf.py # Geração via ACF fields
│   ├── gerar_lpp_ia.py       # Geração de LPP com IA
│   ├── normalizadores.py     # Normalização de dados
│   ├── regras.py             # Regras de negócio e validação
│   └── renderizador.py       # Renderização de templates
├── mapeamento de produto/    # Pipeline de mapeamento de catálogo
│   ├── mapping/              # Lógica de mapeamento
│   ├── scripts/              # Scripts auxiliares
│   └── tests/                # Testes unitários
├── scripts/                  # Utilitários gerais
│   ├── gerar_pdf.py
│   └── toolbox.py
├── requirements.txt
└── .env.example
```

---

## ⚙️ Configuração

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/seu-repositorio.git
cd seu-repositorio
```

### 2. Instale as dependências

```bash
pip install -r requirements.txt
```

### 3. Configure as variáveis de ambiente

```bash
cp .env.example .env
```

Edite o `.env` com suas credenciais:

```env
# WordPress / WooCommerce REST API
WP_USERNAME=seu_usuario
WP_APP_PASSWORD=sua_application_password
WP_BASE_URL=https://seu-site.com

# Google Gemini (opcional — enriquece texto de mercado)
GEMINI_API_KEY=sua_chave_gemini
```

### 4. Inicie o painel

```bash
streamlit run dashboard.py
```

Ou use o script de atalho (Windows):

```bash
iniciar_dashboard.bat
```

---

## 🔌 Plugin WordPress

A pasta `ecommerce-core/` contém um plugin WordPress customizado. Para instalar:

1. Copie a pasta para `wp-content/plugins/`
2. Ative o plugin no painel do WordPress

---

## 🧪 Testes

```bash
# Testes de integração WooCommerce API
python -m pytest gerador/tests/

# Testes do pipeline de mapeamento
python -m pytest "mapeamento de produto/tests/"
```

---

## 📦 Dependências Principais

| Pacote | Uso |
|--------|-----|
| `streamlit` | Painel interativo |
| `google-generativeai` | Geração de conteúdo com IA |
| `requests` | Integração REST API |
| `openpyxl` | Leitura/escrita de planilhas |

Ver lista completa em [`requirements.txt`](requirements.txt).

---

## 📄 Licença

MIT — sinta-se livre para usar e adaptar.
