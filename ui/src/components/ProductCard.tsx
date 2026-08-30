import { Link } from 'react-router-dom';
import { Star, ShoppingCart, Heart } from 'lucide-react';
import type { Product } from '../types';

interface ProductCardProps {
  product: Product;
  loading?: boolean;
}

function StarRating({ rating, size = 14 }: { rating: number | undefined; size?: number }) {
  const fullStars = Math.floor(rating || 0);
  const hasHalf = (rating || 0) - fullStars >= 0.5;
  const emptyStars = 5 - fullStars - (hasHalf ? 1 : 0);

  return (
    <div className="flex items-center gap-0.5">
      {Array.from({ length: fullStars }).map((_, i) => (
        <Star key={`f-${i}`} size={size} className="fill-amber-400 text-amber-400" />
      ))}
      {hasHalf && (
        <svg width={size} height={size} viewBox="0 0 24 24" className="fill-amber-400 text-amber-400">
          <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
          <path d="M12 2v15.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" fill="currentColor" opacity="0.5" />
        </svg>
      )}
      {Array.from({ length: emptyStars }).map((_, i) => (
        <Star key={`e-${i}`} size={size} className="text-gray-300 dark:text-gray-600" />
      ))}
    </div>
  );
}

function SkeletonCard() {
  return (
    <div className="card overflow-hidden animate-pulse">
      <div className="aspect-square bg-gray-200 dark:bg-gray-700" />
      <div className="p-4 space-y-3">
        <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4" />
        <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-full" />
        <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-2/3" />
        <div className="flex items-center gap-2 pt-2">
          <div className="h-5 w-16 bg-gray-200 dark:bg-gray-700 rounded" />
          <div className="h-4 w-24 bg-gray-200 dark:bg-gray-700 rounded" />
        </div>
        <div className="h-10 bg-gray-200 dark:bg-gray-700 rounded-xl" />
      </div>
    </div>
  );
}

export default function ProductCard({ product, loading = false }: ProductCardProps) {
  if (loading) return <SkeletonCard />;

  const discount = product.compare_at_price
    ? Math.round(((product.compare_at_price - product.price) / product.compare_at_price) * 100)
    : 0;

  const imageUrl = product.image_urls?.[0] || '';

  return (
    <div className="card overflow-hidden group flex flex-col h-full">
      {/* Image */}
      <Link to={`/product/${product.id}`} className="relative aspect-square overflow-hidden bg-gray-100 dark:bg-gray-800">
        {imageUrl ? (
          <img
            src={imageUrl}
            alt={product.name}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            loading="lazy"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-400">
            <span className="text-4xl">📦</span>
          </div>
        )}

        {/* Discount badge */}
        {discount > 0 && (
          <span className="absolute top-3 left-3 badge badge-danger bg-red-500 text-white">
            -{discount}%
          </span>
        )}

        {/* Featured badge */}
        {product.is_featured && (
          <span className="absolute top-3 left-3 badge badge-warning bg-amber-500 text-white">
            Featured
          </span>
        )}

        {/* Quick actions */}
        <div className="absolute top-3 right-3 flex flex-col gap-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
          <button
            className="w-9 h-9 bg-white dark:bg-gray-800 rounded-xl shadow-md flex items-center justify-center hover:bg-primary-50 dark:hover:bg-primary-900 transition-colors"
            aria-label="Add to wishlist"
          >
            <Heart size={16} className="text-gray-600 dark:text-gray-300" />
          </button>
        </div>

        {/* Quick add overlay */}
        <div className="absolute bottom-0 left-0 right-0 p-3 translate-y-full group-hover:translate-y-0 transition-transform duration-300">
          <button
            className="w-full btn-primary text-sm py-2.5 gap-2"
            aria-label={`Add ${product.name} to cart`}
          >
            <ShoppingCart size={16} />
            Add to Cart
          </button>
        </div>
      </Link>

      {/* Content */}
      <div className="p-4 flex flex-col flex-1">
        {/* Brand */}
        {product.brand_name && (
          <span className="text-xs text-primary-600 dark:text-primary-400 font-medium mb-1">
            {product.brand_name}
          </span>
        )}

        {/* Name */}
        <Link
          to={`/product/${product.id}`}
          className="font-semibold text-gray-900 dark:text-white text-sm leading-snug line-clamp-2 hover:text-primary-600 dark:hover:text-primary-400 transition-colors mb-2"
        >
          {product.name}
        </Link>

        {/* Rating */}
        {product.avg_rating !== undefined && (
          <div className="flex items-center gap-1.5 mb-2">
            <StarRating rating={product.avg_rating} size={13} />
            <span className="text-xs text-gray-500 dark:text-gray-400">
              ({product.review_count || 0})
            </span>
          </div>
        )}

        {/* Price */}
        <div className="mt-auto flex items-baseline gap-2">
          <span className="text-lg font-bold text-gray-900 dark:text-white">
            ${product.price.toFixed(2)}
          </span>
          {product.compare_at_price && product.compare_at_price > product.price && (
            <span className="text-sm text-gray-400 line-through">
              ${product.compare_at_price.toFixed(2)}
            </span>
          )}
        </div>

        {/* Stock status */}
        {product.quantity > 0 && product.quantity <= 5 && (
          <p className="text-xs text-amber-600 dark:text-amber-400 mt-1">
            Only {product.quantity} left in stock
          </p>
        )}
        {product.quantity === 0 && (
          <p className="text-xs text-red-500 dark:text-red-400 mt-1">Out of stock</p>
        )}
      </div>
    </div>
  );
}
