import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Shield, Search, Trash2, RefreshCw } from 'lucide-react'
import toast from 'react-hot-toast'
import { scanAPI } from '../utils/api'
import ScanHistoryTable from '../components/scanner/ScanHistoryTable'

export default function ScansHistory() {
  const [scans, setScans]     = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch]   = useState('')

  const load = async () => {
    setLoading(true)
    try {
      const { data } = await scanAPI.getHistory(100)
      setScans(data)
    } catch { toast.error('Failed to load scans') }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  const handleDelete = async (id) => {
    if (!confirm('Delete this scan?')) return
    try {
      await scanAPI.deleteScan(id)
      setScans(p => p.filter(s => s.id !== id))
      toast.success('Scan deleted')
    } catch { toast.error('Failed to delete') }
  }

  const filtered = scans.filter(s =>
    s.target_url.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="p-4 md:p-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between gap-3 mb-5">
        <div>
          <h1 className="text-xl md:text-2xl font-bold text-slate-100">Scan History</h1>
          <p className="text-slate-400 text-sm mt-0.5">{scans.length} total scans</p>
        </div>
        <div className="flex gap-2">
          <button onClick={load} className="btn-secondary flex items-center gap-2 text-sm">
            <RefreshCw size={14} /> Refresh
          </button>
          <Link to="/dashboard/scan" className="btn-primary flex items-center gap-2 text-sm">
            <Shield size={14} /> New Scan
          </Link>
        </div>
      </div>

      {/* Search */}
      <div className="card flex items-center gap-3 px-4 py-2.5 mb-4">
        <Search size={15} className="text-slate-500 flex-shrink-0" />
        <input
          type="text"
          placeholder="Search by URL…"
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="bg-transparent text-sm text-slate-200 placeholder-slate-500 outline-none flex-1"
        />
        {search && (
          <button onClick={() => setSearch('')} className="text-slate-500 hover:text-slate-300 text-xs">
            Clear
          </button>
        )}
      </div>

      {loading ? (
        <div className="card p-12 flex items-center justify-center">
          <RefreshCw size={22} className="animate-spin text-blue-400" />
        </div>
      ) : (
        <ScanHistoryTable scans={filtered} onDelete={handleDelete} showDelete />
      )}
    </div>
  )
}
