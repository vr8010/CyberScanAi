import { CheckCircle2, XCircle, AlertCircle } from 'lucide-react'
import clsx from 'clsx'

const STATUS_CONFIG = {
  pass:    { icon: CheckCircle2, color: 'text-green-400', bg: 'bg-green-500/5', border: 'border-green-500/10' },
  fail:    { icon: XCircle,      color: 'text-red-400',   bg: 'bg-red-500/5',   border: 'border-red-500/10' },
  warning: { icon: AlertCircle,  color: 'text-yellow-400',bg: 'bg-yellow-500/5',border: 'border-yellow-500/10' },
}

export default function FindingsChecklist({ findings = [] }) {
  if (!findings.length) return (
    <p className="text-slate-500 text-sm text-center py-6">No findings available.</p>
  )

  const passes   = findings.filter(f => f.status === 'pass')
  const fails    = findings.filter(f => f.status === 'fail')
  const warnings = findings.filter(f => f.status === 'warning')

  const ordered = [...fails, ...warnings, ...passes]

  return (
    <div className="space-y-1.5">
      {ordered.map((finding, i) => {
        const cfg = STATUS_CONFIG[finding.status] || STATUS_CONFIG.warning
        const Icon = cfg.icon
        return (
          <div
            key={i}
            className={clsx('flex items-start gap-3 p-3 rounded-lg border text-sm', cfg.bg, cfg.border)}
          >
            <Icon size={15} className={clsx('mt-0.5 flex-shrink-0', cfg.color)} />
            <div className="flex-1 min-w-0">
              <p className="font-medium text-slate-200 text-xs">{finding.check}</p>
              <p className="text-slate-400 text-xs mt-0.5 leading-relaxed">{finding.detail}</p>
            </div>
          </div>
        )
      })}
    </div>
  )
}
