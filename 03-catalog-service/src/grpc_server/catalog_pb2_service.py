"""gRPC Catalog service implementation.

Implements all RPCs for categories, brands, tags, and products
using the service layer.
"""

import uuid
from datetime import datetime, timezone

import grpc
from catalog.v1.catalog_pb2 import (
    Brand,
    Category,
    CreateBrandRequest,
    CreateCategoryRequest,
    CreateProductRequest,
    CreateTagRequest,
    DeleteBrandRequest,
    DeleteCategoryRequest,
    DeleteProductRequest,
    DeleteTagRequest,
    Empty,
    GetBrandRequest,
    GetCategoryRequest,
    GetCategoryTreeRequest,
    GetCategoryTreeResponse,
    GetCategoryChildrenRequest,
    GetCategoryChildrenResponse,
    GetProductRequest,
    GetProductsByCategoryRequest,
    GetProductsByCategoryResponse,
    GetProductsByTagRequest,
    GetProductsByTagResponse,
    GetTagRequest,
    ListBrandsRequest,
    ListBrandsResponse,
    ListCategoriesRequest,
    ListCategoriesResponse,
    ListProductsRequest,
    ListProductsResponse,
    ListTagsRequest,
    ListTagsResponse,
    Pagination,
    Product,
    SearchBrandsRequest,
    SearchBrandsResponse,
    SearchProductsRequest,
    SearchProductsResponse,
    Tag,
    UpdateBrandRequest,
    UpdateCategoryRequest,
    UpdateProductRequest,
    UpdateTagRequest,
)
from catalog.v1.catalog_pb2_grpc import CatalogServiceServicer as CatalogServicerBase

from src.config import settings
from src.services.brand_service import BrandService
from src.services.category_service import CategoryService
from src.services.product_service import ProductService
from src.services.tag_service import TagService


def _category_to_pb(category) -> dict:
    """Convert a SQLAlchemy Category row to a protobuf-compatible dict."""
    return {
        "id": str(category.id),
        "name": category.name,
        "slug": category.slug,
        "description": category.description,
        "parent_id": str(category.parent_id) if category.parent_id else None,
        "image_urls": category.image_urls or [],
        "metadata": category.meta_data or {},
        "is_active": category.is_active,
        "created_at": category.created_at.isoformat() if category.created_at else "",
        "updated_at": category.updated_at.isoformat() if category.updated_at else "",
    }


def _brand_to_pb(brand) -> dict:
    return {
        "id": str(brand.id),
        "name": brand.name,
        "slug": brand.slug,
        "description": brand.description,
        "logo_url": brand.logo_url,
        "website_url": brand.website_url,
        "metadata": brand.meta_data or {},
        "is_active": brand.is_active,
        "created_at": brand.created_at.isoformat() if brand.created_at else "",
        "updated_at": brand.updated_at.isoformat() if brand.updated_at else "",
    }


def _tag_to_pb(tag) -> dict:
    return {
        "id": str(tag.id),
        "name": tag.name,
        "slug": tag.slug,
        "metadata": tag.meta_data or {},
        "is_active": tag.is_active,
        "created_at": tag.created_at.isoformat() if tag.created_at else "",
        "updated_at": tag.updated_at.isoformat() if tag.updated_at else "",
    }


def _product_to_pb(product) -> dict:
    return {
        "id": str(product.id),
        "name": product.name,
        "slug": product.slug,
        "description": product.description,
        "category_id": str(product.category_id) if product.category_id else None,
        "brand_id": str(product.brand_id) if product.brand_id else None,
        "price": product.price,
        "compare_at_price": product.compare_at_price,
        "sku": product.sku,
        "stock_quantity": product.stock_quantity,
        "image_urls": product.image_urls or [],
        "tag_ids": [str(t) for t in product.tag_ids] if product.tag_ids else [],
        "metadata": product.meta_data or {},
        "is_active": product.is_active,
        "created_at": product.created_at.isoformat() if product.created_at else "",
        "updated_at": product.updated_at.isoformat() if product.updated_at else "",
    }


