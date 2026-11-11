import os

os.environ["DATABASE_URL"] = "sqlite:///./test_restaurant.db"
os.environ["SEED_DATA"] = "false"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture()
def client():
    Base.metadata.drop_all(bind=engine)
    with TestClient(app) as c:
        yield c


def _restaurant(client, **overrides):
    body = {"name": "Test Kitchen", "cuisine": "Indian", "city": "Pune", "address": "Kothrud"}
    body.update(overrides)
    return client.post("/api/v1/restaurants", json=body).json()


def test_health(client):
    assert client.get("/health/live").json()["status"] == "UP"
    assert client.get("/health/ready").json()["status"] == "READY"


def test_create_and_search_restaurant(client):
    r = _restaurant(client)
    assert r["id"] > 0
    assert len(client.get("/api/v1/restaurants?city=pune").json()) == 1
    assert client.get("/api/v1/restaurants?city=Delhi").json() == []


def test_menu_and_validate_order(client):
    r = _restaurant(client)
    item = client.post(f"/api/v1/restaurants/{r['id']}/menu-items",
                       json={"name": "Thali", "price": "150.50"}).json()
    res = client.post(f"/api/v1/restaurants/{r['id']}/validate-order",
                      json={"items": [{"menu_item_id": item["id"], "quantity": 2}]})
    assert res.status_code == 200
    assert res.json()["total_amount"] == "301.00"


def test_validate_rejects_unavailable_and_closed(client):
    r = _restaurant(client)
    item = client.post(f"/api/v1/restaurants/{r['id']}/menu-items",
                       json={"name": "Thali", "price": "150"}).json()
    client.patch(f"/api/v1/menu-items/{item['id']}", json={"is_available": False})
    res = client.post(f"/api/v1/restaurants/{r['id']}/validate-order",
                      json={"items": [{"menu_item_id": item["id"], "quantity": 1}]})
    assert res.status_code == 422

    client.patch(f"/api/v1/restaurants/{r['id']}/status", json={"is_open": False})
    res = client.post(f"/api/v1/restaurants/{r['id']}/validate-order",
                      json={"items": [{"menu_item_id": item["id"], "quantity": 1}]})
    assert res.status_code == 409


def test_unknown_restaurant_404(client):
    assert client.get("/api/v1/restaurants/999").status_code == 404
