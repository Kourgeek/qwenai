import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowRight,
  ShoppingBag,
  Shield,
  Truck,
  Headphones,
  Star,
  TrendingUp,
  Zap,
  Gift,
  ChevronRight,
} from 'lucide-react';
import ProductCard from '../components/ProductCard';
import SearchBar from '../components/SearchBar';
import { getFeaturedProducts, getCategories } from '../services/products';
import type { Product } from '../types';

const CATEGORIES = [
  { id: 'electronics', name: 'Electronics', icon: '💻', color: 'from-blue-500 to-blue-600' },
  { id: 'clothing', name: 'Fashion', icon: '👔', color: 'from-pink-500 to-rose-500' },
  { id: 'home', name: 'Home & Garden', icon: '🏠', color: 'from-green-500 to-emerald-500' },
  { id: 'sports', name: 'Sports', icon: '⚽', color: 'from-orange-500 to-amber-500' },
  { id: 'books', name: 'Books', icon: '📚', color: 'from-purple-500 to-violet-500' },
  { id: 'beauty', name: 'Beauty', icon: '💄', color: 'from-fuchsia-500 to-pink-500' },
  { id: 'toys', name: 'Toys', icon: '🎮', color: 'from-cyan-500 to-teal-500' },
  { id: 'food', name: 'Food', icon: '🍕', color: 'from-red-500 to-orange-500' },
];

const FEATURES = [
  { icon: Shield, title: 'Secure Payments', desc: '256-bit SSL encryption' },
  { icon: Truck, title: 'Free Shipping', desc: 'On orders over $50' },
  { icon: Headphones, title: '24/7 Support', desc: 'Dedicated help center' },
  { icon: Zap, title: 'Fast Delivery', desc: 'Express options available' },
];

