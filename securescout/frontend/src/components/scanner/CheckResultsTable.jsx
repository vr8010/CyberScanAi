import { CheckCircle, XCircle, AlertCircle } from 'lucide-react'
import clsx from 'clsx'

const STATUS_CONFIG = {
  pass:    { icon: CheckCircle,  label: 'Pass',    className: 'text-green-400' },
  fail:    { icon: XCircle,     label: 'Fail',    className: 'text-red-400' },
  warning: { icon: AlertCircle, label: 'Warning', className: 'text-yellow-400' },
}

export default function CheckResultsTable({ findings = [] }) {
  if (!findings.length) return null

  return (
    <div className="card overflow-hidden">
      <div className="px-5 py-4 border-b border-slate-800">
        <h3 className="font-semibold text-slate-100">Detailed Check Results</h3>
        <p className="text-xs text-slate-500 mt-0.5">{findings.length} security checks performed</p>
      </div>
      <div className="divide-y divide-slate-800/60">
        {findings.map((f, i) => {
          const cfg = STATUS_CONFIG[f.status] || STATUS_CONFIG.warning
          const Icon = cfg.icon
          return (
            <div key={i} className="flex items-start gap-3 px-5 py-3 hover:bg-slate-800/30 transition-colors">
              <Icon size={16} className={clsx('mt-0.5 flex-shrink-0', cfg.className)} />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-slate-200">{f.check}</p>
                <p className="text-xs text-slate-400 mt-0.5 leading-relaxed">{f.detail}</p>
              </div>
              <span className={clsx('text-xs font-semibold flex-shrink-0', cfg.className)}>
                {cfg.label}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
