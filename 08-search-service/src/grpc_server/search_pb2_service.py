"""gRPC SearchService implementation — binds SearchService RPCs to SearchService."""

from __future__ import annotations

import logging
from typing import Any

import grpc

from src.grpc_server import search_pb2
from src.grpc_server import search_pb2_grpc
from src.services.search_service import SearchService

logger = logging.getLogger(__name__)


class SearchServiceServicer(search_pb2_grpc.SearchServiceServicer):
    """Concrete gRPC servicer delegating to the SearchService business layer."""

    def __init__(self, search_service: SearchService) -> None:
        self._search = search_service

    # ── SearchProducts ─────────────────────────────────────────────────────

    async def SearchProducts(
        self, request: search_pb2.SearchProductsRequest, context: grpc.ServicerContext
    ) -> search_pb2.SearchProductsResponse:
        try:
            result = await self._search.search_products(
                query=request.query,
                categories=list(request.categories) if request.categories else None,
                brands=list(request.brands) if request.brands else None,
                min_price=request.min_price if request.HasField("min_price") else None,
                max_price=request.max_price if request.HasField("max_price") else None,
                sort_by=request.sort_by or "_score",
                sort_order=request.sort_order or "desc",
                page=request.page if request.page else 1,
                page_size=request.page_size if request.page_size else 20,
            )

            products = [
                search_pb2.Product(
                    id=h["id"],
                    name=h["name"],
                    description=h["description"],
                    category=h["category"],
                    brand=h["brand"],
                    price=h["price"],
                    attributes=h.get("attributes", {}),
                )
                for h in result["hits"]
            ]

            return search_pb2.SearchProductsResponse(
                products=products,
                total=result["total"],
                page=result["page"],
                page_size=result["page_size"],
            )
        except Exception as exc:
            logger.exception("SearchProducts RPC failed")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            return search_pb2.SearchProductsResponse()

    # ── SuggestProducts ────────────────────────────────────────────────────

    async def SuggestProducts(
        self, request: search_pb2.SuggestProductsRequest, context: grpc.ServicerContext
    ) -> search_pb2.SuggestProductsResponse:
        try:
            suggestions = await self._search.suggest_products(
                query=request.query,
                limit=request.limit if request.limit else 10,
            )
            return search_pb2.SuggestProductsResponse(suggestions=suggestions)
        except Exception as exc:
            logger.exception("SuggestProducts RPC failed")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            return search_pb2.SuggestProductsResponse()

    # ── IndexProduct ───────────────────────────────────────────────────────

    async def IndexProduct(
        self, request: search_pb2.IndexProductRequest, context: grpc.ServicerContext
    ) -> search_pb2.IndexProductResponse:
        try:
            result = await self._search.index_product(product_id=request.product_id)
            return search_pb2.IndexProductResponse(
                success=result["success"],
                message=result["message"],
            )
        except Exception as exc:
            logger.exception("IndexProduct RPC failed")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            return search_pb2.IndexProductResponse(success=False, message=str(exc))

    # ── ReindexCatalog ─────────────────────────────────────────────────────

    async def ReindexCatalog(
        self, request: search_pb2.ReindexCatalogRequest, context: grpc.ServicerContext
    ) -> search_pb2.ReindexCatalogResponse:
        try:
            batch_size = request.batch_size if request.batch_size else 50
            result = await self._search.reindex_catalog(batch_size=batch_size)
            return search_pb2.ReindexCatalogResponse(
                indexed_count=result["indexed_count"],
                success=result["success"],
            )
        except Exception as exc:
            logger.exception("ReindexCatalog RPC failed")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            return search_pb2.ReindexCatalogResponse(indexed_count=0, success=False)
