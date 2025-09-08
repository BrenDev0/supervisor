from dotenv import load_dotenv
load_dotenv()
import pytest
from httpx import AsyncClient, ASGITransport
from src.api.server import app
from src.utils.http.get_hmac_header import generate_hmac_headers
import os
from asgi_lifespan import LifespanManager

@pytest.mark.asyncio
async def test_interaction():
    # Prepare a realistic legal query state
    state = {
        "input": "¿Cuál es la primera articulo del CONSTITUCIÓN POLÍTICA DE LOS ESTADOS UNIDOS MEXICANOS"
    }

    headers = {
        "Authorization": f"Bearer {os.getenv("TEST_TOKEN")}"
    }
    
    async with LifespanManager(app):

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/interactions/secure/0e4c6ce5-0cae-436c-bbd1-62201a422ac6",
                headers=headers,
                json=state
            )

            data = response.json()
            print(data)
            assert response.status_code == 202
            

    