import { useState, useEffect } from 'react'
import {
  Globe, Search, Shield, Server, Wifi, FolderOpen, Mail,
  Code2, AlertTriangle, CheckCircle, Loader2, ChevronDown, ChevronUp,
  Clock, Trash2, RefreshCw, ArrowLeft
} from 'lucide-react'
import toast from 'react-hot-toast'
import { attackSurfaceAPI } from '../utils/api'
import { formatDistanceToNow } from 'date-fns'
import clsx from 'clsx'

const SEV_COLOR = {
  critical: 'text-red-400 bg-red-500/10 border-red-500/20',
  high:     'text-orange-400 bg-orange-500/10 border-orange-500/20',
  medium:   'text-yellow-400 bg-yellow-500/10 border-yellow-500/20',
  low:      'text-blue-400 bg-blue-500/10 border-blue-500/20',
  info:     'text-slate-400 bg-slate-500/10 border-slate-500/20',
  pass:     'text-green-400 bg-green-500/10 border-green-500/20',
  fail:     'text-red-400 bg-red-500/10 border-red-500/20',
}

function SevBadge({ level }) {
  return (
    <span className={clsx('text-xs px-2 py-0.5 rounded-full border font-medium capitalize', SEV_COLOR[level] || SEV_COLOR.info)}>
      {level}
    </span>
  )
}

function Section({ icon: Icon, title, count, color = 'text-blue-400', children, defaultOpen = false }) {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <div className="card overflow-hidden">
      <button
        onClick={() => setOpen(v => !v)}
        className="w-full flex items-center justify-between px-5 py-4 hover:bg-slate-800/30 transition-colors"
      >
        <div className="flex items-center gap-3">
          <Icon size={18} className={color} />
          <span className="font-semibold text-slate-200">{title}</span>
          {count !== undefined && (
            <span className="text-xs bg-slate-700 text-slate-300 px-2 py-0.5 rounded-full">{count}</span>
          )}
        </div>
        {open ? <ChevronUp size={16} className="text-slate-500" /> : <ChevronDown size={16} className="text-slate-500" />}
      </button>
      {open && <div className="border-t border-slate-800 px-5 py-4">{children}</div>}
    </div>
  )
}

function SummaryCard({ label, value, icon: Icon, color }) {
  return (
    <div className="card p-4 text-center">
      <Icon size={18} className={clsx('mx-auto mb-2', color)} />
      <p className="text-2xl font-bold text-slate-100">{value}</p>
      <p className="text-xs text-slate-500 mt-0.5">{label}</p>
    </div>
  )
}

