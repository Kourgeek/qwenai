/**
 * Seller API service — all calls to BFF seller endpoints.
 * Provides the sellerApi interface expected by SellerDashboard.
 */

import { api } from './api';
import { ENDPOINTS, STORAGE_KEYS } from '../utils/constants';
import type {
  Seller,
  SellerStats,
  Product,
  Category,
  Order,
} from '../types';

// ------------------------------------------------------------------
// Helpers
// ------------------------------------------------------------------

function getAccessToken(): string | null {
  try {
    return localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
  } catch {
    return null;
  }
}

function authHeaders(): Record<string, string> {
  const token = getAccessToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

// ------------------------------------------------------------------
// sellerApi — interface used by SellerDashboard
// ------------------------------------------------------------------

export const sellerApi = {
  /** Get seller profile info */
  async getProfile(sellerId: string): Promise<Seller> {
    return api.get<Seller>(ENDPOINTS.SELLER.INFO.replace(':seller_id', sellerId), undefined, {
      headers: authHeaders(),
    });
  },

  /** Get seller statistics */
  async getStats(sellerId: string): Promise<SellerStats> {
    return api.get<SellerStats>(ENDPOINTS.SELLER.STATS.replace(':seller_id', sellerId), undefined, {
      headers: authHeaders(),
    });
  },

  /** Get products for a seller */
  async getProducts(
    sellerId: string,
    options?: { limit?: number; offset?: number },
  ): Promise<{ products: Product[]; total: number }> {
    const params = new URLSearchParams({
      limit: String(options?.limit ?? 20),
      offset: String(options?.offset ?? 0),
    });
    const data = await api.get<{ items: Product[]; total: number }>(
      `${ENDPOINTS.SELLER.PRODUCTS.replace(':seller_id', sellerId)}?${params}`,
      undefined,
      { headers: authHeaders() },
    );
    return {
      products: data.items || [],
      total: data.total || 0,
    };
  },

  /** Create a new product */
  async createProduct(sellerId: string, productData: Partial<Product>): Promise<Product> {
    return api.post<Product>(
      ENDPOINTS.SELLER.PRODUCT_CREATE.replace(':seller_id', sellerId),
      productData,
      { headers: authHeaders() },
    );
  },

  /** Update a product */
  async updateProduct(productId: string, updates: Partial<Product>): Promise<Product> {
    return api.patch<Product>(
      ENDPOINTS.SELLER.PRODUCT_UPDATE.replace(':product_id', productId),
      updates,
      { headers: authHeaders() },
    );
  },

  /** Delete a product */
  async deleteProduct(productId: string): Promise<void> {
    await api.delete<void>(
      ENDPOINTS.SELLER.PRODUCT_DELETE.replace(':product_id', productId),
      { headers: authHeaders() },
    );
  },

  /** Toggle product active status */
  async toggleProductStatus(productId: string, isActive: boolean): Promise<Product> {
    return api.patch<Product>(
      ENDPOINTS.SELLER.PRODUCT_UPDATE.replace(':product_id', productId),
      { is_active: isActive },
      { headers: authHeaders() },
    );
  },

  /** Get categories for product creation */
  async getCategories(isActive = true): Promise<{ items: Category[]; total: number }> {
    const data = await api.get<{ items: Category[]; total: number }>(
      `${ENDPOINTS.SELLER.CATEGORIES}?is_active=${isActive}`,
      undefined,
      { headers: authHeaders() },
    );
    return data;
  },

  /** Get orders for a seller */
  async getOrders(
    sellerId: string,
    options?: { limit?: number; offset?: number },
  ): Promise<{ orders: Order[]; total: number }> {
    const params = new URLSearchParams({
      limit: String(options?.limit ?? 20),
      offset: String(options?.offset ?? 0),
    });
    const data = await api.get<{ items: Order[]; total: number }>(
      `${ENDPOINTS.SELLER.ORDERS.replace(':seller_id', sellerId)}?${params}`,
      undefined,
      { headers: authHeaders() },
    );
    return {
      orders: data.items || [],
      total: data.total || 0,
    };
  },
};

// ------------------------------------------------------------------
// Legacy exports (for backward compatibility)
// ------------------------------------------------------------------

export async function getSellerInfo(sellerId: string): Promise<Seller> {
  return sellerApi.getProfile(sellerId);
}

export async function getSellerStats(sellerId: string): Promise<SellerStats> {
  return sellerApi.getStats(sellerId);
}

export async function getSellerProducts(
  sellerId: string,
  options?: { limit?: number; offset?: number },
): Promise<{ items: Product[]; total: number; skip: number; limit: number }> {
  const result = await sellerApi.getProducts(sellerId, options);
  return {
    items: result.products,
    total: result.total,
    skip: options?.offset ?? 0,
    limit: options?.limit ?? 20,
  };
}

export async function createProduct(
  sellerId: string,
  productData: Partial<Product>,
): Promise<Product> {
  return sellerApi.createProduct(sellerId, productData);
}

export async function updateProduct(
  productId: string,
  updates: Partial<Product>,
): Promise<Product> {
  return sellerApi.updateProduct(productId, updates);
}

export async function deleteProduct(productId: string): Promise<void> {
  return sellerApi.deleteProduct(productId);
}

export async function getCategories(isActive = true): Promise<{ items: Category[]; total: number }> {
  return sellerApi.getCategories(isActive);
}

export async function getSellerOrders(
  sellerId: string,
  options?: { limit?: number; offset?: number },
): Promise<{ items: Order[]; total: number; skip: number; limit: number }> {
  const result = await sellerApi.getOrders(sellerId, options);
  return {
    items: result.orders,
    total: result.total,
    skip: options?.offset ?? 0,
    limit: options?.limit ?? 20,
  };
}
