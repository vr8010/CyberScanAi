import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  ArrowLeft, Download, Mail, Shield, CheckCircle, XCircle,
  Clock, Globe, Lock, AlertTriangle, Loader2, RefreshCw
} from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import toast from 'react-hot-toast'
import { format } from 'date-fns'
import { scanAPI } from '../utils/api'
import RiskScoreRing from '../components/scanner/RiskScoreRing'
import VulnerabilityList from '../components/scanner/VulnerabilityList'
import clsx from 'clsx'

const STATUS_ICON = {
  pass:    { icon: CheckCircle, color: 'text-green-400' },
  fail:    { icon: XCircle,     color: 'text-red-400' },
  warning: { icon: AlertTriangle, color: 'text-yellow-400' },
}

function MetaBadge({ icon: Icon, label, value, ok }) {
  return (
    <div className="card p-4 flex items-center gap-3">
      <div className={clsx('w-9 h-9 rounded-lg flex items-center justify-center',
        ok === true  ? 'bg-green-500/10' :
        ok === false ? 'bg-red-500/10' : 'bg-slate-800'
      )}>
        <Icon size={18} className={
          ok === true  ? 'text-green-400' :
          ok === false ? 'text-red-400'   : 'text-slate-400'
        } />
      </div>
      <div>
        <p className="text-xs text-slate-500">{label}</p>
        <p className="text-sm font-semibold text-slate-200">{value}</p>
      </div>
    </div>
  )
}