class CatalogServiceServicer(CatalogServicerBase):
    """Implements all Catalog gRPC RPCs."""

    async def CreateCategory(self, request, context):
        try:
            parent_id = uuid.UUID(request.parent_id) if request.parent_id else None
            image_urls = list(request.image_urls) if request.image_urls else None
            metadata = dict(request.metadata) if request.metadata else None
            category_service = CategoryService(None)
            category = await category_service.create_category(
                name=request.name,
                slug=request.slug,
                description=request.description or None,
                parent_id=parent_id,
                image_urls=image_urls,
                metadata=metadata,
            )
            return Category(id=str(category.id))
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return Category()

    async def GetCategory(self, request, context):
        try:
            category_id = uuid.UUID(request.id)
            category_service = CategoryService(None)
            category = await category_service.get_category_by_id(category_id)
            if not category:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Category {request.id} not found")
                return Category()
            resp = Category()
            resp.id = str(category.id)
            resp.name = category.name
            resp.slug = category.slug
            resp.description = category.description or ""
            resp.parent_id = str(category.parent_id) if category.parent_id else ""
            resp.image_urls.extend(category.image_urls or [])
            resp.metadata.update(category.meta_data or {})
            resp.is_active = category.is_active
            resp.created_at = category.created_at.isoformat() if category.created_at else ""
            resp.updated_at = category.updated_at.isoformat() if category.updated_at else ""
            return resp
        except ValueError:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(f"Invalid UUID: {request.id}")
            return Category()
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return Category()

    async def UpdateCategory(self, request, context):
        try:
            category_id = uuid.UUID(request.id)
            parent_id = uuid.UUID(request.parent_id) if request.parent_id else None
            image_urls = list(request.image_urls) if request.image_urls else None
            metadata = dict(request.metadata) if request.metadata else None
            category_service = CategoryService(None)
            category = await category_service.update_category(
                category_id,
                name=request.name or None,
                description=request.description or None,
                parent_id=parent_id,
                image_urls=image_urls,
                metadata=metadata,
                is_active=request.is_active if request.HasField("is_active") else None,
            )
            if not category:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Category {request.id} not found")
                return Category()
            return Category(id=str(category.id))
        except ValueError:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Invalid UUID")
            return Category()
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return Category()

    async def DeleteCategory(self, request, context):
        try:
            category_id = uuid.UUID(request.id)
            category_service = CategoryService(None)
            deleted = await category_service.delete_category(category_id)
            if not deleted:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Category {request.id} not found")
                return Empty()
            return Empty(success=True)
        except ValueError:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Invalid UUID")
            return Empty()
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return Empty()

    async def ListCategories(self, request, context):
        try:
            category_service = CategoryService(None)
            parent_id = uuid.UUID(request.parent_id) if request.parent_id else None
            categories = await category_service.list_categories(
                skip=request.skip,
                limit=request.limit,
                is_active=request.is_active if request.HasField("is_active") else None,
                parent_id=parent_id,
            )
            resp = ListCategoriesResponse()
            for cat in categories:
                item = resp.items.add()
                item.id = str(cat.id)
                item.name = cat.name
                item.slug = cat.slug
                item.description = cat.description or ""
                item.parent_id = str(cat.parent_id) if cat.parent_id else ""
                item.image_urls.extend(cat.image_urls or [])
                item.meta_data.update(cat.meta_data or {})
                item.is_active = cat.is_active
                item.created_at = cat.created_at.isoformat() if cat.created_at else ""
                item.updated_at = cat.updated_at.isoformat() if cat.updated_at else ""
            return resp
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ListCategoriesResponse()

    async def GetCategory(self, request, context):
        try:
            category_id = uuid.UUID(request.id)
            category_service = CategoryService(None)
            tree = await category_service.get_category_tree(category_id)
            resp = GetCategoryTreeResponse()
            for cat in tree:
                item = resp.tree.add()
                item.id = str(cat.id)
                item.name = cat.name
                item.slug = cat.slug
                item.description = cat.description or ""
                item.parent_id = str(cat.parent_id) if cat.parent_id else ""
                item.image_urls.extend(cat.image_urls or [])
                item.meta_data.update(cat.meta_data or {})
                item.is_active = cat.is_active
                item.created_at = cat.created_at.isoformat() if cat.created_at else ""
                item.updated_at = cat.updated_at.isoformat() if cat.updated_at else ""
            return resp
        except ValueError:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Invalid UUID")
            return GetCategoryTreeResponse()
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return GetCategoryTreeResponse()

    async def GetCategoryChildren(self, request, context):
        try:
            category_id = uuid.UUID(request.id)
            category_service = CategoryService(None)
            children = await category_service.get_category_children(category_id)
            resp = ListCategoriesResponse()
            for cat in children:
                item = resp.items.add()
                item.id = str(cat.id)
                item.name = cat.name
                item.slug = cat.slug
                item.description = cat.description or ""
                item.parent_id = str(cat.parent_id) if cat.parent_id else ""
                item.image_urls.extend(cat.image_urls or [])
                item.meta_data.update(cat.meta_data or {})
                item.is_active = cat.is_active
                item.created_at = cat.created_at.isoformat() if cat.created_at else ""
                item.updated_at = cat.updated_at.isoformat() if cat.updated_at else ""
            return resp
        except ValueError:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Invalid UUID")
            return ListCategoriesResponse()
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ListCategoriesResponse()

    # ---- Brand RPCs ----

    async def CreateBrand(self, request, context):
        try:
            metadata = dict(request.metadata) if request.metadata else None
            brand_service = BrandService(None)
            brand = await brand_service.create_brand(
                name=request.name,
                slug=request.slug,
                description=request.description or None,
                logo_url=request.logo_url or None,
                website_url=request.website_url or None,
                metadata=metadata,
            )
            return Brand(id=str(brand.id))
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return Brand()

    async def GetBrand(self, request, context):
        try:
            brand_id = uuid.UUID(request.id)
            brand_service = BrandService(None)
            brand = await brand_service.get_brand_by_id(brand_id)
            if not brand:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Brand {request.id} not found")
                return Brand()
            resp = Brand()
            resp.id = str(brand.id)
            resp.name = brand.name
            resp.slug = brand.slug
            resp.description = brand.description or ""
            resp.logo_url = brand.logo_url or ""
            resp.website_url = brand.website_url or ""
            resp.metadata.update(brand.meta_data or {})
            resp.is_active = brand.is_active
            resp.created_at = brand.created_at.isoformat() if brand.created_at else ""
            resp.updated_at = brand.updated_at.isoformat() if brand.updated_at else ""
            return resp
        except ValueError:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Invalid UUID")
            return Brand()
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return Brand()

    async def UpdateBrand(self, request, context):
        try:
            brand_id = uuid.UUID(request.id)
            metadata = dict(request.metadata) if request.metadata else None
            brand_service = BrandService(None)
            brand = await brand_service.update_brand(
                brand_id,
                name=request.name or None,
                description=request.description or None,
                logo_url=request.logo_url or None,
                website_url=request.website_url or None,
                metadata=metadata,
                is_active=request.is_active if request.HasField("is_active") else None,
            )
            if not brand:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Brand {request.id} not found")
                return Brand()
            return Brand(id=str(brand.id))
        except ValueError:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Invalid UUID")
            return Brand()
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return Brand()

    async def DeleteBrand(self, request, context):
        try:
            brand_id = uuid.UUID(request.id)
            brand_service = BrandService(None)
            deleted = await brand_service.delete_brand(brand_id)
            if not deleted:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Brand {request.id} not found")
                return Empty()
            return Empty(success=True)
        except ValueError:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Invalid UUID")
            return Empty()
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return Empty()

    async def ListBrands(self, request, context):
        try:
            brand_service = BrandService(None)
            brands = await brand_service.list_brands(
                skip=request.skip,
                limit=request.limit,
                is_active=request.is_active if request.HasField("is_active") else None,
            )
            resp = ListBrandsResponse()
            for b in brands:
                item = resp.items.add()
                item.id = str(b.id)
                item.name = b.name
                item.slug = b.slug
                item.description = b.description or ""
                item.logo_url = b.logo_url or ""
                item.website_url = b.website_url or ""
                item.meta_data.update(b.meta_data or {})
                item.is_active = b.is_active
                item.created_at = b.created_at.isoformat() if b.created_at else ""
                item.updated_at = b.updated_at.isoformat() if b.updated_at else ""
            return resp
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ListBrandsResponse()

    async def SearchBrands(self, request, context):
        try:
            brand_service = BrandService(None)
            brands = await brand_service.search_brands(request.query, limit=request.limit)
            resp = SearchBrandsResponse()
            for b in brands:
                item = resp.items.add()
                item.id = str(b.id)
                item.name = b.name
                item.slug = b.slug
                item.description = b.description or ""
                item.logo_url = b.logo_url or ""
                item.website_url = b.website_url or ""
                item.meta_data.update(b.meta_data or {})
                item.is_active = b.is_active
                item.created_at = b.created_at.isoformat() if b.created_at else ""
                item.updated_at = b.updated_at.isoformat() if b.updated_at else ""
            return resp
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return SearchBrandsResponse()

    # ---- Tag RPCs ----

    async def CreateTag(self, request, context):
        try:
            metadata = dict(request.metadata) if request.metadata else None
            tag_service = TagService(None)
            tag = await tag_service.create_tag(
                name=request.name,
                slug=request.slug,
                metadata=metadata,
            )
            return Tag(id=str(tag.id))
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return Tag()

    async def GetTag(self, request, context):
        try:
            tag_id = uuid.UUID(request.id)
            tag_service = TagService(None)
            tag = await tag_service.get_tag_by_id(tag_id)
            if not tag:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Tag {request.id} not found")
                return Tag()
            resp = Tag()
            resp.id = str(tag.id)
            resp.name = tag.name
            resp.slug = tag.slug
            resp.metadata.update(tag.meta_data or {})
            resp.is_active = tag.is_active
            resp.created_at = tag.created_at.isoformat() if tag.created_at else ""
            resp.updated_at = tag.updated_at.isoformat() if tag.updated_at else ""
            return resp
        except ValueError:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Invalid UUID")
            return Tag()
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return Tag()

    async def UpdateTag(self, request, context):
        try:
            tag_id = uuid.UUID(request.id)
            metadata = dict(request.metadata) if request.metadata else None
            tag_service = TagService(None)
            tag = await tag_service.update_tag(
                tag_id,
                name=request.name or None,
                metadata=metadata,
                is_active=request.is_active if request.HasField("is_active") else None,
            )
            if not tag:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Tag {request.id} not found")
                return Tag()
            return Tag(id=str(tag.id))
        except ValueError:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Invalid UUID")
            return Tag()
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return Tag()

    async def DeleteTag(self, request, context):
        try:
            tag_id = uuid.UUID(request.id)
            tag_service = TagService(None)
            deleted = await tag_service.delete_tag(tag_id)
            if not deleted:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Tag {request.id} not found")
                return Empty()
            return Empty(success=True)
        except ValueError:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Invalid UUID")
            return Empty()
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return Empty()

    async def ListTags(self, request, context):
        try:
            tag_service = TagService(None)
            tags = await tag_service.list_tags(
                skip=request.skip,
                limit=request.limit,
                is_active=request.is_active if request.HasField("is_active") else None,
            )
            resp = ListTagsResponse()
            for t in tags:
                item = resp.items.add()
                item.id = str(t.id)
                item.name = t.name
                item.slug = t.slug
                item.meta_data.update(t.meta_data or {})
                item.is_active = t.is_active
                item.created_at = t.created_at.isoformat() if t.created_at else ""
                item.updated_at = t.updated_at.isoformat() if t.updated_at else ""
            return resp
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ListTagsResponse()

    # ---- Product RPCs ----

    async def CreateProduct(self, request, context):
        try:
            category_id = uuid.UUID(request.category_id) if request.category_id else None
            brand_id = uuid.UUID(request.brand_id) if request.brand_id else None
            image_urls = list(request.image_urls) if request.image_urls else None
            tag_ids = [uuid.UUID(t) for t in request.tag_ids] if request.tag_ids else None
            metadata = dict(request.metadata) if request.metadata else None
            product_service = ProductService(None)
            product = await product_service.create_product(
                name=request.name,
                slug=request.slug,
                price=request.price,
                description=request.description or None,
                category_id=category_id,
                brand_id=brand_id,
                compare_at_price=request.compare_at_price or None,
                sku=request.sku or None,
                stock_quantity=request.stock_quantity,
                image_urls=image_urls,
                tag_ids=tag_ids,
                metadata=metadata,
            )
            return Product(id=str(product.id))
        except ValueError:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Invalid UUID")
            return Product()
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return Product()

    async def GetProduct(self, request, context):
        try:
            product_id = uuid.UUID(request.id)
            product_service = ProductService(None)
            product = await product_service.get_product_by_id(product_id)
            if not product:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Product {request.id} not found")
                return Product()
            resp = Product()
            resp.id = str(product.id)
            resp.name = product.name
            resp.slug = product.slug
            resp.description = product.description or ""
            resp.category_id = str(product.category_id) if product.category_id else ""
            resp.brand_id = str(product.brand_id) if product.brand_id else ""
            resp.price = product.price
            resp.compare_at_price = product.compare_at_price or 0.0
            resp.sku = product.sku or ""
            resp.stock_quantity = product.stock_quantity
            resp.image_urls.extend(product.image_urls or [])
            resp.tag_ids.extend([str(t) for t in (product.tag_ids or [])])
            resp.metadata.update(product.meta_data or {})
            resp.is_active = product.is_active
            resp.created_at = product.created_at.isoformat() if product.created_at else ""
            resp.updated_at = product.updated_at.isoformat() if product.updated_at else ""
            return resp
        except ValueError:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Invalid UUID")
            return Product()
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return Product()

    async def UpdateProduct(self, request, context):
        try:
            product_id = uuid.UUID(request.id)
            category_id = uuid.UUID(request.category_id) if request.category_id else None
            brand_id = uuid.UUID(request.brand_id) if request.brand_id else None
            image_urls = list(request.image_urls) if request.image_urls else None
            tag_ids = [uuid.UUID(t) for t in request.tag_ids] if request.tag_ids else None
            metadata = dict(request.metadata) if request.metadata else None
            product_service = ProductService(None)
            product = await product_service.update_product(
                product_id,
                name=request.name or None,
                description=request.description or None,
                price=request.price if request.HasField("price") else None,
                category_id=category_id,
                brand_id=brand_id,
                compare_at_price=request.compare_at_price if request.HasField("compare_at_price") else None,
                sku=request.sku or None,
                stock_quantity=request.stock_quantity if request.HasField("stock_quantity") else None,
                image_urls=image_urls,
                tag_ids=tag_ids,
                metadata=metadata,
                is_active=request.is_active if request.HasField("is_active") else None,
            )
            if not product:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Product {request.id} not found")
                return Product()
            return Product(id=str(product.id))
        except ValueError:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Invalid UUID")
            return Product()
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return Product()

    async def DeleteProduct(self, request, context):
        try:
            product_id = uuid.UUID(request.id)
            product_service = ProductService(None)
            deleted = await product_service.delete_product(product_id)
            if not deleted:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Product {request.id} not found")
                return Empty()
            return Empty(success=True)
        except ValueError:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Invalid UUID")
            return Empty()
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return Empty()

    async def ListProducts(self, request, context):
        try:
            product_service = ProductService(None)
            products = await product_service.list_products(
                skip=request.skip,
                limit=request.limit,
                is_active=request.is_active if request.HasField("is_active") else None,
            )
            resp = ListProductsResponse()
            for p in products:
                item = resp.items.add()
                item.id = str(p.id)
                item.name = p.name
                item.slug = p.slug
                item.description = p.description or ""
                item.category_id = str(p.category_id) if p.category_id else ""
                item.brand_id = str(p.brand_id) if p.brand_id else ""
                item.price = p.price
                item.compare_at_price = p.compare_at_price or 0.0
                item.sku = p.sku or ""
                item.stock_quantity = p.stock_quantity
                item.image_urls.extend(p.image_urls or [])
                item.tag_ids.extend([str(t) for t in (p.tag_ids or [])])
                item.meta_data.update(p.meta_data or {})
                item.is_active = p.is_active
                item.created_at = p.created_at.isoformat() if p.created_at else ""
                item.updated_at = p.updated_at.isoformat() if p.updated_at else ""
            return resp
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return ListProductsResponse()

    async def SearchProducts(self, request, context):
        try:
            product_service = ProductService(None)
            products = await product_service.search_products(request.query, limit=request.limit)
            resp = SearchProductsResponse()
            for p in products:
                item = resp.items.add()
                item.id = str(p.id)
                item.name = p.name
                item.slug = p.slug
                item.description = p.description or ""
                item.category_id = str(p.category_id) if p.category_id else ""
                item.brand_id = str(p.brand_id) if p.brand_id else ""
                item.price = p.price
                item.compare_at_price = p.compare_at_price or 0.0
                item.sku = p.sku or ""
                item.stock_quantity = p.stock_quantity
                item.image_urls.extend(p.image_urls or [])
                item.tag_ids.extend([str(t) for t in (p.tag_ids or [])])
                item.meta_data.update(p.meta_data or {})
                item.is_active = p.is_active
                item.created_at = p.created_at.isoformat() if p.created_at else ""
                item.updated_at = p.updated_at.isoformat() if p.updated_at else ""
            return resp
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return SearchProductsResponse()

    async def GetProductsByCategory(self, request, context):
        try:
            category_id = uuid.UUID(request.category_id)
            product_service = ProductService(None)
            products = await product_service.get_products_by_category(
                category_id, skip=request.skip, limit=request.limit
            )
            resp = GetProductsByCategoryResponse()
            for p in products:
                item = resp.items.add()
                item.id = str(p.id)
                item.name = p.name
                item.slug = p.slug
                item.description = p.description or ""
                item.category_id = str(p.category_id) if p.category_id else ""
                item.brand_id = str(p.brand_id) if p.brand_id else ""
                item.price = p.price
                item.compare_at_price = p.compare_at_price or 0.0
                item.sku = p.sku or ""
                item.stock_quantity = p.stock_quantity
                item.image_urls.extend(p.image_urls or [])
                item.tag_ids.extend([str(t) for t in (p.tag_ids or [])])
                item.meta_data.update(p.meta_data or {})
                item.is_active = p.is_active
                item.created_at = p.created_at.isoformat() if p.created_at else ""
                item.updated_at = p.updated_at.isoformat() if p.updated_at else ""
            return resp
        except ValueError:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Invalid UUID")
            return GetProductsByCategoryResponse()
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return GetProductsByCategoryResponse()

    async def GetProductsByTag(self, request, context):
        try:
            tag_id = uuid.UUID(request.tag_id)
            product_service = ProductService(None)
            products = await product_service.get_products_by_tag(
                tag_id, skip=request.skip, limit=request.limit
            )
            resp = GetProductsByTagResponse()
            for p in products:
                item = resp.items.add()
                item.id = str(p.id)
                item.name = p.name
                item.slug = p.slug
                item.description = p.description or ""
                item.category_id = str(p.category_id) if p.category_id else ""
                item.brand_id = str(p.brand_id) if p.brand_id else ""
                item.price = p.price
                item.compare_at_price = p.compare_at_price or 0.0
                item.sku = p.sku or ""
                item.stock_quantity = p.stock_quantity
                item.image_urls.extend(p.image_urls or [])
                item.tag_ids.extend([str(t) for t in (p.tag_ids or [])])
                item.meta_data.update(p.meta_data or {})
                item.is_active = p.is_active
                item.created_at = p.created_at.isoformat() if p.created_at else ""
                item.updated_at = p.updated_at.isoformat() if p.updated_at else ""
            return resp
        except ValueError:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Invalid UUID")
            return GetProductsByTagResponse()
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return GetProductsByTagResponse()
