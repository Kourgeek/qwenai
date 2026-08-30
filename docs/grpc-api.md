# gRPC API Reference

Complete reference for all gRPC service definitions, message types, and RPC methods in the HyperScale Marketplace.

---

## Table of Contents

- [Overview](#overview)
- [Service Index](#service-index)
- [Common Messages](#common-messages)
- [AuthService](#authservice)
- [UserService](#user-service)
- [CatalogService](#catalog-service)
- [CartService](#cart-service)
- [OrderService](#order-service)
- [PaymentService](#payment-service)
- [NotificationService](#notification-service)
- [SearchService](#search-service)
- [SellerService](#seller-service)
- [BffService](#bff-service)
- [Code Generation](#code-generation)

---

## Overview

All inter-service communication uses gRPC with Protocol Buffers (protobuf) v3. Services expose both HTTP REST and gRPC interfaces; the gRPC interface is primarily for internal service-to-service communication.

### Service List

| # | Service | Package | Proto File | gRPC Port (host) |
|---|---------|---------|------------|------------------|
| 1 | AuthService | auth.v1 | `proto/auth/v1/auth.proto` | 50051 |
| 2 | UserService | user.v1 | `proto/user/v1/user.proto` | 50052 |
| 3 | CatalogService | catalog.v1 | `proto/catalog/v1/catalog.proto` | 50053 |
| 4 | CartService | cart.v1 | `proto/cart/v1/cart.proto` | 50054 |
| 5 | OrderService | order.v1 | `proto/order/v1/order.proto` | 50055 |
| 6 | PaymentService | payment.v1 | `proto/payment/v1/payment.proto` | 50056 |
| 7 | NotificationService | notification.v1 | `proto/notification/v1/notification.proto` | 50057 |
| 8 | SearchService | search.v1 | `proto/search/v1/search.proto` | 50058 |
| 9 | SellerService | seller.v1 | `proto/seller/v1/seller.proto` | 19090 |
| 10 | BffService | bff.v1 | `proto/bff/v1/bff.proto` | 50059 |

---

## Common Messages

### Empty

```protobuf
message Empty {}
```

### Pagination

```protobuf
message Pagination {
  int32 page = 1;
  int32 page_size = 2;
  int32 total = 3;
  int32 total_pages = 4;
}
```

### Timestamp

```protobuf
message Timestamp {
  int64 seconds = 1;
  int32 nanos = 2;
}
```

### ShippingAddress

```protobuf
message ShippingAddress {
  string full_name = 1;
  string line1 = 2;
  string line2 = 3;
  string city = 4;
  string state = 5;
  string postal_code = 6;
  string country = 7;
  string phone = 8;
}
```

### Product (shared across services)

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

---

## AuthService

**Package:** `auth.v1`
**Proto:** `proto/auth/v1/auth.proto`
**Port:** 50051 (host-mapped)

### Service

```protobuf
service AuthService {
  rpc Register(RegisterRequest) returns (RegisterResponse);
  rpc Login(LoginRequest) returns (LoginResponse);
  rpc Refresh(RefreshRequest) returns (RefreshResponse);
  rpc Logout(LogoutRequest) returns (LogoutResponse);
  rpc ForgotPassword(ForgotPasswordRequest) returns (ForgotPasswordResponse);
}
```

### Messages

| Message | Fields |
|---------|--------|
| `RegisterRequest` | `string email`, `string password`, `string first_name`, `string last_name` |
| `RegisterResponse` | `string id`, `string email`, `string first_name`, `string last_name`, `Timestamp created_at` |
| `LoginRequest` | `string email`, `string password` |
| `LoginResponse` | `string access_token`, `string refresh_token`, `Timestamp access_expires_at`, `Timestamp refresh_expires_at`, `string user_id`, `string email`, `string first_name`, `string last_name` |
| `RefreshRequest` | `string refresh_token` |
| `RefreshResponse` | `string access_token`, `string refresh_token`, `Timestamp access_expires_at`, `Timestamp refresh_expires_at` |
| `LogoutRequest` | `string refresh_token` |
| `LogoutResponse` | `bool success`, `string message` |
| `ForgotPasswordRequest` | `string email` |
| `ForgotPasswordResponse` | `bool success`, `string message` |

---

## UserService

**Package:** `user.v1`
**Proto:** `proto/user/v1/user.proto`
**Port:** 50052 (host-mapped)

### Service

```protobuf
service UserService {
  // Profile RPCs
  rpc GetUser(GetUserRequest) returns (User);
  rpc UpdateUser(UpdateUserRequest) returns (User);

  // Address RPCs
  rpc AddAddress(AddAddressRequest) returns (Address);
  rpc UpdateAddress(UpdateAddressRequest) returns (Address);
  rpc DeleteAddress(DeleteAddressRequest) returns (Empty);
  rpc GetUserAddresses(GetUserAddressesRequest) returns (AddressList);

  // Wishlist RPCs
  rpc AddToWishlist(AddToWishlistRequest) returns (WishlistItem);
  rpc GetUserWishlist(GetUserWishlistRequest) returns (WishlistItemList);
  rpc RemoveFromWishlist(RemoveFromWishlistRequest) returns (Empty);
}
```

### Key Messages

| Message | Fields |
|---------|--------|
| `User` | `string id`, `string email`, `string phone`, `string first_name`, `string last_name`, `string avatar_url`, `string role`, `Timestamp created_at`, `Timestamp updated_at` |
| `Address` | `string id`, `string user_id`, `string type`, `string full_name`, `string line1`, `string line2`, `string city`, `string postal_code`, `string country`, `bool is_default`, `Timestamp created_at`, `Timestamp updated_at` |
| `WishlistItem` | `string id`, `string user_id`, `string product_id`, `Timestamp added_at` |
| `AddressList` | `repeated Address addresses` |
| `WishlistItemList` | `repeated WishlistItem items` |

---

## CatalogService

**Package:** `catalog.v1`
**Proto:** `proto/catalog/v1/catalog.proto`
**Port:** 50053 (host-mapped)

### Service

```protobuf
service CatalogService {
  // Category RPCs (7 methods)
  rpc CreateCategory(CreateCategoryRequest) returns (Category);
  rpc GetCategory(GetCategoryRequest) returns (Category);
  rpc UpdateCategory(UpdateCategoryRequest) returns (Category);
  rpc DeleteCategory(DeleteCategoryRequest) returns (Empty);
  rpc ListCategories(ListCategoriesRequest) returns (ListCategoriesResponse);
  rpc GetCategoryTree(GetCategoryTreeRequest) returns (GetCategoryTreeResponse);
  rpc GetCategoryChildren(GetCategoryChildrenRequest) returns (GetCategoryChildrenResponse);

  // Brand RPCs (6 methods)
  rpc CreateBrand(CreateBrandRequest) returns (Brand);
  rpc GetBrand(GetBrandRequest) returns (Brand);
  rpc UpdateBrand(UpdateBrandRequest) returns (Brand);
  rpc DeleteBrand(DeleteBrandRequest) returns (Empty);
  rpc ListBrands(ListBrandsRequest) returns (ListBrandsResponse);
  rpc SearchBrands(SearchBrandsRequest) returns (SearchBrandsResponse);

  // Tag RPCs (5 methods)
  rpc CreateTag(CreateTagRequest) returns (Tag);
  rpc GetTag(GetTagRequest) returns (Tag);
  rpc UpdateTag(UpdateTagRequest) returns (Tag);
  rpc DeleteTag(DeleteTagRequest) returns (Empty);
  rpc ListTags(ListTagsRequest) returns (ListTagsResponse);

  // Product RPCs (8 methods)
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

### Key Messages

| Message | Fields |
|---------|--------|
| `Category` | `string id`, `string name`, `string slug`, `string description`, `string parent_id`, `int32 level`, `string path`, `bool is_active`, `repeated Category children`, `int32 product_count`, `Timestamp created_at`, `Timestamp updated_at` |
| `Brand` | `string id`, `string name`, `string slug`, `string description`, `string logo_url`, `bool is_active`, `int32 product_count`, `Timestamp created_at`, `Timestamp updated_at` |
| `Tag` | `string id`, `string name`, `string slug`, `string description`, `bool is_active`, `int32 product_count`, `Timestamp created_at`, `Timestamp updated_at` |
| `ListCategoriesResponse` | `repeated Category categories`, `Pagination pagination` |
| `ListBrandsResponse` | `repeated Brand brands`, `Pagination pagination` |
| `ListTagsResponse` | `repeated Tag tags`, `Pagination pagination` |
| `ListProductsResponse` | `repeated Product products`, `Pagination pagination` |
| `SearchProductsResponse` | `repeated Product products` |
| `SearchProductsRequest` | `string query`, `string category_id`, `string brand_id`, `int32 limit` |

---

## CartService

**Package:** `cart.v1`
**Proto:** `proto/cart/v1/cart.proto`
**Port:** 50054 (host-mapped)

### Service

```protobuf
service CartService {
  rpc GetCart(GetCartRequest) returns (Cart);
  rpc AddItem(AddItemRequest) returns (CartItem);
  rpc UpdateItem(UpdateItemRequest) returns (CartItem);
  rpc RemoveItem(RemoveItemRequest) returns (Empty);
  rpc ClearCart(ClearCartRequest) returns (Empty);
  rpc SaveForLater(SaveForLaterRequest) returns (SavedItem);
  rpc MoveToCart(MoveToCartRequest) returns (CartItem);
}
```

### Key Messages

| Message | Fields |
|---------|--------|
| `Cart` | `string user_id`, `repeated CartItem items`, `int32 total_items`, `double total_price`, `Timestamp updated_at` |
| `CartItem` | `string id`, `string user_id`, `string product_id`, `string product_name`, `string product_sku`, `string product_image_url`, `double unit_price`, `int32 quantity`, `double subtotal`, `string status`, `Timestamp created_at`, `Timestamp updated_at` |
| `SavedItem` | `string id`, `string user_id`, `string product_id`, `string product_name`, `string product_sku`, `double unit_price`, `int32 quantity`, `string status`, `Timestamp saved_at`, `Timestamp created_at` |
| `GetCartRequest` | `string user_id` |
| `AddItemRequest` | `string user_id`, `string product_id`, `int32 quantity` |
| `UpdateItemRequest` | `string user_id`, `string product_id`, `int32 quantity` |
| `RemoveItemRequest` | `string user_id`, `string product_id` |
| `ClearCartRequest` | `string user_id` |
| `SaveForLaterRequest` | `string user_id`, `string product_id` |
| `MoveToCartRequest` | `string user_id`, `string product_id` |

---

## OrderService

**Package:** `order.v1`
**Proto:** `proto/order/v1/order.proto`
**Port:** 50055 (host-mapped)

### Service

```protobuf
service OrderService {
  rpc CreateOrder(CreateOrderRequest) returns (Order);
  rpc GetOrder(GetOrderRequest) returns (Order);
  rpc GetUserOrders(GetUserOrdersRequest) returns (GetUserOrdersResponse);
  rpc CancelOrder(CancelOrderRequest) returns (CancelOrderResponse);
  rpc UpdateOrderStatus(UpdateOrderStatusRequest) returns (Order);
}
```

### Key Messages

| Message | Fields |
|---------|--------|
| `Order` | `string id`, `string user_id`, `string cart_id`, `string status`, `double total_amount`, `string currency`, `repeated OrderItem items`, `ShippingAddress shipping_address`, `string payment_method`, `string tracking_number`, `string cancelled_by`, `string cancellation_reason`, `int64 created_at`, `int64 updated_at`, `int64 completed_at`, `int64 cancelled_at` |
| `OrderItem` | `string id`, `string product_id`, `string product_name`, `string sku`, `int32 quantity`, `double unit_price`, `double total_price`, `string image_url` |
| `CreateOrderRequest` | `string user_id`, `string cart_id`, `ShippingAddress shipping_address`, `string payment_method` |
| `GetOrderRequest` | `string order_id` |
| `GetUserOrdersRequest` | `string user_id`, `int32 page`, `int32 page_size`, `string status` |
| `GetUserOrdersResponse` | `repeated Order orders`, `Pagination pagination` |
| `CancelOrderRequest` | `string order_id`, `string user_id`, `string reason` |
| `CancelOrderResponse` | `bool success`, `string message` |
| `UpdateOrderStatusRequest` | `string order_id`, `string status` |

---

## PaymentService

**Package:** `payment.v1`
**Proto:** `proto/payment/v1/payment.proto`
**Port:** 50056 (host-mapped)

### Service

```protobuf
service PaymentService {
  rpc CreatePayment(CreatePaymentRequest) returns (Payment);
  rpc ConfirmPayment(ConfirmPaymentRequest) returns (Payment);
  rpc GetPayment(GetPaymentRequest) returns (Payment);
  rpc RefundPayment(RefundPaymentRequest) returns (Refund);
  rpc GetUserPayments(GetUserPaymentsRequest) returns (PaymentList);
  rpc Webhook(WebhookRequest) returns (WebhookResponse);
}
```

### Enums

```protobuf
enum PaymentStatus {
  PAYMENT_STATUS_UNSPECIFIED = 0;
  PAYMENT_STATUS_PENDING = 1;
  PAYMENT_STATUS_CREATED = 2;
  PAYMENT_STATUS_PROCESSING = 3;
  PAYMENT_STATUS_COMPLETED = 4;
  PAYMENT_STATUS_FAILED = 5;
  PAYMENT_STATUS_REFUNDED = 6;
  PAYMENT_STATUS_PARTIALLY_REFUNDED = 7;
  PAYMENT_STATUS_CANCELLED = 8;
}

enum PaymentProvider {
  PAYMENT_PROVIDER_UNSPECIFIED = 0;
  PAYMENT_PROVIDER_STRIPE = 1;
  PAYMENT_PROVIDER_YOOMONEY = 2;
}

enum PaymentMethodType {
  PAYMENT_METHOD_TYPE_UNSPECIFIED = 0;
  PAYMENT_METHOD_TYPE_CARD = 1;
  PAYMENT_METHOD_TYPE_BANK_TRANSFER = 2;
  PAYMENT_METHOD_TYPE_E_WALLET = 3;
  PAYMENT_METHOD_TYPE_CRYPTO = 4;
}
```

### Key Messages

| Message | Fields |
|---------|--------|
| `Payment` | `string id`, `string order_id`, `string user_id`, `int64 amount`, `string currency`, `PaymentStatus status`, `PaymentProvider provider`, `string provider_payment_id`, `string provider_error`, `string payment_method_id`, `Timestamp created_at`, `Timestamp updated_at`, `Timestamp paid_at` |
| `PaymentList` | `repeated Payment payments`, `Pagination pagination` |
| `Refund` | `string id`, `string payment_id`, `string user_id`, `int64 amount`, `string currency`, `string status`, `string provider_refund_id`, `string reason`, `Timestamp created_at`, `Timestamp refunded_at` |
| `PaymentMethod` | `string id`, `string user_id`, `PaymentMethodType type`, `string last_four`, `string expiry`, `bool is_default`, `Timestamp created_at` |
| `CreatePaymentRequest` | `string order_id`, `string user_id`, `string payment_method_id`, `string currency`, `int64 amount`, `PaymentProvider provider` |
| `ConfirmPaymentRequest` | `string payment_id`, `map<string, string> provider_data` |
| `GetPaymentRequest` | `string payment_id` |
| `RefundPaymentRequest` | `string payment_id`, `int64 amount`, `string reason` |
| `GetUserPaymentsRequest` | `string user_id`, `int32 page`, `int32 page_size`, `PaymentStatus status_filter` |
| `WebhookRequest` | `string event_type`, `map<string, string> payload` |
| `WebhookResponse` | `bool success`, `string message` |

---

## NotificationService

**Package:** `notification.v1`
**Proto:** `proto/notification/v1/notification.proto`
**Port:** 50057 (host-mapped)

### Service

```protobuf
service NotificationService {
  rpc SendNotification(SendNotificationRequest) returns (Notification);
  rpc GetUserNotifications(GetUserNotificationsRequest) returns (GetUserNotificationsResponse);
  rpc UpdateNotificationPreferences(UpdateNotificationPreferencesRequest) returns (NotificationPreferences);
}
```

### Key Messages

| Message | Fields |
|---------|--------|
| `Notification` | `string id`, `string user_id`, `string type`, `string channel`, `string template`, `string title`, `string body`, `string recipient`, `string status`, `int64 created_at`, `int64 delivered_at`, `map<string, string> metadata` |
| `NotificationPreferences` | `string user_id`, `EmailPreferences email`, `PushPreferences push`, `SmsPreferences sms`, `int64 updated_at` |
| `SendNotificationRequest` | `string user_id`, `string type`, `string channel`, `string template`, `map<string, string> data` |
| `GetUserNotificationsRequest` | `string user_id`, `int32 page`, `int32 page_size`, `string type` |
| `GetUserNotificationsResponse` | `repeated Notification notifications`, `Pagination pagination` |
| `UpdateNotificationPreferencesRequest` | `string user_id`, `string channel`, `bool enabled` |

---

## SearchService

**Package:** `search.v1`
**Proto:** `proto/search/v1/search.proto`
**Port:** 50058 (host-mapped)

### Service

```protobuf
service SearchService {
  rpc SearchProducts(SearchProductsRequest) returns (SearchProductsResponse);
  rpc SuggestProducts(SuggestProductsRequest) returns (SuggestProductsResponse);
  rpc IndexProduct(IndexProductRequest) returns (IndexProductResponse);
  rpc ReindexCatalog(ReindexCatalogRequest) returns (ReindexCatalogResponse);
}
```

### Key Messages

| Message | Fields |
|---------|--------|
| `ProductHit` | `string id`, `string name`, `string description`, `string sku`, `string category_id`, `repeated string category_ids`, `string brand_id`, `string brand_name`, `double price`, `double compare_at_price`, `double cost_price`, `int32 quantity`, `double rating`, `int32 review_count`, `repeated string image_urls`, `map<string, string> metadata`, `double score`, `string status`, `bool is_featured`, `bool is_active` |
| `SearchProductsRequest` | `string query`, `repeated string category_ids`, `repeated string brand_ids`, `double min_price`, `double max_price`, `double min_rating`, `string sort_by`, `string sort_order`, `int32 page`, `int32 page_size` |
| `SearchProductsResponse` | `repeated ProductHit products`, `Pagination pagination`, `repeated Aggregation aggregations`, `double took_ms` |
| `SuggestProductsRequest` | `string query`, `int32 limit` |
| `SuggestProductsResponse` | `repeated Suggestion suggestions`, `double took_ms` |
| `Suggestion` | `string text`, `int32 count` |
| `IndexProductRequest` | `string product_id` |
| `IndexProductResponse` | `string product_id`, `bool indexed`, `string message` |
| `ReindexCatalogRequest` | (empty) |
| `ReindexCatalogResponse` | `int32 total_products`, `int32 indexed`, `int32 failed`, `string message` |
| `Aggregation` | `string key`, `string field`, `repeated AggBucket buckets` |
| `AggBucket` | `string key`, `int64 count` |

---

## SellerService

**Package:** `seller.v1`
**Proto:** `proto/seller/v1/seller.proto`
**Port:** 19090 (host-mapped)

### Service

```protobuf
service SellerService {
  // Seller Operations (7 methods)
  rpc RegisterSeller(RegisterSellerRequest) returns (Seller);
  rpc GetSeller(GetSellerRequest) returns (Seller);
  rpc GetSellerByUserId(GetSellerByUserIdRequest) returns (Seller);
  rpc UpdateSeller(UpdateSellerRequest) returns (Seller);
  rpc UpdateSellerStatus(UpdateSellerStatusRequest) returns (Seller);
  rpc DeleteSeller(DeleteSellerRequest) returns (Empty);

  // Account Operations (3 methods)
  rpc CreateSellerAccount(CreateSellerAccountRequest) returns (SellerAccount);
  rpc GetSellerAccount(GetSellerAccountRequest) returns (SellerAccount);
  rpc UpdateSellerAccount(UpdateSellerAccountRequest) returns (SellerAccount);

  // Document Operations (4 methods)
  rpc UploadSellerDocument(UploadSellerDocumentRequest) returns (SellerDocument);
  rpc GetSellerDocument(GetSellerDocumentRequest) returns (SellerDocument);
  rpc ListSellerDocuments(ListSellerDocumentsRequest) returns (ListSellerDocumentsResponse);
  rpc VerifySellerDocument(VerifySellerDocumentRequest) returns (SellerDocument);

  // Product Operations (2 methods)
  rpc GetSellerProducts(GetSellerProductsRequest) returns (GetSellerProductsResponse);
  rpc UpdateProductStatus(UpdateProductStatusRequest) returns (Product);

  // Order Operations (2 methods)
  rpc GetSellerOrders(GetSellerOrdersRequest) returns (GetSellerOrdersResponse);
  rpc UpdateOrderStatus(UpdateOrderStatusRequest) returns (Order);

  // Statistics (1 method)
  rpc GetSellerStats(GetSellerStatsRequest) returns (SellerStats);
}
```

### Key Messages

| Message | Fields |
|---------|--------|
| `Seller` | `string id`, `string user_id`, `string business_name`, `string business_description`, `string tax_id`, `string logo_url`, `string status`, `double rating`, `int32 total_ratings`, `int64 total_sales`, `int64 total_products`, `string verification_doc_url`, `Timestamp created_at`, `Timestamp updated_at` |
| `SellerAccount` | `string id`, `string seller_id`, `string bank_name`, `string account_number`, `string routing_number`, `string account_holder_name`, `string status`, `Timestamp created_at`, `Timestamp updated_at` |
| `SellerDocument` | `string id`, `string seller_id`, `string type`, `string file_url`, `string status`, `string verification_notes`, `Timestamp created_at`, `Timestamp updated_at` |
| `SellerStats` | `string seller_id`, `int64 total_orders`, `int64 pending_orders`, `int64 processing_orders`, `int64 shipped_orders`, `int64 delivered_orders`, `int64 cancelled_orders`, `double total_revenue`, `double average_order_value`, `double rating`, `int32 total_ratings`, `int64 total_products`, `int64 active_products`, `int32 low_stock_products`, `double monthly_revenue`, `int64 monthly_orders`, `double revenue_growth_rate` |

---

## BffService

**Package:** `bff.v1`
**Proto:** `proto/bff/v1/bff.proto`
**Port:** 50059 (host-mapped)

### Service

```protobuf
service BffService {
  rpc GetProductCatalog(ProductCatalogRequest) returns (ProductCatalogResponse);
  rpc GetProductDetails(ProductDetailsRequest) returns (ProductDetailsResponse);
  rpc GetCartWithPrices(CartWithPricesRequest) returns (CartWithPricesResponse);
  rpc Checkout(CheckoutRequest) returns (CheckoutResponse);
  rpc GetOrderHistory(GetOrderHistoryRequest) returns (GetOrderHistoryResponse);
  rpc GetUserProfile(GetUserProfileRequest) returns (UserProfileResponse);
  rpc GetSellerProfile(GetSellerProfileRequest) returns (SellerProfileResponse);
  rpc GetUserNotifications(GetUserNotificationsRequest) returns (UserNotificationsResponse);
}
```

### Key Messages

| Message | Fields |
|---------|--------|
| `ProductCatalogRequest` | `string query`, `string category`, `string brand`, `float min_price`, `float max_price`, `string sort`, `int32 page`, `int32 page_size` |
| `ProductCatalogResponse` | `repeated Product products`, `Pagination pagination` |
| `ProductDetailsRequest` | `string product_id` |
| `ProductDetailsResponse` | `Product product`, `SellerInfo seller`, `DeliveryInfo delivery`, `repeated Review reviews` |
| `CartWithPricesRequest` | `string user_id` |
| `CartWithPricesResponse` | `string cart_id`, `repeated CartItem items`, `float subtotal`, `float shipping_cost`, `float total`, `string currency` |
| `CheckoutRequest` | `string user_id`, `string cart_id`, `ShippingAddress shipping_address`, `string payment_method` |
| `CheckoutResponse` | `string order_id`, `string status`, `float total_amount`, `string currency`, `int64 created_at` |
| `GetOrderHistoryRequest` | `string user_id`, `int32 page`, `int32 page_size`, `string status` |
| `GetOrderHistoryResponse` | `repeated Order orders`, `Pagination pagination` |
| `GetUserProfileRequest` | `string user_id` |
| `UserProfileResponse` | `User user`, `repeated Address addresses`, `repeated WishlistItem wishlist` |
| `GetSellerProfileRequest` | `string seller_id`, `int32 page`, `int32 page_size` |
| `SellerProfileResponse` | `Seller seller`, `repeated Product products`, `Pagination pagination` |
| `GetUserNotificationsRequest` | `string user_id`, `int32 page`, `int32 page_size`, `bool unread_only` |
| `UserNotificationsResponse` | `repeated Notification notifications`, `Pagination pagination`, `int32 unread_count` |

---

## Code Generation

### Generate Python gRPC Code

```bash
# Generate from proto files
grpc_tools.protoc \
  -I proto \
  --python_out=. \
  --grpc_python_out=. \
  --pyi_out=. \
  proto/auth/v1/auth.proto
```

### Generate Go gRPC Code

```bash
protoc \
  -I proto \
  --go_out=. --go_opt=paths=source_relative \
  --go-grpc_out=. --go-grpc_opt=paths=source_relative \
  proto/auth/v1/auth.proto
```

### Generate TypeScript gRPC Code

```bash
grpc_tools_node_protoc \
  -I proto \
  --js_out=import_style=commonjs,binary:./gen \
  --grpc_out=./gen \
  --grpc_js_out=./gen \
  proto/auth/v1/auth.proto
```

### Generate from Docker

```bash
# From project root
docker run --rm \
  -v ${PWD}:/workspace \
  -w /workspace \
  grpcio/tools:latest \
  protoc -I proto \
    --python_out=. \
    --grpc_python_out=. \
    --pyi_out=. \
    proto/auth/v1/auth.proto
```

---

## Related Documentation

- [Auth Service API](api/auth-service.md)
- [Catalog Service API](api/catalog-service.md)
- [Order Service API](api/order-service.md)
- [Payment Service API](api/payment-service.md)
- [BFF Service API](api/bff-service.md)
- [Services Overview](services.md)
