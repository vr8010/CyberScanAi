import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Search, Shield, AlertTriangle, TrendingUp, Clock, ChevronRight } from 'lucide-react'
import useAuthStore from '../store/authStore'
import { scanAPI, userAPI } from '../utils/api'
import StatCard from '../components/common/StatCard'
import ScanHistoryTable from '../components/scanner/ScanHistoryTable'
import { RadialBarChart, RadialBar, ResponsiveContainer, Tooltip } from 'recharts'

export default function Dashboard() {
  const { user } = useAuthStore()
  const [stats, setStats]   = useState(null)
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = async () => {
      try {
        const [statsRes, histRes] = await Promise.all([
          userAPI.getStats(),
          scanAPI.getHistory(5),
        ])
        setStats(statsRes.data)
        setHistory(histRes.data)
      } catch (e) {
        console.error(e)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const greeting = () => {
    const h = new Date().getHours()
    if (h < 12) return 'Good morning'
    if (h < 18) return 'Good afternoon'
    return 'Good evening'
  }

  return (
    <div className="p-6 space-y-6 animate-fade-in">
      {/* ── Header ───────────────────────────────────────────────────── */}
      <div className="flex items-start justify-between gap-3">
        <div>
          <h1 className="text-xl md:text-2xl font-bold text-slate-100">
            {greeting()}, {user?.full_name?.split(' ')[0] || 'there'} 👋
          </h1>
          <p className="text-slate-400 mt-1 text-sm">Here's your security overview</p>
        </div>
        <Link to="/dashboard/scan" className="btn-primary flex items-center gap-2 text-sm whitespace-nowrap flex-shrink-0">
          <Search size={16} /> New Scan
        </Link>
      </div>

      {/* ── Stats ────────────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 md:gap-4">
        <StatCard
          label="Total Scans"
          value={loading ? '…' : stats?.total_scans ?? 0}
          icon={Shield}
          color="blue"
        />
        <StatCard
          label="Scans Today"
          value={loading ? '…' : stats?.scans_today ?? 0}
          sub={user?.plan === 'free' ? 'Unlimited' : 'Unlimited'}
          icon={Clock}
          color="purple"
        />
        <StatCard
          label="Avg Risk Score"
          value={loading ? '…' : stats?.average_risk_score != null ? `${stats.average_risk_score}` : '—'}
          sub="Lower is better"
          icon={TrendingUp}
          color={
            !stats?.average_risk_score ? 'green' :
            stats.average_risk_score >= 70 ? 'red' :
            stats.average_risk_score >= 40 ? 'yellow' : 'green'
          }
        />
        <StatCard
          label="High-Risk Scans"
          value={loading ? '…' : stats?.high_risk_scans ?? 0}
          sub="Score ≥ 70"
          icon={AlertTriangle}
          color="red"
        />
      </div>

      {/* ── Recent Scans ─────────────────────────────────────────────── */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-base font-semibold text-slate-100">Recent Scans</h2>
          <Link to="/dashboard/scan" className="text-sm text-blue-400 hover:text-blue-300 flex items-center gap-1">
            View all <ChevronRight size={14} />
          </Link>
        </div>
        {loading ? (
          <div className="card p-8 flex items-center justify-center">
            <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : (
          <ScanHistoryTable scans={history} />
        )}
      </div>

      {/* ── Quick Actions ────────────────────────────────────────────── */}
      {!loading && history.length === 0 && (
        <div className="card p-8 text-center border-dashed">
          <div className="w-16 h-16 bg-blue-600/10 border border-blue-500/20 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <Shield size={32} className="text-blue-400" />
          </div>
          <h3 className="font-semibold text-slate-200 mb-2">Run your first security scan</h3>
          <p className="text-slate-400 text-sm mb-4 max-w-sm mx-auto">
            Enter any website URL to get an instant AI-powered security report with vulnerabilities and fixes.
          </p>
          <Link to="/dashboard/scan" className="btn-primary inline-flex items-center gap-2">
            <Search size={16} /> Start Scanning
          </Link>
        </div>
      )}
    </div>
  )
}
