import { useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, Trash2, ShoppingBag, Package } from 'lucide-react';
import CartItemCard from '../components/CartItem';
import { useCart } from '../contexts/CartContext';
import { useAuth } from '../contexts/AuthContext';
import { toast } from '../components/Toast';
import { clearCart } from '../services/cart';
import type { ShippingAddress } from '../types';

export default function Cart() {
  const { items, isLoading, removeItem, updateQuantity, clearCart, totalPrice, totalItems } = useCart();
  const { isAuthenticated } = useAuth();
  const [shipping, setShipping] = useState<ShippingAddress>({
    full_name: '',
    line1: '',
    city: '',
    postal_code: '',
    country: '',
  });
  const [showCheckout, setShowCheckout] = useState(false);
  const [processing, setProcessing] = useState(false);

  const shippingCost = totalPrice > 50 ? 0 : 9.99;
  const tax = totalPrice * 0.08;
  const orderTotal = totalPrice + shippingCost + tax;

  const handleClearCart = useCallback(async () => {
    await clearCart();
    toast.success('Cart cleared');
  }, [clearCart]);

  const handleCheckout = useCallback(async () => {
    if (!isAuthenticated) {
      window.location.href = `/login?redirect=/cart`;
      return;
    }

    if (!shipping.full_name || !shipping.line1 || !shipping.city || !shipping.postal_code || !shipping.country) {
      toast.warning('Please fill in all shipping fields');
      return;
    }

    setProcessing(true);
    try {
      await clearCart(shipping);
      await clearCart();
      setShowCheckout(false);
      toast.success('Order placed successfully! 🎉');
      window.location.href = '/profile';
    } catch {
      toast.error('Failed to place order. Please try again.');
    } finally {
      setProcessing(false);
    }
  }, [isAuthenticated, shipping, clearCart]);

  if (isLoading) {
    return (
      <div className="min-h-screen pt-24 lg:pt-28 pb-16 bg-gray-50 dark:bg-gray-950 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin" />
          <p className="text-gray-500 dark:text-gray-400 text-sm">Loading your cart...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950 pt-24 lg:pt-28 pb-16">
      <div className="max-w-7xl mx-auto px-4">
        {/* Breadcrumb */}
        <nav className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400 mb-6">
          <Link to="/" className="hover:text-primary-600 dark:hover:text-primary-400 transition-colors">Home</Link>
          <span>/</span>
          <span className="text-gray-900 dark:text-white font-medium">Shopping Cart</span>
        </nav>

        <h1 className="text-2xl lg:text-3xl font-bold text-gray-900 dark:text-white mb-8">
          Shopping Cart ({totalItems} {totalItems === 1 ? 'item' : 'items'})
        </h1>

        {items.length === 0 ? (
          /* Empty cart */
          <div className="text-center py-20 card">
            <div className="text-7xl mb-6">🛒</div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Your cart is empty</h2>
            <p className="text-gray-500 dark:text-gray-400 mb-8 max-w-md mx-auto">
              Looks like you haven't added anything to your cart yet. Start shopping to find great deals!
            </p>
            <Link to="/products" className="btn-primary text-base gap-2">
              <ShoppingBag size={20} />
              Start Shopping
            </Link>
          </div>
        ) : showCheckout ? (
          /* Checkout form */
          <div className="grid lg:grid-cols-5 gap-8">
            <div className="lg:col-span-3">
              <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-6">Shipping Information</h2>
              <div className="card p-6 space-y-4">
                <div className="grid sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Full Name</label>
                    <input
                      type="text"
                      value={shipping.full_name}
                      onChange={(e) => setShipping((p) => ({ ...p, full_name: e.target.value }))}
                      className="input"
                      placeholder="John Doe"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Phone</label>
                    <input
                      type="tel"
                      value={shipping.phone || ''}
                      onChange={(e) => setShipping((p) => ({ ...p, phone: e.target.value }))}
                      className="input"
                      placeholder="+1 234 567 890"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Address</label>
                  <input
                    type="text"
                    value={shipping.line1}
                    onChange={(e) => setShipping((p) => ({ ...p, line1: e.target.value }))}
                    className="input"
                    placeholder="123 Main St"
                  />
                </div>
                <div className="grid sm:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">City</label>
                    <input
                      type="text"
                      value={shipping.city}
                      onChange={(e) => setShipping((p) => ({ ...p, city: e.target.value }))}
                      className="input"
                      placeholder="San Francisco"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">State</label>
                    <input
                      type="text"
                      value={shipping.state || ''}
                      onChange={(e) => setShipping((p) => ({ ...p, state: e.target.value }))}
                      className="input"
                      placeholder="California"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Postal Code</label>
                    <input
                      type="text"
                      value={shipping.postal_code}
                      onChange={(e) => setShipping((p) => ({ ...p, postal_code: e.target.value }))}
                      className="input"
                      placeholder="94102"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Country</label>
                  <input
                    type="text"
                    value={shipping.country}
                    onChange={(e) => setShipping((p) => ({ ...p, country: e.target.value }))}
                    className="input"
                    placeholder="United States"
                  />
                </div>
                <div className="flex gap-3 pt-4">
                  <button onClick={() => setShowCheckout(false)} className="btn-secondary gap-2">
                    <ArrowLeft size={18} />
                    Back to Cart
                  </button>
                  <button
                    onClick={handleCheckout}
                    disabled={processing}
                    className="btn-primary flex-1 gap-2"
                  >
                    {processing ? (
                      <>
                        <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        Processing...
                      </>
                    ) : (
                      <>
                        <Package size={18} />
                        Place Order — ${orderTotal.toFixed(2)}
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>

            {/* Order summary */}
            <div className="lg:col-span-2">
              <div className="card p-6 sticky top-28">
                <h3 className="font-bold text-gray-900 dark:text-white mb-4">Order Summary</h3>
                <div className="space-y-3 mb-4">
                  {items.map((item) => (
                    <div key={item.id} className="flex items-center gap-3">
                      <div className="w-12 h-12 rounded-lg overflow-hidden bg-gray-100 dark:bg-gray-800 flex-shrink-0">
                        {item.product_image_url ? (
                          <img src={item.product_image_url} alt="" className="w-full h-full object-cover" />
                        ) : (
                          <span className="text-xs">📦</span>
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-gray-900 dark:text-white truncate">{item.product_name}</p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">Qty: {item.quantity}</p>
                      </div>
                      <span className="text-sm font-semibold text-gray-900 dark:text-white">
                        ${item.subtotal.toFixed(2)}
                      </span>
                    </div>
                  ))}
                </div>
                <hr className="my-4" />
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between text-gray-600 dark:text-gray-400">
                    <span>Subtotal</span>
                    <span>${totalPrice.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between text-gray-600 dark:text-gray-400">
                    <span>Shipping</span>
                    <span>{shippingCost === 0 ? 'Free' : `$${shippingCost.toFixed(2)}`}</span>
                  </div>
                  <div className="flex justify-between text-gray-600 dark:text-gray-400">
                    <span>Tax</span>
                    <span>${tax.toFixed(2)}</span>
                  </div>
                  <hr />
                  <div className="flex justify-between font-bold text-lg text-gray-900 dark:text-white">
                    <span>Total</span>
                    <span>${orderTotal.toFixed(2)}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ) : (
          /* Cart items */
          <div className="grid lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2 space-y-4">
              {items.map((item) => (
                <CartItemCard
                  key={item.id}
                  item={item}
                  onUpdateQuantity={updateQuantity}
                  onRemove={removeItem}
                />
              ))}
              <button onClick={handleClearCart} className="btn-danger gap-2 text-sm">
                <Trash2 size={16} />
                Clear Cart
              </button>
            </div>

            {/* Order summary */}
            <div>
              <div className="card p-6 sticky top-28">
                <h3 className="font-bold text-gray-900 dark:text-white mb-4">Order Summary</h3>
                <div className="space-y-3 mb-4">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600 dark:text-gray-400">Subtotal ({totalItems} items)</span>
                    <span className="font-semibold text-gray-900 dark:text-white">${totalPrice.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600 dark:text-gray-400">Shipping</span>
                    <span className={shippingCost === 0 ? 'text-green-600 dark:text-green-400 font-medium' : 'font-semibold text-gray-900 dark:text-white'}>
                      {shippingCost === 0 ? 'Free' : `$${shippingCost.toFixed(2)}`}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600 dark:text-gray-400">Tax</span>
                    <span className="font-semibold text-gray-900 dark:text-white">${tax.toFixed(2)}</span>
                  </div>
                </div>
                <hr className="my-4" />
                <div className="flex justify-between font-bold text-xl text-gray-900 dark:text-white mb-6">
                  <span>Total</span>
                  <span>${orderTotal.toFixed(2)}</span>
                </div>
                {shippingCost > 0 && (
                  <p className="text-xs text-gray-500 dark:text-gray-400 mb-4 text-center">
                    Add ${(50 - totalPrice).toFixed(2)} more for free shipping!
                  </p>
                )}
                <button
                  onClick={() => setShowCheckout(true)}
                  className="btn-primary w-full text-base gap-2 py-3"
                >
                  <Package size={20} />
                  Proceed to Checkout
                </button>
                <Link to="/products" className="block text-center text-sm text-primary-600 dark:text-primary-400 mt-4 hover:underline">
                  Continue Shopping
                </Link>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
