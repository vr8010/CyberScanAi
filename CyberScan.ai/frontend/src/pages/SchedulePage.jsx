import { useEffect, useState } from 'react'
import { Clock, Plus, Trash2, ToggleLeft, ToggleRight, Calendar, Mail, RefreshCw, Globe, Edit2, X, Check } from 'lucide-react'
import toast from 'react-hot-toast'
import { scheduleAPI } from '../utils/api'
import clsx from 'clsx'

const DAYS = ['mon','tue','wed','thu','fri','sat','sun']
const DAY_LABELS = { mon:'Monday', tue:'Tuesday', wed:'Wednesday', thu:'Thursday', fri:'Friday', sat:'Saturday', sun:'Sunday' }
const HOURS = Array.from({ length: 24 }, (_, i) => i)

const FREQ_COLORS = {
  daily:   'bg-blue-500/10 text-blue-400 border-blue-500/20',
  weekly:  'bg-purple-500/10 text-purple-400 border-purple-500/20',
  monthly: 'bg-orange-500/10 text-orange-400 border-orange-500/20',
}

function formatHour(h) {
  const ampm = h < 12 ? 'AM' : 'PM'
  const display = h === 0 ? 12 : h > 12 ? h - 12 : h
  return `${display}:00 ${ampm}`
}

