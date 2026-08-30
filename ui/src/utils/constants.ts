// API Base URLs from environment
export const API_BASE_URL = import.meta.env.VITE_API_GATEWAY || 'http://localhost:8080';
export const API_CART_URL = import.meta.env.VITE_API_CART || 'http://localhost:8081';
export const API_CATALOG_URL = import.meta.env.VITE_API_CATALOG || 'http://localhost:8084';
export const API_SEARCH_URL = import.meta.env.VITE_API_SEARCH || 'http://localhost:8087';
export const API_ADMIN_URL = import.meta.env.VITE_API_ADMIN || 'http://localhost:8088';
export const API_SELLER_URL = import.meta.env.VITE_API_SELLER || 'http://localhost:8090';
export const API_PAYMENT_URL = import.meta.env.VITE_API_PAYMENT || 'http://localhost:8082';

// Local storage keys
export const STORAGE_KEYS = {
  ACCESS_TOKEN: 'access_token',
  REFRESH_TOKEN: 'refresh_token',
  ACCESS_EXPIRES_AT: 'access_expires_at',
  REFRESH_EXPIRES_AT: 'refresh_expires_at',
  USER: 'user',
  CART_ID: 'cart_id',
  DARK_MODE: 'dark_mode',
  RECENT_SEARCHES: 'recent_searches',
} as const;

// Default values
export const DEFAULTS = {
  PAGE_SIZE: 12,
  DEFAULT_PAGE: 1,
  MAX_RATING: 5,
  DEFAULT_SORT: 'relevance',
  SORT_OPTIONS: [
    { value: 'relevance', label: 'Relevance' },
    { value: 'price_asc', label: 'Price: Low to High' },
    { value: 'price_desc', label: 'Price: High to Low' },
    { value: 'rating', label: 'Highest Rated' },
    { value: 'newest', label: 'Newest First' },
    { value: 'name_asc', label: 'Name: A-Z' },
    { value: 'name_desc', label: 'Name: Z-A' },
  ] as const,
  CATEGORIES: [
    { id: 'all', name: 'All Categories', slug: 'all' },
    { id: 'electronics', name: 'Electronics', slug: 'electronics' },
    { id: 'clothing', name: 'Clothing & Fashion', slug: 'clothing' },
    { id: 'home', name: 'Home & Garden', slug: 'home' },
    { id: 'sports', name: 'Sports & Outdoors', slug: 'sports' },
    { id: 'books', name: 'Books', slug: 'books' },
    { id: 'toys', name: 'Toys & Games', slug: 'toys' },
    { id: 'beauty', name: 'Beauty & Health', slug: 'beauty' },
    { id: 'food', name: 'Food & Beverages', slug: 'food' },
  ],
  BRANDS: [
    { id: 'all', name: 'All Brands', slug: 'all' },
  ],
} as const;

// Route paths
export const ROUTES = {
  HOME: '/',
  PRODUCTS: '/products',
  PRODUCT_DETAIL: '/product/:id',
  CART: '/cart',
  LOGIN: '/login',
  REGISTER: '/register',
  PROFILE: '/profile',
  SELLER_DASHBOARD: '/seller/dashboard',
  ADMIN_DASHBOARD: '/admin/dashboard',
  SEARCH: '/search',
} as const;

// API endpoints
export const ENDPOINTS = {
  AUTH: {
    LOGIN: '/auth/login',
    REGISTER: '/auth/register',
    REFRESH: '/auth/refresh',
    LOGOUT: '/auth/logout',
    PROFILE: '/auth/profile',
    FORGOT_PASSWORD: '/auth/forgot-password',
  },
  PRODUCTS: {
    LIST: '/products',
    DETAIL: '/products',
    FEATURED: '/products/featured',
    CATEGORIES: '/products/categories',
    BRANDS: '/products/brands',
  },
  SEARCH: {
    QUERY: '/search/products',
    SUGGESTIONS: '/search/suggestions',
  },
  CART: {
    GET: '/cart',
    ADD: '/cart/items',
    UPDATE: '/cart/items',
    REMOVE: '/cart/items',
    CLEAR: '/cart',
    CHECKOUT: '/cart/checkout',
  },
  ORDERS: {
    LIST: '/orders',
    DETAIL: '/orders',
    USER_ORDERS: '/orders/user',
  },
  USERS: {
    LIST: '/admin/users',
    STATS: '/admin/stats',
  },
  SELLER: {
    INFO: '/seller/:seller_id',
    STATS: '/seller/:seller_id/stats',
    PRODUCTS: '/seller/:seller_id/products',
    PRODUCT_CREATE: '/seller/:seller_id/products',
    PRODUCT_UPDATE: '/seller/products/:product_id',
    PRODUCT_DELETE: '/seller/products/:product_id',
    ORDERS: '/seller/:seller_id/orders',
    CATEGORIES: '/seller/:seller_id/categories',
  },
} as const;

// Toast auto-dismiss durations (ms)
export const TOAST_DURATIONS = {
  SUCCESS: 3000,
  ERROR: 5000,
  WARNING: 4000,
  INFO: 3000,
} as const;

// Image placeholder
export const PLACEHOLDER_IMAGE =
  'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400" fill="%23e5e7eb"><rect width="400" height="400" rx="12"/><text x="50%25" y="50%25" dominant-baseline="middle" text-anchor="middle" fill="%239ca3af" font-size="18" font-family="sans-serif">No Image</text></svg>';
