import pytest
from httpx import AsyncClient

from tests.conftest import auth_header, create_test_user, login_user

# uv run pytest tests/test_users.py -v
# uv run pytest tests/test_users.py::test_forgot_password_sends_email -v


## Test Create User Validation Error
@pytest.mark.anyio
async def test_create_user_validation_error(client: AsyncClient):
    response = await client.post(
        "/api/v1/users/",
        json={
            "username": "testuser",
        },
    )

    assert response.status_code == 422
    assert "email" in response.text
    assert "password" in response.text


## Test Create User Duplicate Email
@pytest.mark.anyio
async def test_create_user_duplicate_email(client: AsyncClient):
    await create_test_user(client)

    response = await client.post(
        "/api/v1/users/",
        json={
            "username": "different_user",
            "email": "test@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Email test@example.com already exists"


## Test Create User Success
@pytest.mark.anyio
async def test_create_user_success(client: AsyncClient):
    response = await client.post(
        "/api/v1/users/",
        json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "securepassword123",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "newuser@example.com"
    assert "id" in data
    assert "password" not in data
    assert "password_hash" not in data


# Me Endpoints left for practice testing
@pytest.mark.anyio
async def test_me_fail(client: AsyncClient):
    response = await client.get("/api/v1/users/me")
    print(response.headers.get("allow"))

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    response = await client.patch("/api/v1/users/me/password")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


# Me
@pytest.mark.anyio
async def test_me_successful(client: AsyncClient):
    await create_test_user(client)
    token = await login_user(client)
    header = auth_header(token)

    response = await client.get("/api/v1/users/me", headers=header)
    print(response.headers.get("allow"))

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert "id" in data
    assert "password" not in data
    assert "password_hash" not in data

    response = await client.patch(
        "/api/v1/users/me/password",
        json={"current_password": "testpassword123", "new_password": "newpassword123"},
        headers=header,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Password changed successfully"

    # old password now rejected
    resp = await client.post(
        "/api/v1/users/token",
        data={"username": "test@example.com", "password": "testpassword123"},
    )
    assert resp.status_code == 401
    # new password works
    assert await login_user(client, password="newpassword123")


@pytest.mark.anyio
async def test_create_user_one_pokemon(client: AsyncClient):
    from main import app

    # 1. Create a user and log in
    user = await create_test_user(client)
    token = await login_user(client)
    headers = auth_header(token)

    # 2. Add two pokemon (attached to the logged-in user via the token)
    resp = await client.post(
        "/api/v1/pokemons/",
        json={"pokemon_id": 1},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text

    # 3. Stub the external PokeAPI names (keyed by pokemon_id, as the service uses them)
    # Mocking
    app.state.pokeapi_client.get_names.reset_mock()
    app.state.pokeapi_client.get_names.return_value = {1: "bulbasaur"}

    # 4. Hit the user-centric route with the real user id
    response = await client.get(f"/api/v1/users/{user['id']}/pokemon")
    assert response.status_code == 200

    data = response.json()

    # user appears once at the top
    assert data["user"]["id"] == user["id"]
    assert data["total"] == 1

    # 5. Validate names without depending on ordering
    names_by_id = {p["pokemon_id"]: p["name"] for p in data["pokemons"]}
    assert names_by_id == {1: "bulbasaur"}

    # and confirm owner was stripped from each entry (PokemonForOwner shape)
    assert all("owner" not in p for p in data["pokemons"])
    app.state.pokeapi_client.get_names.assert_awaited_once()


@pytest.mark.anyio
async def test_create_user_multiple_pokemon(client: AsyncClient):
    from main import app

    # 1. Create a user and log in
    user = await create_test_user(client)
    token = await login_user(client)
    headers = auth_header(token)

    # 2. Add two pokemon (attached to the logged-in user via the token)
    for pokemon_id in (1, 5, 7, 10):
        resp = await client.post(
            "/api/v1/pokemons/",
            json={"pokemon_id": pokemon_id},
            headers=headers,
        )
        assert resp.status_code == 201, resp.text

    # 3. Stub the external PokeAPI names (keyed by pokemon_id, as the service uses them)
    # Mocking
    app.state.pokeapi_client.get_names.reset_mock()
    app.state.pokeapi_client.get_names.return_value = {
        1: "bulbasaur",
        5: "charmeleon",
        7: "squirtle",
        10: "caterpie",
    }

    # 4. Hit the user-centric route with the real user id
    response = await client.get(f"/api/v1/users/{user['id']}/pokemon")
    assert response.status_code == 200

    data = response.json()

    # user appears once at the top
    assert data["user"]["id"] == user["id"]
    assert data["total"] == 4

    # 5. Validate names without depending on ordering
    names_by_id = {p["pokemon_id"]: p["name"] for p in data["pokemons"]}
    assert names_by_id == {
        1: "bulbasaur",
        5: "charmeleon",
        7: "squirtle",
        10: "caterpie",
    }

    # and confirm owner was stripped from each entry (PokemonForOwner shape)
    assert all("owner" not in p for p in data["pokemons"])
    app.state.pokeapi_client.get_names.assert_awaited_once()


@pytest.mark.anyio
async def test_update_partial_username(client: AsyncClient):
    user = await create_test_user(client)
    token = await login_user(client)

    resp = await client.patch(
        f"/api/v1/users/{user['id']}",  # adjust to your actual update route
        json={"username": "updated_name"},
        headers=auth_header(token),
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["username"] == "updated_name"  # will fail: value gets hashed


@pytest.mark.anyio
async def test_update_other_user_forbidden(client: AsyncClient):
    owner = await create_test_user(client)  # id belongs to testuser
    # a second user, logged in
    await create_test_user(client, username="other", email="other@example.com")
    other_token = await login_user(client, email="other@example.com")

    resp = await client.patch(
        f"/api/v1/users/{owner['id']}",
        json={"username": "hacked"},
        headers=auth_header(other_token),
    )
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_login_wrong_password(client: AsyncClient):
    await create_test_user(client)
    resp = await client.post(
        "/api/v1/users/token",
        data={"username": "test@example.com", "password": "wrongpassword"},
    )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Incorrect email or password"


@pytest.mark.anyio
async def test_change_password_wrong_current(client: AsyncClient):
    await create_test_user(client)
    token = await login_user(client)
    resp = await client.patch(
        "/api/v1/users/me/password",
        json={"current_password": "WRONG", "new_password": "newpassword123"},
        headers=auth_header(token),
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Current password is incorrect"
