import { api } from './api';
import { ENDPOINTS, STORAGE_KEYS } from '../utils/constants';
import type {
  Cart,
  CartItem,
  CartWithPrices,
  AddToCartRequest,
  Order,
} from '../types';

// Get cart ID from localStorage
function getCartId(): string | null {
  try {
    return localStorage.getItem(STORAGE_KEYS.CART_ID);
  } catch {
    return null;
  }
}

function saveCartId(cartId: string): void {
  try {
    localStorage.setItem(STORAGE_KEYS.CART_ID, cartId);
  } catch (e) {
    console.error('Failed to save cart ID to localStorage', e);
  }
}

// Get cart with prices (for frontend calculations)
export async function getCartWithPrices(): Promise<CartWithPrices> {
  const cartId = getCartId();
  if (!cartId) {
    // Create a new cart
    const response = await api.post<{ cart_id: string }>(ENDPOINTS.CART.GET);
    const newCartId = response.cart_id;
    saveCartId(newCartId);
    return getCartWithPrices();
  }

  const response = await api.get<CartWithPrices>(`${ENDPOINTS.CART.GET}/${cartId}/prices`);
  return response;
}

// Get current cart
export async function getCart(): Promise<Cart> {
  let cartId = getCartId();

  // If no cart ID, create one
  if (!cartId) {
    const response = await api.post<{ cart_id: string }>(ENDPOINTS.CART.GET);
    cartId = response.cart_id;
    saveCartId(cartId);
    return getCart(); // Recurse with new cart ID
  }

  const response = await api.get<Cart>(`${ENDPOINTS.CART.GET}/${cartId}`);
  return response;
}

// Add item to cart
export async function addToCart(item: AddToCartRequest): Promise<CartItem> {
  const response = await api.post<CartItem>(ENDPOINTS.CART.ADD, item);
  return response;
}

// Update cart item quantity
export async function updateCartItem(itemId: string, quantity: number): Promise<CartItem> {
  const response = await api.patch<CartItem>(`${ENDPOINTS.CART.UPDATE}/${itemId}`, { quantity });
  return response;
}

// Remove item from cart
export async function removeFromCart(itemId: string): Promise<void> {
  await api.delete(`${ENDPOINTS.CART.REMOVE}/${itemId}`);
}

// Clear entire cart
export async function clearCart(): Promise<void> {
  const cartId = getCartId();
  if (cartId) {
    await api.delete(`${ENDPOINTS.CART.CLEAR}/${cartId}`);
    localStorage.removeItem(STORAGE_KEYS.CART_ID);
  }
}

// Checkout cart
export async function checkoutCart(
  shippingAddress: { full_name: string; line1: string; line2?: string; city: string; state?: string; postal_code: string; country: string; phone?: string },
  paymentMethod?: string
): Promise<Order> {
  const cartId = getCartId();
  if (!cartId) throw new Error('No active cart');

  const response = await api.post<Order>(`${ENDPOINTS.CART.CHECKOUT}/${cartId}`, {
    shipping_address: shippingAddress,
    payment_method: paymentMethod,
  });
  return response;
}
