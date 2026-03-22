import { useState } from 'react'
import { Search, Shield, AlertCircle, Loader2 } from 'lucide-react'
import clsx from 'clsx'

export default function ScanForm({ onScan, isScanning }) {
  const [url, setUrl] = useState('')
  const [error, setError] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    setError('')

    let cleanUrl = url.trim()
    if (!cleanUrl) { setError('Please enter a website URL'); return }
    if (!cleanUrl.startsWith('http://') && !cleanUrl.startsWith('https://')) {
      cleanUrl = 'https://' + cleanUrl
    }

    try {
      new URL(cleanUrl)
    } catch {
      setError('Please enter a valid URL (e.g. https://example.com)')
      return
    }

    onScan(cleanUrl)
  }

  return (
    <div className="card p-6">
      <div className="flex items-center gap-3 mb-5">
        <div className="w-10 h-10 bg-blue-600/20 border border-blue-500/30 rounded-lg flex items-center justify-center">
          <Search size={20} className="text-blue-400" />
        </div>
        <div>
          <h2 className="font-semibold text-slate-100">Scan a Website</h2>
          <p className="text-sm text-slate-400">Enter any URL to run a full AI security analysis</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="flex gap-3">
        <div className="flex-1 relative">
          <Shield size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500 pointer-events-none" />
          <input
            type="text"
            value={url}
            onChange={e => { setUrl(e.target.value); setError('') }}
            placeholder="https://yourwebsite.com"
            disabled={isScanning}
            className={clsx(
              'input-field pl-10',
              error && 'border-red-500/50 focus:ring-red-500'
            )}
          />
        </div>
        <button
          type="submit"
          disabled={isScanning || !url.trim()}
          className="btn-primary flex items-center gap-2 whitespace-nowrap"
        >
          {isScanning ? (
            <><Loader2 size={16} className="animate-spin" /> Scanning…</>
          ) : (
            <><Search size={16} /> Scan Now</>
          )}
        </button>
      </form>

      {error && (
        <p className="text-red-400 text-sm mt-2 flex items-center gap-1.5">
          <AlertCircle size={14} /> {error}
        </p>
      )}

      {isScanning && (
        <div className="mt-4 scan-overlay rounded-lg bg-slate-800 p-4">
          <div className="flex items-center gap-3">
            <Loader2 size={18} className="text-blue-400 animate-spin flex-shrink-0" />
            <div>
              <p className="text-sm font-medium text-slate-200">Scanning in progress…</p>
              <p className="text-xs text-slate-400 mt-0.5">
                Checking SSL, HTTP headers, XSS patterns, and generating AI report. This takes 10–20 seconds.
              </p>
            </div>
          </div>
          <div className="mt-3 h-1.5 bg-slate-700 rounded-full overflow-hidden">
            <div className="h-full bg-blue-500 rounded-full animate-pulse" style={{ width: '60%' }} />
          </div>
        </div>
      )}
    </div>
  )
}
