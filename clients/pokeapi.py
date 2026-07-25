import asyncio

import httpx

from config import settings


class PokeAPIClient:
    def __init__(self, base_url: str = settings.external_api_url, timeout: float = 5.0):
        # One shared client → connection pooling across all requests.
        self._client = httpx.AsyncClient(base_url=base_url, timeout=timeout)
        self._cache: dict[int, str | None] = {}

    async def get_name(self, pokemon_id: int) -> str | None:  # pragma: no cover
        if pokemon_id in self._cache:
            return self._cache[pokemon_id]

        try:
            response = await self._client.get(f"/pokemon/{pokemon_id}")
            response.raise_for_status()
            name = response.json()["name"]
        except httpx.HTTPError, KeyError:
            # API down, timeout, 404, unexpected shape → don't crash the endpoint.
            name = None

        self._cache[pokemon_id] = name
        return name

    async def get_names(
        self, pokemon_ids: list[int]
    ) -> dict[int, str | None]:  # pragma: no cover
        # Deduplicate first — a page may hold the same pokemon_id many times
        # (several users caught the same species).
        unique_ids = list(set(pokemon_ids))
        results = await asyncio.gather(*(self.get_name(pid) for pid in unique_ids))
        return dict(zip(unique_ids, results))

    async def close(self) -> None:  # pragma: no cover
        await self._client.aclose()
