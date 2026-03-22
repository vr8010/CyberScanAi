import { Link } from 'react-router-dom'
import { Shield, Search, FileText, Lock, Zap, CheckCircle, ArrowRight, Globe, AlertTriangle, TrendingUp } from 'lucide-react'

const FEATURES = [
  { icon: Search,       title: 'Deep Security Scan',     desc: 'SSL/TLS, HTTP headers, XSS patterns, cookie flags, mixed content — all in one scan.' },
  { icon: Shield,       title: 'AI-Powered Reports',     desc: 'LangChain + GPT generates plain-English reports with prioritised action plans.' },
  { icon: FileText,     title: 'PDF Export',             desc: 'Download a professional security report PDF to share with your team or client.' },
  { icon: Lock,         title: 'Risk Score 0–100',       desc: 'A single number that tells you exactly how exposed your site is right now.' },
  { icon: TrendingUp,   title: 'Scan History',           desc: 'Track your security posture over time. See progress as you fix issues.' },
  { icon: Zap,          title: 'Instant Results',        desc: 'Full scan completes in under 30 seconds. No waiting, no agents to install.' },
]

const CHECKS = [
  'HTTP Security Headers (7 checks)',
  'SSL/TLS Certificate Validation',
  'Certificate Expiry Warning',
  'XSS Pattern Detection',
  'Cookie Security Flags',
  'Mixed Content Detection',
  'Server Info Leakage',
  'HTTPS Redirect Verification',
]

export default function Landing() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      {/* ── Navbar ──────────────────────────────────────────────────────── */}
      <nav className="border-b border-slate-800 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <Shield size={18} className="text-white" />
            </div>
            <span className="font-bold text-lg">CyberScan.Ai</span>
          </div>
          <div className="flex items-center gap-3">
            <Link to="/login"   className="btn-secondary text-sm py-2 px-4">Sign in</Link>
            <Link to="/register" className="btn-primary text-sm py-2 px-4">Get Started Free</Link>
          </div>
        </div>
      </nav>

      {/* ── Hero ────────────────────────────────────────────────────────── */}
      <section className="relative max-w-6xl mx-auto px-6 pt-24 pb-20 text-center overflow-hidden">
        {/* Glow */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[400px] bg-blue-600/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-blue-600/15 border border-blue-500/25 rounded-full text-blue-400 text-sm font-medium mb-6">
            <Zap size={13} />
            AI-Powered Security for Small Businesses
          </div>

          <h1 className="text-5xl md:text-6xl font-extrabold tracking-tight mb-6 leading-tight">
            Is your website
            <br />
            <span className="text-blue-400">actually secure?</span>
          </h1>

          <p className="text-xl text-slate-400 max-w-2xl mx-auto mb-10 leading-relaxed">
            CyberScan.Ai scans your site for vulnerabilities, grades your security posture,
            and gives you an AI-generated action plan — in under 30 seconds.
          </p>

          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Link to="/register" className="btn-primary inline-flex items-center gap-2 text-base py-3 px-6">
              Scan Your Website Free <ArrowRight size={18} />
            </Link>
            <Link to="/login" className="btn-secondary inline-flex items-center gap-2 text-base py-3 px-6">
              Sign In
            </Link>
          </div>

          <p className="text-sm text-slate-500 mt-4">No credit card required · Unlimited free scans</p>
        </div>
      </section>

      {/* ── What we check ───────────────────────────────────────────────── */}
      <section className="max-w-6xl mx-auto px-6 py-16">
        <div className="card p-8">
          <div className="flex items-center gap-3 mb-6">
            <Globe size={20} className="text-blue-400" />
            <h2 className="text-lg font-semibold">What we scan for</h2>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {CHECKS.map((c, i) => (
              <div key={i} className="flex items-center gap-2 text-sm text-slate-300">
                <CheckCircle size={14} className="text-green-400 flex-shrink-0" />
                {c}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Features ────────────────────────────────────────────────────── */}
      <section className="max-w-6xl mx-auto px-6 py-16">
        <h2 className="text-3xl font-bold text-center mb-12">Everything you need to stay secure</h2>
        <div className="grid md:grid-cols-3 gap-5">
          {FEATURES.map(({ icon: Icon, title, desc }) => (
            <div key={title} className="card p-6 hover:border-slate-700 transition-colors group">
              <div className="w-10 h-10 bg-blue-600/15 border border-blue-500/20 rounded-lg flex items-center justify-center mb-4 group-hover:bg-blue-600/25 transition-colors">
                <Icon size={20} className="text-blue-400" />
              </div>
              <h3 className="font-semibold text-slate-100 mb-2">{title}</h3>
              <p className="text-sm text-slate-400 leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Risk Stat banner ────────────────────────────────────────────── */}
      <section className="max-w-6xl mx-auto px-6 py-12">
        <div className="bg-gradient-to-r from-red-500/10 to-orange-500/10 border border-red-500/20 rounded-2xl p-8 flex flex-col md:flex-row items-center gap-6">
          <AlertTriangle size={48} className="text-red-400 flex-shrink-0" />
          <div>
            <h3 className="text-xl font-bold mb-2">43% of cyberattacks target small businesses</h3>
            <p className="text-slate-400">
              Most attacks exploit simple misconfigurations — missing headers, expired SSL certs, insecure cookies.
              CyberScan.Ai finds these in seconds before attackers do.
            </p>
          </div>
          <Link to="/register" className="btn-primary whitespace-nowrap flex-shrink-0 py-3 px-6 inline-flex items-center gap-2">
            Scan Now <ArrowRight size={16} />
          </Link>
        </div>
      </section>

      {/* ── CTA ─────────────────────────────────────────────────────────── */}
      <section className="max-w-6xl mx-auto px-6 py-20 text-center">
        <h2 className="text-3xl font-bold mb-4">Start your free security scan</h2>
        <p className="text-slate-400 mb-8">No installation. No credit card. Results in 30 seconds.</p>
        <Link to="/register" className="btn-primary inline-flex items-center gap-2 text-base py-3 px-8">
          Create Free Account <ArrowRight size={18} />
        </Link>
      </section>

      {/* ── Footer ──────────────────────────────────────────────────────── */}
      <footer className="border-t border-slate-800 px-6 py-8">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4 text-sm text-slate-500">
          <div className="flex items-center gap-2">
            <Shield size={16} className="text-blue-400" />
            <span>CyberScan.Ai — AI Website Security Scanner</span>
          </div>
          <div className="flex gap-6">
            <Link to="/login"   className="hover:text-slate-300">Login</Link>
            <Link to="/register" className="hover:text-slate-300">Sign Up</Link>
          </div>
        </div>
      </footer>
    </div>
  )
}
