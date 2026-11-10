import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app

@pytest.mark.asyncio
async def test_root():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:

        response = await client.get("/")

    assert response.status_code == 200