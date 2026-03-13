from typing import Annotated
from fastapi import APIRouter, Request, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.order import create_order
from app.schemas.order import TransactionCreate
from app.config import settings
import httpx
import hashlib
import hmac

router = APIRouter()


@router.post("")
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
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url=f"{settings.paystack_url}/verify/{reference}", headers=headers
            )

            print("Response text:", response.text)
            if response.status_code == 200:
                result = response.json()
                message = result["message"]
                if not message == "Verification successful":
                    raise HTTPException(
                        status.HTTP_400_BAD_REQUEST, detail="Payment failed"
                    )
                print(result)
                # return result
                user_id = data["customer"]["user_id"]
                reference = data["reference"]
                email = data["customer"]["email"]
                amount = data["amount"]
                order_data = TransactionCreate(
                    user_id=int(user_id),
                    reference=reference,
                    email=email,
                    amount=amount,
                )
                await create_order(user_id, order_data, db)
            else:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST, detail="Verification failed"
                )

    return {"message": "Successfull"}