function ResultSections({ result }) {
  return (
    <div className="space-y-4">
      {/* Open Ports */}
      <Section icon={Wifi} title="Open Ports" count={result.open_ports.length} color="text-blue-400" defaultOpen={result.open_ports.length > 0}>
        {result.open_ports.length === 0 ? <p className="text-slate-500 text-sm">No common ports found open</p> : (
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
            {result.open_ports.map(p => (
              <div key={p.port} className={clsx('flex items-center justify-between p-3 rounded-lg border',
                p.risk === 'high' ? 'bg-red-500/5 border-red-500/20' : 'bg-slate-800/50 border-slate-700')}>
                <div><span className="font-mono font-bold text-slate-200">{p.port}</span><span className="text-xs text-slate-500 ml-2">{p.service}</span></div>
                <SevBadge level={p.risk} />
              </div>
            ))}
          </div>
        )}
      </Section>

      {/* Subdomains */}
      <Section icon={Globe} title="Subdomains" count={result.subdomains.length} color="text-purple-400" defaultOpen={result.subdomains.length > 0}>
        {result.subdomains.length === 0 ? <p className="text-slate-500 text-sm">No common subdomains found</p> : (
          <div className="space-y-2">
            {result.subdomains.map(s => (
              <div key={s.subdomain} className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg border border-slate-700">
                <div className="flex items-center gap-2"><Globe size={13} className="text-purple-400" /><span className="text-sm font-medium text-slate-200">{s.subdomain}</span></div>
                <span className="font-mono text-xs text-slate-500">{s.ip}</span>
              </div>
            ))}
          </div>
        )}
      </Section>

      {/* Exposed Paths */}
      <Section icon={FolderOpen} title="Exposed Paths / Files" count={result.exposed_paths.length} color="text-orange-400" defaultOpen={result.exposed_paths.length > 0}>
        {result.exposed_paths.length === 0 ? <p className="text-slate-500 text-sm">No sensitive paths found</p> : (
          <div className="space-y-2">
            {result.exposed_paths.map((p, i) => (
              <div key={i} className={clsx('p-3 rounded-lg border', SEV_COLOR[p.severity] || SEV_COLOR.info)}>
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="font-mono text-sm font-medium truncate">{p.path}</span>
                    <span className="text-xs opacity-60">HTTP {p.status_code}</span>
                  </div>
                  <SevBadge level={p.severity} />
                </div>
                <p className="text-xs opacity-70 mt-1">{p.description}</p>
              </div>
            ))}
          </div>
        )}
      </Section>

      {/* DNS */}
      <Section icon={Server} title="DNS Records" color="text-green-400" defaultOpen>
        <div className="space-y-3">
          {Object.entries(result.dns_records).map(([type, records]) => records.length > 0 && (
            <div key={type}>
              <p className="text-xs font-semibold text-slate-500 uppercase mb-1">{type}</p>
              <div className="space-y-1">
                {records.map((r, i) => (
                  <div key={i} className="font-mono text-xs text-slate-300 bg-slate-800 px-3 py-1.5 rounded border border-slate-700 truncate">{r}</div>
                ))}
              </div>
            </div>
          ))}
          {Object.values(result.dns_records).every(r => r.length === 0) && <p className="text-slate-500 text-sm">No DNS records found</p>}
        </div>
      </Section>

      {/* Technologies */}
      <Section icon={Code2} title="Technologies Detected" count={result.technologies.length} color="text-cyan-400" defaultOpen={result.technologies.length > 0}>
        {result.technologies.length === 0 ? <p className="text-slate-500 text-sm">No technologies fingerprinted</p> : (
          <div className="flex flex-wrap gap-2">
            {result.technologies.map((t, i) => (
              <div key={i} className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 border border-slate-700 rounded-lg">
                <Code2 size={12} className="text-cyan-400" />
                <span className="text-sm text-slate-200">{t.name}</span>
                <span className="text-xs text-slate-500">· {t.category}</span>
              </div>
            ))}
          </div>
        )}
      </Section>

      {/* Email Security */}
      <Section icon={Mail} title="Email Security (SPF / DMARC)" count={result.email_security.length} color="text-yellow-400" defaultOpen>
        {result.email_security.length === 0 ? <p className="text-slate-500 text-sm">Could not check email security</p> : (
          <div className="space-y-2">
            {result.email_security.map((e, i) => (
              <div key={i} className={clsx('flex items-start gap-3 p-3 rounded-lg border',
                e.status === 'pass' ? 'bg-green-500/5 border-green-500/20' : 'bg-red-500/5 border-red-500/20')}>
                {e.status === 'pass'
                  ? <CheckCircle size={15} className="text-green-400 flex-shrink-0 mt-0.5" />
                  : <AlertTriangle size={15} className="text-red-400 flex-shrink-0 mt-0.5" />}
                <div>
                  <p className="text-sm font-medium text-slate-200">{e.check}</p>
                  <p className="text-xs text-slate-400 mt-0.5">{e.detail}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </Section>
    </div>
  )
}

export default function AttackSurface() {
  const [url, setUrl]         = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult]   = useState(null)
  const [history, setHistory] = useState([])
  const [histLoading, setHistLoading] = useState(true)
  const [view, setView]       = useState('scan') // 'scan' | 'history'

  useEffect(() => { loadHistory() }, [])

  const loadHistory = async () => {
    setHistLoading(true)
    try { const { data } = await attackSurfaceAPI.getHistory(); setHistory(data) }
    catch {}
    finally { setHistLoading(false) }
  }

  const handleScan = async (e) => {
    e.preventDefault()
    if (!url.trim()) return
    setLoading(true)
    setResult(null)
    try {
      const { data } = await attackSurfaceAPI.discover(url)
      setResult(data)
      toast.success('Discovery complete!')
      loadHistory() // refresh history
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Discovery failed')
    } finally {
      setLoading(false)
    }
  }

  const loadHistoryItem = async (id) => {
    try {
      const { data } = await attackSurfaceAPI.getHistoryItem(id)
      setResult(data)
      setView('scan')
      window.scrollTo(0, 0)
    } catch { toast.error('Failed to load') }
  }

  const deleteHistoryItem = async (id, e) => {
    e.stopPropagation()
    if (!confirm('Delete this record?')) return
    try {
      await attackSurfaceAPI.deleteHistory(id)
      setHistory(p => p.filter(h => h.id !== id))
      if (result?.id === id) setResult(null)
      toast.success('Deleted')
    } catch { toast.error('Failed') }
  }

  return (
    <div className="p-4 md:p-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between gap-3 mb-5">
        <div>
          <h1 className="text-xl md:text-2xl font-bold text-slate-100 flex items-center gap-2">
            <Globe size={22} className="text-blue-400" /> Attack Surface Discovery
          </h1>
          <p className="text-slate-400 text-sm mt-1">Discover open ports, subdomains, exposed files, DNS records, and tech stack</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 p-1 bg-slate-900 rounded-xl border border-slate-800 mb-5 w-fit">
        {['scan','history'].map(t => (
          <button key={t} onClick={() => setView(t)}
            className={clsx('px-4 py-1.5 rounded-lg text-sm font-medium capitalize transition-all',
              view === t ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-slate-200')}>
            {t === 'history' ? `History (${history.length})` : 'New Scan'}
          </button>
        ))}
      </div>

      {/* ── SCAN VIEW ── */}
      {view === 'scan' && (<>
        <form onSubmit={handleScan} className="card p-5 mb-6">
          <div className="flex gap-3">
            <div className="flex-1 relative">
              <Globe size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
              <input type="text" value={url} onChange={e => setUrl(e.target.value)}
                placeholder="https://example.com" className="input-field pl-9 w-full" disabled={loading} />
            </div>
            <button type="submit" disabled={loading || !url.trim()} className="btn-primary flex items-center gap-2 whitespace-nowrap">
              {loading ? <><Loader2 size={15} className="animate-spin" /> Scanning…</> : <><Search size={15} /> Discover</>}
            </button>
          </div>
          {loading && (
            <div className="mt-4 p-3 bg-slate-800/50 rounded-lg">
              <div className="flex items-center gap-2 text-sm text-slate-400 mb-2">
                <Loader2 size={14} className="animate-spin text-blue-400" />
                Running port scan, subdomain enumeration, path probing, DNS lookup…
              </div>
              <div className="h-1.5 bg-slate-700 rounded-full overflow-hidden">
                <div className="h-full bg-blue-500 rounded-full animate-pulse w-3/4" />
              </div>
            </div>
          )}
        </form>

        {result && (
          <div className="space-y-4 animate-fade-in">
            {/* Summary */}
            <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
              <SummaryCard label="Open Ports"    value={result.summary.open_ports_count}    icon={Wifi}          color="text-blue-400" />
              <SummaryCard label="Subdomains"    value={result.summary.subdomains_found}    icon={Globe}         color="text-purple-400" />
              <SummaryCard label="Exposed Paths" value={result.summary.exposed_paths_count} icon={FolderOpen}    color="text-orange-400" />
              <SummaryCard label="Critical"      value={result.summary.critical_exposures}  icon={AlertTriangle} color="text-red-400" />
              <SummaryCard label="Technologies"  value={result.summary.technologies_found}  icon={Code2}         color="text-green-400" />
              <SummaryCard label="High Risk"     value={result.summary.high_exposures}      icon={Shield}        color="text-yellow-400" />
            </div>
            <ResultSections result={result} />
          </div>
        )}

        {!result && !loading && (
          <div className="card p-12 text-center border-dashed">
            <div className="w-16 h-16 bg-blue-600/10 border border-blue-500/20 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <Globe size={32} className="text-blue-400" />
            </div>
            <p className="text-slate-300 font-medium">Enter a domain to start discovery</p>
            <p className="text-slate-500 text-sm mt-1">Scans ports, subdomains, files, DNS, and tech stack</p>
          </div>
        )}
      </>)}

      {/* ── HISTORY VIEW ── */}
      {view === 'history' && (
        <div>
          <div className="flex items-center justify-between mb-3">
            <p className="text-sm text-slate-400">{history.length} saved discoveries</p>
            <button onClick={loadHistory} className="btn-secondary text-xs flex items-center gap-1.5 py-1.5">
              <RefreshCw size={12} /> Refresh
            </button>
          </div>

          {histLoading ? (
            <div className="card p-10 flex items-center justify-center">
              <RefreshCw size={20} className="animate-spin text-blue-400" />
            </div>
          ) : history.length === 0 ? (
            <div className="card p-10 text-center border-dashed">
              <Clock size={28} className="text-slate-600 mx-auto mb-2" />
              <p className="text-slate-400">No history yet — run a discovery first</p>
            </div>
          ) : (
            <div className="space-y-2">
              {history.map(h => (
                <div key={h.id} onClick={() => loadHistoryItem(h.id)}
                  className="card p-4 cursor-pointer hover:border-slate-600 transition-all group">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <Globe size={13} className="text-blue-400 flex-shrink-0" />
                        <p className="text-sm font-medium text-slate-200 truncate">{h.domain}</p>
                      </div>
                      <div className="flex items-center gap-3 flex-wrap text-xs text-slate-500">
                        <span className="flex items-center gap-1"><Clock size={11} />{formatDistanceToNow(new Date(h.created_at), { addSuffix: true })}</span>
                        {h.summary.open_ports_count > 0    && <span className="text-blue-400">{h.summary.open_ports_count} ports</span>}
                        {h.summary.subdomains_found > 0    && <span className="text-purple-400">{h.summary.subdomains_found} subdomains</span>}
                        {h.summary.critical_exposures > 0  && <span className="text-red-400">{h.summary.critical_exposures} critical</span>}
                        {h.summary.exposed_paths_count > 0 && <span className="text-orange-400">{h.summary.exposed_paths_count} paths</span>}
                      </div>
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      <span className="text-xs text-blue-400 opacity-0 group-hover:opacity-100 transition-opacity">View →</span>
                      <button onClick={e => deleteHistoryItem(h.id, e)}
                        className="p-1.5 rounded hover:bg-red-500/10 text-slate-600 hover:text-red-400 transition-colors opacity-0 group-hover:opacity-100">
                        <Trash2 size={13} />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
