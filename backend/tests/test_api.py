"""Tests for the StockRoom API."""


def test_health_returns_healthy(client):
    """The liveness endpoint answers with the code 200."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_ready_checks_the_database(client):
    """The readiness endpoint answers with the code 200 when the database is available."""
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["database"] == "connected"


def test_list_items_is_empty_at_the_start(client):
    """A new database contains no items."""
    response = client.get("/api/items")
    assert response.status_code == 200
    assert response.json() == []


def test_create_item(client, sample_item):
    """A POST request makes a new item."""
    response = client.post("/api/items", json=sample_item)
    assert response.status_code == 201
    body = response.json()
    assert body["id"] > 0
    assert body["sku"] == sample_item["sku"]
    assert body["stock_value"] == 108.0
    assert body["low_stock"] is False


def test_create_item_rejects_a_duplicate_sku(client, sample_item):
    """The API refuses a second item with the same SKU."""
    assert client.post("/api/items", json=sample_item).status_code == 201
    response = client.post("/api/items", json=sample_item)
    assert response.status_code == 409


def test_get_item_by_id(client, sample_item):
    """A GET request gives one item."""
    item_id = client.post("/api/items", json=sample_item).json()["id"]
    response = client.get(f"/api/items/{item_id}")
    assert response.status_code == 200
    assert response.json()["name"] == sample_item["name"]


def test_get_item_gives_404_for_an_unknown_id(client):
    """The API answers with the code 404 when the item does not exist."""
    assert client.get("/api/items/9999").status_code == 404


def test_update_item_changes_the_quantity(client, sample_item):
    """A PUT request changes the quantity and the low stock state."""
    item_id = client.post("/api/items", json=sample_item).json()["id"]
    response = client.put(f"/api/items/{item_id}", json={"quantity": 10})
    assert response.status_code == 200
    body = response.json()
    assert body["quantity"] == 10
    assert body["low_stock"] is True


def test_delete_item(client, sample_item):
    """A DELETE request removes the item."""
    item_id = client.post("/api/items", json=sample_item).json()["id"]
    assert client.delete(f"/api/items/{item_id}").status_code == 204
    assert client.get(f"/api/items/{item_id}").status_code == 404


def test_stats_gives_the_totals(client, sample_item):
    """The statistics endpoint counts the items, the units and the low stock items."""
    client.post("/api/items", json=sample_item)
    client.post(
        "/api/items",
        json={
            "name": "Steel washer",
            "sku": "WASH-01",
            "category": "fasteners",
            "quantity": 5,
            "unit_price": 2.00,
            "reorder_level": 20,
        },
    )
    client.post(
        "/api/items",
        json={
            "name": "Cable tie",
            "sku": "TIE-200",
            "category": "consumables",
            "quantity": 1000,
            "unit_price": 0.02,
            "reorder_level": 100,
        },
    )

    body = client.get("/api/items/stats").json()
    assert body["total_items"] == 3
    assert body["total_units"] == 1245
    assert body["total_value"] == 138.0
    assert body["low_stock_items"] == 1
    assert body["categories"] == 2


def test_filter_by_low_stock(client, sample_item):
    """The list endpoint can give only the items below the reorder level."""
    client.post("/api/items", json=sample_item)
    client.post(
        "/api/items",
        json={"name": "Steel washer", "sku": "WASH-01", "quantity": 5, "reorder_level": 20},
    )
    response = client.get("/api/items", params={"low_stock": "true"})
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["sku"] == "WASH-01"


def test_metrics_endpoint_is_prometheus_format(client):
    """The metrics endpoint gives text in the Prometheus format."""
    client.get("/health")
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text
