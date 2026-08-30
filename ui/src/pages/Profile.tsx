import { useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import {
  User,
  Package,
  Heart,
  MapPin,
  Settings,
  Edit3,
  Shield,
  Bell,
  CreditCard,
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { toast } from '../components/Toast';

type Tab = 'profile' | 'orders' | 'wishlist' | 'addresses' | 'settings';

const mockOrders = [
  { id: 'ORD-001', date: '2024-01-15', total: 129.99, status: 'delivered', items: 3 },
  { id: 'ORD-002', date: '2024-01-10', total: 49.99, status: 'shipped', items: 1 },
  { id: 'ORD-003', date: '2024-01-05', total: 259.98, status: 'processing', items: 5 },
  { id: 'ORD-004', date: '2023-12-28', total: 89.99, status: 'delivered', items: 2 },
];

const mockWishlist = [
  { id: 'p1', name: 'Wireless Headphones', price: 79.99, image_urls: [] },
  { id: 'p2', name: 'Smart Watch Pro', price: 199.99, image_urls: [] },
  { id: 'p3', name: 'Leather Backpack', price: 149.99, image_urls: [] },
];

const statusColors: Record<string, string> = {
  delivered: 'badge-success',
  shipped: 'badge-primary',
  processing: 'badge-warning',
  cancelled: 'badge-danger',
};

export default function Profile() {
  const { user, isAuthenticated, isLoading } = useAuth();
  const [activeTab, setActiveTab] = useState<Tab>('profile');
  const [editing, setEditing] = useState(false);
  const [formData, setFormData] = useState({
    first_name: user?.first_name || '',
    last_name: user?.last_name || '',
    phone: user?.phone || '',
  });

  // Redirect if not logged in
  if (!isAuthenticated && !isLoading) {
    window.location.href = '/login';
    return null;
  }

  const handleSave = useCallback(() => {
    setEditing(false);
    toast.success('Profile updated successfully');
  }, []);

  const handleTabChange = useCallback((tab: Tab) => {
    setActiveTab(tab);
  }, []);

  const tabs: { key: Tab; label: string; icon: React.ReactNode }[] = [
    { key: 'profile', label: 'Profile', icon: <User size={18} /> },
    { key: 'orders', label: 'Orders', icon: <Package size={18} /> },
    { key: 'wishlist', label: 'Wishlist', icon: <Heart size={18} /> },
    { key: 'addresses', label: 'Addresses', icon: <MapPin size={18} /> },
    { key: 'settings', label: 'Settings', icon: <Settings size={18} /> },
  ];

  if (isLoading || !user) {
    return (
      <div className="min-h-screen pt-24 lg:pt-28 pb-16 bg-gray-50 dark:bg-gray-950 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin" />
          <p className="text-gray-500 dark:text-gray-400 text-sm">Loading profile...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950 pt-24 lg:pt-28 pb-16">
      <div className="max-w-7xl mx-auto px-4">
        {/* Profile header */}
        <div className="card p-6 mb-6">
          <div className="flex flex-col sm:flex-row items-center gap-6">
            <div className="w-20 h-20 bg-gradient-to-br from-primary-500 to-primary-600 rounded-2xl flex items-center justify-center shadow-lg shadow-primary-500/30">
              <span className="text-white text-2xl font-bold">
                {user.first_name?.[0]?.toUpperCase() || 'U'}
                {user.last_name?.[0]?.toUpperCase() || ''}
              </span>
            </div>
            <div className="text-center sm:text-left flex-1">
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                {user.first_name} {user.last_name}
              </h1>
              <p className="text-gray-500 dark:text-gray-400">{user.email}</p>
              <span className="inline-block mt-2 badge badge-primary">
                {user.role === 'seller' ? '🏪 Seller' : user.role === 'admin' ? '🛡️ Admin' : '👤 Customer'}
              </span>
            </div>
            <button
              onClick={() => setEditing(!editing)}
              className="btn-secondary gap-2"
            >
              <Edit3 size={18} />
              {editing ? 'Cancel' : 'Edit Profile'}
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 mb-6 bg-white dark:bg-gray-900 rounded-2xl p-1.5 shadow-sm overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => handleTabChange(tab.key)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all whitespace-nowrap ${
                activeTab === tab.key
                  ? 'bg-primary-600 text-white shadow-md shadow-primary-500/30'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-50 dark:hover:bg-gray-800'
              }`}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab content */}
        <div className="card p-6">
          {activeTab === 'profile' && (
            <div className="space-y-6 max-w-2xl">
              <h2 className="text-lg font-bold text-gray-900 dark:text-white">Personal Information</h2>
              <div className="grid sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">First Name</label>
                  {editing ? (
                    <input
                      type="text"
                      value={formData.first_name}
                      onChange={(e) => setFormData((p) => ({ ...p, first_name: e.target.value }))}
                      className="input"
                    />
                  ) : (
                    <p className="text-gray-900 dark:text-white py-2.5">{user.first_name}</p>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Last Name</label>
                  {editing ? (
                    <input
                      type="text"
                      value={formData.last_name}
                      onChange={(e) => setFormData((p) => ({ ...p, last_name: e.target.value }))}
                      className="input"
                    />
                  ) : (
                    <p className="text-gray-900 dark:text-white py-2.5">{user.last_name}</p>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Email</label>
                  <p className="text-gray-900 dark:text-white py-2.5">{user.email}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Phone</label>
                  {editing ? (
                    <input
                      type="tel"
                      value={formData.phone}
                      onChange={(e) => setFormData((p) => ({ ...p, phone: e.target.value }))}
                      className="input"
                      placeholder="+1 234 567 890"
                    />
                  ) : (
                    <p className="text-gray-900 dark:text-white py-2.5">{user.phone || 'Not set'}</p>
                  )}
                </div>
              </div>
              {editing && (
                <button onClick={handleSave} className="btn-primary gap-2">
                  <Shield size={18} />
                  Save Changes
                </button>
              )}
            </div>
          )}

          {activeTab === 'orders' && (
            <div>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-bold text-gray-900 dark:text-white">Order History</h2>
              </div>
              {mockOrders.length > 0 ? (
                <div className="space-y-3">
                  {mockOrders.map((order) => (
                    <div key={order.id} className="card p-4 hover:shadow-md transition-shadow">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <div className="w-12 h-12 bg-primary-50 dark:bg-primary-950/30 rounded-xl flex items-center justify-center">
                            <Package size={20} className="text-primary-600 dark:text-primary-400" />
                          </div>
                          <div>
                            <p className="font-semibold text-gray-900 dark:text-white">{order.id}</p>
                            <p className="text-sm text-gray-500 dark:text-gray-400">{order.date} • {order.items} items</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="font-bold text-gray-900 dark:text-white">${order.total.toFixed(2)}</p>
                          <span className={`badge ${statusColors[order.status]}`}>
                            {order.status.charAt(0).toUpperCase() + order.status.slice(1)}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12">
                  <div className="text-5xl mb-3">📦</div>
                  <p className="text-gray-500 dark:text-gray-400">No orders yet</p>
                  <Link to="/products" className="text-primary-600 dark:text-primary-400 text-sm hover:underline mt-2 inline-block">
                    Start Shopping
                  </Link>
                </div>
              )}
            </div>
          )}

          {activeTab === 'wishlist' && (
            <div>
              <h2 className="text-lg font-bold text-gray-900 dark:text-white mb-4">My Wishlist</h2>
              {mockWishlist.length > 0 ? (
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                  {mockWishlist.map((item) => (
                    <div key={item.id} className="card overflow-hidden group">
                      <div className="aspect-square bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
                        <span className="text-4xl">🛍️</span>
                      </div>
                      <div className="p-3">
                        <p className="font-semibold text-sm text-gray-900 dark:text-white truncate">{item.name}</p>
                        <p className="text-lg font-bold text-primary-600 dark:text-primary-400">${item.price.toFixed(2)}</p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12">
                  <div className="text-5xl mb-3">❤️</div>
                  <p className="text-gray-500 dark:text-gray-400">Your wishlist is empty</p>
                </div>
              )}
            </div>
          )}

          {activeTab === 'addresses' && (
            <div>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-bold text-gray-900 dark:text-white">Saved Addresses</h2>
                <button className="btn-primary text-sm gap-2">
                  <MapPin size={16} />
                  Add Address
                </button>
              </div>
              <div className="grid sm:grid-cols-2 gap-4">
                <div className="card p-5 border-primary-200 dark:border-primary-800 relative">
                  <span className="absolute top-3 right-3 badge badge-primary">Default</span>
                  <h3 className="font-semibold text-gray-900 dark:text-white mb-1">Home</h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    John Doe<br />
                    123 Main Street, Apt 4B<br />
                    San Francisco, CA 94102<br />
                    United States
                  </p>
                  <div className="flex gap-2 mt-3">
                    <button className="text-xs text-primary-600 dark:text-primary-400 hover:underline">Edit</button>
                    <button className="text-xs text-red-500 hover:underline">Delete</button>
                  </div>
                </div>
                <div className="card p-5 border-dashed border-2 border-gray-200 dark:border-gray-700 flex items-center justify-center cursor-pointer hover:border-primary-300 dark:hover:border-primary-700 transition-colors">
                  <div className="text-center text-gray-400">
                    <MapPin size={32} className="mx-auto mb-2" />
                    <p className="text-sm">Add new address</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'settings' && (
            <div className="space-y-6 max-w-2xl">
              <h2 className="text-lg font-bold text-gray-900 dark:text-white">Account Settings</h2>

              {/* Notifications */}
              <div>
                <h3 className="font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                  <Bell size={18} />
                  Notifications
                </h3>
                <div className="space-y-3">
                  {[
                    { label: 'Order updates', desc: 'Get notified about order status changes' },
                    { label: 'Promotional emails', desc: 'Receive deals and offers' },
                    { label: 'New arrivals', desc: 'Be the first to know about new products' },
                  ].map((setting) => (
                    <label key={setting.label} className="flex items-center justify-between p-3 rounded-xl bg-gray-50 dark:bg-gray-800/50 cursor-pointer">
                      <div>
                        <p className="font-medium text-sm text-gray-900 dark:text-white">{setting.label}</p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">{setting.desc}</p>
                      </div>
                      <input type="checkbox" defaultChecked className="w-5 h-5 rounded border-gray-300 text-primary-600 focus:ring-primary-500" />
                    </label>
                  ))}
                </div>
              </div>

              {/* Payment methods */}
              <div>
                <h3 className="font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                  <CreditCard size={18} />
                  Payment Methods
                </h3>
                <div className="space-y-3">
                  <div className="flex items-center gap-4 p-4 rounded-xl bg-gray-50 dark:bg-gray-800/50">
                    <div className="w-12 h-8 bg-gradient-to-r from-blue-600 to-blue-800 rounded flex items-center justify-center">
                      <span className="text-white text-xs font-bold">VISA</span>
                    </div>
                    <div className="flex-1">
                      <p className="font-medium text-sm text-gray-900 dark:text-white">•••• •••• •••• 4242</p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">Expires 12/2026</p>
                    </div>
                    <span className="badge badge-primary text-xs">Default</span>
                  </div>
                  <button className="w-full p-4 rounded-xl border-2 border-dashed border-gray-200 dark:border-gray-700 text-gray-400 hover:border-primary-300 hover:text-primary-600 dark:hover:border-primary-700 dark:hover:text-primary-400 transition-colors">
                    + Add new payment method
                  </button>
                </div>
              </div>

              {/* Danger zone */}
              <div className="pt-6 border-t border-gray-200 dark:border-gray-800">
                <h3 className="font-semibold text-red-600 dark:text-red-400 mb-3">Danger Zone</h3>
                <div className="flex items-center justify-between p-4 rounded-xl bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-800">
                  <div>
                    <p className="font-medium text-sm text-red-700 dark:text-red-300">Delete Account</p>
                    <p className="text-xs text-red-500 dark:text-red-400">Permanently delete your account and all data</p>
                  </div>
                  <button className="px-4 py-2 rounded-xl bg-red-600 text-white text-sm font-medium hover:bg-red-700 transition-colors">
                    Delete
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
