import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Shield, Lightbulb } from 'lucide-react'
import toast from 'react-hot-toast'
import useAuthStore from '../store/authStore'
import { scanAPI } from '../utils/api'
import ScanForm from '../components/scanner/ScanForm'

const TIPS = [
  'Always ensure your SSL certificate is valid and not expiring soon.',
  'Content Security Policy (CSP) headers dramatically reduce XSS risk.',
  'Hiding your server version (e.g. removing "Server: nginx/1.24") stops fingerprinting.',
  'HttpOnly cookies prevent JavaScript from reading session tokens.',
  'HSTS forces browsers to always use HTTPS, even if users type http://',
  'A risk score under 20 means your site has excellent baseline security.',
]

export default function ScanPage() {
  const navigate = useNavigate()
  const { user, refreshUser } = useAuthStore()
  const [isScanning, setIsScanning] = useState(false)

  const handleScan = async (url) => {
    setIsScanning(true)
    try {
      // Wake up Render if sleeping (retry up to 3x with delay)
      let startResp
      for (let attempt = 0; attempt < 3; attempt++) {
        try {
          startResp = await scanAPI.startScan(url)
          break
        } catch (err) {
          // 502/503 = Render waking up, wait and retry
          const status = err.response?.status
          if ((status === 502 || status === 503 || !status) && attempt < 2) {
            await new Promise(r => setTimeout(r, 5000))
            continue
          }
          throw err
        }
      }

      const scanId = startResp.data.id

      // Poll until completed or failed (max 2 min)
      let scan = startResp.data
      for (let i = 0; i < 40; i++) {
        if (scan.status === 'completed' || scan.status === 'failed') break
        await new Promise(r => setTimeout(r, 3000))
        try {
          const { data: polled } = await scanAPI.getScan(scanId)
          scan = polled
        } catch { /* ignore transient poll errors */ }
      }

      await refreshUser()

      if (scan.status === 'failed') {
        toast.error('Scan failed. Please try again.')
        return
      }

      if (scan.status !== 'completed') {
        toast.error('Scan timed out. Please try again.')
        return
      }

      toast.success('Scan completed!')
      navigate(`/dashboard/scans/${scanId}`)
    } catch (err) {
      const detail = err.response?.data?.detail
      if (typeof detail === 'object' && detail?.error === 'scan_limit_exceeded') {
        toast.error(detail.message)
      } else {
        toast.error(detail || 'Scan failed. Please try again.')
      }
    } finally {
      setIsScanning(false)
    }
  }

  return (
    <div className="p-6 max-w-3xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-100">New Security Scan</h1>
        <p className="text-slate-400 mt-1">
          Enter a URL to run an AI-powered security analysis. Results appear instantly.
        </p>
      </div>

      {/* Scan Form */}
      <ScanForm
        onScan={handleScan}
        isScanning={isScanning}
      />

      {/* What we check */}
      <div className="mt-6 card p-5">
        <h3 className="text-sm font-semibold text-slate-300 mb-3 flex items-center gap-2">
          <Shield size={16} className="text-blue-400" />
          What CyberScan.Ai checks
        </h3>
        <div className="grid grid-cols-2 gap-2">
          {[
            ['SSL/TLS Certificate', 'Validity, expiry, configuration'],
            ['Security Headers', 'HSTS, CSP, X-Frame-Options, etc.'],
            ['Server Info Leakage', 'Hidden tech stack disclosure'],
            ['Cookie Security', 'Secure, HttpOnly, SameSite flags'],
            ['XSS Patterns', 'Dangerous JS patterns in source'],
            ['Mixed Content', 'HTTP resources on HTTPS pages'],
            ['HTTPS Redirect', 'Proper HTTP→HTTPS enforcement'],
            ['AI Risk Report', 'Plain-English fixes and priority plan'],
          ].map(([title, desc]) => (
            <div key={title} className="bg-slate-800/50 rounded-lg p-3">
              <p className="text-sm font-medium text-slate-200">{title}</p>
              <p className="text-xs text-slate-500 mt-0.5">{desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Security tip */}
      <div className="mt-4 flex items-start gap-3 p-4 bg-blue-500/5 border border-blue-500/15 rounded-lg">
        <Lightbulb size={16} className="text-blue-400 mt-0.5 flex-shrink-0" />
        <div>
          <p className="text-xs font-semibold text-blue-400 uppercase tracking-wider mb-1">Security Tip</p>
          <p className="text-sm text-slate-400">
            {TIPS[Math.floor(Math.random() * TIPS.length)]}
          </p>
        </div>
      </div>
    </div>
  )
}
