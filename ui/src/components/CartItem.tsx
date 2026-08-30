import { Minus, Plus, Trash2 } from 'lucide-react';
import type { CartItem } from '../types';

interface CartItemCardProps {
  item: CartItem;
  onUpdateQuantity: (itemId: string, quantity: number) => void;
  onRemove: (itemId: string) => void;
}

export default function CartItemCard({ item, onUpdateQuantity, onRemove }: CartItemCardProps) {
  const handleDecrease = () => {
    if (item.quantity > 1) {
      onUpdateQuantity(item.id, item.quantity - 1);
    }
  };

  const handleIncrease = () => {
    onUpdateQuantity(item.id, item.quantity + 1);
  };

  const imageUrl = item.product_image_url || '';

  return (
    <div className="flex gap-4 p-4 card-hover">
      {/* Image */}
      <div className="w-24 h-24 sm:w-28 sm:h-28 flex-shrink-0 rounded-xl overflow-hidden bg-gray-100 dark:bg-gray-800">
        {imageUrl ? (
          <img
            src={imageUrl}
            alt={item.product_name}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-400">
            <span className="text-2xl">📦</span>
          </div>
        )}
      </div>

      {/* Info */}
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <h3 className="font-semibold text-gray-900 dark:text-white text-sm sm:text-base truncate">
              {item.product_name}
            </h3>
            {item.product_sku && (
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                SKU: {item.product_sku}
              </p>
            )}
            <p className="text-xs text-primary-600 dark:text-primary-400 mt-1">
              ${item.unit_price.toFixed(2)} each
            </p>
          </div>
          <button
            onClick={() => onRemove(item.id)}
            className="p-1.5 rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-950/30 transition-colors flex-shrink-0"
            aria-label="Remove item"
          >
            <Trash2 size={18} />
          </button>
        </div>

        {/* Quantity controls */}
        <div className="flex items-center justify-between mt-3">
          <div className="flex items-center gap-1">
            <button
              onClick={handleDecrease}
              className="w-8 h-8 rounded-lg border border-gray-200 dark:border-gray-700 flex items-center justify-center hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
              disabled={item.quantity <= 1}
            >
              <Minus size={14} />
            </button>
            <span className="w-10 text-center font-semibold text-gray-900 dark:text-white text-sm">
              {item.quantity}
            </span>
            <button
              onClick={handleIncrease}
              className="w-8 h-8 rounded-lg border border-gray-200 dark:border-gray-700 flex items-center justify-center hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
            >
              <Plus size={14} />
            </button>
          </div>

          <p className="font-bold text-gray-900 dark:text-white">
            ${item.subtotal.toFixed(2)}
          </p>
        </div>
      </div>
    </div>
  );
}
