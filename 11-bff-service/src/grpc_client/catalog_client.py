"""HTTP client for Catalog service."""

import logging
import aiohttp
from typing import Optional

logger = logging.getLogger(__name__)


class CatalogHttpClient:
    """Client for Catalog service HTTP API."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')

    async def get_products(
        self,
        seller_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> dict:
        """Get products for a seller."""
        url = f"{self.base_url}/products?seller_id={seller_id}&limit={limit}&offset={offset}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    elif resp.status == 404:
                        return {"products": [], "total": 0, "skip": offset, "limit": limit}
                    else:
                        body = await resp.text()
                        logger.error("Catalog API error: %d - %s", resp.status, body)
                        raise Exception(f"Catalog service error: {resp.status}")
        except Exception as exc:
            logger.error("Catalog HTTP request failed: %s", exc)
            raise

    async def create_product(self, product_data: dict) -> dict:
        """Create a new product."""
        url = f"{self.base_url}/products"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=product_data, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status in (200, 201):
                        return await resp.json()
                    body = await resp.text()
                    raise Exception(f"Catalog service error: {resp.status} - {body}")
        except Exception as exc:
            logger.error("Catalog create product failed: %s", exc)
            raise

    async def update_product(self, product_id: str, updates: dict) -> dict:
        """Update a product."""
        url = f"{self.base_url}/products/{product_id}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.patch(url, json=updates, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    body = await resp.text()
                    raise Exception(f"Catalog service error: {resp.status} - {body}")
        except Exception as exc:
            logger.error("Catalog update product failed: %s", exc)
            raise

    async def delete_product(self, product_id: str) -> bool:
        """Delete a product."""
        url = f"{self.base_url}/products/{product_id}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.delete(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    return resp.status == 204
        except Exception as exc:
            logger.error("Catalog delete product failed: %s", exc)
            raise

    async def get_categories(self, is_active: bool = True) -> dict:
        """Get all categories."""
        url = f"{self.base_url}/categories?is_active={str(is_active).lower()}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    return {"items": []}
        except Exception as exc:
            logger.error("Catalog get categories failed: %s", exc)
            return {"items": []}
