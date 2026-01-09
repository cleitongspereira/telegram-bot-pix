from fastapi import FastAPI, HTTPException
import requests
import os

app = FastAPI()

ASAAS_API_KEY = os.getenv("ASAAS_API_KEY")
ASAAS_URL = "https://api.asaas.com/v3"

HEADERS = {
    "access_token": ASAAS_API_KEY,
    "Content-Type": "application/json"
}

@app.post("/payments/create")
def create_payment(data: dict):
    payload = {
        "customer": data["customer_id"],
        "billingType": "PIX",
        "value": data["value"],
        "description": data.get("description", "Pagamento via Telegram")
    }

    r = requests.post(
        f"{ASAAS_URL}/payments",
        json=payload,
        headers=HEADERS
    )

    if r.status_code != 200:
        raise HTTPException(status_code=400, detail=r.text)

    p = r.json()

    return {
        "payment_id": p["id"],
        "qr_code": p["pixTransaction"]["qrCodeImage"],
        "pix_code": p["pixTransaction"]["payload"]
    }


@app.get("/payments/status/{payment_id}")
def payment_status(payment_id: str):
    r = requests.get(
        f"{ASAAS_URL}/payments/{payment_id}",
        headers=HEADERS
    )

    if r.status_code != 200:
        raise HTTPException(status_code=400, detail=r.text)

    status = r.json()["status"]

    return {
        "status": "paid" if status in ["RECEIVED", "CONFIRMED"] else "pending"
    }
