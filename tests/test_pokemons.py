import pytest
from httpx import AsyncClient

from tests.conftest import auth_header, create_test_user, login_user

# uv run pytest tests/test_users.py -v
# uv run pytest tests/test_users.py::test_forgot_password_sends_email -v


@pytest.mark.anyio
async def test_create_pokemon_requires_auth(client: AsyncClient):
    resp = await client.post("/api/v1/pokemons/", json={"pokemon_id": 1})  # no headers
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_create_pokemon_invalid_id(client: AsyncClient):
    user = await create_test_user(client)
    token = await login_user(client)
    headers = auth_header(token)
    resp = await client.post(
        "/api/v1/pokemons/", json={"pokemon_id": 999999}, headers=headers
    )
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_list_pokemons_empty(client: AsyncClient):
    user = await create_test_user(client)
    token = await login_user(client)
    headers = auth_header(token)
    resp = await client.get("/api/v1/pokemons/")
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_get_pokemon_by_id(client: AsyncClient):
    from main import app

    await create_test_user(client)
    token = await login_user(client)
    resp = await client.post(
        "/api/v1/pokemons/", json={"pokemon_id": 1}, headers=auth_header(token)
    )
    created_id = resp.json()["id"]

    app.state.pokeapi_client.get_name.reset_mock()
    app.state.pokeapi_client.get_name.return_value = "bulbasaur"
    resp = await client.get(f"/api/v1/pokemons/{created_id}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "bulbasaur"
    assert resp.json()["pokemon_id"] == 1
    app.state.pokeapi_client.get_name.assert_awaited_once()


@pytest.mark.anyio
async def test_get_pokemon_by_id_not_found(client: AsyncClient):
    resp = await client.get("/api/v1/pokemons/99999")
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_list_pokemons(client: AsyncClient):
    from main import app

    await create_test_user(client)
    token = await login_user(client)
    for pid in (1, 5):
        await client.post(
            "/api/v1/pokemons/", json={"pokemon_id": pid}, headers=auth_header(token)
        )

    app.state.pokeapi_client.get_names.reset_mock()
    app.state.pokeapi_client.get_names.return_value = {1: "bulbasaur", 5: "charmeleon"}
    resp = await client.get("/api/v1/pokemons/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert {p["pokemon_id"] for p in data["pokemons"]} == {1, 5}
    app.state.pokeapi_client.get_names.assert_awaited_once()


@pytest.mark.anyio
async def test_delete_pokemon(client: AsyncClient):
    await create_test_user(client)
    token = await login_user(client)
    resp = await client.post(
        "/api/v1/pokemons/", json={"pokemon_id": 1}, headers=auth_header(token)
    )
    created_id = resp.json()["id"]

    resp = await client.delete(
        f"/api/v1/pokemons/{created_id}", headers=auth_header(token)
    )
    assert resp.status_code == 204

    # gone now
    resp = await client.get(f"/api/v1/pokemons/{created_id}")
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_delete_pokemon_not_owner(client: AsyncClient):
    # owner creates a pokemon
    await create_test_user(client)
    owner_token = await login_user(client)
    resp = await client.post(
        "/api/v1/pokemons/", json={"pokemon_id": 1}, headers=auth_header(owner_token)
    )
    created_id = resp.json()["id"]

    # a different user tries to delete it
    await create_test_user(client, username="thief", email="thief@example.com")
    thief_token = await login_user(client, email="thief@example.com")
    resp = await client.delete(
        f"/api/v1/pokemons/{created_id}", headers=auth_header(thief_token)
    )
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_delete_pokemon_not_found(client: AsyncClient):
    await create_test_user(client)
    token = await login_user(client)
    resp = await client.delete("/api/v1/pokemons/99999", headers=auth_header(token))
    assert resp.status_code == 404  # ← currently 500 until you add the None-check guard


@pytest.mark.anyio
async def test_update_pokemon(client: AsyncClient):
    from main import app

    await create_test_user(client)
    token = await login_user(client)
    resp = await client.post(
        "/api/v1/pokemons/", json={"pokemon_id": 1}, headers=auth_header(token)
    )
    created_id = resp.json()["id"]

    app.state.pokeapi_client.get_name.reset_mock()
    app.state.pokeapi_client.get_name.return_value = "charmeleon"
    resp = await client.patch(
        f"/api/v1/pokemons/{created_id}",
        json={"pokemon_id": 5},
        headers=auth_header(token),
    )
    assert resp.status_code == 200
    assert resp.json()["pokemon_id"] == 5
    assert resp.json()["name"] == "charmeleon"

    app.state.pokeapi_client.get_name.assert_awaited_once()
