/**
 * Product service — handles product-related API calls.
 */

import { api } from './api';
import { ENDPOINTS, DEFAULTS } from '../utils/constants';
import type {
  Product,
  Category,
  Brand,
  SearchResponse,
  ApiResponse,
} from '../types';

// Get products with pagination
export async function getProducts(options?: {
  page?: number;
  page_size?: number;
  category?: string;
  brand?: string;
  sort?: string;
  min_price?: number;
  max_price?: number;
}): Promise<ApiResponse<Product[]>> {
  const params: Record<string, unknown> = {
    page: options?.page || DEFAULTS.DEFAULT_PAGE,
    page_size: options?.page_size || DEFAULTS.PAGE_SIZE,
  };

  if (options?.category) params.category = options.category;
  if (options?.brand) params.brand = options.brand;
  if (options?.sort) params.sort = options.sort;
  if (options?.min_price) params.min_price = options.min_price;
  if (options?.max_price) params.max_price = options.max_price;

  const response = await api.get<ApiResponse<Product[]>>(ENDPOINTS.PRODUCTS.LIST, params);
  return response;
}

// Get product by slug
export async function getProductBySlug(slug: string): Promise<Product> {
  const response = await api.get<Product>(`${ENDPOINTS.PRODUCTS.LIST}/${slug}`);
  return response;
}

// Get product by ID
export async function getProductById(id: string): Promise<Product> {
  const response = await api.get<Product>(`${ENDPOINTS.PRODUCTS.LIST}/${id}`);
  return response;
}

// Get featured products
export async function getFeaturedProducts(limit: number = 8): Promise<Product[]> {
  const response = await api.get<Product[]>(ENDPOINTS.PRODUCTS.FEATURED, { params: { limit } });
  return response;
}

// Get all categories
export async function getCategories(): Promise<Category[]> {
  const response = await api.get<Category[]>(ENDPOINTS.PRODUCTS.CATEGORIES);
  return response;
}

// Get all brands
export async function getBrands(): Promise<Brand[]> {
  const response = await api.get<Brand[]>(ENDPOINTS.PRODUCTS.BRANDS);
  return response;
}

// Search products
export async function searchProducts(
  query: string,
  options?: { page?: number; page_size?: number; category?: string }
): Promise<SearchResponse> {
  const params: Record<string, unknown> = {
    q: query,
    page: options?.page || DEFAULTS.DEFAULT_PAGE,
    page_size: options?.page_size || DEFAULTS.PAGE_SIZE,
  };
  if (options?.category) {
    params.category = options.category;
  }

  const response = await api.get<SearchResponse>(ENDPOINTS.SEARCH.QUERY, params);
  return response;
}

// Get search suggestions
export async function getSearchSuggestions(query: string, limit: number = 5): Promise<{ suggestions: string[] }> {
  const response = await api.get<{ suggestions: string[] }>(ENDPOINTS.SEARCH.SUGGESTIONS, {
    params: { q: query, limit },
  });
  return response;
}

// Get related products
export async function getRelatedProducts(productId: string, limit: number = 6): Promise<Product[]> {
  const response = await api.get<Product[]>(`${ENDPOINTS.PRODUCTS.DETAIL}/${productId}/related`, {
    params: { limit },
  });
  return response;
}
