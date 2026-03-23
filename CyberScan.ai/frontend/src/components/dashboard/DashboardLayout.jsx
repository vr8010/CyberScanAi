import { useState } from 'react'
import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { Shield, LayoutDashboard, Search, User, LogOut, Zap, ShieldAlert, Menu, X } from 'lucide-react'
import useAuthStore from '../../store/authStore'
import toast from 'react-hot-toast'
import clsx from 'clsx'

const navItems = [
  { to: '/dashboard',         label: 'Dashboard',  icon: LayoutDashboard, end: true },
  { to: '/dashboard/scan',    label: 'New Scan',    icon: Search },
  { to: '/dashboard/profile', label: 'Profile',     icon: User },
]

export default function DashboardLayout() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)

  const handleLogout = () => {
    logout()
    toast.success('Logged out')
    navigate('/login')
  }

  const SidebarContent = () => (
    <>
      {/* Logo */}
      <div className="px-6 py-5 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
            <Shield size={18} className="text-white" />
          </div>
          <span className="font-bold text-lg tracking-tight">CyberScan.Ai</span>
        </div>
        <button onClick={() => setOpen(false)} className="md:hidden text-slate-400 hover:text-slate-200">
          <X size={20} />
        </button>
      </div>

      {/* Plan badge */}
      <div className="px-4 py-3 border-b border-slate-800">
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-semibold bg-green-500/10 text-green-400 border border-green-500/20">
          <Zap size={12} />
          Full Access — Free
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {navItems.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            onClick={() => setOpen(false)}
            className={({ isActive }) => clsx(
              'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all',
              isActive
                ? 'bg-blue-600/20 text-blue-400 border border-blue-500/20'
                : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800'
            )}
          >
            <Icon size={18} />
            {label}
          </NavLink>
        ))}
        {user?.is_admin && (
          <NavLink
            to="/dashboard/admin"
            onClick={() => setOpen(false)}
            className={({ isActive }) => clsx(
              'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all mt-2',
              isActive
                ? 'bg-red-600/20 text-red-400 border border-red-500/20'
                : 'text-slate-400 hover:text-red-400 hover:bg-red-500/10'
            )}
          >
            <ShieldAlert size={18} />
            Admin Panel
          </NavLink>
        )}
      </nav>

      {/* User + Logout */}
      <div className="px-3 py-4 border-t border-slate-800">
        <div className="flex items-center gap-3 px-3 py-2 mb-1">
          <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0">
            {user?.full_name?.[0]?.toUpperCase() || user?.email?.[0]?.toUpperCase() || 'U'}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-slate-100 truncate">{user?.full_name || 'User'}</p>
            <p className="text-xs text-slate-500 truncate">{user?.email}</p>
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-slate-400 hover:text-red-400 hover:bg-red-500/10 transition-all"
        >
          <LogOut size={18} />
          Sign out
        </button>
      </div>
    </>
  )

  return (
    <div className="flex h-screen bg-slate-950 overflow-hidden">
      {/* ── Desktop Sidebar ─────────────────────────────────────────── */}
      <aside className="hidden md:flex w-64 bg-slate-900 border-r border-slate-800 flex-col flex-shrink-0">
        <SidebarContent />
      </aside>

      {/* ── Mobile Overlay ───────────────────────────────────────────── */}
      {open && (
        <div className="fixed inset-0 z-40 md:hidden">
          <div className="absolute inset-0 bg-black/60" onClick={() => setOpen(false)} />
          <aside className="absolute left-0 top-0 h-full w-72 bg-slate-900 border-r border-slate-800 flex flex-col z-50">
            <SidebarContent />
          </aside>
        </div>
      )}

      {/* ── Main content ─────────────────────────────────────────────── */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Mobile topbar */}
        <div className="md:hidden flex items-center gap-3 px-4 py-3 bg-slate-900 border-b border-slate-800 flex-shrink-0">
          <button onClick={() => setOpen(true)} className="text-slate-400 hover:text-slate-200">
            <Menu size={22} />
          </button>
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 bg-blue-600 rounded flex items-center justify-center">
              <Shield size={13} className="text-white" />
            </div>
            <span className="font-bold text-sm">CyberScan.Ai</span>
          </div>
        </div>
        <main className="flex-1 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
