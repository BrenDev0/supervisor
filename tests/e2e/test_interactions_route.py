from dotenv import load_dotenv
load_dotenv()
import pytest
from httpx import AsyncClient, ASGITransport
from src.api.server import app
from src.utils.http.get_hmac_header import generate_hmac_headers
import os
from asgi_lifespan import LifespanManager

@pytest.mark.asyncio
async def test_interaction_legal():
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

@pytest.mark.asyncio
async def test_interaction_accounting():
    # Prepare a realistic legal query state
    state = {
        "input": "caules son los mejores practicad de  contabilidad?"
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
            


@pytest.mark.asyncio
async def test_interaction_accounting_data_vis():
    # Prepare a realistic legal query state
    state = {
        "input": "muestrame total bike rentado por el verano como rentales verano, y total bikes rentad por el inveirno como rentales invierno"
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
            

@pytest.mark.asyncio
async def test_interaction_accounting_no_vis():
    # Prepare a realistic legal query state
    state = {
        "input": "cuantos bike fue rentado en total "
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
            
    