export default function ScanResult() {
  const { id } = useParams()
  const [scan, setScan]       = useState(null)
  const [loading, setLoading] = useState(true)
  const [downloading, setDownloading] = useState(false)
  const [activeTab, setActiveTab] = useState('vulnerabilities')

  useEffect(() => {
    loadScan()
  }, [id])

  const loadScan = async () => {
    setLoading(true)
    try {
      const { data } = await scanAPI.getScan(id)
      setScan(data)
    } catch {
      toast.error('Could not load scan result')
    } finally {
      setLoading(false)
    }
  }

  const handleDownloadPDF = async () => {
    setDownloading(true)
    try {
      const { data } = await scanAPI.downloadPDF(id)
      const url   = window.URL.createObjectURL(new Blob([data], { type: 'application/pdf' }))
      const link  = document.createElement('a')
      link.href   = url
      link.download = `security-report-${id.slice(0, 8)}.pdf`
      link.click()
      window.URL.revokeObjectURL(url)
      toast.success('PDF downloaded!')
    } catch {
      toast.error('Failed to download PDF')
    } finally {
      setDownloading(false)
    }
  }

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center min-h-64">
        <Loader2 size={32} className="animate-spin text-blue-400" />
      </div>
    )
  }

  if (!scan) {
    return (
      <div className="p-6 text-center">
        <p className="text-slate-400">Scan not found.</p>
        <Link to="/dashboard" className="text-blue-400 hover:underline mt-2 inline-block">← Back to dashboard</Link>
      </div>
    )
  }

  const tabs = [
    { id: 'vulnerabilities', label: `Vulnerabilities (${scan.vulnerabilities?.length ?? 0})` },
    { id: 'checks',          label: `All Checks (${scan.raw_findings?.length ?? 0})` },
    { id: 'report',          label: 'AI Report' },
  ]

  return (
    <div className="p-6 max-w-4xl mx-auto animate-fade-in">
      {/* Back */}
      <Link to="/dashboard" className="flex items-center gap-1.5 text-sm text-slate-400 hover:text-slate-200 mb-5 transition-colors">
        <ArrowLeft size={16} /> Back to Dashboard
      </Link>

      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-6">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <Globe size={16} className="text-slate-400 flex-shrink-0" />
            <h1 className="text-base md:text-lg font-bold text-slate-100 truncate">{scan.target_url}</h1>
          </div>
          <p className="text-sm text-slate-400">
            Scanned {scan.created_at ? format(new Date(scan.created_at), 'MMM d, yyyy · HH:mm') : '—'}
          </p>
        </div>
        <div className="flex gap-2 flex-shrink-0">
          <button onClick={loadScan} className="btn-secondary flex items-center gap-2 text-sm py-2 px-3">
            <RefreshCw size={14} />
          </button>
          <button
            onClick={handleDownloadPDF}
            disabled={downloading || scan.status !== 'completed'}
            className="btn-secondary flex items-center gap-2 text-sm py-2 px-3"
          >
            {downloading ? <Loader2 size={14} className="animate-spin" /> : <Download size={14} />}
            <span className="hidden sm:inline">PDF</span>
          </button>
        </div>
      </div>

      {/* Score + Meta grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        <div className="card p-4 flex items-center justify-center col-span-2 md:col-span-1">
          <RiskScoreRing score={scan.risk_score ?? 0} size="md" />
        </div>
        <MetaBadge icon={Lock}   label="SSL Certificate" value={scan.ssl_valid ? `Valid · ${scan.ssl_expiry_days}d left` : 'Invalid / Missing'} ok={scan.ssl_valid} />
        <MetaBadge icon={Clock}  label="Response Time"   value={scan.response_time_ms ? `${scan.response_time_ms}ms` : 'N/A'} ok={scan.response_time_ms < 1000} />
        <MetaBadge icon={Shield} label="Server Header"   value={scan.server_header || 'Hidden ✓'} ok={!scan.server_header} />
      </div>

      {/* Severity counts */}
      <div className="grid grid-cols-4 gap-2 md:gap-3 mb-6">
        {[
          { label: 'Critical', count: scan.critical_count, cls: 'severity-critical' },
          { label: 'High',     count: scan.high_count,     cls: 'severity-high' },
          { label: 'Medium',   count: scan.medium_count,   cls: 'severity-medium' },
          { label: 'Low',      count: scan.low_count,      cls: 'severity-low' },
        ].map(({ label, count, cls }) => (
          <div key={label} className={clsx('card p-3 text-center rounded-xl', count > 0 ? '' : 'opacity-50')}>
            <p className={clsx('text-2xl font-bold', cls.replace('severity-', 'text-').replace('-', '-400').split(' ')[0])}>{count}</p>
            <p className="text-xs text-slate-400 mt-0.5">{label}</p>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div className="flex gap-1 p-1 bg-slate-900 rounded-xl border border-slate-800 mb-4 overflow-x-auto">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={clsx(
              'flex-1 min-w-max px-3 py-2 text-xs md:text-sm font-medium rounded-lg transition-all whitespace-nowrap',
              activeTab === tab.id
                ? 'bg-blue-600 text-white shadow'
                : 'text-slate-400 hover:text-slate-200'
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="animate-fade-in">
        {activeTab === 'vulnerabilities' && (
          <VulnerabilityList vulnerabilities={scan.vulnerabilities ?? []} />
        )}

        {activeTab === 'checks' && (
          <div className="space-y-2">
            {(scan.raw_findings ?? []).map((f, i) => {
              const cfg = STATUS_ICON[f.status] || STATUS_ICON.warning
              const Icon = cfg.icon
              return (
                <div key={i} className="card flex items-start gap-3 p-3.5">
                  <Icon size={16} className={clsx('flex-shrink-0 mt-0.5', cfg.color)} />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-slate-200">{f.check}</p>
                    <p className="text-xs text-slate-400 mt-0.5 leading-relaxed">{f.detail}</p>
                  </div>
                </div>
              )
            })}
            {(scan.raw_findings ?? []).length === 0 && (
              <p className="text-slate-400 text-sm text-center py-8">No check data available.</p>
            )}
          </div>
        )}

        {activeTab === 'report' && (
          <div className="card p-6">
            {scan.ai_report ? (
              <div className="prose prose-invert prose-sm max-w-none
                prose-headings:text-slate-100 prose-h3:text-blue-400
                prose-strong:text-slate-200 prose-code:text-blue-300
                prose-code:bg-slate-800 prose-code:px-1 prose-code:rounded
                prose-a:text-blue-400 prose-li:text-slate-300">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {scan.ai_report}
                </ReactMarkdown>
              </div>
            ) : (
              <p className="text-slate-400 text-sm text-center py-8">
                AI report not available. Ensure OPENAI_API_KEY is configured.
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
