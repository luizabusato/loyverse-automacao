import requests
import time
import logging
from datetime import datetime

# ============================================================
# COLE SEU TOKEN AQUI (só você vê este arquivo)
# ============================================================
TOKEN = "COLE_SEU_TOKEN_AQUI"
# ============================================================

BASE_URL = "https://api.loyverse.com/v1.0"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}
INTERVALO_MINUTOS = 30  # verifica a cada 30 minutos

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    handlers=[
        logging.FileHandler("automacao.log"),
        logging.StreamHandler()
    ]
)

def buscar_todos_itens():
    """Busca todos os itens do Loyverse."""
    itens = []
    cursor = None

    while True:
        params = {"limit": 250}
        if cursor:
            params["cursor"] = cursor

        response = requests.get(f"{BASE_URL}/items", headers=HEADERS, params=params)
        
        if response.status_code != 200:
            logging.error(f"Erro ao buscar itens: {response.status_code} - {response.text}")
            break

        data = response.json()
        itens.extend(data.get("items", []))

        cursor = data.get("cursor")
        if not cursor:
            break

    return itens

def ocultar_item(item):
    """Marca o item como não disponível para venda."""
    payload = {
        "item_name": item["item_name"],
        "available_for_sale": False
    }

    response = requests.post(
        f"{BASE_URL}/items/{item['id']}",
        headers=HEADERS,
        json=payload
    )

    if response.status_code == 200:
        logging.info(f"✅ Ocultado: {item['item_name']} (estoque zerado)")
    else:
        logging.error(f"❌ Erro ao ocultar {item['item_name']}: {response.status_code} - {response.text}")

def reativar_item(item):
    """Marca o item como disponível para venda."""
    payload = {
        "item_name": item["item_name"],
        "available_for_sale": True
    }

    response = requests.post(
        f"{BASE_URL}/items/{item['id']}",
        headers=HEADERS,
        json=payload
    )

    if response.status_code == 200:
        logging.info(f"🟢 Reativado: {item['item_name']} (estoque reposto)")
    else:
        logging.error(f"❌ Erro ao reativar {item['item_name']}: {response.status_code} - {response.text}")

def verificar_estoque(item):
    """Retorna o estoque total do item somando todas as variantes."""
    total = 0
    for variante in item.get("variants", []):
        stores = variante.get("stores", [])
        for store in stores:
            in_stock = store.get("in_stock") or 0
            total += in_stock
    return total

def rodar_verificacao():
    """Verifica todos os itens e oculta/reativa conforme estoque."""
    logging.info("🔍 Iniciando verificação de estoque...")
    itens = buscar_todos_itens()
    logging.info(f"Total de itens encontrados: {len(itens)}")

    ocultados = 0
    reativados = 0

    for item in itens:
        # Ignora itens que não controlam estoque
        if not item.get("track_stock"):
            continue

        estoque = verificar_estoque(item)
        disponivel = item.get("available_for_sale", True)

        if estoque <= 0 and disponivel:
            ocultar_item(item)
            ocultados += 1

        elif estoque > 0 and not disponivel:
            reativar_item(item)
            reativados += 1

    logging.info(f"✅ Verificação concluída — Ocultados: {ocultados} | Reativados: {reativados}")

def main():
    logging.info("🚀 Sistema de automação de estoque iniciado!")
    logging.info(f"⏱️ Verificando a cada {INTERVALO_MINUTOS} minutos")

    while True:
        try:
            rodar_verificacao()
        except Exception as e:
            logging.error(f"Erro inesperado: {e}")

        logging.info(f"⏳ Próxima verificação em {INTERVALO_MINUTOS} minutos...")
        time.sleep(INTERVALO_MINUTOS * 60)

if __name__ == "__main__":
    main()
