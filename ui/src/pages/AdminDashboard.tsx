import { useState, useEffect } from 'react';
import {
  Users,
  Store,
  Package,
  DollarSign,
  Activity,

  Database,
  Cpu,
  Globe,
  Plus,
  Search,
  Eye,
  Shield,
  Ban,

  RefreshCw,
  BarChart3,
  AlertTriangle,
  CheckCircle,

} from 'lucide-react';
import type { AdminStats, AdminUser } from '../types';

const mockStats: AdminStats = {
  total_users: 15420,
  total_sellers: 842,
  total_products: 28450,
  total_orders: 52340,
  total_revenue: 2450000,
  monthly_revenue: 345000,
  monthly_orders: 4230,
  revenue_growth_rate: 18.5,
  user_growth_rate: 12.3,
};

const mockUsers: AdminUser[] = [
  { id: 'u1', email: 'alice@example.com', first_name: 'Alice', last_name: 'Johnson', role: 'customer', status: 'active', created_at: 1704067200000 },
  { id: 'u2', email: 'bob@example.com', first_name: 'Bob', last_name: 'Smith', role: 'seller', status: 'active', created_at: 1703980800000 },
  { id: 'u3', email: 'carol@example.com', first_name: 'Carol', last_name: 'Davis', role: 'customer', status: 'suspended', created_at: 1703894400000 },
  { id: 'u4', email: 'david@example.com', first_name: 'David', last_name: 'Wilson', role: 'customer', status: 'active', created_at: 1703808000000 },
  { id: 'u5', email: 'eva@example.com', first_name: 'Eva', last_name: 'Martinez', role: 'seller', status: 'active', created_at: 1703721600000 },
  { id: 'u6', email: 'frank@example.com', first_name: 'Frank', last_name: 'Lee', role: 'customer', status: 'active', created_at: 1703635200000 },
];

const systemHealth = [
  { name: 'API Gateway', status: 'healthy', uptime: '99.98%', responseTime: '45ms' },
  { name: 'Auth Service', status: 'healthy', uptime: '99.95%', responseTime: '32ms' },
  { name: 'Catalog Service', status: 'healthy', uptime: '99.92%', responseTime: '67ms' },
  { name: 'Cart Service', status: 'warning', uptime: '98.50%', responseTime: '234ms' },
  { name: 'Payment Service', status: 'healthy', uptime: '99.99%', responseTime: '120ms' },
  { name: 'Search Service', status: 'healthy', uptime: '99.90%', responseTime: '28ms' },
];

const recentActivity = [
  { action: 'New user registered', user: 'alice@example.com', time: '2 min ago', type: 'user' },
  { action: 'New product listed', user: 'bob@example.com', time: '15 min ago', type: 'product' },
  { action: 'Order completed', user: 'david@example.com', time: '30 min ago', type: 'order' },
  { action: 'Payment received', user: 'carol@example.com', time: '1 hour ago', type: 'payment' },
  { action: 'Seller verified', user: 'eva@example.com', time: '2 hours ago', type: 'seller' },
];