function nextRunLabel(next_run_at) {
  if (!next_run_at) return '—'
  const d = new Date(next_run_at)
  return d.toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function ScheduleForm({ onSave, onCancel, initial = null }) {
  const [url, setUrl]           = useState(initial?.url || '')
  const [freq, setFreq]         = useState(initial?.frequency || 'daily')
  const [day, setDay]           = useState(initial?.day_of_week || 'mon')
  const [hour, setHour]         = useState(initial?.hour ?? 8)
  const [notify, setNotify]     = useState(initial?.email_notify ?? true)
  const [saving, setSaving]     = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!url.trim()) { toast.error('Enter a URL'); return }
    let cleanUrl = url.trim()
    if (!cleanUrl.startsWith('http')) cleanUrl = 'https://' + cleanUrl

    setSaving(true)
    try {
      const payload = {
        url: cleanUrl, frequency: freq,
        day_of_week: freq === 'weekly' ? day : null,
        hour, email_notify: notify,
      }
      await onSave(payload)
    } finally {
      setSaving(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* URL */}
      <div>
        <label className="block text-sm text-slate-400 mb-1">Website URL</label>
        <div className="relative">
          <Globe size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            type="text" value={url} onChange={e => setUrl(e.target.value)}
            placeholder="https://yourwebsite.com"
            className="input-field pl-9 w-full" required
          />
        </div>
      </div>

      {/* Frequency */}
      <div>
        <label className="block text-sm text-slate-400 mb-2">Frequency</label>
        <div className="flex gap-2">
          {['daily','weekly','monthly'].map(f => (
            <button key={f} type="button" onClick={() => setFreq(f)}
              className={clsx('flex-1 py-2 rounded-lg text-sm font-medium border capitalize transition-all',
                freq === f ? FREQ_COLORS[f] : 'border-slate-700 text-slate-500 hover:text-slate-300'
              )}>
              {f}
            </button>
          ))}
        </div>
      </div>

      {/* Day of week (weekly only) */}
      {freq === 'weekly' && (
        <div>
          <label className="block text-sm text-slate-400 mb-2">Day of Week</label>
          <div className="flex gap-1 flex-wrap">
            {DAYS.map(d => (
              <button key={d} type="button" onClick={() => setDay(d)}
                className={clsx('px-3 py-1.5 rounded-lg text-xs font-medium border transition-all',
                  day === d ? 'bg-purple-500/20 text-purple-400 border-purple-500/30' : 'border-slate-700 text-slate-500 hover:text-slate-300'
                )}>
                {d.charAt(0).toUpperCase() + d.slice(1)}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Hour */}
      <div>
        <label className="block text-sm text-slate-400 mb-1">Time (UTC)</label>
        <select value={hour} onChange={e => setHour(+e.target.value)} className="input-field w-full">
          {HOURS.map(h => (
            <option key={h} value={h}>{formatHour(h)}</option>
          ))}
        </select>
      </div>

      {/* Email notify */}
      <div className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg border border-slate-700">
        <div className="flex items-center gap-2">
          <Mail size={15} className="text-slate-400" />
          <span className="text-sm text-slate-300">Email report after scan</span>
        </div>
        <button type="button" onClick={() => setNotify(v => !v)}>
          {notify
            ? <ToggleRight size={24} className="text-blue-400" />
            : <ToggleLeft  size={24} className="text-slate-600" />}
        </button>
      </div>

      {/* Actions */}
      <div className="flex gap-2 pt-1">
        <button type="submit" disabled={saving}
          className="btn-primary flex items-center gap-2 flex-1 justify-center">
          {saving ? <RefreshCw size={14} className="animate-spin" /> : <Check size={14} />}
          {initial ? 'Save Changes' : 'Create Schedule'}
        </button>
        <button type="button" onClick={onCancel} className="btn-secondary px-4">
          <X size={14} />
        </button>
      </div>
    </form>
  )
}

function ScheduleCard({ schedule, onToggle, onDelete, onEdit }) {
  return (
    <div className={clsx('card p-4 transition-all', !schedule.is_active && 'opacity-50')}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <Globe size={13} className="text-slate-500 flex-shrink-0" />
            <p className="text-sm font-medium text-slate-200 truncate">{schedule.url}</p>
          </div>
          <div className="flex items-center gap-2 flex-wrap mt-2">
            <span className={clsx('text-xs px-2 py-0.5 rounded-full border capitalize', FREQ_COLORS[schedule.frequency])}>
              {schedule.frequency}
              {schedule.frequency === 'weekly' && schedule.day_of_week && ` · ${DAY_LABELS[schedule.day_of_week]}`}
            </span>
            <span className="text-xs text-slate-500 flex items-center gap-1">
              <Clock size={11} /> {formatHour(schedule.hour)} UTC
            </span>
            {schedule.email_notify && (
              <span className="text-xs text-slate-500 flex items-center gap-1">
                <Mail size={11} /> Email on
              </span>
            )}
          </div>
          <div className="flex items-center gap-3 mt-2 text-xs text-slate-600">
            <span>Runs: {schedule.run_count}</span>
            {schedule.next_run_at && <span>Next: {nextRunLabel(schedule.next_run_at)}</span>}
          </div>
        </div>

        <div className="flex items-center gap-1 flex-shrink-0">
          <button onClick={() => onEdit(schedule)} className="p-1.5 rounded hover:bg-slate-700 text-slate-500 hover:text-blue-400 transition-colors">
            <Edit2 size={14} />
          </button>
          <button onClick={() => onToggle(schedule)} className="p-1.5 rounded hover:bg-slate-700 text-slate-500 hover:text-yellow-400 transition-colors">
            {schedule.is_active ? <ToggleRight size={16} className="text-green-400" /> : <ToggleLeft size={16} />}
          </button>
          <button onClick={() => onDelete(schedule.id)} className="p-1.5 rounded hover:bg-red-500/10 text-slate-500 hover:text-red-400 transition-colors">
            <Trash2 size={14} />
          </button>
        </div>
      </div>
    </div>
  )
}

export default function SchedulePage() {
  const [schedules, setSchedules] = useState([])
  const [loading, setLoading]     = useState(true)
  const [showForm, setShowForm]   = useState(false)
  const [editing, setEditing]     = useState(null)

  const load = async () => {
    setLoading(true)
    try { const { data } = await scheduleAPI.list(); setSchedules(data) }
    catch { toast.error('Failed to load schedules') }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  const handleCreate = async (payload) => {
    try {
      const { data } = await scheduleAPI.create(payload)
      setSchedules(p => [data, ...p])
      setShowForm(false)
      toast.success('Schedule created!')
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to create')
    }
  }

  const handleEdit = async (payload) => {
    try {
      const { data } = await scheduleAPI.update(editing.id, payload)
      setSchedules(p => p.map(s => s.id === data.id ? data : s))
      setEditing(null)
      toast.success('Schedule updated!')
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to update')
    }
  }

  const handleToggle = async (schedule) => {
    try {
      const { data } = await scheduleAPI.update(schedule.id, { is_active: !schedule.is_active })
      setSchedules(p => p.map(s => s.id === data.id ? data : s))
      toast.success(data.is_active ? 'Schedule enabled' : 'Schedule paused')
    } catch { toast.error('Failed to update') }
  }

  const handleDelete = async (id) => {
    if (!confirm('Delete this schedule?')) return
    try {
      await scheduleAPI.delete(id)
      setSchedules(p => p.filter(s => s.id !== id))
      toast.success('Deleted')
    } catch { toast.error('Failed to delete') }
  }

  return (
    <div className="p-4 md:p-6 max-w-2xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between gap-3 mb-5">
        <div>
          <h1 className="text-xl md:text-2xl font-bold text-slate-100">Scheduled Scans</h1>
          <p className="text-slate-400 text-sm mt-0.5">Automate security scans on a schedule</p>
        </div>
        {!showForm && !editing && (
          <button onClick={() => setShowForm(true)} className="btn-primary flex items-center gap-2 text-sm">
            <Plus size={15} /> New Schedule
          </button>
        )}
      </div>

      {/* Create form */}
      {showForm && (
        <div className="card p-5 mb-5 border-blue-500/20">
          <h2 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">
            <Calendar size={15} className="text-blue-400" /> New Scheduled Scan
          </h2>
          <ScheduleForm onSave={handleCreate} onCancel={() => setShowForm(false)} />
        </div>
      )}

      {/* Edit form */}
      {editing && (
        <div className="card p-5 mb-5 border-yellow-500/20">
          <h2 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">
            <Edit2 size={15} className="text-yellow-400" /> Edit Schedule
          </h2>
          <ScheduleForm onSave={handleEdit} onCancel={() => setEditing(null)} initial={editing} />
        </div>
      )}

      {/* List */}
      {loading ? (
        <div className="card p-12 flex items-center justify-center">
          <RefreshCw size={22} className="animate-spin text-blue-400" />
        </div>
      ) : schedules.length === 0 ? (
        <div className="card p-12 text-center border-dashed">
          <div className="w-14 h-14 bg-slate-800 rounded-2xl flex items-center justify-center mx-auto mb-3">
            <Clock size={28} className="text-slate-600" />
          </div>
          <p className="text-slate-300 font-medium">No schedules yet</p>
          <p className="text-slate-500 text-sm mt-1">Create a schedule to automate your security scans</p>
          <button onClick={() => setShowForm(true)} className="btn-primary mt-4 inline-flex items-center gap-2 text-sm">
            <Plus size={14} /> Create First Schedule
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {schedules.map(s => (
            <ScheduleCard
              key={s.id} schedule={s}
              onToggle={handleToggle}
              onDelete={handleDelete}
              onEdit={(s) => { setEditing(s); setShowForm(false) }}
            />
          ))}
        </div>
      )}

      {/* Info box */}
      <div className="mt-6 p-4 bg-slate-800/40 border border-slate-700 rounded-lg text-xs text-slate-500 space-y-1">
        <p>• All times are in <span className="text-slate-400">UTC</span></p>
        <p>• Scans run automatically — no action needed</p>
        <p>• Email report is sent after each scan if enabled</p>
        <p>• Max 10 schedules per account</p>
      </div>
    </div>
  )
}
