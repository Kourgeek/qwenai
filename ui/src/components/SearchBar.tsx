import { useState, useRef, useEffect, useCallback } from 'react';
import { Search, X, Clock } from 'lucide-react';
import type { Category } from '../types';

interface SearchBarProps {
  onSearch?: (query: string, category?: string) => void;
  categories?: Category[];
  compact?: boolean;
}

export default function SearchBar({ onSearch, categories, compact = false }: SearchBarProps) {
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState('');
  const [recentSearches, setRecentSearches] = useState<string[]>([]);
  const [showRecent, setShowRecent] = useState(false);
  const [focused, setFocused] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Load recent searches
  useEffect(() => {
    try {
      const stored = localStorage.getItem('recent_searches');
      if (stored) setRecentSearches(JSON.parse(stored));
    } catch {}
  }, []);

  // Close recent searches on outside click
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setShowRecent(false);
      }
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const handleSearch = useCallback(
    (e?: React.FormEvent) => {
      e?.preventDefault();
      if (!query.trim()) return;

      // Save to recent searches
      const updated = [query, ...recentSearches.filter((s) => s !== query)].slice(0, 8);
      setRecentSearches(updated);
      try {
        localStorage.setItem('recent_searches', JSON.stringify(updated));
      } catch {}

      setShowRecent(false);
      onSearch?.(query.trim(), category || undefined);
    },
    [query, category, recentSearches, onSearch]
  );

  const clearRecent = useCallback(() => {
    setRecentSearches([]);
    try {
      localStorage.removeItem('recent_searches');
    } catch {}
  }, []);

  const removeRecent = useCallback((search: string) => {
    const updated = recentSearches.filter((s) => s !== search);
    setRecentSearches(updated);
    try {
      localStorage.setItem('recent_searches', JSON.stringify(updated));
    } catch {}
  }, [recentSearches]);

  const allCategories = [
    { id: 'all', name: 'All' },
    ...(categories || []).map((c) => ({ id: c.slug || c.id, name: c.name })),
  ];

  return (
    <div ref={containerRef} className="relative w-full">
      <form onSubmit={handleSearch} className="relative">
        <div
          className={`flex items-center bg-gray-100 dark:bg-gray-800 rounded-xl border-2 transition-all ${
            focused
              ? 'border-primary-500 bg-white dark:bg-gray-900 shadow-md shadow-primary-500/10'
              : 'border-transparent'
          }`}
        >
          {/* Category select */}
          {!compact && categories && (
            <div className="relative flex-shrink-0">
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="h-full pl-3 pr-8 bg-transparent text-sm text-gray-600 dark:text-gray-300 border-r border-gray-200 dark:border-gray-700 appearance-none cursor-pointer focus:outline-none"
              >
                <option value="">All</option>
                {categories.map((cat) => (
                  <option key={cat.id} value={cat.slug || cat.id}>
                    {cat.name}
                  </option>
                ))}
              </select>
              <div className="absolute right-1 top-1/2 -translate-y-1/2 pointer-events-none">
                <svg width="10" height="6" viewBox="0 0 10 6" fill="none">
                  <path d="M1 1L5 5L9 1" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                </svg>
              </div>
            </div>
          )}

          {/* Input */}
          <input
            ref={inputRef}
            type="text"
            placeholder={compact ? 'Search products...' : 'Search for products, brands, and more...'}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onFocus={() => {
              setFocused(true);
              if (recentSearches.length > 0) setShowRecent(true);
            }}
            onBlur={() => setFocused(false)}
            className={`flex-1 bg-transparent py-2.5 px-3 text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none ${
              !compact && categories ? '' : 'w-full'
            }`}
          />

          {/* Search button */}
          <button
            type="submit"
            className="p-2.5 text-primary-600 dark:text-primary-400 hover:bg-primary-100 dark:hover:bg-primary-900/30 rounded-r-xl transition-colors"
            aria-label="Search"
          >
            <Search size={20} />
          </button>
        </div>
      </form>

      {/* Recent searches dropdown */}
      {showRecent && recentSearches.length > 0 && (
        <div className="absolute top-full left-0 right-0 mt-2 card z-50 overflow-hidden animate-scale-in">
          <div className="p-3">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Recent Searches
              </span>
              <button onClick={clearRecent} className="text-xs text-primary-600 dark:text-primary-400 hover:underline">
                Clear all
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              {recentSearches.map((search) => (
                <button
                  key={search}
                  onClick={() => {
                    setQuery(search);
                    setShowRecent(false);
                    inputRef.current?.focus();
                  }}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gray-50 dark:bg-gray-800 text-sm text-gray-600 dark:text-gray-400 hover:bg-primary-50 dark:hover:bg-primary-900/30 hover:text-primary-600 dark:hover:text-primary-400 transition-colors"
                >
                  <Clock size={12} />
                  <span className="truncate max-w-[150px]">{search}</span>
                  <X
                    size={12}
                    className="ml-1 text-gray-400 hover:text-red-500"
                    onClick={(e) => {
                      e.stopPropagation();
                      removeRecent(search);
                    }}
                  />
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
