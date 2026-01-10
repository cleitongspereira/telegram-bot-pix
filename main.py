from fastapi import FastAPI, HTTPException
import requests
import os
from datetime import date, timedelta

app = FastAPI()

# =========================
# Configurações Asaas
# =========================

ASAAS_API_KEY = os.getenv("ASAAS_API_KEY")
ASAAS_URL = "https://api.asaas.com/v3"

HEADERS = {
    "access_token": ASAAS_API_KEY,
    "Content-Type": "application/json"
}

# =========================
# Utilidades
# =========================

def criar_customer(telegram_user_id: int, cpf_cnpj: str) -> str:
    payload = {
        "name": f"Telegram User {telegram_user_id}",
        "cpfCnpj": cpf_cnpj
    }

    r = requests.post(
        f"{ASAAS_URL}/customers",
        json=payload,
        headers=HEADERS,
        timeout=15
    )

    if r.status_code not in (200, 201):
        raise HTTPException(
            status_code=400,
            detail=f"Erro ao criar customer: {r.text}"
        )

    return r.json()["id"]


def criar_pagamento_pix(customer_id: str, value: float, description: str) -> str:
    due_date = (date.today() + timedelta(days=1)).isoformat()

    payload = {
        "customer": customer_id,
        "billingType": "PIX",
        "value": value,
        "dueDate": due_date,
        "description": description
    }

    r = requests.post(
        f"{ASAAS_URL}/payments",
        json=payload,
        headers=HEADERS,
        timeout=15
    )

    if r.status_code not in (200, 201):
        raise HTTPException(
            status_code=400,
            detail=f"Erro ao criar pagamento: {r.text}"
        )

    return r.json()["id"]


def obter_pix(payment_id: str) -> dict:
    r = requests.get(
        f"{ASAAS_URL}/payments/{payment_id}/pixQrCode",
        headers=HEADERS,
        timeout=15
    )

    if r.status_code != 200:
        raise HTTPException(
            status_code=400,
            detail=f"Erro ao obter Pix: {r.text}"
        )

    pix = r.json()

    return {
        "qr_code": pix["encodedImage"],
        "pix_code": pix["payload"]
    }


# =========================
# Endpoints
# =========================

@app.post("/payments/create")
def create_payment(data: dict):
    """
    Cria uma cobrança Pix no Asaas e retorna:
    - payment_id
    - QR Code (base64)
    - Pix copia e cola
    """

    # Validações básicas
    if "telegram_user_id" not in data:
        raise HTTPException(status_code=400, detail="telegram_user_id é obrigatório")

    if "cpf_cnpj" not in data:
        raise HTTPException(status_code=400, detail="cpf_cnpj é obrigatório")

    if "value" not in data or data["value"] < 5:
        raise HTTPException(
            status_code=400,
            detail="O valor mínimo para Pix é R$ 5,00"
        )

    telegram_user_id = data["telegram_user_id"]
    cpf_cnpj = data["cpf_cnpj"]
    value = float(data["value"])
    description = data.get("description", "Pagamento via Telegram")

    # 1. Cria customer
    customer_id = criar_customer(
        telegram_user_id=telegram_user_id,
        cpf_cnpj=cpf_cnpj
    )

    # 2. Cria pagamento
    payment_id = criar_pagamento_pix(
        customer_id=customer_id,
        value=value,
        description=description
    )

    # 3. Obtém QR Code Pix
    pix = obter_pix(payment_id)

    return {
        "payment_id": payment_id,
        "qr_code": pix["qr_code"],
        "pix_code": pix["pix_code"]
    }


@app.get("/payments/status/{payment_id}")
def payment_status(payment_id: str):
    """
    Consulta o status do pagamento no Asaas
    """

    r = requests.get(
        f"{ASAAS_URL}/payments/{payment_id}",
        headers=HEADERS,
        timeout=15
    )

    if r.status_code != 200:
        raise HTTPException(
            status_code=400,
            detail=f"Erro ao consultar pagamento: {r.text}"
        )

    status_asaas = r.json()["status"]

    if status_asaas in ("RECEIVED", "CONFIRMED"):
        return {"status": "paid"}

    return {"status": "pending"}
