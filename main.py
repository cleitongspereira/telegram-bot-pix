from fastapi import FastAPI, HTTPException
import requests
import os
from datetime import date, timedelta

app = FastAPI()

ASAAS_API_KEY = os.getenv("ASAAS_API_KEY")
ASAAS_URL = "https://api.asaas.com/v3"

HEADERS = {
    "access_token": ASAAS_API_KEY,
    "Content-Type": "application/json"
}

@app.post("/payments/create")
def create_payment(data: dict):
    # LOG simples
    print("Dados recebidos:", data)

    customer_payload = {
        "name": f"Telegram User {data.get('telegram_user_id')}",
        "cpfCnpj": data["cpf_cnpj"]
    }

    print("Criando customer:", customer_payload)

    r_customer = requests.post(
        f"{ASAAS_URL}/customers",
        json=customer_payload,
        headers=HEADERS
    )

    print("Resposta customer:", r_customer.status_code, r_customer.text)

    if r_customer.status_code not in [200, 201]:
        raise HTTPException(status_code=400, detail=r_customer.text)

    customer_id = r_customer.json()["id"]

    due_date = (date.today() + timedelta(days=1)).isoformat()

    payment_payload = {
        "customer": customer_id,
        "billingType": "PIX",
        "value": data["value"],
        "dueDate": due_date,
        "description": data.get("description", "Pagamento via Telegram")
    }

    print("Criando pagamento:", payment_payload)

    r_payment = requests.post(
        f"{ASAAS_URL}/payments",
        json=payment_payload,
        headers=HEADERS
    )

    print("Resposta pagamento:", r_payment.status_code, r_payment.text)

    if r_payment.status_code not in [200, 201]:
        raise HTTPException(status_code=400, detail=r_payment.text)

    p = r_payment.json()

    return {
        "payment_id": p["id"],
        "qr_code": p["pixTransaction"]["qrCodeImage"],
        "pix_code": p["pixTransaction"]["payload"]
    }
