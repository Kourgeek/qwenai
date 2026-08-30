import { useState, useEffect, useCallback } from 'react';
import { X, Check, AlertTriangle, Info } from 'lucide-react';
import type { ToastType } from '../types';

interface ToastProps {
  id: string;
  type: ToastType;
  title: string;
  description?: string;
  duration?: number;
  onClose: (id: string) => void;
}

const toastConfig: Record<ToastType, { bg: string; iconBg: string; icon: React.ReactNode; border: string }> = {
  success: {
    bg: 'bg-green-50 dark:bg-green-950/50',
    iconBg: 'bg-green-100 dark:bg-green-900/50',
    icon: <Check size={18} className="text-green-600 dark:text-green-400" />,
    border: 'border-green-200 dark:border-green-800',
  },
  error: {
    bg: 'bg-red-50 dark:bg-red-950/50',
    iconBg: 'bg-red-100 dark:bg-red-900/50',
    icon: <X size={18} className="text-red-600 dark:text-red-400" />,
    border: 'border-red-200 dark:border-red-800',
  },
  warning: {
    bg: 'bg-amber-50 dark:bg-amber-950/50',
    iconBg: 'bg-amber-100 dark:bg-amber-900/50',
    icon: <AlertTriangle size={18} className="text-amber-600 dark:text-amber-400" />,
    border: 'border-amber-200 dark:border-amber-800',
  },
  info: {
    bg: 'bg-blue-50 dark:bg-blue-950/50',
    iconBg: 'bg-blue-100 dark:bg-blue-900/50',
    icon: <Info size={18} className="text-blue-600 dark:text-blue-400" />,
    border: 'border-blue-200 dark:border-blue-800',
  },
};

export default function Toast({ id, type, title, description, duration = 4000, onClose }: ToastProps) {
  const [progress, setProgress] = useState(100);
  const config = toastConfig[type];

  useEffect(() => {
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev <= 0) {
          clearInterval(interval);
          return 0;
        }
        return prev - 100 / (duration / 100);
      });
    }, duration / 10);

    const timer = setTimeout(() => {
      onClose(id);
    }, duration);

    return () => {
      clearInterval(interval);
      clearTimeout(timer);
    };
  }, [id, duration, onClose]);

  return (
    <div
      className={`flex items-start gap-3 w-80 card p-4 ${config.bg} ${config.border} animate-slide-down shadow-lg`}
      role="alert"
    >
      <div className={`w-9 h-9 rounded-lg ${config.iconBg} flex items-center justify-center flex-shrink-0`}>
        {config.icon}
      </div>
      <div className="flex-1 min-w-0">
        <p className="font-semibold text-sm text-gray-900 dark:text-white">{title}</p>
        {description && (
          <p className="text-xs text-gray-600 dark:text-gray-400 mt-0.5 line-clamp-2">{description}</p>
        )}
      </div>
      <button
        onClick={() => onClose(id)}
        className="p-1 rounded-lg text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors flex-shrink-0"
        aria-label="Close notification"
      >
        <X size={16} />
      </button>
      {/* Progress bar */}
      <div className="absolute bottom-0 left-0 right-0 h-1 bg-gray-200 dark:bg-gray-700 rounded-b-2xl overflow-hidden">
        <div
          className={`h-full ${
            type === 'success'
              ? 'bg-green-500'
              : type === 'error'
              ? 'bg-red-500'
              : type === 'warning'
              ? 'bg-amber-500'
              : 'bg-blue-500'
          } transition-all duration-100`}
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
}

// Toast manager
interface ToastItem {
  id: string;
  type: ToastType;
  title: string;
  description?: string;
  duration?: number;
}

let toasts: ToastItem[] = [];
const listeners = new Set<() => void>();

export const toast = {
  success: (title: string, description?: string, duration?: number) => {
    toasts = [...toasts, { id: `toast-${Date.now()}-${Math.random()}`, type: 'success', title, description, duration }];
    listeners.forEach((fn) => fn());
  },
  error: (title: string, description?: string, duration?: number) => {
    toasts = [...toasts, { id: `toast-${Date.now()}-${Math.random()}`, type: 'error', title, description, duration }];
    listeners.forEach((fn) => fn());
  },
  warning: (title: string, description?: string, duration?: number) => {
    toasts = [...toasts, { id: `toast-${Date.now()}-${Math.random()}`, type: 'warning', title, description, duration }];
    listeners.forEach((fn) => fn());
  },
  info: (title: string, description?: string, duration?: number) => {
    toasts = [...toasts, { id: `toast-${Date.now()}-${Math.random()}`, type: 'info', title, description, duration }];
    listeners.forEach((fn) => fn());
  },
};

export function useToastManager() {
  const [activeToasts, setActiveToasts] = useState<ToastItem[]>([]);

  useEffect(() => {
    const update = () => setActiveToasts([...toasts]);
    update();
    listeners.add(update);
    return () => {
      listeners.delete(update);
    };
  }, []);

  const removeToast = useCallback((id: string) => {
    toasts = toasts.filter((t) => t.id !== id);
    setActiveToasts([...toasts]);
  }, []);

  return { activeToasts, removeToast };
}
