# 🚀 Santander Dev Week 2023 — Pipeline ETL com IA Generativa

Projeto desenvolvido durante a **Santander Dev Week 2023** na [DIO](https://dio.me).  
Implementa um pipeline **ETL completo** que consome a API do Santander, enriquece os dados com IA generativa e devolve o resultado à origem.

---

## 📐 Arquitetura

```
SDW2023.csv  (lista de IDs)
      │
      ▼
┌──────────────┐
│  EXTRAÇÃO    │  GET /users/{id} → busca dados de cada cliente na API
└──────┬───────┘
       │
       ▼
┌──────────────────┐
│  TRANSFORMAÇÃO   │  Claude (Anthropic API) gera mensagem personalizada
│  (IA Generativa) │  sobre investimentos para cada cliente
└──────┬───────────┘
       │
       ▼
┌──────────────┐
│ CARREGAMENTO │  PUT /users/{id} → salva a mensagem no campo "news" da API
└──────────────┘
       │
       └─ Se a API estiver fora do ar: salva resultado em resultado_etl.json
```

---

## 📁 Estrutura

```
santander-etl/
├── SDW2023.csv          # IDs dos usuários (entrada)
├── etl.py               # Pipeline ETL completo
├── resultado_etl.json   # Saída gerada quando a API está fora do ar
└── README.md
```

---

## ▶️ Executando

### 1. Repositório
```bash
git clone https://github.com/seu-usuario/santander-etl.git
cd santander-etl
```

### 2. Chave da Anthropic (opcional)
Sem a chave o pipeline roda com mensagens padrão — ótimo para testes.

```bash
# Linux / macOS
export ANTHROPIC_API_KEY="sk-ant-..."

# Windows (PowerShell)
$env:ANTHROPIC_API_KEY="sk-ant-..."
```

### 3. Executar
```bash
python etl.py
```

---

## 🔄 Comportamento com a API fora do ar

A API pública (`sdw-2023-prd.up.railway.app`) foi descontinuada. O script lida com isso automaticamente:

| Situação | Extração | Carregamento |
|----------|----------|--------------|
| API disponível | GET /users/{id} | PUT /users/{id} |
| API fora do ar | Dados fictícios (fallback) | Salva `resultado_etl.json` |

O fluxo ETL funciona nos dois casos — o aprendizado é o mesmo.

---

## 📊 Exemplo de Saída (`resultado_etl.json`)

```json
[
  {
    "id": 1,
    "name": "Ana Lima",
    "account": { "balance": 2500.0, "limit": 500.0 },
    "card": { "limit": 3000.0 },
    "news": [
      {
        "icon": "https://.../icons/credit.svg",
        "description": "Ana, invista hoje para garantir um futuro seguro e próspero!"
      }
    ]
  }
]
```

---

## 🛠 Tecnologias

- **Python 3.11+** — apenas bibliotecas padrão (`csv`, `json`, `urllib`)
- **Claude Sonnet (Anthropic API)** — geração de mensagens personalizadas
- **Santander Dev Week 2023 API** — fonte e destino dos dados
- Sem dependências externas (sem `pandas`, sem `requests`)

---

## 💡 Conceitos Demonstrados

| Conceito | Onde |
|----------|------|
| Pipeline ETL | Funções `extrair`, `transformar`, `carregar` |
| Consumo de API REST | `urllib.request` — GET e PUT |
| IA Generativa | Prompt engineering com Claude |
| Fallback gracioso | Funciona mesmo sem API disponível |
| Variáveis de ambiente | `os.getenv` para a chave da API |
| Tratamento de erros | `try/except` em todas as chamadas de rede |

---

Baseado no projeto original da [DIO — Santander Dev Week 2023](https://github.com/falvojr/santander-dev-week-2023).  
Feito com 🧡 por Algarve94

