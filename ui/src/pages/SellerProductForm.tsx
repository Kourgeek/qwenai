/**
 * SellerProductForm — create/edit product form for seller cabinet.
 */

import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import {
  X,
  Save,
  Package,
  Tag,
  DollarSign,
  Package2,
  Image as ImageIcon,
  Eye,
} from 'lucide-react';
import { createProduct, updateProduct, getCategories } from '../services/seller';
import type { Product, Category } from '../types';
import { PLACEHOLDER_IMAGE } from '../utils/constants';

interface SellerProductFormProps {
  productId?: string;
  mode: 'create' | 'edit';
}

interface FormData {
  name: string;
  slug: string;
  description: string;
  category_id: string;
  brand_id: string;
  price: string;
  compare_at_price: string;
  sku: string;
  quantity: string;
  image_urls: string;
  tag_ids: string;
  is_active: boolean;
}

export default function SellerProductForm({ productId, mode }: SellerProductFormProps) {
  const navigate = useNavigate();
  const [saving, setSaving] = useState(false);
  const [categories, setCategories] = useState<Category[]>([]);
  const [showPreview, setShowPreview] = useState(false);

  const [form, setForm] = useState<FormData>({
    name: '',
    slug: '',
    description: '',
    category_id: '',
    brand_id: '',
    price: '',
    compare_at_price: '',
    sku: '',
    quantity: '0',
    image_urls: '',
    tag_ids: '',
    is_active: true,
  });

  // Load categories
  useEffect(() => {
    getCategories(true).then((res) => setCategories(res.items || [])).catch(() => {});
  }, []);

  // Load product data for edit mode
  useEffect(() => {
    if (mode === 'edit' && productId) {
      // In a real app, fetch product data here
      // For now, we'll use the URL params or mock data
    }
  }, [mode, productId]);

  // Auto-generate slug from name
  const handleNameChange = useCallback((value: string) => {
    setForm((prev) => ({
      ...prev,
      name: value,
      slug: value
        .toLowerCase()
        .replace(/[^a-z0-9а-яё\s-]/g, '')
        .replace(/\s+/g, '-')
        .replace(/-+/g, '-')
        .trim(),
    }));
  }, []);

  const handleInputChange = (field: keyof FormData, value: string | boolean) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);

    try {
      const productData: Partial<Product> = {
        name: form.name,
        slug: form.slug,
        description: form.description || undefined,
        category_id: form.category_id || undefined,
        brand_id: form.brand_id || undefined,
        price: parseFloat(form.price),
        compare_at_price: form.compare_at_price ? parseFloat(form.compare_at_price) : undefined,
        sku: form.sku || undefined,
        quantity: parseInt(form.quantity) || 0,
        image_urls: form.image_urls
          ? form.image_urls.split(',').map((url) => url.trim()).filter(Boolean)
          : undefined,
        tag_ids: form.tag_ids
          ? form.tag_ids.split(',').map((id) => id.trim()).filter(Boolean)
          : undefined,
        is_active: form.is_active,
      };

      if (mode === 'create') {
        // Get seller_id from auth context or URL
        const sellerId = (localStorage.getItem('user') as any)?.seller_id || 'demo-seller';
        await createProduct(sellerId, productData);
        toast.success('Product created successfully');
      } else if (mode === 'edit' && productId) {
        await updateProduct(productId, productData);
        toast.success('Product updated successfully');
      }

      navigate('/seller/dashboard?tab=products');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to save product');
    } finally {
      setSaving(false);
    }
  };

  // Product preview component
  const ProductPreview = () => (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" onClick={() => setShowPreview(false)}>
      <div className="bg-white dark:bg-gray-800 rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between p-4 border-b dark:border-gray-700">
          <h3 className="text-lg font-semibold">Product Preview</h3>
          <button onClick={() => setShowPreview(false)} className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded">
            <X size={20} />
          </button>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="aspect-square bg-gray-100 dark:bg-gray-700 rounded-lg flex items-center justify-center">
              {form.image_urls ? (
                <img
                  src={form.image_urls.split(',')[0]}
                  alt={form.name}
                  className="w-full h-full object-cover rounded-lg"
                  onError={(e) => {
                    (e.target as HTMLImageElement).src = PLACEHOLDER_IMAGE;
                  }}
                />
              ) : (
                <ImageIcon size={48} className="text-gray-400" />
              )}
            </div>
            <div>
              <h4 className="text-xl font-bold mb-2">{form.name || 'Product Name'}</h4>
              {form.category_id && (
                <span className="inline-block px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 text-sm rounded mb-3">
                  {categories.find((c) => c.id === form.category_id)?.name || 'Category'}
                </span>
              )}
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-500">Price:</span>
                  <span className="font-semibold text-green-600">{form.price ? `$${form.price}` : '$0.00'}</span>
                </div>
                {form.compare_at_price && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">Was:</span>
                    <span className="line-through text-gray-400">${form.compare_at_price}</span>
                  </div>
                )}
                <div className="flex justify-between">
                  <span className="text-gray-500">Stock:</span>
                  <span>{form.quantity || 0} units</span>
                </div>
                {form.sku && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">SKU:</span>
                    <span className="font-mono text-xs">{form.sku}</span>
                  </div>
                )}
              </div>
              {form.description && (
                <div className="mt-4 pt-4 border-t dark:border-gray-700">
                  <h5 className="font-medium mb-2">Description</h5>
                  <p className="text-sm text-gray-600 dark:text-gray-400">{form.description}</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <>
      {showPreview && <ProductPreview />}
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold">{mode === 'create' ? 'Add New Product' : 'Edit Product'}</h1>
            <p className="text-gray-500 dark:text-gray-400 mt-1">
              {mode === 'create' ? 'Fill in the details to list your product' : 'Update product information'}
            </p>
          </div>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setShowPreview(true)}
              className="flex items-center gap-2 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
            >
              <Eye size={18} />
              Preview
            </button>
            <button
              onClick={() => navigate('/seller/dashboard?tab=products')}
              className="flex items-center gap-2 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
            >
              <X size={18} />
              Cancel
            </button>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Basic Information */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Package size={20} className="text-blue-500" />
              Basic Information
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="md:col-span-2">
                <label className="block text-sm font-medium mb-1">Product Name *</label>
                <input
                  type="text"
                  value={form.name}
                  onChange={(e) => handleNameChange(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white"
                  placeholder="e.g., Wireless Bluetooth Headphones"
                  required
                />
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium mb-1">Slug</label>
                <input
                  type="text"
                  value={form.slug}
                  onChange={(e) => handleInputChange('slug', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white font-mono text-sm"
                  placeholder="auto-generated-from-name"
                />
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium mb-1">Description</label>
                <textarea
                  value={form.description}
                  onChange={(e) => handleInputChange('description', e.target.value)}
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white"
                  placeholder="Describe your product..."
                />
              </div>
            </div>
          </div>

          {/* Pricing */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <DollarSign size={20} className="text-green-500" />
              Pricing
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">Price * *</label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">$</span>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={form.price}
                    onChange={(e) => handleInputChange('price', e.target.value)}
                    className="w-full pl-8 pr-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white"
                    placeholder="0.00"
                    required
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Compare at Price</label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">$</span>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={form.compare_at_price}
                    onChange={(e) => handleInputChange('compare_at_price', e.target.value)}
                    className="w-full pl-8 pr-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white"
                    placeholder="0.00"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">SKU</label>
                <input
                  type="text"
                  value={form.sku}
                  onChange={(e) => handleInputChange('sku', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white font-mono text-sm"
                  placeholder="PROD-001"
                />
              </div>
            </div>
          </div>

          {/* Inventory */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Package2 size={20} className="text-purple-500" />
              Inventory
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">Stock Quantity</label>
                <input
                  type="number"
                  min="0"
                  value={form.quantity}
                  onChange={(e) => handleInputChange('quantity', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white"
                  placeholder="0"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Category</label>
                <select
                  value={form.category_id}
                  onChange={(e) => handleInputChange('category_id', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white"
                >
                  <option value="">Select category</option>
                  {categories.map((cat) => (
                    <option key={cat.id} value={cat.id}>
                      {cat.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Images */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <ImageIcon size={20} className="text-orange-500" />
              Images
            </h2>
            <div>
              <label className="block text-sm font-medium mb-1">Image URLs (comma-separated)</label>
              <textarea
                value={form.image_urls}
                onChange={(e) => handleInputChange('image_urls', e.target.value)}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white font-mono text-sm"
                placeholder="https://example.com/image1.jpg, https://example.com/image2.jpg"
              />
              <p className="text-xs text-gray-500 mt-1">Enter full URLs separated by commas</p>
            </div>
          </div>

          {/* Tags */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Tag size={20} className="text-teal-500" />
              Tags
            </h2>
            <div>
              <label className="block text-sm font-medium mb-1">Tag IDs (comma-separated)</label>
              <input
                type="text"
                value={form.tag_ids}
                onChange={(e) => handleInputChange('tag_ids', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white font-mono text-sm"
                placeholder="tag1, tag2, tag3"
              />
            </div>
          </div>

          {/* Status */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold">Product Status</h2>
                <p className="text-sm text-gray-500">Enable or disable product visibility</p>
              </div>
              <button
                type="button"
                onClick={() => handleInputChange('is_active', !form.is_active)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  form.is_active ? 'bg-green-500' : 'bg-gray-300 dark:bg-gray-600'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    form.is_active ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
            <p className="text-sm text-gray-500 mt-2">
              {form.is_active ? 'Product is visible to customers' : 'Product is hidden from customers'}
            </p>
          </div>

          {/* Submit */}
          <div className="flex justify-end gap-3">
            <button
              type="button"
              onClick={() => navigate('/seller/dashboard?tab=products')}
              className="px-6 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="flex items-center gap-2 px-6 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              <Save size={18} />
              {saving ? 'Saving...' : mode === 'create' ? 'Create Product' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </>
  );
}
