from typing import Annotated
from fastapi import APIRouter, Request, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from services.order import create_order
from services.cart import delete_cart
from schemas.order import TransactionCreate
from config import settings
import httpx
import hashlib
import hmac

router = APIRouter()


@router.post("", status_code=200)
async def webhook_listener(
    request: Request, db: Annotated[AsyncSession, Depends(get_db)]
):
    body = await request.body()

    signature = request.headers.get("x-paystack-signature")

    # verify signature
    try:
        computed_signature = hmac.new(
            settings.paystack_secret_key.get_secret_value().encode(),
            body,
            hashlib.sha512,
        ).hexdigest()
    except Exception as e:
        raise RuntimeError(f"Failed to compute signature{str(e)}")

    if computed_signature != signature:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid signature")

    payload = await request.json()
    event = payload.get("event")

    if event == "charge.success":
        data = payload["data"]
        reference = data["reference"]

        headers = {
            "Authorization": f"Bearer {settings.paystack_secret_key.get_secret_value()}",
            "Accept": "application/json",
        }
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url=f"{settings.paystack_url}/verify/{reference}", headers=headers
                )

                # print("Response text:", response.text)
                if response.status_code == 200:
                    result = response.json()
                    message = result["message"]
                    if not message == "Verification successful":
                        raise HTTPException(
                            status.HTTP_400_BAD_REQUEST, detail="Payment failed"
                        )

                    user_id = data["metadata"]["user_id"]
                    # name = data["metadata"]["name"]
                    reference = data["reference"]
                    email = data["customer"]["email"]
                    amount = data["amount"]
                    order_data = TransactionCreate(
                        user_id=int(user_id),
                        reference=reference,
                        email=email,
                        amount=amount,
                    )
                    await create_order(order_data, db)
                    await delete_cart(user_id, db)
                else:
                    raise HTTPException(
                        status.HTTP_400_BAD_REQUEST, detail="Verification failed"
                    )
        except ConnectionError as e:
            return {"message": f"Connection error: {e}"}

    return {"message": "Successfull"}
