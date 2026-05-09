"""
Santander Dev Week 2023 — Pipeline ETL com IA Generativa
=========================================================
Fluxo:
  EXTRAÇÃO   → Lê IDs do CSV e busca dados de cada usuário via GET na API
  TRANSFORMAÇÃO → Usa Claude (Anthropic) para gerar mensagem personalizada
  CARREGAMENTO → Envia a mensagem de volta à API via PUT no campo "news"

Como a API pública pode estar fora do ar, o script tem fallback automático:
  - Se a API responder: fluxo completo (GET → IA → PUT)
  - Se a API estiver fora do ar: usa dados fictícios e salva resultado em JSON local
"""

import csv
import json
import os
import urllib.request
import urllib.error

# ==============================================================
# CONFIGURAÇÃO
# ==============================================================
SDW_API_URL   = "https://sdw-2023-prd.up.railway.app"
ARQUIVO_CSV   = "SDW2023.csv"
ARQUIVO_SAIDA = "resultado_etl.json"

# Cole sua chave aqui OU defina a variável de ambiente ANTHROPIC_API_KEY
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "SUA_CHAVE_AQUI")

# Dados fictícios usados quando a API está fora do ar
USUARIOS_FALLBACK = [
    {
        "id": 1,
        "name": "Ana Lima",
        "account": {"number": "001-1", "agency": "0001", "balance": 2500.0, "limit": 500.0},
        "card": {"number": "1234 **** **** 5678", "limit": 3000.0},
        "news": [],
    },
    {
        "id": 2,
        "name": "Bruno Souza",
        "account": {"number": "002-2", "agency": "0001", "balance": 8900.5, "limit": 2000.0},
        "card": {"number": "9012 **** **** 3456", "limit": 10000.0},
        "news": [],
    },
    {
        "id": 3,
        "name": "Carla Mendes",
        "account": {"number": "003-3", "agency": "0001", "balance": 450.75, "limit": 200.0},
        "card": {"number": "7890 **** **** 1234", "limit": 1000.0},
        "news": [],
    },
]


# ==============================================================
# ETAPA 1 — EXTRAÇÃO
# ==============================================================
def ler_ids_do_csv(caminho: str) -> list:
    """Lê o arquivo CSV e retorna a lista de IDs de usuário."""
    ids = []
    with open(caminho, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for linha in reader:
            ids.append(int(linha["UserID"]))
    return ids


def buscar_usuario_api(user_id: int):
    """Faz GET /users/{id} na API. Retorna None se a API estiver indisponível."""
    url = f"{SDW_API_URL}/users/{user_id}"
    try:
        with urllib.request.urlopen(url, timeout=8) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


def extrair(caminho_csv: str):
    """
    Tenta buscar os usuários na API a partir dos IDs do CSV.
    Se a API estiver fora do ar, usa dados fictícios (fallback).
    Retorna (lista_de_usuarios, api_disponivel).
    """
    print("[EXTRAÇÃO] Lendo IDs do CSV...")
    ids = ler_ids_do_csv(caminho_csv)
    print(f"           IDs encontrados: {ids}")

    print("[EXTRAÇÃO] Consultando a API da Santander Dev Week 2023...")
    usuarios = []
    for uid in ids:
        usuario = buscar_usuario_api(uid)
        if usuario:
            usuarios.append(usuario)
            print(f"  ✔ ID {uid} — {usuario['name']} obtido da API.")
        else:
            print(f"  ✗ ID {uid} — API indisponível.")

    if not usuarios:
        print("[EXTRAÇÃO] API fora do ar. Usando dados fictícios (fallback).")
        return USUARIOS_FALLBACK, False

    return usuarios, True


# ==============================================================
# ETAPA 2 — TRANSFORMAÇÃO
# ==============================================================
def gerar_mensagem_ia(usuario: dict) -> str:
    """
    Chama a API da Anthropic (Claude) para criar uma mensagem personalizada.
    Se a chave não estiver configurada, usa mensagem padrão.
    """
    if ANTHROPIC_API_KEY == "SUA_CHAVE_AQUI":
        return (
            f"{usuario['name']}, cada investimento que você faz hoje "
            f"é um passo em direção ao seu futuro. Conte com o Santander!"
        )

    prompt = (
        f"Você é especialista em marketing bancário do Santander. "
        f"Crie UMA mensagem curta (máximo 100 caracteres) e motivacional "
        f"sobre investimentos para o cliente abaixo.\n"
        f"Nome: {usuario['name']}\n"
        f"Saldo: R$ {usuario['account']['balance']:.2f}\n"
        f"Limite do cartão: R$ {usuario['card']['limit']:.2f}\n"
        f"Responda APENAS com a mensagem, sem aspas, sem prefixos."
    )

    payload = json.dumps({
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 100,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["content"][0]["text"].strip()
    except urllib.error.HTTPError as e:
        print(f"  [AVISO] Erro HTTP {e.code} na IA. Usando mensagem padrão.")
    except Exception as e:
        print(f"  [AVISO] {e}. Usando mensagem padrão.")

    return f"{usuario['name']}, invista hoje para garantir um futuro seguro e próspero!"


def transformar(usuarios: list) -> list:
    """Gera uma mensagem personalizada e adiciona ao campo 'news' de cada usuário."""
    print("\n[TRANSFORMAÇÃO] Gerando mensagens com IA...")
    icon_url = "https://digitalinnovationone.github.io/santander-dev-week-2023-api/icons/credit.svg"

    for usuario in usuarios:
        mensagem = gerar_mensagem_ia(usuario)
        usuario["news"].append({"icon": icon_url, "description": mensagem})
        print(f"  ✔ {usuario['name']}: {mensagem}")

    return usuarios


# ==============================================================
# ETAPA 3 — CARREGAMENTO
# ==============================================================
def atualizar_usuario_api(usuario: dict) -> bool:
    """Faz PUT /users/{id} com os dados atualizados. Retorna True se sucesso."""
    url = f"{SDW_API_URL}/users/{usuario['id']}"
    payload = json.dumps(usuario).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="PUT",
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            return resp.status == 200
    except Exception:
        return False


def carregar(usuarios: list, api_disponivel: bool) -> None:
    """
    Se a API estiver disponível: envia os dados atualizados via PUT.
    Caso contrário: salva o resultado em um arquivo JSON local.
    """
    if api_disponivel:
        print("\n[CARREGAMENTO] Enviando mensagens de volta à API...")
        for usuario in usuarios:
            ok = atualizar_usuario_api(usuario)
            status = "✔ Atualizado" if ok else "✗ Falhou"
            print(f"  {status}: {usuario['name']}")
    else:
        print(f"\n[CARREGAMENTO] API indisponível. Salvando resultado em '{ARQUIVO_SAIDA}'...")
        with open(ARQUIVO_SAIDA, "w", encoding="utf-8") as f:
            json.dump(usuarios, f, ensure_ascii=False, indent=2)
        print(f"  ✔ Arquivo '{ARQUIVO_SAIDA}' gerado com sucesso.")


# ==============================================================
# PIPELINE PRINCIPAL
# ==============================================================
if __name__ == "__main__":
    print("=" * 55)
    print("  PIPELINE ETL — SANTANDER DEV WEEK 2023")
    print("=" * 55)

    usuarios, api_disponivel = extrair(ARQUIVO_CSV)
    usuarios = transformar(usuarios)
    carregar(usuarios, api_disponivel)

    print("=" * 55)
    print("  Pipeline concluído com sucesso! ✅")
    print("=" * 55)
