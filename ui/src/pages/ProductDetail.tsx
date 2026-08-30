import { useState, useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  Star,
  ShoppingCart,
  Heart,
  Share2,
  Truck,
  Shield,
  ArrowLeft,
  Minus,
  Plus,
} from 'lucide-react';
import ProductCard from '../components/ProductCard';
import { getProductById, getRelatedProducts } from '../services/products';
import { useCart } from '../contexts/CartContext';
import { useAuth } from '../contexts/AuthContext';
import { toast } from '../components/Toast';
import type { ProductDetail } from '../types';

function StarRating({ rating, size = 18 }: { rating: number; size?: number }) {
  return (
    <div className="flex items-center gap-0.5">
      {Array.from({ length: 5 }).map((_, i) => (
        <Star
          key={i}
          size={size}
          className={i < Math.floor(rating) ? 'fill-amber-400 text-amber-400' : 'text-gray-300 dark:text-gray-600'}
        />
      ))}
    </div>
  );
}

export default function ProductDetail() {
  const { id } = useParams<{ id: string }>();
  const [product, setProduct] = useState<ProductDetail | null>(null);
  const [relatedProducts, setRelatedProducts] = useState<ProductDetail[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeImage, setActiveImage] = useState(0);
  const [quantity, setQuantity] = useState(1);
  const [isWishlisted, setIsWishlisted] = useState(false);
  const [activeTab, setActiveTab] = useState<'description' | 'reviews'>('description');
  const { addItem } = useCart();
  const { isAuthenticated } = useAuth();

  useEffect(() => {
    const loadData = async () => {
      if (!id) return;
      setLoading(true);
      try {
        const [detail, related] = await Promise.all([
          getProductById(id),
          getRelatedProducts(id, 6),
        ]);
        setProduct(detail);
        setRelatedProducts(related);
      } catch (error) {
        console.error('Failed to load product:', error);
        toast.error('Failed to load product details');
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, [id]);

  const handleAddToCart = useCallback(() => {
    if (!product) return;
    if (!isAuthenticated) {
      toast.warning('Please sign in to add items to cart');
      window.location.href = `/login?redirect=/product/${id}`;
      return;
    }
    addItem(product, quantity);
    toast.success('Added to cart!', product.name);
  }, [product, quantity, addItem, isAuthenticated, id]);

  const handleBuyNow = useCallback(() => {
    if (!product) return;
    if (!isAuthenticated) {
      window.location.href = `/login?redirect=/product/${id}`;
      return;
    }
    addItem(product, quantity);
    window.location.href = '/cart';
  }, [product, quantity, addItem, isAuthenticated, id]);

  if (loading) {
    return (
      <div className="min-h-screen pt-24 lg:pt-28 pb-16 bg-gray-50 dark:bg-gray-950">
        <div className="max-w-7xl mx-auto px-4">
          <div className="animate-pulse grid lg:grid-cols-2 gap-8">
            <div className="aspect-square bg-gray-200 dark:bg-gray-800 rounded-2xl" />
            <div className="space-y-4">
              <div className="h-8 bg-gray-200 dark:bg-gray-800 rounded w-3/4" />
              <div className="h-4 bg-gray-200 dark:bg-gray-800 rounded w-1/2" />
              <div className="h-10 bg-gray-200 dark:bg-gray-800 rounded w-1/4" />
              <div className="h-24 bg-gray-200 dark:bg-gray-800 rounded" />
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!product) {
    return (
      <div className="min-h-screen pt-24 lg:pt-28 pb-16 bg-gray-50 dark:bg-gray-950 flex items-center justify-center">
        <div className="text-center">
          <div className="text-6xl mb-4">😕</div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Product not found</h2>
          <p className="text-gray-500 dark:text-gray-400 mb-6">The product you're looking for doesn't exist.</p>
          <Link to="/products" className="btn-primary">Browse Products</Link>
        </div>
      </div>
    );
  }

  const images = product.image_urls && product.image_urls.length > 0 ? product.image_urls : [];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950 pt-24 lg:pt-28 pb-16">
      <div className="max-w-7xl mx-auto px-4">
        {/* Breadcrumb */}
        <nav className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400 mb-6">
          <Link to="/" className="hover:text-primary-600 dark:hover:text-primary-400 transition-colors">Home</Link>
          <span>/</span>
          <Link to="/products" className="hover:text-primary-600 dark:hover:text-primary-400 transition-colors">Products</Link>
          <span>/</span>
          <span className="text-gray-900 dark:text-white font-medium truncate">{product.name}</span>
        </nav>

        {/* Product Section */}
        <div className="grid lg:grid-cols-2 gap-8 mb-12">
          {/* Images */}
          <div>
            <div className="aspect-square rounded-2xl overflow-hidden bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 mb-4">
              {images[activeImage] ? (
                <img
                  src={images[activeImage]}
                  alt={product.name}
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-gray-400">
                  <span className="text-6xl">📦</span>
                </div>
              )}
            </div>
            {images.length > 1 && (
              <div className="flex gap-3 overflow-x-auto pb-2">
                {images.map((img, idx) => (
                  <button
                    key={idx}
                    onClick={() => setActiveImage(idx)}
                    className={`w-16 h-16 flex-shrink-0 rounded-xl overflow-hidden border-2 transition-colors ${
                      activeImage === idx
                        ? 'border-primary-500'
                        : 'border-transparent hover:border-gray-300 dark:hover:border-gray-600'
                    }`}
                  >
                    <img src={img} alt="" className="w-full h-full object-cover" />
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Info */}
          <div>
            {product.brand_name && (
              <span className="text-sm text-primary-600 dark:text-primary-400 font-medium">{product.brand_name}</span>
            )}
            <h1 className="text-2xl lg:text-3xl font-bold text-gray-900 dark:text-white mt-1 mb-3">
              {product.name}
            </h1>

            {/* Rating */}
            {product.avg_rating !== undefined && (
              <div className="flex items-center gap-2 mb-4">
                <StarRating rating={product.avg_rating} />
                <span className="text-sm text-gray-500 dark:text-gray-400">
                  {product.avg_rating.toFixed(1)} ({product.review_count || 0} reviews)
                </span>
              </div>
            )}

            {/* Price */}
            <div className="flex items-baseline gap-3 mb-6">
              <span className="text-3xl font-bold text-gray-900 dark:text-white">
                ${product.price.toFixed(2)}
              </span>
              {product.compare_at_price && product.compare_at_price > product.price && (
                <span className="text-lg text-gray-400 line-through">
                  ${product.compare_at_price.toFixed(2)}
                </span>
              )}
              {product.compare_at_price && product.compare_at_price > product.price && (
                <span className="badge badge-danger bg-red-500 text-white">
                  -{Math.round(((product.compare_at_price - product.price) / product.compare_at_price) * 100)}%
                </span>
              )}
            </div>

            {/* Description */}
            <p className="text-gray-600 dark:text-gray-400 mb-6 leading-relaxed">
              {product.description}
            </p>

            {/* Quantity */}
            <div className="flex items-center gap-4 mb-6">
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Quantity:</span>
              <div className="flex items-center border border-gray-200 dark:border-gray-700 rounded-xl overflow-hidden">
                <button
                  onClick={() => setQuantity(Math.max(1, quantity - 1))}
                  className="p-2.5 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                  disabled={quantity <= 1}
                >
                  <Minus size={16} />
                </button>
                <span className="w-12 text-center font-semibold text-gray-900 dark:text-white">{quantity}</span>
                <button
                  onClick={() => setQuantity(quantity + 1)}
                  className="p-2.5 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                  disabled={quantity >= product.quantity}
                >
                  <Plus size={16} />
                </button>
              </div>
              <span className="text-sm text-gray-500 dark:text-gray-400">
                {product.quantity > 0 ? `${product.quantity} in stock` : 'Out of stock'}
              </span>
            </div>

            {/* Actions */}
            <div className="flex gap-3 mb-6">
              <button
                onClick={handleAddToCart}
                disabled={product.quantity === 0}
                className="btn-primary flex-1 gap-2 text-base py-3"
              >
                <ShoppingCart size={20} />
                Add to Cart
              </button>
              <button
                onClick={handleBuyNow}
                disabled={product.quantity === 0}
                className="btn-primary flex-1 gap-2 text-base py-3 bg-gradient-to-r from-accent-500 to-amber-500 hover:from-accent-600 hover:to-amber-600 shadow-amber-500/25"
              >
                Buy Now
              </button>
              <button
                onClick={() => setIsWishlisted(!isWishlisted)}
                className={`p-3 rounded-xl border transition-colors ${
                  isWishlisted
                    ? 'border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-950/30 text-red-500'
                    : 'border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 text-gray-400'
                }`}
              >
                <Heart size={20} className={isWishlisted ? 'fill-red-500' : ''} />
              </button>
              <button className="p-3 rounded-xl border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 text-gray-400 transition-colors">
                <Share2 size={20} />
              </button>
            </div>

            {/* Features */}
            <div className="grid grid-cols-3 gap-4 p-4 bg-gray-50 dark:bg-gray-900/50 rounded-xl">
              <div className="flex flex-col items-center gap-2 text-center">
                <Truck size={20} className="text-primary-600 dark:text-primary-400" />
                <span className="text-xs text-gray-600 dark:text-gray-400">Free Shipping</span>
              </div>
              <div className="flex flex-col items-center gap-2 text-center">
                <Shield size={20} className="text-primary-600 dark:text-primary-400" />
                <span className="text-xs text-gray-600 dark:text-gray-400">2 Year Warranty</span>
              </div>
              <div className="flex flex-col items-center gap-2 text-center">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-primary-600 dark:text-primary-400">
                  <path d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  <path d="M9 12l2 2 4-4" />
                </svg>
                <span className="text-xs text-gray-600 dark:text-gray-400">30-Day Returns</span>
              </div>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="mb-12">
          <div className="flex border-b border-gray-200 dark:border-gray-800 mb-6">
            <button
              onClick={() => setActiveTab('description')}
              className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'description'
                  ? 'border-primary-500 text-primary-600 dark:text-primary-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
              }`}
            >
              Description
            </button>
            <button
              onClick={() => setActiveTab('reviews')}
              className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'reviews'
                  ? 'border-primary-500 text-primary-600 dark:text-primary-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
              }`}
            >
              Reviews ({product.review_count || 0})
            </button>
          </div>

          {activeTab === 'description' && (
            <div className="prose dark:prose-invert max-w-none">
              <p className="text-gray-600 dark:text-gray-400 leading-relaxed whitespace-pre-wrap">
                {product.description}
              </p>
            </div>
          )}

          {activeTab === 'reviews' && (
            <div>
              {product.reviews && product.reviews.length > 0 ? (
                <div className="space-y-4">
                  {product.reviews.map((review) => (
                    <div key={review.id} className="card p-5">
                      <div className="flex items-center gap-3 mb-3">
                        <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-primary-600 rounded-full flex items-center justify-center text-white font-semibold text-sm">
                          {review.username?.[0]?.toUpperCase() || 'U'}
                        </div>
                        <div>
                          <p className="font-semibold text-sm text-gray-900 dark:text-white">{review.username}</p>
                          <StarRating rating={review.rating} size={12} />
                        </div>
                      </div>
                      <p className="text-gray-600 dark:text-gray-400 text-sm">{review.comment}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12">
                  <div className="text-5xl mb-3">📝</div>
                  <p className="text-gray-500 dark:text-gray-400">No reviews yet. Be the first to review!</p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Related Products */}
        {relatedProducts.length > 0 && (
          <div>
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl lg:text-2xl font-bold text-gray-900 dark:text-white">Related Products</h2>
              <Link to="/products" className="btn-ghost text-sm font-medium">
                View all <ArrowLeft size={16} className="rotate-180" />
              </Link>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
              {relatedProducts.slice(0, 4).map((p) => (
                <ProductCard key={p.id} product={p} />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