export default function Home() {
  const [featuredProducts, setFeaturedProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [featured] = await Promise.all([
          getFeaturedProducts(8),
          getCategories(),
        ]);
        setFeaturedProducts(featured);
      } catch (error) {
        console.error('Failed to load home data:', error);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  const handleSearch = useCallback((query: string) => {
    window.location.href = `/products?query=${encodeURIComponent(query)}`;
  }, []);

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-br from-primary-600 via-primary-700 to-primary-900 dark:from-primary-950 dark:via-primary-900 dark:to-gray-950">
        {/* Background pattern */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-10 left-10 w-72 h-72 bg-white rounded-full blur-3xl" />
          <div className="absolute bottom-10 right-10 w-96 h-96 bg-accent-400 rounded-full blur-3xl" />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-primary-300 rounded-full blur-3xl" />
        </div>

        <div className="relative max-w-7xl mx-auto px-4 py-20 sm:py-28 lg:py-36">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div className="text-center lg:text-left">
              <span className="inline-block px-4 py-1.5 bg-white/20 backdrop-blur-sm rounded-full text-sm text-white font-medium mb-6">
                New arrivals just dropped
              </span>
              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black text-white leading-tight mb-6">
                Discover Everything
                <br />
                <span className="bg-gradient-to-r from-accent-300 to-amber-200 bg-clip-text text-transparent">
                  You Need
                </span>
              </h1>
              <p className="text-lg text-primary-100 mb-8 max-w-lg mx-auto lg:mx-0">
                Shop millions of products from trusted sellers. From electronics to fashion, find it all at the best prices.
              </p>

              {/* Search */}
              <div className="max-w-xl mx-auto lg:mx-0">
                <SearchBar onSearch={handleSearch} />
              </div>

              <div className="flex items-center justify-center lg:justify-start gap-6 mt-8 text-sm text-primary-200">
                <span className="flex items-center gap-2">
                  <ShoppingBag size={16} />
                  10K+ Products
                </span>
                <span className="flex items-center gap-2">
                  <Star size={16} className="fill-amber-400 text-amber-400" />
                  4.8 Rating
                </span>
              </div>
            </div>

            {/* Hero visual */}
            <div className="hidden lg:flex justify-center">
              <div className="relative">
                <div className="w-80 h-80 bg-gradient-to-br from-white/10 to-white/5 backdrop-blur-sm rounded-3xl border border-white/20 flex items-center justify-center">
                  <div className="text-center">
                    <div className="text-8xl mb-4">🛍️</div>
                    <p className="text-white/80 font-medium">Shop Smart</p>
                  </div>
                </div>
                {/* Floating badges */}
                <div className="absolute -top-4 -right-4 px-4 py-2 bg-accent-400 text-white rounded-xl font-bold text-sm shadow-lg animate-bounce">
                  50% OFF
                </div>
                <div className="absolute -bottom-2 -left-4 px-4 py-2 bg-white dark:bg-gray-800 text-gray-900 rounded-xl font-semibold text-sm shadow-lg">
                  Free Shipping
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-12 bg-white dark:bg-gray-900 border-b border-gray-100 dark:border-gray-800">
        <div className="max-w-7xl mx-auto px-4">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
            {FEATURES.map((feature) => (
              <div key={feature.title} className="flex items-center gap-4 p-4">
                <div className="w-12 h-12 rounded-xl bg-primary-50 dark:bg-primary-950/50 flex items-center justify-center flex-shrink-0">
                  <feature.icon size={22} className="text-primary-600 dark:text-primary-400" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900 dark:text-white text-sm">{feature.title}</h3>
                  <p className="text-xs text-gray-500 dark:text-gray-400">{feature.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Categories */}
      <section className="py-16 bg-gray-50 dark:bg-gray-950">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="text-2xl lg:text-3xl font-bold text-gray-900 dark:text-white">Shop by Category</h2>
              <p className="text-gray-500 dark:text-gray-400 mt-1">Browse our wide selection</p>
            </div>
            <Link to="/products" className="btn-ghost text-sm font-medium">
              View all <ChevronRight size={16} />
            </Link>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-8 gap-4">
            {CATEGORIES.map((cat) => (
              <Link
                key={cat.id}
                to={`/products?category=${cat.id}`}
                className="group flex flex-col items-center gap-3 p-4 card-hover cursor-pointer"
              >
                <div className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${cat.color} flex items-center justify-center text-2xl shadow-md group-hover:shadow-lg transition-shadow`}>
                  {cat.icon}
                </div>
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300 group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors text-center">
                  {cat.name}
                </span>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Featured Products */}
      <section className="py-16 bg-white dark:bg-gray-900">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="text-2xl lg:text-3xl font-bold text-gray-900 dark:text-white">Featured Products</h2>
              <p className="text-gray-500 dark:text-gray-400 mt-1">Handpicked just for you</p>
            </div>
            <Link to="/products?is_featured=true" className="btn-ghost text-sm font-medium">
              View all <ChevronRight size={16} />
            </Link>
          </div>
          {loading ? (
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4 lg:gap-6">
              {Array.from({ length: 8 }).map((_, i) => (
                <ProductCard key={i} product={{
                  id: `skeleton-${i}`,
                  name: '',
                  description: '',
                  price: 0,
                  quantity: 0,
                  is_active: true,
                  is_featured: false,
                  image_urls: [],
                  status: 'draft',
                  seller_id: '',
                } as Product} loading />
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4 lg:gap-6">
              {featuredProducts.slice(0, 8).map((product) => (
                <ProductCard key={product.id} product={product} />
              ))}
            </div>
          )}
        </div>
      </section>

      {/* Promotions Banner */}
      <section className="py-16 bg-gradient-to-r from-primary-600 to-primary-700 dark:from-primary-800 dark:to-primary-900 relative overflow-hidden">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-0 right-0 w-96 h-96 bg-accent-400 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2" />
          <div className="absolute bottom-0 left-0 w-72 h-72 bg-white rounded-full blur-3xl translate-y-1/2 -translate-x-1/2" />
        </div>
        <div className="relative max-w-7xl mx-auto px-4">
          <div className="grid lg:grid-cols-2 gap-8 items-center">
            <div>
              <span className="inline-flex items-center gap-2 px-3 py-1 bg-white/20 backdrop-blur-sm rounded-full text-sm text-white font-medium mb-4">
                <Gift size={14} />
                Limited Offer
              </span>
              <h2 className="text-3xl lg:text-4xl font-black text-white mb-4">
                Summer Sale
                <br />
                Up to 60% Off
              </h2>
              <p className="text-primary-100 mb-6">
                Don't miss out on incredible deals across all categories. Sale ends soon!
              </p>
              <Link to="/products?is_featured=true" className="btn-primary text-base gap-2 bg-white text-primary-700 hover:bg-gray-100 shadow-none">
                Shop Now <ArrowRight size={18} />
              </Link>
            </div>
            <div className="hidden lg:flex justify-center gap-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 text-center border border-white/20">
                  <div className="text-4xl font-black text-white">60%</div>
                  <div className="text-primary-200 text-sm mt-1">Max Discount</div>
                </div>
                <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 text-center border border-white/20">
                  <div className="text-4xl font-black text-white">24h</div>
                  <div className="text-primary-200 text-sm mt-1">Flash Deals</div>
                </div>
                <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 text-center border border-white/20">
                  <div className="text-4xl font-black text-white">1000+</div>
                  <div className="text-primary-200 text-sm mt-1">Products</div>
                </div>
                <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 text-center border border-white/20">
                  <div className="text-4xl font-black text-white">Free</div>
                  <div className="text-primary-200 text-sm mt-1">Shipping</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Trending */}
      <section className="py-16 bg-gray-50 dark:bg-gray-950">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex items-center justify-between mb-8">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <TrendingUp size={20} className="text-primary-600 dark:text-primary-400" />
                <h2 className="text-2xl lg:text-3xl font-bold text-gray-900 dark:text-white">Trending Now</h2>
              </div>
              <p className="text-gray-500 dark:text-gray-400">What everyone's buying this week</p>
            </div>
          </div>
          {loading ? (
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4 lg:gap-6">
              {Array.from({ length: 4 }).map((_, i) => (
                <ProductCard key={i} product={{
                  id: `skeleton-t-${i}`,
                  name: '',
                  description: '',
                  price: 0,
                  quantity: 0,
                  is_active: true,
                  is_featured: false,
                  image_urls: [],
                  status: 'draft',
                  seller_id: '',
                } as Product} loading />
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4 lg:gap-6">
              {featuredProducts.slice(0, 4).map((product) => (
                <ProductCard key={product.id} product={product} />
              ))}
            </div>
          )}
        </div>
      </section>

      {/* Newsletter */}
      <section className="py-16 bg-white dark:bg-gray-900">
        <div className="max-w-7xl mx-auto px-4">
          <div className="card p-8 lg:p-12 bg-gradient-to-br from-primary-50 to-accent-50 dark:from-primary-950/30 dark:to-accent-950/20 border-primary-100 dark:border-primary-800/50">
            <div className="max-w-2xl mx-auto text-center">
              <h2 className="text-2xl lg:text-3xl font-bold text-gray-900 dark:text-white mb-3">
                Get 10% Off Your First Order
              </h2>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                Subscribe to our newsletter and receive exclusive deals, new arrivals, and more.
              </p>
              <div className="flex flex-col sm:flex-row gap-3 max-w-md mx-auto">
                <input
                  type="email"
                  placeholder="Enter your email"
                  className="flex-1 px-4 py-3 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
                <button className="btn-primary whitespace-nowrap">Subscribe</button>
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-500 mt-4">
                By subscribing, you agree to our Privacy Policy. Unsubscribe anytime.
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
