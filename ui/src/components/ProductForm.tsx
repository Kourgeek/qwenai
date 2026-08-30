/**
 * ProductForm — Create/Edit product form for seller dashboard.
 */

import { useState, useEffect } from 'react';
import { X, Plus, Trash2, Save } from 'lucide-react';
import { sellerApi } from '../services/seller';
import { toast } from 'react-hot-toast';

interface ProductFormProps {
  isOpen: boolean;
  onClose: () => void;
  editingProduct?: {
    id: string;
    name: string;
    slug: string;
    description: string | null;
    sku: string | null;
    category_id: string | null;
    brand_id: string | null;
    price: number;
    compare_at_price: number | null;
    stock_quantity: number;
    image_urls: string[];
  } | null;
  sellerId: string;
  onSuccess: () => void;
}

interface Category {
  id: string;
  name: string;
  slug: string;
  parent_id: string | null;
  level: number;
  is_active: boolean;
}

export function ProductForm({ isOpen, onClose, editingProduct, sellerId, onSuccess }: ProductFormProps) {
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [categories, setCategories] = useState<Category[]>([]);
  const [form, setForm] = useState({
    name: '',
    slug: '',
    description: '',
    category_id: '',
    brand_id: '',
    price: '',
    compare_at_price: '',
    sku: '',
    stock_quantity: '0',
    image_urls: [''] as string[],
  });

  useEffect(() => {
    if (isOpen) {
      loadCategories();
      if (editingProduct) {
        setForm({
          name: editingProduct.name,
          slug: editingProduct.slug,
          description: editingProduct.description || '',
          category_id: editingProduct.category_id || '',
          brand_id: editingProduct.brand_id || '',
          price: editingProduct.price.toString(),
          compare_at_price: editingProduct.compare_at_price?.toString() || '',
          sku: editingProduct.sku || '',
          stock_quantity: editingProduct.stock_quantity.toString(),
          image_urls: editingProduct.image_urls?.length ? editingProduct.image_urls : [''],
        });
      } else {
        setForm({
          name: '',
          slug: '',
          description: '',
          category_id: '',
          brand_id: '',
          price: '',
          compare_at_price: '',
          sku: '',
          stock_quantity: '0',
          image_urls: [''],
        });
      }
    }
  }, [isOpen, editingProduct]);

  const loadCategories = async () => {
    try {
      const res = await fetch('/bff/categories?is_active=true', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });
      if (res.ok) {
        const data = await res.json();
        setCategories(data.items || data);
      }
    } catch (err) {
      console.error('Failed to load categories:', err);
    }
  };

  // Auto-generate slug from name
  useEffect(() => {
    if (!editingProduct && form.name) {
      const slug = form.name
        .toLowerCase()
        .replace(/[^a-z0-9а-яё\s-]/g, '')
        .replace(/\s+/g, '-')
        .replace(/-+/g, '-')
        .trim();
      setForm(prev => ({ ...prev, slug }));
    }
  }, [form.name, editingProduct]);

  const handleImageChange = (index: number, value: string) => {
    const newImages = [...form.image_urls];
    newImages[index] = value;
    setForm(prev => ({ ...prev, image_urls: newImages }));
  };

  const addImage = () => {
    setForm(prev => ({ ...prev, image_urls: [...prev.image_urls, ''] }));
  };

  const removeImage = (index: number) => {
    setForm(prev => ({
      ...prev,
      image_urls: prev.image_urls.filter((_, i) => i !== index),
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);

    try {
      const price = parseFloat(form.price);
      const stockQuantity = parseInt(form.stock_quantity) || 0;
      const compareAtPrice = form.compare_at_price ? parseFloat(form.compare_at_price) : null;
      const validImages = form.image_urls.filter(url => url.trim());

      const productData = {
        name: form.name,
        price,
        seller_id: sellerId,
        slug: form.slug || undefined,
        description: form.description || undefined,
        category_id: form.category_id || undefined,
        brand_id: form.brand_id || undefined,
        compare_at_price: compareAtPrice,
        sku: form.sku || undefined,
        stock_quantity: stockQuantity,
        image_urls: validImages.length ? validImages : undefined,
      };

      if (editingProduct) {
        await sellerApi.updateProduct(editingProduct.id, productData);
        toast.success('Product updated successfully');
      } else {
        await sellerApi.createProduct(sellerId, productData);
        toast.success('Product created successfully');
      }

      onSuccess();
      onClose();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to save product';
      toast.error(message);
    } finally {
      setSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />

      {/* Modal */}
      <div className="relative w-full max-w-3xl max-h-[90vh] overflow-y-auto bg-white dark:bg-gray-900 rounded-2xl shadow-2xl">
        {/* Header */}
        <div className="sticky top-0 flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 rounded-t-2xl">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">
            {editingProduct ? 'Edit Product' : 'Add New Product'}
          </h2>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Name & Slug */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                Product Name *
              </label>
              <input
                type="text"
                value={form.name}
                onChange={e => setForm(prev => ({ ...prev, name: e.target.value }))}
                className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="e.g., Wireless Bluetooth Headphones"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                SKU
              </label>
              <input
                type="text"
                value={form.sku}
                onChange={e => setForm(prev => ({ ...prev, sku: e.target.value }))}
                className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="e.g., WBH-001"
              />
            </div>
          </div>

          {/* Slug */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
              URL Slug
            </label>
            <input
              type="text"
              value={form.slug}
              onChange={e => setForm(prev => ({ ...prev, slug: e.target.value }))}
              className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              placeholder="e.g., wireless-bluetooth-headphones"
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
              Description
            </label>
            <textarea
              value={form.description}
              onChange={e => setForm(prev => ({ ...prev, description: e.target.value }))}
              rows={4}
              className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              placeholder="Describe your product..."
            />
          </div>

          {/* Price & Stock */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                Price *
              </label>
              <input
                type="number"
                step="0.01"
                min="0"
                value={form.price}
                onChange={e => setForm(prev => ({ ...prev, price: e.target.value }))}
                className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="0.00"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                Compare at Price
              </label>
              <input
                type="number"
                step="0.01"
                min="0"
                value={form.compare_at_price}
                onChange={e => setForm(prev => ({ ...prev, compare_at_price: e.target.value }))}
                className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="Original price"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                Stock Quantity *
              </label>
              <input
                type="number"
                min="0"
                value={form.stock_quantity}
                onChange={e => setForm(prev => ({ ...prev, stock_quantity: e.target.value }))}
                className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="0"
                required
              />
            </div>
          </div>

          {/* Category & Brand */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                Category
              </label>
              <select
                value={form.category_id}
                onChange={e => setForm(prev => ({ ...prev, category_id: e.target.value }))}
                className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              >
                <option value="">Select category</option>
                {categories.map(cat => (
                  <option key={cat.id} value={cat.id}>
                    {'  '.repeat(cat.level)}{cat.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                Brand
              </label>
              <input
                type="text"
                value={form.brand_id}
                onChange={e => setForm(prev => ({ ...prev, brand_id: e.target.value }))}
                className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="Brand name or ID"
              />
            </div>
          </div>

          {/* Images */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
              Product Images (URLs)
            </label>
            <div className="space-y-2">
              {form.image_urls.map((url, index) => (
                <div key={index} className="flex gap-2">
                  <input
                    type="text"
                    value={url}
                    onChange={e => handleImageChange(index, e.target.value)}
                    className="flex-1 px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    placeholder="https://example.com/image.jpg"
                  />
                  {form.image_urls.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeImage(index)}
                      className="p-2.5 text-red-500 hover:text-red-700 transition-colors"
                    >
                      <Trash2 size={18} />
                    </button>
                  )}
                </div>
              ))}
              <button
                type="button"
                onClick={addImage}
                className="flex items-center gap-2 px-4 py-2 text-sm text-primary-600 dark:text-primary-400 hover:bg-primary-50 dark:hover:bg-primary-900/20 rounded-lg transition-colors"
              >
                <Plus size={16} />
                Add Image URL
              </button>
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
            <button
              type="button"
              onClick={onClose}
              className="px-6 py-2.5 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving || !form.name || !form.price}
              className="flex items-center gap-2 px-6 py-2.5 text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg transition-colors"
            >
              <Save size={16} />
              {saving ? 'Saving...' : (editingProduct ? 'Update Product' : 'Create Product')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
