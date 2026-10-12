import asyncio
from decimal import Decimal
import httpx

BASE_URL = "http://127.0.0.1:8000/api/v1"

async def test_full_flow():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        # 1. Obtener mesas públicas
        res = await client.get("/mesas")
        mesas = res.json()
        print(f"Total mesas: {len(mesas)}")
        target_mesa = mesas[0]
        mesa_id = target_mesa["id"]
        qr_code = target_mesa["qr_code"]
        print(f"Probando Mesa #{target_mesa['number']} con QR {qr_code}")

        # 2. Obtener un plato del menú
        res = await client.get("/catalogo/platos")
        platos = res.json()
        assert len(platos) > 0
        dish = platos[0]
        print(f"Plato seleccionado: {dish['name']} (ID: {dish['id']}, Base: {dish['price_base']})")

        # 3. Crear orden desde la mesa (cliente)
        order_payload = {
            "codigo_qr": qr_code,
            "items": [
                {
                    "dish_id": dish["id"],
                    "quantity": 2,
                    "observations": "Sin cebolla, urgente",
                    "modifications": []
                }
            ]
        }
        res = await client.post("/ordenes", json=order_payload)
        print("Status POST /ordenes:", res.status_code)
        if res.status_code != 201:
            print("Error:", res.text)
            return
        order = res.json()
        order_id = order["id"]
        print(f"Orden creada exitosamente: ID={order_id}, Subtotal={order['subtotal']}, Total={order['total']}, Status={order['status']}")
        assert float(order["total"]) > 0, "El total de la orden no debe ser 0"

        # 4. Consultar la mesa por QR para confirmar que retorna la orden activa
        res = await client.get(f"/mesas/qr/{qr_code}")
        mesa_info = res.json()
        print(f"Estado de la mesa tras orden: {mesa_info['status']}")
        assert mesa_info["status"] == "OCUPADA"
        assert mesa_info["open_order"] is not None
        print(f"Open Order en mesa: Total={mesa_info['open_order']['total']}, Items={len(mesa_info['open_order']['items'])}")

        # 5. Pagar la orden desde el cliente (pago público)
        total_a_pagar = float(order["total"])
        pay_payload = {
            "codigo_qr": qr_code,
            "payment_method": "EFECTIVO",
            "amount": total_a_pagar,
            "note": "Pago simulado cliente"
        }
        res = await client.post(f"/ordenes/{order_id}/pagos", json=pay_payload)
        print("Status POST /ordenes/{id}/pagos:", res.status_code)
        if res.status_code != 201:
            print("Error pago:", res.text)
            return
        pay_res = res.json()
        print(f"Pago registrado: {pay_res['id']}, Monto={pay_res['amount']}, Status Orden={pay_res.get('order_status')}")

        # 6. Consultar la mesa nuevamente: debe estar LIBRE y sin open_order
        res = await client.get(f"/mesas/qr/{qr_code}")
        mesa_info_post = res.json()
        print(f"Estado mesa post-pago: {mesa_info_post['status']}, Open order: {mesa_info_post['open_order']}")
        assert mesa_info_post["status"] == "LIBRE"
        assert mesa_info_post["open_order"] is None

        print(">>> TODO EL FLUJO TRANSACCIONAL OPERA DE MANERA IMPECABLE <<<")

if __name__ == "__main__":
    asyncio.run(test_full_flow())
