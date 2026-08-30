import { useState, useEffect, useCallback } from 'react';
import {
  DollarSign,
  ShoppingBag,
  Package,
  Users,
  TrendingUp,
  TrendingDown,

  Plus,
  Filter,
  BarChart3,
  Edit2,
  Trash2,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  XCircle,
} from 'lucide-react';
// import { sellerApi } from '../services/seller';
import { sellerApi as sellerSvc } from '../services/seller';
import { ProductForm } from '../components/ProductForm';
import { useAuth } from '../contexts/AuthContext';
import type { Seller } from '../types';

interface LocalProduct {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  sku: string | null;
  category_id: string | null;
  brand_id: string | null;
  seller_id: string;
  status: string;
  price: number;
  compare_at_price: number | null;
  cost_price: number;
  quantity: number;
  is_active: boolean;
  is_featured: boolean;
  image_urls: string[];
  created_at: string;
  updated_at: string;
}

interface SellerStats {
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


const revenueData = [
  { month: 'Jul', revenue: 9200 },
  { month: 'Aug', revenue: 11500 },
  { month: 'Sep', revenue: 8900 },
  { month: 'Oct', revenue: 14200 },
  { month: 'Nov', revenue: 16800 },
  { month: 'Dec', revenue: 19500 },
  { month: 'Jan', revenue: 15600 },
];

const maxRevenue = Math.max(...revenueData.map((d) => d.revenue));

const productStatusColors: Record<string, string> = {
  active: 'badge-success',
  inactive: 'badge-gray',
  low_stock: 'badge-warning',
  out_of_stock: 'badge-danger',
  draft: 'badge-primary',
};

export default function SellerDashboard() {
  const { user } = useAuth();
  const [stats, setStats] = useState<SellerStats | null>(null);
  const [products, setProducts] = useState<LocalProduct[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'products' | 'orders'>('overview');
  const [showProductForm, setShowProductForm] = useState(false);
  const [editingProduct, setEditingProduct] = useState<LocalProduct | null>(null);
  const [sellerProfile, setSellerProfile] = useState<Seller | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [productPage, setProductPage] = useState(1);
  const [productTotal, setProductTotal] = useState(0);
  const [productLoading, setProductLoading] = useState(false);

  const PAGE_SIZE = 10;

  // Get seller_id from user
  const getSellerId = useCallback(() => {
    if (user?.role === 'seller' && user?.id) {
      return user.id;
    }
    // Try to get from localStorage
    const stored = localStorage.getItem('seller_id');
    if (stored) return stored;
    // Fallback: use user_id as seller_id (some users may not have separate seller accounts)
    return user?.id || '';
  }, [user]);

  const loadStats = useCallback(async (sellerId: string) => {
    try {
      const data = await sellerSvc.getStats(sellerId);
      setStats(data);
    } catch (err) {
      console.error('Failed to load seller stats:', err);
      // Use mock data as fallback
      setStats({
        seller_id: sellerId,
        total_orders: 0,
        pending_orders: 0,
        processing_orders: 0,
        shipped_orders: 0,
        delivered_orders: 0,
        cancelled_orders: 0,
        total_revenue: 0,
        average_order_value: 0,
        rating: 0,
        total_ratings: 0,
        total_products: 0,
        active_products: 0,
        low_stock_products: 0,
        monthly_revenue: 0,
        monthly_orders: 0,
        revenue_growth_rate: 0,
      });
    }
  }, []);

  const loadProducts = useCallback(async (sellerId: string, page: number = 1) => {
    setProductLoading(true);
    try {
      const offset = (page - 1) * PAGE_SIZE;
      const data = await sellerSvc.getProducts(sellerId, {
        limit: PAGE_SIZE,
        offset,
      });
      setProducts((data.products || []) as any);
      setProductTotal(data.total || 0);
    } catch (err) {
      console.error('Failed to load products:', err);
      setProducts([] as LocalProduct[]);
      setProductTotal(0);
    } finally {
      setProductLoading(false);
    }
  }, []);

  const loadSellerProfile = useCallback(async (sellerId: string) => {
    try {
      const profile = await sellerSvc.getProfile(sellerId);
      setSellerProfile(profile);
    } catch (err) {
      console.error('Failed to load seller profile:', err);
    }
  }, []);

  useEffect(() => {
    const init = async () => {
      setLoading(true);
      setError(null);
      const sellerId = getSellerId();

      if (!sellerId) {
        setError('No seller account found. Please register as a seller first.');
        setLoading(false);
        return;
      }

      // Store seller_id for later use
      localStorage.setItem('seller_id', sellerId);

      await Promise.all([
        loadStats(sellerId),
        loadProducts(sellerId, 1),
        loadSellerProfile(sellerId),
      ]);
      setLoading(false);
    };

    init();
  }, [getSellerId, loadStats, loadProducts, loadSellerProfile]);

  const handleProductSuccess = () => {
    const sellerId = getSellerId();
    loadStats(sellerId);
    loadProducts(sellerId, productPage);
  };

  const handleDeleteProduct = async (productId: string) => {
    if (!confirm('Are you sure you want to delete this product?')) return;
    try {
      await sellerSvc.deleteProduct(productId);
      handleProductSuccess();
    } catch (err) {
      alert('Failed to delete product');
    }
  };

  const handleEditProduct = (product: LocalProduct) => {
    setEditingProduct(product);
    setShowProductForm(true);
  };

  const handleToggleStatus = async (product: LocalProduct) => {
    try {
      await sellerSvc.toggleProductStatus(product.id, !product.is_active);
      handleProductSuccess();
    } catch {
      alert('Failed to update product status');
    }
  };

  const formatCurrency = (amount: number) =>
    new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount);

  if (loading) {
    return (
      <div className="min-h-screen pt-24 lg:pt-28 pb-16 bg-gray-50 dark:bg-gray-950 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin" />
          <p className="text-gray-500 dark:text-gray-400 text-sm">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen pt-24 lg:pt-28 pb-16 bg-gray-50 dark:bg-gray-950 flex items-center justify-center">
        <div className="card max-w-md p-8 text-center">
          <AlertCircle size={48} className="mx-auto text-amber-500 mb-4" />
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Seller Account Required</h2>
          <p className="text-gray-500 dark:text-gray-400 mb-6">{error}</p>
          <button
            onClick={() => window.location.href = '/seller/register'}
            className="btn-primary"
          >
            Register as Seller
          </button>
        </div>
      </div>
    );
  }

  const statsData = stats || {
    seller_id: getSellerId(),
    total_orders: 0,
    pending_orders: 0,
    processing_orders: 0,
    shipped_orders: 0,
    delivered_orders: 0,
    cancelled_orders: 0,
    total_revenue: 0,
    average_order_value: 0,
    rating: 0,
    total_ratings: 0,
    total_products: 0,
    active_products: 0,
    low_stock_products: 0,
    monthly_revenue: 0,
    monthly_orders: 0,
    revenue_growth_rate: 0,
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950 pt-24 lg:pt-28 pb-16">
      <div className="max-w-7xl mx-auto px-4">
        {/* Header */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-8">
          <div>
            <h1 className="text-2xl lg:text-3xl font-bold text-gray-900 dark:text-white">
              Seller Dashboard
            </h1>
            {sellerProfile && (
              <p className="text-gray-500 dark:text-gray-400 mt-1">
                {sellerProfile.business_name || 'Your Store'} • {sellerProfile.status ? 'Verified' : 'Pending Verification'}
              </p>
            )}
          </div>
          <button
            onClick={() => {
              setEditingProduct(null);
              setShowProductForm(true);
            }}
            className="btn-primary gap-2"
          >
            <Plus size={18} />
            Add Product
          </button>
        </div>

        {/* Stats cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <div className="stat-card bg-gradient-to-br from-primary-500 to-primary-600 text-white">
            <div className="flex items-center justify-between mb-3">
              <DollarSign size={20} className="opacity-80" />
              <span className="flex items-center gap-1 text-sm bg-white/20 px-2 py-0.5 rounded-lg">
                {statsData.revenue_growth_rate >= 0 ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
                {Math.abs(statsData.revenue_growth_rate)}%
              </span>
            </div>
            <p className="text-2xl font-bold">{formatCurrency(statsData.total_revenue)}</p>
            <p className="text-sm opacity-80">Total Revenue</p>
          </div>

          <div className="stat-card bg-gradient-to-br from-green-500 to-emerald-600 text-white">
            <div className="flex items-center justify-between mb-3">
              <ShoppingBag size={20} className="opacity-80" />
              <span className="flex items-center gap-1 text-sm bg-white/20 px-2 py-0.5 rounded-lg">
                <TrendingUp size={14} />
                +{statsData.monthly_orders}
              </span>
            </div>
            <p className="text-2xl font-bold">{statsData.total_orders.toLocaleString()}</p>
            <p className="text-sm opacity-80">Total Orders</p>
          </div>

          <div className="stat-card bg-gradient-to-br from-amber-500 to-orange-500 text-white">
            <div className="flex items-center justify-between mb-3">
              <Package size={20} className="opacity-80" />
              <span className="flex items-center gap-1 text-sm bg-white/20 px-2 py-0.5 rounded-lg">
                {statsData.active_products} active
              </span>
            </div>
            <p className="text-2xl font-bold">{statsData.total_products}</p>
            <p className="text-sm opacity-80">Products</p>
          </div>

          <div className="stat-card bg-gradient-to-br from-violet-500 to-purple-600 text-white">
            <div className="flex items-center justify-between mb-3">
              <Users size={20} className="opacity-80" />
              <span className="flex items-center gap-1 text-sm bg-white/20 px-2 py-0.5 rounded-lg">
                ⭐ {statsData.rating}
              </span>
            </div>
            <p className="text-2xl font-bold">{statsData.total_ratings}</p>
            <p className="text-sm opacity-80">Ratings</p>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 mb-6 bg-white dark:bg-gray-900 rounded-2xl p-1.5 shadow-sm max-w-md">
          {(['overview', 'products', 'orders'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`flex-1 px-4 py-2.5 rounded-xl text-sm font-medium transition-all capitalize ${
                activeTab === tab
                  ? 'bg-primary-600 text-white shadow-md shadow-primary-500/30'
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>

        {/* Tab content */}
        {activeTab === 'overview' && (
          <div className="grid lg:grid-cols-3 gap-6">
            {/* Revenue chart */}
            <div className="lg:col-span-2 card p-6">
              <h3 className="font-bold text-gray-900 dark:text-white mb-6 flex items-center gap-2">
                <BarChart3 size={20} className="text-primary-600 dark:text-primary-400" />
                Revenue Overview
              </h3>
              <div className="flex items-end gap-3 h-48">
                {revenueData.map((data) => (
                  <div key={data.month} className="flex-1 flex flex-col items-center gap-2">
                    <span className="text-xs font-medium text-gray-900 dark:text-white">
                      ${Math.round(data.revenue / 1000)}k
                    </span>
                    <div
                      className="w-full bg-gradient-to-t from-primary-600 to-primary-400 rounded-t-lg transition-all duration-500 hover:from-primary-500 hover:to-primary-300"
                      style={{ height: `${(data.revenue / maxRevenue) * 100}%` }}
                    />
                    <span className="text-xs text-gray-500 dark:text-gray-400">{data.month}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Order status breakdown */}
            <div className="card p-6">
              <h3 className="font-bold text-gray-900 dark:text-white mb-4">Order Status</h3>
              <div className="space-y-4">
                {[
                  { label: 'Pending', count: statsData.pending_orders, color: 'bg-amber-500' },
                  { label: 'Processing', count: statsData.processing_orders, color: 'bg-blue-500' },
                  { label: 'Shipped', count: statsData.shipped_orders, color: 'bg-primary-500' },
                  { label: 'Delivered', count: statsData.delivered_orders, color: 'bg-green-500' },
                  { label: 'Cancelled', count: statsData.cancelled_orders, color: 'bg-red-500' },
                ].map((item) => (
                  <div key={item.label}>
                    <div className="flex items-center justify-between text-sm mb-1">
                      <span className="text-gray-600 dark:text-gray-400">{item.label}</span>
                      <span className="font-semibold text-gray-900 dark:text-white">{item.count}</span>
                    </div>
                    <div className="h-2 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
                      <div
                        className={`h-full ${item.color} rounded-full transition-all duration-500`}
                        style={{ width: `${statsData.total_orders > 0 ? (item.count / statsData.total_orders) * 100 : 0}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'products' && (
          <div className="card overflow-hidden">
            <div className="p-4 border-b border-gray-100 dark:border-gray-800 flex items-center justify-between">
              <h3 className="font-bold text-gray-900 dark:text-white">
                Products ({productTotal})
              </h3>
              <div className="flex gap-2">
                <button className="btn-secondary gap-2 text-sm" onClick={() => loadProducts(getSellerId(), productPage)}>
                  <RefreshCw size={16} />
                  Refresh
                </button>
              </div>
            </div>
            {productLoading ? (
              <div className="p-8 text-center">
                <div className="w-8 h-8 border-3 border-primary-200 border-t-primary-600 rounded-full animate-spin mx-auto" />
              </div>
            ) : products.length === 0 ? (
              <div className="p-12 text-center">
                <Package size={48} className="mx-auto text-gray-300 dark:text-gray-600 mb-4" />
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">No products yet</h3>
                <p className="text-gray-500 dark:text-gray-400 mb-4">Start by adding your first product</p>
                <button
                  onClick={() => {
                    setEditingProduct(null);
                    setShowProductForm(true);
                  }}
                  className="btn-primary gap-2"
                >
                  <Plus size={16} />
                  Add Product
                </button>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="table-base">
                  <thead>
                    <tr>
                      <th>Product</th>
                      <th>Price</th>
                      <th>Compare</th>
                      <th>Stock</th>
                      <th>Status</th>
                      <th>SKU</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {products.map((product) => (
                      <tr key={product.id}>
                        <td className="font-medium text-gray-900 dark:text-white max-w-[200px] truncate">
                          {product.name}
                        </td>
                        <td className="font-semibold text-gray-900 dark:text-white">
                          ${product.price.toFixed(2)}
                        </td>
                        <td className="text-gray-500">
                          {product.compare_at_price ? `$${product.compare_at_price.toFixed(2)}` : '—'}
                        </td>
                        <td>
                          <span className={product.quantity <= 5 ? 'text-amber-600 font-medium' : 'text-gray-600 dark:text-gray-400'}>
                            {product.quantity}
                          </span>
                        </td>
                        <td>
                          <span className={`badge ${productStatusColors[product.is_active ? 'active' : 'inactive']}`}>
                            {product.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </td>
                        <td className="text-gray-500 text-sm font-mono">
                          {product.sku || '—'}
                        </td>
                        <td>
                          <div className="flex gap-1">
                            <button
                              onClick={() => handleEditProduct(product)}
                              className="btn-ghost text-sm gap-1 p-1.5"
                              title="Edit"
                            >
                              <Edit2 size={14} />
                            </button>
                            <button
                              onClick={() => handleToggleStatus(product)}
                              className="btn-ghost text-sm gap-1 p-1.5"
                              title={product.is_active ? 'Deactivate' : 'Activate'}
                            >
                              {product.is_active ? <CheckCircle size={14} className="text-green-500" /> : <XCircle size={14} className="text-amber-500" />}
                            </button>
                            <button
                              onClick={() => handleDeleteProduct(product.id)}
                              className="btn-ghost text-sm gap-1 p-1.5 text-red-500 hover:text-red-700"
                              title="Delete"
                            >
                              <Trash2 size={14} />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            {/* Pagination */}
            {productTotal > PAGE_SIZE && (
              <div className="p-4 border-t border-gray-100 dark:border-gray-800 flex items-center justify-between">
                <span className="text-sm text-gray-500 dark:text-gray-400">
                  Page {productPage} of {Math.ceil(productTotal / PAGE_SIZE)}
                </span>
                <div className="flex gap-2">
                  <button
                    onClick={() => setProductPage(p => Math.max(1, p - 1))}
                    disabled={productPage <= 1}
                    className="btn-secondary text-sm disabled:opacity-50"
                  >
                    Previous
                  </button>
                  <button
                    onClick={() => setProductPage(p => p + 1)}
                    disabled={productPage * PAGE_SIZE >= productTotal}
                    className="btn-secondary text-sm disabled:opacity-50"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'orders' && (
          <div className="card overflow-hidden">
            <div className="p-4 border-b border-gray-100 dark:border-gray-800 flex items-center justify-between">
              <h3 className="font-bold text-gray-900 dark:text-white">Recent Orders</h3>
              <button className="btn-ghost text-sm gap-1">
                <Filter size={14} />
                Filter
              </button>
            </div>
            <div className="p-12 text-center">
              <ShoppingBag size={48} className="mx-auto text-gray-300 dark:text-gray-600 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">No orders yet</h3>
              <p className="text-gray-500 dark:text-gray-400">
                Orders will appear here once customers start purchasing your products.
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Product Form Modal */}
      <ProductForm
        isOpen={showProductForm}
        onClose={() => {
          setShowProductForm(false);
          setEditingProduct(null);
        }}
        editingProduct={editingProduct ? {
          id: editingProduct.id,
          name: editingProduct.name,
          slug: editingProduct.slug,
          description: editingProduct.description,
          sku: editingProduct.sku,
          category_id: editingProduct.category_id,
          brand_id: editingProduct.brand_id,
          price: editingProduct.price,
          compare_at_price: editingProduct.compare_at_price,
          stock_quantity: editingProduct.quantity,
          image_urls: editingProduct.image_urls,
        } : null}
        sellerId={getSellerId()}
        onSuccess={handleProductSuccess}
      />
    </div>
  );
}
