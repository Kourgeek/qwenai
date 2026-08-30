import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  useMemo,
  type ReactNode,
} from 'react';
import type { CartItem, Cart, Product } from '../types';

interface CartContextType {
  items: CartItem[];
  isLoading: boolean;
  totalItems: number;
  totalPrice: number;
  addItem: (product: Product, quantity?: number) => Promise<void>;
  removeItem: (itemId: string) => Promise<void>;
  updateQuantity: (itemId: string, quantity: number) => Promise<void>;
  clearCart: () => Promise<void>;
}

const CartContext = createContext<CartContextType | undefined>(undefined);

const CART_STORAGE_KEY = 'hyperscale_cart_local';

function loadLocalCart(): CartItem[] {
  try {
    const stored = localStorage.getItem(CART_STORAGE_KEY);
    return stored ? JSON.parse(stored) : [];
  } catch {
    return [];
  }
}

function saveLocalCart(items: CartItem[]): void {
  try {
    localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(items));
  } catch {
    console.error('Failed to save cart to localStorage');
  }
}

export function CartProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<CartItem[]>(loadLocalCart);
  const [isLoading, setIsLoading] = useState(true);

  // Sync local cart on mount
  useEffect(() => {
    const syncCart = async () => {
      try {
        const { getCart } = await import('../services/cart');
        const cart = await getCart();
        if (cart.items && cart.items.length > 0) {
          setItems(cart.items);
        }
      } catch {
        // Use local cart as fallback
      } finally {
        setIsLoading(false);
      }
    };
    syncCart();
  }, []);

  // Persist items to localStorage whenever they change
  useEffect(() => {
    if (!isLoading) {
      saveLocalCart(items);
    }
  }, [items, isLoading]);

  const addItem = useCallback(async (product: Product, quantity: number = 1) => {
    try {
      const { addToCart: addToCartService } = await import('../services/cart');
      const { getCurrentUser } = await import('../services/auth');
      const user = getCurrentUser();

      if (user) {
        const newItem = await addToCartService({
          user_id: user.id,
          product_id: product.id,
          quantity,
        });
        setItems((prev) => {
          const existing = prev.find((item) => item.product_id === product.id);
          if (existing) {
            return prev.map((item) =>
              item.product_id === product.id
                ? { ...item, quantity: item.quantity + quantity, subtotal: item.unit_price * (item.quantity + quantity) }
                : item
            );
          }
          return [
            ...prev,
            {
              id: newItem.id || `local-${Date.now()}`,
              user_id: user.id,
              product_id: product.id,
              product_name: product.name,
              product_sku: product.sku,
              product_image_url: product.image_urls?.[0] || '',
              unit_price: product.price,
              quantity,
              subtotal: product.price * quantity,
              status: 'active',
            },
          ];
        });
      } else {
        // Local cart for anonymous users
        setItems((prev) => {
          const existing = prev.find((item) => item.product_id === product.id);
          if (existing) {
            return prev.map((item) =>
              item.product_id === product.id
                ? { ...item, quantity: item.quantity + quantity, subtotal: item.unit_price * (item.quantity + quantity) }
                : item
            );
          }
          return [
            ...prev,
            {
              id: `local-${Date.now()}`,
              user_id: '',
              product_id: product.id,
              product_name: product.name,
              product_sku: product.sku,
              product_image_url: product.image_urls?.[0] || '',
              unit_price: product.price,
              quantity,
              subtotal: product.price * quantity,
              status: 'active',
            },
          ];
        });
      }
    } catch (error) {
      console.error('Failed to add item to cart:', error);
    }
  }, []);

  const removeItem = useCallback(async (itemId: string) => {
    try {
      const { removeFromCart: removeFromCartService } = await import('../services/cart');
      const { getCurrentUser } = await import('../services/auth');
      const user = getCurrentUser();

      if (user) {
        await removeFromCartService(itemId);
      }
    } catch {
      // Silent fail for local cart
    } finally {
      setItems((prev) => prev.filter((item) => item.id !== itemId));
    }
  }, []);

  const updateQuantity = useCallback(async (itemId: string, quantity: number) => {
    if (quantity < 1) return;

    try {
      const { updateCartItem } = await import('../services/cart');
      const { getCurrentUser } = await import('../services/auth');
      const user = getCurrentUser();

      if (user) {
        await updateCartItem(itemId, quantity);
      }
    } catch {
      // Silent fail for local cart
    }

    setItems((prev) =>
      prev.map((item) =>
        item.id === itemId ? { ...item, quantity, subtotal: item.unit_price * quantity } : item
      )
    );
  }, []);

  const clearCart = useCallback(async () => {
    try {
      const { clearCart: clearCartService } = await import('../services/cart');
      await clearCartService();
    } catch {
      // Silent fail
    } finally {
      setItems([]);
    }
  }, []);

  const totalItems = useMemo(() => items.reduce((sum, item) => sum + item.quantity, 0), [items]);

  const totalPrice = useMemo(
    () => items.reduce((sum, item) => sum + item.subtotal, 0),
    [items]
  );

  const value = useMemo(
    () => ({ items, isLoading, totalItems, totalPrice, addItem, removeItem, updateQuantity, clearCart }),
    [items, isLoading, totalItems, totalPrice, addItem, removeItem, updateQuantity, clearCart]
  );

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}

export function useCart(): CartContextType {
  const context = useContext(CartContext);
  if (context === undefined) {
    throw new Error('useCart must be used within a CartProvider');
  }
  return context;
}

export default CartContext;
