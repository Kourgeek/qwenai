// ==================== Auth Types ====================

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterCredentials {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  access_expires_at?: number;
  refresh_expires_at?: number;
}

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  phone?: string;
  avatar_url?: string;
  role: string;
  created_at?: number;
  updated_at?: number;
}

// ==================== Product Types ====================

export interface Product {
  id: string;
  name: string;
  slug?: string;
  description: string;
  sku?: string;
  barcode?: string;
  category_id?: string;
  category_ids?: string[];
  brand_id?: string;
  brand_name?: string;
  seller_id: string;
  seller_name?: string;
  status: string;
  price: number;
  compare_at_price?: number;
  cost_price?: number;
  quantity: number;
  is_active: boolean;
  is_featured: boolean;
  image_urls: string[];
  tag_ids?: string[];
  avg_rating?: number;
  review_count?: number;
  metadata?: Record<string, string>;
  created_at?: number;
  updated_at?: number;
}

export interface ProductDetail extends Product {
  seller?: SellerInfo;
  delivery?: DeliveryInfo;
  reviews?: Review[];
}

export interface SellerInfo {
  id: string;
  name: string;
  description: string;
  avg_rating: number;
  product_count: number;
  logo_url?: string;
}

export interface DeliveryInfo {
  method: string;
  estimated_days: number;
  cost: number;
}

export interface Review {
  id: string;
  user_id: string;
  username: string;
  rating: number;
  comment: string;
  created_at: number;
}

export interface Category {
  id: string;
  name: string;
  slug: string;
  description: string;
  parent_id?: string;
  level?: number;
  path?: string;
  is_active: boolean;
  children?: Category[];
  product_count?: number;
}

export interface Brand {
  id: string;
  name: string;
  slug: string;
  description: string;
  logo_url?: string;
  is_active: boolean;
  product_count: number;
}

export interface Pagination {
  page: number;
  page_size: number;
  total: number;
  total_pages?: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  pagination: Pagination;
}

// ==================== Cart Types ====================

export interface CartItem {
  id: string;
  user_id: string;
  product_id: string;
  product_name: string;
  product_sku?: string;
  product_image_url?: string;
  unit_price: number;
  quantity: number;
  subtotal: number;
  status: string;
  created_at?: number;
  updated_at?: number;
}

export interface Cart {
  user_id: string;
  items: CartItem[];
  total_items: number;
  total_price: number;
  updated_at?: number;
}

export interface CartWithPrices {
  cart_id: string;
  items: CartItemWithPrice[];
  subtotal: number;
  shipping_cost: number;
  total: number;
  currency: string;
}

export interface CartItemWithPrice {
  id: string;
  product_id: string;
  product_name: string;
  sku?: string;
  quantity: number;
  unit_price: number;
  total_price: number;
  image_url?: string;
  is_available: boolean;
}

export interface AddToCartRequest {
  user_id: string;
  product_id: string;
  quantity: number;
}

// ==================== Order Types ====================

export interface Order {
  id: string;
  user_id: string;
  cart_id?: string;
  status: string;
  total_amount: number;
  currency: string;
  items: OrderItem[];
  shipping_address?: ShippingAddress;
  payment_method?: string;
  tracking_number?: string;
  created_at: number;
  updated_at: number;
  completed_at?: number;
  cancelled_at?: number;
}

export interface OrderItem {
  id: string;
  product_id: string;
  product_name: string;
  sku: string;
  quantity: number;
  unit_price: number;
  total_price: number;
  image_url?: string;
}

export interface ShippingAddress {
  full_name: string;
  line1: string;
  line2?: string;
  city: string;
  state?: string;
  postal_code: string;
  country: string;
  phone?: string;
}

// ==================== User Profile Types ====================

export interface Address {
  id: string;
  user_id: string;
  type: string;
  full_name: string;
  line1: string;
  line2?: string;
  city: string;
  state?: string;
  postal_code: string;
  country: string;
  phone?: string;
  is_default: boolean;
  created_at?: number;
  updated_at?: number;
}

export interface WishlistItem {
  id: string;
  user_id: string;
  product_id: string;
  product_name?: string;
  image_url?: string;
  price?: number;
  currency?: string;
  added_at: number;
}

export interface UserProfile {
  user: User;
  addresses: Address[];
  wishlist: WishlistItem[];
}

// ==================== Seller Types ====================

export interface Seller {
  id: string;
  user_id: string;
  business_name: string;
  business_description: string;
  tax_id?: string;
  logo_url?: string;
  status: string;
  rating: number;
  total_ratings: number;
  total_sales: number;
  total_products: number;
  verification_doc_url?: string;
  created_at: number;
  updated_at: number;
}

export interface SellerStats {
  seller_id: string;
  total_orders: number;
  pending_orders: number;
  processing_orders: number;
  shipped_orders: number;
  delivered_orders: number;
  cancelled_orders: number;
  total_revenue: number;
  average_order_value: number;
  rating: number;
  total_ratings: number;
  total_products: number;
  active_products: number;
  low_stock_products: number;
  monthly_revenue: number;
  monthly_orders: number;
  revenue_growth_rate: number;
}

// ==================== Notification Types ====================

export interface Notification {
  id: string;
  user_id: string;
  type: string;
  channel?: string;
  template?: string;
  title: string;
  message: string;
  body?: string;
  recipient?: string;
  status?: string;
  is_read: boolean;
  created_at: number;
  delivered_at?: number;
}

// ==================== Payment Types ====================

export interface Payment {
  id: string;
  order_id: string;
  user_id: string;
  amount: number;
  currency: string;
  status: string;
  provider: string;
  provider_payment_id?: string;
  payment_method_id?: string;
  created_at: number;
  updated_at: number;
  paid_at?: number;
}

// ==================== Admin Types ====================

export interface AdminUser extends User {
  role: string;
  status: string;
  last_login_at?: number;
}

export interface AdminStats {
  total_users: number;
  total_sellers: number;
  total_products: number;
  total_orders: number;
  total_revenue: number;
  monthly_revenue: number;
  monthly_orders: number;
  revenue_growth_rate: number;
  user_growth_rate: number;
}

// ==================== Search Types ====================

export interface ProductHit {
  id: string;
  name: string;
  description: string;
  sku: string;
  category_id: string;
  category_ids: string[];
  brand_id: string;
  brand_name: string;
  price: number;
  compare_at_price: number;
  cost_price: number;
  quantity: number;
  rating: number;
  review_count: number;
  image_urls: string[];
  metadata: Record<string, string>;
  score: number;
  status: string;
  is_featured: boolean;
  is_active: boolean;
}

export interface SearchAggregation {
  key: string;
  field: string;
  buckets: AggBucket[];
}

export interface AggBucket {
  key: string;
  count: number;
}

export interface SearchResponse {
  products: ProductHit[];
  pagination: Pagination;
  aggregations: SearchAggregation[];
  took_ms: number;
}

export interface Suggestion {
  text: string;
  count: number;
}

// ==================== API Response Types ====================

export interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

export interface ApiError {
  success: boolean;
  message: string;
  error?: string;
  status?: number;
}

// ==================== Product Filters ====================

export interface ProductFilters {
  query?: string;
  category?: string;
  brand?: string;
  min_price?: number;
  max_price?: number;
  sort?: string;
  page: number;
  page_size: number;
  is_featured?: boolean;
  min_rating?: number;
}

// ==================== Toast Types ====================

export type ToastType = 'success' | 'error' | 'warning' | 'info';

export interface ToastMessage {
  id: string;
  type: ToastType;
  title: string;
  description?: string;
}
