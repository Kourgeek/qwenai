# Catalog Service API Documentation

Product catalog service providing CRUD operations for products, categories, brands, and tags.

---

## Table of Contents

- [Overview](#overview)
- [Protocol](#protocol)
- [HTTP Endpoints](#http-endpoints)
- [gRPC API](#grpc-api)
- [Error Codes](#error-codes)
- [Examples](#examples)

---

## Overview

The Catalog Service manages the marketplace product catalog including products, categories, brands, and tags. It provides both HTTP REST and gRPC interfaces.

**Base URL (HTTP):** `http://localhost:8084` (host-mapped)
**gRPC Target:** `localhost:50053` (host-mapped)

---

## Protocol

| Protocol | Port | Description |
|----------|------|-------------|
| HTTP (REST) | 8084 (host-mapped) | Public API for catalog operations |
| gRPC | 50053 (host-mapped) | Service-to-service catalog queries |

---

## HTTP Endpoints

### Products

#### Create Product

**POST** `/products`

Create a new product listing.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | Product name |
| slug | string | Yes | URL-friendly slug |
| description | string | Yes | Product description |
| price | number | Yes | Product price |
| category_id | string | Yes | UUID of the category |
| brand_id | string | No | UUID of the brand |
| sku | string | No | Stock keeping unit |
| barcode | string | No | Product barcode |
| stock_quantity | integer | No | Available stock (default: 0) |
| image_urls | string[] | No | Product image URLs |
| tag_ids | string[] | No | Associated tag UUIDs |
| metadata | object | No | Custom key-value metadata |
| is_active | boolean | No | Product visibility (default: true) |

**Example Request:**

```bash
curl -X POST http://localhost:8084/products \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Wireless Headphones",
    "slug": "wireless-headphones",
    "description": "Premium noise-cancelling wireless headphones",
    "price": 99.99,
    "category_id": "cat_123",
    "brand_id": "brand_456",
    "sku": "WH-001",
    "stock_quantity": 100,
    "image_urls": ["https://cdn.example.com/headphones.jpg"],
    "tag_ids": ["tag_electronics", "tag_audio"],
    "is_active": true
  }'
```

**Response (201 Created):**

```json
{
  "id": "prod_abc123",
  "name": "Wireless Headphones",
  "slug": "wireless-headphones",
  "description": "Premium noise-cancelling wireless headphones",
  "price": 99.99,
  "category_id": "cat_123",
  "brand_id": "brand_456",
  "sku": "WH-001",
  "stock_quantity": 100,
  "image_urls": ["https://cdn.example.com/headphones.jpg"],
  "is_active": true,
  "created_at": "2026-08-03T10:00:00Z",
  "updated_at": "2026-08-03T10:00:00Z"
}
```

#### List Products

**GET** `/products`

Retrieve a paginated list of products.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| skip | integer | 0 | Number of records to skip |
| limit | integer | 100 | Max records to return (1-500) |
| is_active | boolean | null | Filter by active status |

**Example Request:**

```bash
curl "http://localhost:8084/products?skip=0&limit=20&is_active=true"
```

**Response:**

```json
{
  "items": [
    {
      "id": "prod_abc123",
      "name": "Wireless Headphones",
      "price": 99.99,
      "category_id": "cat_123",
      "brand_id": "brand_456",
      "is_active": true
    }
  ],
  "total": 150,
  "skip": 0,
  "limit": 20
}
```

#### Get Product

**GET** `/products/{product_id}`

Retrieve a single product by ID.

**Response (200 OK):**

```json
{
  "id": "prod_abc123",
  "name": "Wireless Headphones",
  "slug": "wireless-headphones",
  "description": "Premium noise-cancelling wireless headphones",
  "price": 99.99,
  "compare_at_price": 149.99,
  "category_id": "cat_123",
  "brand_id": "brand_456",
  "sku": "WH-001",
  "stock_quantity": 100,
  "image_urls": ["https://cdn.example.com/headphones.jpg"],
  "is_active": true,
  "is_featured": true,
  "created_at": "2026-08-03T10:00:00Z",
  "updated_at": "2026-08-03T10:00:00Z"
}
```

**Response (404):**

```json
{
  "detail": "Product prod_abc123 not found"
}
```

#### Update Product

**PATCH** `/products/{product_id}`

Update an existing product.

**Example Request:**

```bash
curl -X PATCH http://localhost:8084/products/prod_abc123 \
  -H "Content-Type: application/json" \
  -d '{
    "price": 79.99,
    "stock_quantity": 50,
    "is_active": true
  }'
```

#### Delete Product

**DELETE** `/products/{product_id}`

Soft-delete a product.

**Response:** `204 No Content`

#### Search Products

**GET** `/products/search`

Search products by query string.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| q | string | Yes | Search query |
| limit | integer | No | Max results (default: 20, max: 100) |

**Example Request:**

```bash
curl "http://localhost:8084/products/search?q=wireless+headphones&limit=10"
```

**Response:**

```json
{
  "items": [
    {
      "id": "prod_abc123",
      "name": "Wireless Headphones",
      "price": 99.99,
      "score": 0.95
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 10
}
```

#### Products by Category

**GET** `/products/by-category/{category_id}`

List products in a specific category.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| skip | integer | 0 | Records to skip |
| limit | integer | 100 | Max records (1-500) |

#### Products by Tag

**GET** `/products/by-tag/{tag_id}`

List products with a specific tag.

---

### Categories

#### Create Category

**POST** `/categories`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | Category name |
| slug | string | Yes | URL-friendly slug |
| description | string | No | Category description |
| parent_id | string | No | Parent category UUID (for hierarchy) |
| image_urls | string[] | No | Category image URLs |
| metadata | object | No | Custom metadata |

**Example Request:**

```bash
curl -X POST http://localhost:8084/categories \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Electronics",
    "slug": "electronics",
    "description": "Electronic devices and accessories"
  }'
```

#### List Categories

**GET** `/categories`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| skip | integer | 0 | Records to skip |
| limit | integer | 100 | Max records (1-500) |
| is_active | boolean | null | Filter by active status |
| parent_id | string | null | Filter by parent category |

#### Get Category

**GET** `/categories/{category_id}`

Retrieve a single category by ID.

#### Update Category

**PATCH** `/categories/{category_id}`

Update an existing category.

#### Delete Category

**DELETE** `/categories/{category_id}`

Delete a category.

---

### Brands

#### Create Brand

**POST** `/brands`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | Brand name |
| slug | string | Yes | URL-friendly slug |
| description | string | No | Brand description |
| logo_url | string | No | Brand logo URL |
| is_active | boolean | No | Brand visibility (default: true) |

#### List Brands

**GET** `/brands`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| skip | integer | 0 | Records to skip |
| limit | integer | 100 | Max records (1-500) |
| is_active | boolean | null | Filter by active status |

#### Get Brand

**GET** `/brands/{brand_id}`

Retrieve a single brand by ID.

#### Update Brand

**PATCH** `/brands/{brand_id}`

Update an existing brand.

#### Delete Brand

**DELETE** `/brands/{brand_id}`

Delete a brand.

---

### Tags

#### Create Tag

**POST** `/tags`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | Tag name |
| slug | string | Yes | URL-friendly slug |
| description | string | No | Tag description |
| is_active | boolean | No | Tag visibility (default: true) |

#### List Tags

**GET** `/tags`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| skip | integer | 0 | Records to skip |
| limit | integer | 100 | Max records (1-500) |
| is_active | boolean | null | Filter by active status |

#### Get Tag

**GET** `/tags/{tag_id}`

Retrieve a single tag by ID.

#### Update Tag

**PATCH** `/tags/{tag_id}`

Update an existing tag.

#### Delete Tag

**DELETE** `/tags/{tag_id}`

Delete a tag.

---

## gRPC API

### Service Definition

```protobuf
service CatalogService {
  // Category RPCs
  rpc CreateCategory(CreateCategoryRequest) returns (Category);
  rpc GetCategory(GetCategoryRequest) returns (Category);
  rpc UpdateCategory(UpdateCategoryRequest) returns (Category);
  rpc DeleteCategory(DeleteCategoryRequest) returns (Empty);
  rpc ListCategories(ListCategoriesRequest) returns (ListCategoriesResponse);
  rpc GetCategoryTree(GetCategoryTreeRequest) returns (GetCategoryTreeResponse);
  rpc GetCategoryChildren(GetCategoryChildrenRequest) returns (GetCategoryChildrenResponse);

  // Brand RPCs
  rpc CreateBrand(CreateBrandRequest) returns (Brand);
  rpc GetBrand(GetBrandRequest) returns (Brand);
  rpc UpdateBrand(UpdateBrandRequest) returns (Brand);
  rpc DeleteBrand(DeleteBrandRequest) returns (Empty);
  rpc ListBrands(ListBrandsRequest) returns (ListBrandsResponse);
  rpc SearchBrands(SearchBrandsRequest) returns (SearchBrandsResponse);

  // Tag RPCs
  rpc CreateTag(CreateTagRequest) returns (Tag);
  rpc GetTag(GetTagRequest) returns (Tag);
  rpc UpdateTag(UpdateTagRequest) returns (Tag);
  rpc DeleteTag(DeleteTagRequest) returns (Empty);
  rpc ListTags(ListTagsRequest) returns (ListTagsResponse);

  // Product RPCs
  rpc CreateProduct(CreateProductRequest) returns (Product);
  rpc GetProduct(GetProductRequest) returns (Product);
  rpc UpdateProduct(UpdateProductRequest) returns (Product);
  rpc DeleteProduct(DeleteProductRequest) returns (Empty);
  rpc ListProducts(ListProductsRequest) returns (ListProductsResponse);
  rpc SearchProducts(SearchProductsRequest) returns (SearchProductsResponse);
  rpc GetProductsByCategory(GetProductsByCategoryRequest) returns (GetProductsByCategoryResponse);
  rpc GetProductsByTag(GetProductsByTagRequest) returns (GetProductsByTagResponse);
}
```

### Key Message Types

#### Product

```protobuf
message Product {
  string id = 1;
  string name = 2;
  string slug = 3;
  string description = 4;
  string sku = 5;
  string barcode = 6;
  string category_id = 7;
  repeated string category_ids = 8;
  string brand_id = 9;
  string seller_id = 21;
  string status = 10;
  double price = 11;
  double compare_at_price = 12;
  double cost_price = 13;
  int32 quantity = 14;
  bool is_active = 15;
  bool is_featured = 16;
  repeated string image_urls = 17;
  repeated string tag_ids = 18;
  map<string, string> metadata = 19;
  Timestamp created_at = 20;
  Timestamp updated_at = 22;
  Timestamp deleted_at = 23;
}
```

#### Category

```protobuf
message Category {
  string id = 1;
  string name = 2;
  string slug = 3;
  string description = 4;
  string parent_id = 5;
  int32 level = 6;
  string path = 7;
  bool is_active = 8;
  repeated Category children = 9;
  int32 product_count = 10;
  Timestamp created_at = 11;
  Timestamp updated_at = 12;
}
```

#### Brand

```protobuf
message Brand {
  string id = 1;
  string name = 2;
  string slug = 3;
  string description = 4;
  string logo_url = 5;
  bool is_active = 6;
  int32 product_count = 7;
  Timestamp created_at = 8;
  Timestamp updated_at = 9;
}
```

#### Tag

```protobuf
message Tag {
  string id = 1;
  string name = 2;
  string slug = 3;
  string description = 4;
  bool is_active = 5;
  int32 product_count = 6;
  Timestamp created_at = 7;
  Timestamp updated_at = 8;
}
```

#### Pagination

```protobuf
message Pagination {
  int32 page = 1;
  int32 page_size = 2;
  int32 total = 3;
}
```

### gRPC Examples

#### Python — Get Product

```python
import grpc
import catalog_pb2
import catalog_pb2_grpc

channel = grpc.insecure_channel('localhost:50053')
stub = catalog_pb2_grpc.CatalogServiceStub(channel)

# Get product
response = stub.GetProduct(catalog_pb2.GetProductRequest(id='prod_abc123'))
print(f"Product: {response.name} - ${response.price}")
```

#### Python — Search Products

```python
# Search products
response = stub.SearchProducts(
    catalog_pb2.SearchProductsRequest(
        query='wireless headphones',
        limit=10
    )
)
for product in response.products:
    print(f"{product.name}: ${product.price}")
```

---

## Error Codes

| HTTP Status | Description |
|-------------|-------------|
| 400 | Invalid request parameters |
| 404 | Resource not found |
| 409 | Conflict (e.g., duplicate slug) |
| 500 | Internal server error |

| gRPC Status | Description |
|-------------|-------------|
| `INVALID_ARGUMENT` | Invalid request parameters |
| `NOT_FOUND` | Resource not found |
| `ALREADY_EXISTS` | Duplicate entry |
| `INTERNAL` | Internal server error |

---

## Examples

### Product Search with Filters

```bash
# Search with price range
curl "http://localhost:8084/products/search?q=headphones&limit=10"

# List products by category
curl "http://localhost:8084/products/by-category/cat_123?skip=0&limit=20"

# List products by tag
curl "http://localhost:8084/products/by-tag/tag_electronics?skip=0&limit=20"

# List active products with pagination
curl "http://localhost:8084/products?skip=0&limit=20&is_active=true"
```

### Category Tree

```bash
# Get all categories
curl "http://localhost:8084/categories?skip=0&limit=100"

# Get category children
curl "http://localhost:8084/categories?parent_id=cat_parent"
```

---

## Related Documentation

- [Services Overview](services.md) — Service architecture
- [gRPC API Reference](grpc-api.md) — Full proto definitions
- [Search Service](../api/search-service.md) — Elasticsearch integration
