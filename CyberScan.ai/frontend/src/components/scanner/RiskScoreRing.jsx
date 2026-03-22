import clsx from 'clsx'

const SIZE = 120
const STROKE = 10
const R = (SIZE - STROKE) / 2
const CIRC = 2 * Math.PI * R

function getRiskColor(score) {
  if (score >= 70) return { stroke: '#ef4444', text: 'text-red-400',   label: 'CRITICAL', bg: 'bg-red-500/10' }
  if (score >= 45) return { stroke: '#f97316', text: 'text-orange-400', label: 'HIGH',     bg: 'bg-orange-500/10' }
  if (score >= 20) return { stroke: '#f59e0b', text: 'text-yellow-400', label: 'MEDIUM',   bg: 'bg-yellow-500/10' }
  return              { stroke: '#10b981', text: 'text-green-400',  label: 'LOW',      bg: 'bg-green-500/10' }
}

export default function RiskScoreRing({ score = 0, size = 'md', showLabel = true }) {
  const { stroke, text, label, bg } = getRiskColor(score)
  const pct = Math.min(score / 100, 1)
  const dash = pct * CIRC
  const gap  = CIRC - dash

  const s = size === 'lg' ? 160 : size === 'sm' ? 80 : 120
  const sw = size === 'lg' ? 12 : size === 'sm' ? 7 : 10
  const rr = (s - sw) / 2
  const cc = 2 * Math.PI * rr

  const dashFill = Math.min(score / 100, 1) * cc

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative" style={{ width: s, height: s }}>
        <svg width={s} height={s} className="risk-ring">
          {/* Track */}
          <circle
            cx={s / 2} cy={s / 2} r={rr}
            fill="none" stroke="#1e293b" strokeWidth={sw}
          />
          {/* Fill */}
          <circle
            cx={s / 2} cy={s / 2} r={rr}
            fill="none"
            stroke={stroke}
            strokeWidth={sw}
            strokeDasharray={`${dashFill} ${cc - dashFill}`}
            strokeLinecap="round"
            style={{ transition: 'stroke-dasharray 0.6s ease' }}
          />
        </svg>
        {/* Score label */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={clsx('font-bold leading-none', text, size === 'lg' ? 'text-4xl' : size === 'sm' ? 'text-xl' : 'text-3xl')}>
            {Math.round(score)}
          </span>
          <span className="text-slate-500 text-xs mt-0.5">/100</span>
        </div>
      </div>
      {showLabel && (
        <span className={clsx('text-xs font-semibold px-2.5 py-0.5 rounded-full', text, bg)}>
          {label}
        </span>
      )}
    </div>
  )
}
