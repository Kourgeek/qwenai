import { useState, useEffect, useCallback, useMemo } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { SlidersHorizontal, X, ChevronLeft, ChevronRight, ChevronDown, Grid, List } from 'lucide-react';
import ProductCard from '../components/ProductCard';
import SearchBar from '../components/SearchBar';
import { getProducts, getCategories, getBrands } from '../services/products';
import type { Product, Category, Brand } from '../types';

const PRICE_RANGES = [
  { label: 'All Prices', min: 0, max: Infinity },
  { label: 'Under $25', min: 0, max: 25 },
  { label: '$25 - $50', min: 25, max: 50 },
  { label: '$50 - $100', min: 50, max: 100 },
  { label: '$100 - $500', min: 100, max: 500 },
  { label: '$500+', min: 500, max: Infinity },
];

const SORT_OPTIONS = [
  { value: 'relevance', label: 'Relevance' },
  { value: 'price_asc', label: 'Price: Low to High' },
  { value: 'price_desc', label: 'Price: High to Low' },
  { value: 'rating', label: 'Highest Rated' },
  { value: 'newest', label: 'Newest First' },
  { value: 'name_asc', label: 'Name: A-Z' },
];

const ITEMS_PER_PAGE = 12;

export default function Products() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [brands, setBrands] = useState<Brand[]>([]);
  const [loading, setLoading] = useState(true);
  const [totalPages, setTotalPages] = useState(1);
  const [totalItems, setTotalItems] = useState(0);

  // Filters
  const [searchQuery, setSearchQuery] = useState(searchParams.get('query') || '');
  const [selectedCategory, setSelectedCategory] = useState(searchParams.get('category') || 'all');
  const [selectedBrand, setSelectedBrand] = useState(searchParams.get('brand') || 'all');
  const [priceRange, setPriceRange] = useState({ min: '', max: '' });
  const [sortBy, setSortBy] = useState(searchParams.get('sort') || 'relevance');
  const [showFilters, setShowFilters] = useState(false);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

  // Pagination
  const currentPage = parseInt(searchParams.get('page') || '1', 10);

  // Load data
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      try {
        const [cats, brnds] = await Promise.all([getCategories(), getBrands()]);
        setCategories(cats);
        setBrands(brnds);
      } catch (error) {
        console.error('Failed to load categories/brands:', error);
      }
    };
    loadData();
  }, []);

  // Load products
  useEffect(() => {
    const loadProducts = async () => {
      setLoading(true);
      try {
        const filters: Record<string, unknown> = {
          page: currentPage,
          page_size: ITEMS_PER_PAGE,
          sort: sortBy,
        };

        if (searchQuery) filters.query = searchQuery;
        if (selectedCategory !== 'all') filters.category = selectedCategory;
        if (selectedBrand !== 'all') filters.brand = selectedBrand;
        if (priceRange.min) filters.min_price = Number(priceRange.min);
        if (priceRange.max) filters.max_price = Number(priceRange.max);

        const response = await getProducts(filters);
        setProducts(response.data || []);
        setTotalPages(Math.ceil((response.data?.length || 0) / ITEMS_PER_PAGE));
        setTotalItems(response.data?.length || 0);
      } catch (error) {
        console.error('Failed to load products:', error);
        setProducts([]);
      } finally {
        setLoading(false);
      }
    };

    const timeout = setTimeout(loadProducts, 300);
    return () => clearTimeout(timeout);
  }, [currentPage, sortBy, searchQuery, selectedCategory, selectedBrand, priceRange.min, priceRange.max]);

  // Update URL params - kept for future use
  // const updateFilters = useCallback((updates: Record<string, string>) => {
  //   const params = new URLSearchParams(searchParams);
  //   Object.entries(updates).forEach(([key, value]) => {
  //     if (value) {
  //       params.set(key, value);
  //     } else {
  //       params.delete(key);
  //     }
  //   });
  //   setSearchParams(params);
  // }, [searchParams, setSearchParams]);

  const handleSearch = useCallback((query: string) => {
    setSearchQuery(query);
    setSearchParams({ query, page: '1' });
  }, [setSearchParams]);

  const handleCategoryChange = useCallback((cat: string) => {
    setSelectedCategory(cat);
    setSearchParams({ category: cat, page: '1' });
  }, [setSearchParams]);

  const handleSortChange = useCallback((sort: string) => {
    setSortBy(sort);
    setSearchParams({ sort, page: '1' });
  }, [setSearchParams]);

  const handlePriceRange = useCallback((min: string, max: string) => {
    setPriceRange({ min, max });
    setSearchParams({ page: '1' });
  }, [setSearchParams]);

  const clearFilters = useCallback(() => {
    setSearchQuery('');
    setSelectedCategory('all');
    setSelectedBrand('all');
    setPriceRange({ min: '', max: '' });
    setSortBy('relevance');
    setSearchParams({ page: '1' });
  }, [setSearchParams]);

  const handlePageChange = useCallback((page: number) => {
    setSearchParams({ page: String(page) });
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, [setSearchParams]);

  const activeFiltersCount = useMemo(() => {
    let count = 0;
    if (selectedCategory !== 'all') count++;
    if (selectedBrand !== 'all') count++;
    if (priceRange.min || priceRange.max) count++;
    return count;
  }, [selectedCategory, selectedBrand, priceRange]);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950 pt-24 lg:pt-28 pb-16">
      <div className="max-w-7xl mx-auto px-4">
        {/* Breadcrumb */}
        <nav className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400 mb-6">
          <Link to="/" className="hover:text-primary-600 dark:hover:text-primary-400 transition-colors">Home</Link>
          <span>/</span>
          <span className="text-gray-900 dark:text-white font-medium">Products</span>
        </nav>

        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl lg:text-3xl font-bold text-gray-900 dark:text-white mb-4">
            {searchQuery ? `Results for "${searchQuery}"` : 'All Products'}
          </h1>
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <SearchBar onSearch={handleSearch} />
            </div>
            <div className="flex items-center gap-2">
              {/* Mobile filter toggle */}
              <button
                onClick={() => setShowFilters(!showFilters)}
                className="lg:hidden btn-secondary gap-2"
              >
                <SlidersHorizontal size={18} />
                Filters ({activeFiltersCount})
              </button>
              {/* Sort */}
              <div className="relative">
                <select
                  value={sortBy}
                  onChange={(e) => handleSortChange(e.target.value)}
                  className="appearance-none pl-4 pr-10 py-2.5 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-500/40"
                >
                  {SORT_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
                <ChevronDown size={16} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
              </div>
              {/* View mode */}
              <div className="hidden sm:flex items-center bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-1">
                <button
                  onClick={() => setViewMode('grid')}
                  className={`p-2 rounded-lg transition-colors ${viewMode === 'grid' ? 'bg-primary-100 dark:bg-primary-900/50 text-primary-600' : 'text-gray-400 hover:text-gray-600'}`}
                >
                  <Grid size={18} />
                </button>
                <button
                  onClick={() => setViewMode('list')}
                  className={`p-2 rounded-lg transition-colors ${viewMode === 'list' ? 'bg-primary-100 dark:bg-primary-900/50 text-primary-600' : 'text-gray-400 hover:text-gray-600'}`}
                >
                  <List size={18} />
                </button>
              </div>
            </div>
          </div>
        </div>

        <div className="flex gap-6">
          {/* Sidebar Filters */}
          <aside className={`lg:w-64 flex-shrink-0 ${showFilters ? 'block' : 'hidden lg:block'}`}>
            <div className="lg:sticky lg:top-28 space-y-6">
              {/* Categories */}
              <div className="card p-5">
                <h3 className="font-semibold text-gray-900 dark:text-white mb-3">Categories</h3>
                <div className="space-y-1">
                  <button
                    onClick={() => handleCategoryChange('all')}
                    className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                      selectedCategory === 'all'
                        ? 'bg-primary-50 dark:bg-primary-950/30 text-primary-600 dark:text-primary-400 font-medium'
                        : 'text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800'
                    }`}
                  >
                    All Categories
                  </button>
                  {categories.map((cat) => (
                    <button
                      key={cat.id}
                      onClick={() => handleCategoryChange(cat.slug || cat.id)}
                      className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                        selectedCategory === (cat.slug || cat.id)
                          ? 'bg-primary-50 dark:bg-primary-950/30 text-primary-600 dark:text-primary-400 font-medium'
                          : 'text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800'
                      }`}
                    >
                      {cat.name}
                    </button>
                  ))}
                </div>
              </div>

              {/* Brands */}
              {brands.length > 0 && (
                <div className="card p-5">
                  <h3 className="font-semibold text-gray-900 dark:text-white mb-3">Brands</h3>
                  <div className="space-y-1">
                    <button
                      onClick={() => handleCategoryChange('all')}
                      className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                        selectedBrand === 'all'
                          ? 'bg-primary-50 dark:bg-primary-950/30 text-primary-600 dark:text-primary-400 font-medium'
                          : 'text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800'
                      }`}
                    >
                      All Brands
                    </button>
                    {brands.slice(0, 8).map((brand) => (
                      <button
                        key={brand.id}
                        onClick={() => setSelectedBrand(brand.slug || brand.id)}
                        className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                          selectedBrand === (brand.slug || brand.id)
                            ? 'bg-primary-50 dark:bg-primary-950/30 text-primary-600 dark:text-primary-400 font-medium'
                            : 'text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800'
                        }`}
                      >
                        {brand.name}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Price Range */}
              <div className="card p-5">
                <h3 className="font-semibold text-gray-900 dark:text-white mb-3">Price Range</h3>
                <div className="space-y-2">
                  <div className="flex gap-2">
                    <input
                      type="number"
                      placeholder="Min"
                      value={priceRange.min}
                      onChange={(e) => setPriceRange((prev) => ({ ...prev, min: e.target.value }))}
                      onBlur={() => handlePriceRange(priceRange.min, priceRange.max)}
                      className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500/40"
                    />
                    <span className="text-gray-400 flex items-center">-</span>
                    <input
                      type="number"
                      placeholder="Max"
                      value={priceRange.max}
                      onChange={(e) => setPriceRange((prev) => ({ ...prev, max: e.target.value }))}
                      onBlur={() => handlePriceRange(priceRange.min, priceRange.max)}
                      className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500/40"
                    />
                  </div>
                  <div className="space-y-1">
                    {PRICE_RANGES.map((range) => (
                      <button
                        key={range.label}
                        onClick={() => handlePriceRange(String(range.min), range.max === Infinity ? '' : String(range.max))}
                        className="w-full text-left px-3 py-1.5 rounded-lg text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                      >
                        {range.label}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* Clear filters */}
              {activeFiltersCount > 0 && (
                <button
                  onClick={clearFilters}
                  className="w-full btn-secondary gap-2 text-sm"
                >
                  <X size={16} />
                  Clear All Filters
                </button>
              )}
            </div>
          </aside>

          {/* Products Grid */}
          <main className="flex-1 min-w-0">
            {/* Active filters */}
            {activeFiltersCount > 0 && (
              <div className="flex flex-wrap items-center gap-2 mb-4">
                <span className="text-sm text-gray-500 dark:text-gray-400">Active filters:</span>
                {selectedCategory !== 'all' && (
                  <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-primary-50 dark:bg-primary-950/30 text-primary-700 dark:text-primary-300 text-xs font-medium">
                    {selectedCategory}
                    <button onClick={() => handleCategoryChange('all')} className="hover:text-primary-900">
                      <X size={12} />
                    </button>
                  </span>
                )}
                {selectedBrand !== 'all' && (
                  <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-primary-50 dark:bg-primary-950/30 text-primary-700 dark:text-primary-300 text-xs font-medium">
                    {selectedBrand}
                    <button onClick={() => setSelectedBrand('all')} className="hover:text-primary-900">
                      <X size={12} />
                    </button>
                  </span>
                )}
                {(priceRange.min || priceRange.max) && (
                  <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-primary-50 dark:bg-primary-950/30 text-primary-700 dark:text-primary-300 text-xs font-medium">
                    ${priceRange.min || '0'} - ${priceRange.max || '∞'}
                    <button onClick={() => setPriceRange({ min: '', max: '' })} className="hover:text-primary-900">
                      <X size={12} />
                    </button>
                  </span>
                )}
              </div>
            )}

            {/* Results count */}
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
              {loading ? 'Loading...' : `${totalItems} products found`}
            </p>

            {/* Product grid */}
            {loading ? (
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                {Array.from({ length: ITEMS_PER_PAGE }).map((_, i) => (
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
            ) : products.length > 0 ? (
              <div className={`grid gap-4 ${viewMode === 'grid' ? 'grid-cols-2 sm:grid-cols-3' : 'grid-cols-1'}`}>
                {products.map((product) => (
                  <ProductCard key={product.id} product={product} />
                ))}
              </div>
            ) : (
              <div className="text-center py-20">
                <div className="text-6xl mb-4">🔍</div>
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">No products found</h3>
                <p className="text-gray-500 dark:text-gray-400 mb-6">Try adjusting your search or filters</p>
                <button onClick={clearFilters} className="btn-primary">Clear Filters</button>
              </div>
            )}

            {/* Pagination */}
            {totalPages > 1 && !loading && (
              <div className="flex items-center justify-center gap-2 mt-10">
                <button
                  onClick={() => handlePageChange(currentPage - 1)}
                  disabled={currentPage <= 1}
                  className="p-2 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                >
                  <ChevronLeft size={18} />
                </button>
                {Array.from({ length: totalPages }, (_, i) => i + 1)
                  .filter((page) => {
                    if (page === 1 || page === totalPages) return true;
                    if (Math.abs(page - currentPage) <= 2) return true;
                    return false;
                  })
                  .reduce<(number | string)[]>((acc, page, idx, arr) => {
                    if (idx > 0 && page - (arr[idx - 1] as number) > 1) acc.push('...');
                    acc.push(page);
                    return acc;
                  }, [])
                  .map((page, idx) =>
                    typeof page === 'string' ? (
                      <span key={`ellipsis-${idx}`} className="px-2 text-gray-400">
                        ...
                      </span>
                    ) : (
                      <button
                        key={page}
                        onClick={() => handlePageChange(page)}
                        className={`w-10 h-10 rounded-xl text-sm font-medium transition-colors ${
                          currentPage === page
                            ? 'bg-primary-600 text-white shadow-md shadow-primary-500/30'
                            : 'bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
                        }`}
                      >
                        {page}
                      </button>
                    )
                  )}
                <button
                  onClick={() => handlePageChange(currentPage + 1)}
                  disabled={currentPage >= totalPages}
                  className="p-2 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                >
                  <ChevronRight size={18} />
                </button>
              </div>
            )}
          </main>
        </div>
      </div>
    </div>
  );
}
