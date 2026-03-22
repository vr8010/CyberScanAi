import { CheckCircle, XCircle, AlertTriangle } from 'lucide-react'
import clsx from 'clsx'

const STATUS_CONFIG = {
  pass:    { icon: CheckCircle,   color: 'text-green-400',  bg: 'bg-green-500/10',  label: 'Pass' },
  fail:    { icon: XCircle,       color: 'text-red-400',    bg: 'bg-red-500/10',    label: 'Fail' },
  warning: { icon: AlertTriangle, color: 'text-yellow-400', bg: 'bg-yellow-500/10', label: 'Warn' },
}

export default function FindingsTable({ findings = [] }) {
  if (!findings.length) return null

  return (
    <div className="overflow-hidden rounded-xl border border-slate-800">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-slate-800/80 border-b border-slate-700">
            <th className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider w-1/3">Check</th>
            <th className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider w-24">Status</th>
            <th className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider">Detail</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800/60">
          {findings.map((f, i) => {
            const cfg = STATUS_CONFIG[f.status] || STATUS_CONFIG.warning
            const Icon = cfg.icon
            return (
              <tr key={i} className="hover:bg-slate-800/30 transition-colors">
                <td className="px-4 py-3 font-medium text-slate-300 text-xs font-mono">{f.check}</td>
                <td className="px-4 py-3">
                  <span className={clsx('inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-semibold', cfg.color, cfg.bg)}>
                    <Icon size={11} />
                    {cfg.label}
                  </span>
                </td>
                <td className="px-4 py-3 text-slate-400 text-xs leading-relaxed">{f.detail}</td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
