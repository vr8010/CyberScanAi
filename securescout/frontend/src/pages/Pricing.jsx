import { Link } from 'react-router-dom'
import { Shield, Check, Zap, ArrowLeft } from 'lucide-react'
import useAuthStore from '../store/authStore'

const ALL_FEATURES = [
  'Unlimited scans per day',
  'All 7+ security checks',
  'Full AI-powered vulnerability report',
  'Priority recommendations',
  'Unlimited scan history',
  'PDF download',
  'Email report delivery',
  'Priority support',
]

export default function Pricing() {
  const { token } = useAuthStore()

  return (
    <div className="min-h-screen bg-slate-950 py-16 px-4">
      {/* Back link */}
      <div className="max-w-lg mx-auto mb-8">
        <Link
          to={token ? '/dashboard' : '/'}
          className="flex items-center gap-2 text-sm text-slate-400 hover:text-slate-200 transition-colors"
        >
          <ArrowLeft size={16} /> Back
        </Link>
      </div>

      <div className="max-w-lg mx-auto">
        {/* Heading */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 bg-green-500/10 border border-green-500/20 rounded-full text-sm text-green-400 font-medium mb-4">
            <Zap size={14} />
            100% Free — No credit card needed
          </div>
          <h1 className="text-4xl font-extrabold text-slate-100 mb-3">
            Full Access, Free Forever
          </h1>
          <p className="text-slate-400 text-lg">
            Everything unlocked. No plans, no paywalls.
          </p>
        </div>

        {/* Single Free Card */}
        <div className="card p-8 border-green-500/30 ring-1 ring-green-500/20">
          <div className="mb-6 text-center">
            <p className="text-sm font-semibold text-green-400 uppercase tracking-wider mb-2">Free</p>
            <p className="text-5xl font-bold text-slate-100">₹0</p>
            <p className="text-slate-500 text-sm mt-1">Forever free · No limits</p>
          </div>

          <ul className="space-y-3 mb-8">
            {ALL_FEATURES.map(f => (
              <li key={f} className="flex items-center gap-2.5 text-sm text-slate-300">
                <Check size={15} className="text-green-400 flex-shrink-0" /> {f}
              </li>
            ))}
          </ul>

          {token ? (
            <Link
              to="/dashboard/scan"
              className="btn-primary w-full flex items-center justify-center gap-2"
            >
              <Zap size={16} /> Start Scanning
            </Link>
          ) : (
            <Link
              to="/register"
              className="btn-primary w-full flex items-center justify-center gap-2"
            >
              <Zap size={16} /> Get Started Free
            </Link>
          )}
        </div>

        {/* Trust signals */}
        <div className="mt-8 text-center">
          <div className="flex items-center justify-center gap-6 flex-wrap">
            {['No Credit Card', 'SSL Encrypted', 'Unlimited Scans', 'Free Forever'].map(t => (
              <div key={t} className="flex items-center gap-1.5 text-sm text-slate-400">
                <Shield size={14} className="text-green-400" /> {t}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
