import { Link } from 'react-router-dom'
import { ExternalLink, ChevronRight, Clock, CheckCircle2, XCircle, Loader2 } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import clsx from 'clsx'

function RiskBadge({ score }) {
  if (score == null) return <span className="text-slate-500 text-xs">—</span>
  const color = score >= 70 ? 'severity-critical' : score >= 45 ? 'severity-high' : score >= 20 ? 'severity-medium' : 'severity-low'
  return <span className={clsx('text-xs font-bold px-2 py-0.5 rounded-full', color)}>{Math.round(score)}</span>
}

function StatusIcon({ status }) {
  if (status === 'completed') return <CheckCircle2 size={14} className="text-green-400" />
  if (status === 'failed')    return <XCircle size={14} className="text-red-400" />
  return <Loader2 size={14} className="text-blue-400 animate-spin" />
}

export default function ScanHistoryTable({ scans = [], onDelete }) {
  if (!scans.length) return (
    <div className="card p-12 text-center">
      <div className="w-12 h-12 bg-slate-800 rounded-xl flex items-center justify-center mx-auto mb-3">
        <Clock size={24} className="text-slate-600" />
      </div>
      <p className="text-slate-400 font-medium">No scans yet</p>
      <p className="text-slate-600 text-sm mt-1">Run your first scan to see history here</p>
    </div>
  )

  return (
    <div className="card overflow-hidden">
      <table className="w-full">
        <thead>
          <tr className="border-b border-slate-800">
            <th className="text-left text-xs font-semibold text-slate-500 uppercase tracking-wider px-5 py-3">URL</th>
            <th className="text-left text-xs font-semibold text-slate-500 uppercase tracking-wider px-3 py-3 hidden sm:table-cell">Risk</th>
            <th className="text-left text-xs font-semibold text-slate-500 uppercase tracking-wider px-3 py-3 hidden md:table-cell">Issues</th>
            <th className="text-left text-xs font-semibold text-slate-500 uppercase tracking-wider px-3 py-3 hidden lg:table-cell">Date</th>
            <th className="text-left text-xs font-semibold text-slate-500 uppercase tracking-wider px-3 py-3">Status</th>
            <th className="px-3 py-3" />
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800/60">
          {scans.map(scan => (
            <tr key={scan.id} className="hover:bg-slate-800/30 transition-colors group">
              <td className="px-5 py-3.5">
                <div className="flex items-center gap-2">
                  <span className="text-sm text-slate-200 font-medium truncate max-w-[200px]">
                    {scan.target_url.replace(/^https?:\/\//, '')}
                  </span>
                  <a
                    href={scan.target_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-slate-600 hover:text-blue-400 transition-colors opacity-0 group-hover:opacity-100"
                    onClick={e => e.stopPropagation()}
                  >
                    <ExternalLink size={12} />
                  </a>
                </div>
              </td>
              <td className="px-3 py-3.5 hidden sm:table-cell">
                <RiskBadge score={scan.risk_score} />
              </td>
              <td className="px-3 py-3.5 hidden md:table-cell">
                <div className="flex items-center gap-1.5 text-xs text-slate-400">
                  {scan.critical_count > 0 && <span className="text-red-400 font-medium">{scan.critical_count}C</span>}
                  {scan.high_count > 0    && <span className="text-orange-400 font-medium">{scan.high_count}H</span>}
                  {scan.medium_count > 0  && <span className="text-yellow-400 font-medium">{scan.medium_count}M</span>}
                  {scan.low_count > 0     && <span className="text-green-400 font-medium">{scan.low_count}L</span>}
                  {!scan.critical_count && !scan.high_count && !scan.medium_count && !scan.low_count && (
                    <span className="text-slate-600">—</span>
                  )}
                </div>
              </td>
              <td className="px-3 py-3.5 hidden lg:table-cell">
                <span className="text-xs text-slate-500">
                  {formatDistanceToNow(new Date(scan.created_at), { addSuffix: true })}
                </span>
              </td>
              <td className="px-3 py-3.5">
                <div className="flex items-center gap-1.5">
                  <StatusIcon status={scan.status} />
                  <span className="text-xs text-slate-500 capitalize">{scan.status}</span>
                </div>
              </td>
              <td className="px-3 py-3.5">
                {scan.status === 'completed' && (
                  <Link
                    to={`/dashboard/scans/${scan.id}`}
                    className="flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300 transition-colors"
                  >
                    View <ChevronRight size={12} />
                  </Link>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