export default function AdminDashboard() {
  const [stats] = useState<AdminStats>(mockStats);
  const [users] = useState<AdminUser[]>(mockUsers);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => setLoading(false), 800);
    return () => clearTimeout(timer);
  }, []);

  const formatCurrency = (amount: number) =>
    new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(amount);

  const statusColors: Record<string, string> = {
    active: 'badge-success',
    suspended: 'badge-danger',
    pending: 'badge-warning',
  };

  const activityIcons: Record<string, { icon: React.ReactNode; color: string }> = {
    user: { icon: <Users size={16} />, color: 'text-blue-500 bg-blue-50 dark:bg-blue-950/30' },
    product: { icon: <Package size={16} />, color: 'text-green-500 bg-green-50 dark:bg-green-950/30' },
    order: { icon: <BarChart3 size={16} />, color: 'text-primary-500 bg-primary-50 dark:bg-primary-950/30' },
    payment: { icon: <DollarSign size={16} />, color: 'text-amber-500 bg-amber-50 dark:bg-amber-950/30' },
    seller: { icon: <Store size={16} />, color: 'text-purple-500 bg-purple-50 dark:bg-purple-950/30' },
  };

  if (loading) {
    return (
      <div className="min-h-screen pt-24 lg:pt-28 pb-16 bg-gray-50 dark:bg-gray-950 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin" />
          <p className="text-gray-500 dark:text-gray-400 text-sm">Loading admin panel...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950 pt-24 lg:pt-28 pb-16">
      <div className="max-w-7xl mx-auto px-4">
        {/* Header */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-8">
          <div>
            <h1 className="text-2xl lg:text-3xl font-bold text-gray-900 dark:text-white">Admin Dashboard</h1>
            <p className="text-gray-500 dark:text-gray-400">Monitor and manage your marketplace</p>
          </div>
          <div className="flex gap-2">
            <button className="btn-secondary gap-2 text-sm">
              <RefreshCw size={16} />
              Refresh
            </button>
            <button className="btn-primary gap-2 text-sm">
              <Plus size={16} />
              Add User
            </button>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
          {[
            { label: 'Total Users', value: stats.total_users.toLocaleString(), icon: Users, color: 'from-blue-500 to-blue-600', change: stats.user_growth_rate },
            { label: 'Sellers', value: stats.total_sellers.toLocaleString(), icon: Store, color: 'from-purple-500 to-purple-600', change: 8.2 },
            { label: 'Products', value: stats.total_products.toLocaleString(), icon: Package, color: 'from-green-500 to-emerald-600', change: 15.3 },
            { label: 'Orders', value: stats.total_orders.toLocaleString(), icon: Activity, color: 'from-amber-500 to-orange-500', change: 12.1 },
            { label: 'Revenue', value: formatCurrency(stats.total_revenue), icon: DollarSign, color: 'from-primary-500 to-primary-600', change: stats.revenue_growth_rate },
          ].map((stat) => (
            <div key={stat.label} className={`stat-card bg-gradient-to-br ${stat.color} text-white`}>
              <div className="flex items-center justify-between mb-2">
                <stat.icon size={20} className="opacity-80" />
                <span className="flex items-center gap-1 text-xs bg-white/20 px-2 py-0.5 rounded-lg">
                  {stat.change >= 0 ? '↑' : '↓'} {Math.abs(stat.change)}%
                </span>
              </div>
              <p className="text-xl lg:text-2xl font-bold">{stat.value}</p>
              <p className="text-sm opacity-80">{stat.label}</p>
            </div>
          ))}
        </div>

        {/* Quick actions */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-8">
          {[
            { label: 'Add Product', icon: Plus, color: 'text-green-600 dark:text-green-400' },
            { label: 'Manage Users', icon: Users, color: 'text-blue-600 dark:text-blue-400' },
            { label: 'View Reports', icon: BarChart3, color: 'text-primary-600 dark:text-primary-400' },
            { label: 'System Logs', icon: Activity, color: 'text-amber-600 dark:text-amber-400' },
          ].map((action) => (
            <button
              key={action.label}
              className="card p-4 flex items-center gap-3 hover:shadow-md transition-shadow text-left"
            >
              <div className={`w-10 h-10 rounded-xl bg-gray-50 dark:bg-gray-800 flex items-center justify-center ${action.color}`}>
                <action.icon size={20} />
              </div>
              <span className="font-medium text-sm text-gray-900 dark:text-white">{action.label}</span>
            </button>
          ))}
        </div>

        <div className="grid lg:grid-cols-3 gap-6 mb-8">
          {/* Users table */}
          <div className="lg:col-span-2 card overflow-hidden">
            <div className="p-4 border-b border-gray-100 dark:border-gray-800 flex items-center justify-between">
              <h3 className="font-bold text-gray-900 dark:text-white">User Management</h3>
              <div className="relative">
                <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search users..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9 pr-4 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-sm text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500/40 w-48"
                />
              </div>
            </div>
            <div className="overflow-x-auto">
              <table className="table-base">
                <thead>
                  <tr>
                    <th>User</th>
                    <th>Role</th>
                    <th>Status</th>
                    <th>Joined</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {users
                    .filter((u) =>
                      !searchQuery ||
                      u.first_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                      u.email.toLowerCase().includes(searchQuery.toLowerCase())
                    )
                    .map((user) => (
                      <tr key={user.id}>
                        <td>
                          <div className="flex items-center gap-3">
                            <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-primary-600 rounded-full flex items-center justify-center text-white text-xs font-bold">
                              {user.first_name?.[0]}{user.last_name?.[0]}
                            </div>
                            <div>
                              <p className="font-medium text-sm text-gray-900 dark:text-white">
                                {user.first_name} {user.last_name}
                              </p>
                              <p className="text-xs text-gray-500 dark:text-gray-400">{user.email}</p>
                            </div>
                          </div>
                        </td>
                        <td>
                          <span className="badge badge-primary text-xs capitalize">{user.role}</span>
                        </td>
                        <td>
                          <span className={`badge ${statusColors[user.status]}`}>{user.status}</span>
                        </td>
                        <td className="text-sm text-gray-500 dark:text-gray-400">
                          {user.created_at ? new Date(user.created_at).toLocaleDateString() : '—'}
                        </td>
                        <td>
                          <div className="flex items-center gap-1">
                            <button className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors">
                              <Eye size={14} />
                            </button>
                            <button className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-400 hover:text-amber-600 transition-colors">
                              <Shield size={14} />
                            </button>
                            <button className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-400 hover:text-red-500 transition-colors">
                              <Ban size={14} />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* System health */}
          <div className="card p-5">
            <h3 className="font-bold text-gray-900 dark:text-white mb-4">System Health</h3>
            <div className="space-y-4">
              {systemHealth.map((service) => (
                <div key={service.name} className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    {service.status === 'healthy' ? (
                      <CheckCircle size={16} className="text-green-500" />
                    ) : (
                      <AlertTriangle size={16} className="text-amber-500" />
                    )}
                    <span className="text-sm text-gray-700 dark:text-gray-300">{service.name}</span>
                  </div>
                  <div className="text-right">
                    <span className={`badge ${service.status === 'healthy' ? 'badge-success' : 'badge-warning'} text-xs`}>
                      {service.status}
                    </span>
                    <p className="text-xs text-gray-400 mt-0.5">{service.responseTime}</p>
                  </div>
                </div>
              ))}
            </div>

            {/* Resource usage */}
            <div className="mt-6 pt-4 border-t border-gray-100 dark:border-gray-800">
              <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Resources</h4>
              {[
                { label: 'CPU', value: 45, icon: Cpu },
                { label: 'Memory', value: 68, icon: Database },
                { label: 'Network', value: 32, icon: Globe },
              ].map((resource) => (
                <div key={resource.label} className="mb-3">
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="text-gray-500 dark:text-gray-400 flex items-center gap-1">
                      <resource.icon size={12} />
                      {resource.label}
                    </span>
                    <span className="font-medium text-gray-700 dark:text-gray-300">{resource.value}%</span>
                  </div>
                  <div className="h-2 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all ${
                        resource.value > 70 ? 'bg-amber-500' : resource.value > 50 ? 'bg-primary-500' : 'bg-green-500'
                      }`}
                      style={{ width: `${resource.value}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="card overflow-hidden">
          <div className="p-4 border-b border-gray-100 dark:border-gray-800">
            <h3 className="font-bold text-gray-900 dark:text-white">Recent Activity</h3>
          </div>
          <div className="divide-y divide-gray-100 dark:divide-gray-800">
            {recentActivity.map((activity, idx) => {
              const iconInfo = activityIcons[activity.type] || activityIcons.user;
              return (
                <div key={idx} className="flex items-center gap-4 p-4 hover:bg-gray-50 dark:hover:bg-gray-800/30 transition-colors">
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${iconInfo.color}`}>
                    {iconInfo.icon}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-900 dark:text-white">
                      <span className="font-medium">{activity.action}</span>
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 truncate">{activity.user}</p>
                  </div>
                  <span className="text-xs text-gray-400 whitespace-nowrap">{activity.time}</span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
