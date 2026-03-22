import { useState, useEffect } from 'react'
import { Users, BarChart2, Shield, Zap, Search, RefreshCw, Trash2, Ban,
  ShieldCheck, Crown, Globe, Mail, Settings, Eye } from 'lucide-react'
import api from '../utils/api'
import toast from 'react-hot-toast'

const TABS = ['Overview','Users','Scans','Emails','Settings']

export default function Admin() {
  const [tab, setTab]         = useState('Overview')
  const [stats, setStats]     = useState(null)
  const [users, setUsers]     = useState([])
  const [scans, setScans]     = useState([])
  const [sysSettings, setSysSettings] = useState(null)
  const [search, setSearch]   = useState('')
  const [loading, setLoading] = useState(true)
  // email form
  const [emailTo, setEmailTo]   = useState('')
  const [emailSub, setEmailSub] = useState('')
  const [emailMsg, setEmailMsg] = useState('')
  const [emailSending, setEmailSending] = useState(false)
  // scan detail modal
  const [scanDetail, setScanDetail] = useState(null)

  const fetchData = async () => {
    setLoading(true)
    try {
      const [s, u, sc, ss] = await Promise.all([
        api.get('/admin/stats'),
        api.get('/admin/users?limit=200'),
        api.get('/admin/scans?limit=100'),
        api.get('/admin/settings'),
      ])
      setStats(s.data); setUsers(u.data); setScans(sc.data)
      setSysSettings(ss.data)
    } catch { toast.error('Failed to load admin data') }
    finally { setLoading(false) }
  }
  useEffect(() => { fetchData() }, [])

  const changePlan    = async (id, plan) => { await api.patch(`/admin/users/${id}/plan?plan=${plan}`); toast.success(`Plan → ${plan}`); setUsers(p=>p.map(u=>u.id===id?{...u,plan}:u)) }
  const toggleAdmin   = async (id, cur)  => { await api.patch(`/admin/users/${id}/admin?is_admin=${!cur}`); toast.success(!cur?'Admin granted':'Admin removed'); setUsers(p=>p.map(u=>u.id===id?{...u,is_admin:!cur}:u)) }
  const toggleBan     = async (id, act)  => { await api.patch(`/admin/users/${id}/ban?is_active=${!act}`); toast.success(!act?'Unbanned':'Banned'); setUsers(p=>p.map(u=>u.id===id?{...u,is_active:!act}:u)) }
  const resetScans    = async (id)       => { await api.patch(`/admin/users/${id}/scan-limit?scans_today=0`); toast.success('Scan count reset'); setUsers(p=>p.map(u=>u.id===id?{...u,scans_today:0}:u)) }
  const deleteUser    = async (id, email)=> { if(!confirm(`Delete ${email}?`))return; await api.delete(`/admin/users/${id}`); toast.success('Deleted'); setUsers(p=>p.filter(u=>u.id!==id)) }
  const deleteScan    = async (id)       => { if(!confirm('Delete scan?'))return; await api.delete(`/admin/scans/${id}`); toast.success('Deleted'); setScans(p=>p.filter(s=>s.id!==id)) }

  const sendEmail = async (e) => {
    e.preventDefault(); setEmailSending(true)
    try { await api.post('/admin/send-email',{to_email:emailTo,subject:emailSub,message:emailMsg}); toast.success('Email sent!'); setEmailTo(''); setEmailSub(''); setEmailMsg('') }
    catch(e) { toast.error(e.response?.data?.detail||'Failed') }
    finally { setEmailSending(false) }
  }

  const saveSettings = async () => {
    try {
      await api.patch('/admin/settings', {
        free_scans_per_day: sysSettings.free_scans_per_day,
        pro_scans_per_day: sysSettings.pro_scans_per_day,
      })
      toast.success('Settings saved')
    } catch { toast.error('Failed') }
  }

  const viewScan = async (id) => {
    try { const {data} = await api.get(`/admin/scans/${id}`); setScanDetail(data) }
    catch { toast.error('Failed to load scan') }
  }

  const riskColor = s => !s?'text-slate-500':s>=70?'text-red-400':s>=40?'text-yellow-400':'text-green-400'
  const fU = users.filter(u=>u.email.toLowerCase().includes(search.toLowerCase())||(u.full_name||'').toLowerCase().includes(search.toLowerCase()))
  const fS = scans.filter(s=>s.target_url.toLowerCase().includes(search.toLowerCase()))

  if (loading) return <div className="flex items-center justify-center h-64"><RefreshCw size={24} className="animate-spin text-blue-400"/></div>

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div><h1 className="text-2xl font-bold text-slate-100">Admin Panel</h1><p className="text-slate-400 text-sm">Full platform control</p></div>
        <button onClick={fetchData} className="btn-secondary flex items-center gap-2 text-sm"><RefreshCw size={14}/>Refresh</button>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 bg-slate-900 p-1 rounded-lg w-fit border border-slate-800 flex-wrap">
        {TABS.map(t=>(
          <button key={t} onClick={()=>{setTab(t);setSearch('')}} className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all ${tab===t?'bg-blue-600 text-white':'text-slate-400 hover:text-slate-200'}`}>{t}</button>
        ))}
      </div>

      {/* ── Overview ── */}
      {tab==='Overview' && stats && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {[
              {label:'Total Users',value:stats.total_users,icon:Users,color:'text-blue-400'},
              {label:'Pro Users',value:stats.pro_users,icon:Zap,color:'text-yellow-400'},
              {label:'Free Users',value:stats.free_users,icon:Users,color:'text-slate-400'},
              {label:'Total Scans',value:stats.total_scans,icon:Shield,color:'text-green-400'},
              {label:'Scans Today',value:stats.scans_today,icon:BarChart2,color:'text-purple-400'},
              {label:'Avg Risk',value:stats.avg_risk_score??'N/A',icon:BarChart2,color:'text-red-400'},
            ].map(({label,value,icon:Icon,color})=>(
              <div key={label} className="card p-4"><Icon size={16} className={`${color} mb-2`}/><p className="text-2xl font-bold text-slate-100">{value}</p><p className="text-xs text-slate-500 mt-0.5">{label}</p></div>
            ))}
          </div>
          <div className="grid grid-cols-2 gap-4">
            {[
              {label:'SMTP',ok:sysSettings?.smtp_configured,icon:Mail},
              {label:'Groq AI',ok:sysSettings?.groq_configured,icon:Zap},
            ].map(({label,ok,icon:Icon})=>(
              <div key={label} className={`card p-4 flex items-center gap-3 border ${ok?'border-green-500/20':'border-red-500/20'}`}>
                <Icon size={18} className={ok?'text-green-400':'text-red-400'}/>
                <div><p className="text-sm font-medium text-slate-200">{label}</p><p className={`text-xs ${ok?'text-green-400':'text-red-400'}`}>{ok?'Configured':'Not configured'}</p></div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Users ── */}
      {tab==='Users' && (
        <div className="card overflow-hidden">
          <div className="p-4 border-b border-slate-800 flex items-center gap-3">
            <Search size={16} className="text-slate-500"/>
            <input type="text" placeholder="Search users..." value={search} onChange={e=>setSearch(e.target.value)} className="bg-transparent text-sm text-slate-200 placeholder-slate-500 outline-none flex-1"/>
            <span className="text-xs text-slate-500">{fU.length} users</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead><tr className="border-b border-slate-800 text-slate-500 text-xs uppercase">
                <th className="text-left px-4 py-3">User</th><th className="text-left px-4 py-3">Plan</th>
                <th className="text-left px-4 py-3">Scans</th><th className="text-left px-4 py-3">Status</th>
                <th className="text-left px-4 py-3">Joined</th><th className="text-left px-4 py-3">Actions</th>
              </tr></thead>
              <tbody>
                {fU.map(u=>(
                  <tr key={u.id} className="border-b border-slate-800/50 hover:bg-slate-800/20">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="w-7 h-7 rounded-full bg-blue-600 flex items-center justify-center text-xs font-bold text-white">{(u.full_name?.[0]||u.email[0]).toUpperCase()}</div>
                        <div><p className="font-medium text-slate-200 flex items-center gap-1">{u.full_name||'—'}{u.is_admin&&<Crown size={11} className="text-yellow-400"/>}</p><p className="text-xs text-slate-500">{u.email}</p></div>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <select value={u.plan} onChange={e=>changePlan(u.id,e.target.value)} className={`text-xs rounded px-2 py-1 outline-none cursor-pointer border ${u.plan==='pro'?'bg-yellow-500/10 text-yellow-400 border-yellow-500/30':'bg-slate-800 text-slate-400 border-slate-700'}`}>
                        <option value="free">FREE</option><option value="pro">PRO</option>
                      </select>
                    </td>
                    <td className="px-4 py-3 text-slate-300">{u.total_scans} <span className="text-slate-500 text-xs">({u.scans_today} today)</span></td>
                    <td className="px-4 py-3"><span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${u.is_active!==false?'bg-green-500/10 text-green-400 border border-green-500/20':'bg-red-500/10 text-red-400 border border-red-500/20'}`}>{u.is_active!==false?'Active':'Banned'}</span></td>
                    <td className="px-4 py-3 text-slate-500 text-xs">{new Date(u.created_at).toLocaleDateString()}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1">
                        <button onClick={()=>toggleAdmin(u.id,u.is_admin)} title={u.is_admin?'Remove admin':'Make admin'} className={`p-1.5 rounded hover:bg-slate-700 ${u.is_admin?'text-yellow-400':'text-slate-500'}`}><ShieldCheck size={14}/></button>
                        <button onClick={()=>toggleBan(u.id,u.is_active!==false)} title={u.is_active!==false?'Ban':'Unban'} className={`p-1.5 rounded hover:bg-slate-700 ${u.is_active===false?'text-green-400':'text-orange-400'}`}><Ban size={14}/></button>
                        <button onClick={()=>resetScans(u.id)} title="Reset scan count" className="p-1.5 rounded hover:bg-slate-700 text-blue-400"><RefreshCw size={14}/></button>
                        <button onClick={()=>deleteUser(u.id,u.email)} title="Delete" className="p-1.5 rounded hover:bg-red-500/10 text-red-400"><Trash2 size={14}/></button>
                      </div>
                    </td>
                  </tr>
                ))}
                {fU.length===0&&<tr><td colSpan={6} className="px-4 py-8 text-center text-slate-500">No users found</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── Scans ── */}
      {tab==='Scans' && (
        <div className="card overflow-hidden">
          <div className="p-4 border-b border-slate-800 flex items-center gap-3">
            <Search size={16} className="text-slate-500"/>
            <input type="text" placeholder="Search by URL..." value={search} onChange={e=>setSearch(e.target.value)} className="bg-transparent text-sm text-slate-200 placeholder-slate-500 outline-none flex-1"/>
            <span className="text-xs text-slate-500">{fS.length} scans</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead><tr className="border-b border-slate-800 text-slate-500 text-xs uppercase">
                <th className="text-left px-4 py-3">URL</th><th className="text-left px-4 py-3">Risk</th>
                <th className="text-left px-4 py-3">Severity</th><th className="text-left px-4 py-3">Issues</th>
                <th className="text-left px-4 py-3">Date</th><th className="text-left px-4 py-3">Actions</th>
              </tr></thead>
              <tbody>
                {fS.map(s=>(
                  <tr key={s.id} className="border-b border-slate-800/50 hover:bg-slate-800/20">
                    <td className="px-4 py-3"><div className="flex items-center gap-2"><Globe size={13} className="text-slate-500 flex-shrink-0"/><span className="text-slate-300 truncate max-w-xs">{s.target_url}</span></div></td>
                    <td className={`px-4 py-3 font-bold ${riskColor(s.risk_score)}`}>{s.risk_score?.toFixed(0)??'—'}</td>
                    <td className="px-4 py-3 capitalize text-slate-400">{s.overall_severity??'—'}</td>
                    <td className="px-4 py-3 text-xs">
                      {s.critical_count>0&&<span className="text-red-400 mr-1">{s.critical_count}C</span>}
                      {s.high_count>0&&<span className="text-orange-400 mr-1">{s.high_count}H</span>}
                      {s.medium_count>0&&<span className="text-yellow-400 mr-1">{s.medium_count}M</span>}
                    </td>
                    <td className="px-4 py-3 text-slate-500 text-xs">{new Date(s.created_at).toLocaleDateString()}</td>
                    <td className="px-4 py-3 flex items-center gap-1">
                      <button onClick={()=>viewScan(s.id)} className="p-1.5 rounded hover:bg-slate-700 text-blue-400"><Eye size={14}/></button>
                      <button onClick={()=>deleteScan(s.id)} className="p-1.5 rounded hover:bg-red-500/10 text-red-400"><Trash2 size={14}/></button>
                    </td>
                  </tr>
                ))}
                {fS.length===0&&<tr><td colSpan={6} className="px-4 py-8 text-center text-slate-500">No scans found</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── Emails ── */}
      {tab==='Emails' && (
        <div className="card p-6 max-w-xl">
          <h2 className="text-lg font-semibold text-slate-100 mb-4 flex items-center gap-2"><Mail size={18} className="text-blue-400"/>Send Email</h2>
          <form onSubmit={sendEmail} className="space-y-4">
            <div>
              <label className="block text-sm text-slate-400 mb-1">To Email</label>
              <input type="email" value={emailTo} onChange={e=>setEmailTo(e.target.value)} required placeholder="user@example.com" className="input-field w-full"/>
            </div>
            <div>
              <label className="block text-sm text-slate-400 mb-1">Subject</label>
              <input type="text" value={emailSub} onChange={e=>setEmailSub(e.target.value)} required placeholder="Email subject" className="input-field w-full"/>
            </div>
            <div>
              <label className="block text-sm text-slate-400 mb-1">Message</label>
              <textarea value={emailMsg} onChange={e=>setEmailMsg(e.target.value)} required rows={6} placeholder="Write your message..." className="input-field w-full resize-none"/>
            </div>
            <button type="submit" disabled={emailSending} className="btn-primary w-full flex items-center justify-center gap-2">
              {emailSending?<><RefreshCw size={14} className="animate-spin"/>Sending…</>:<><Mail size={14}/>Send Email</>}
            </button>
          </form>
        </div>
      )}

      {/* ── Settings ── */}
      {tab==='Settings' && sysSettings && (
        <div className="card p-6 max-w-lg space-y-5">
          <h2 className="text-lg font-semibold text-slate-100 flex items-center gap-2"><Settings size={18} className="text-blue-400"/>System Settings</h2>

          <div>
            <p className="text-xs text-slate-500 uppercase font-semibold mb-3">Scan Limits</p>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-slate-400 mb-1">Free Scans/Day</label>
                <input type="number" min={0} value={sysSettings.free_scans_per_day} onChange={e=>setSysSettings(p=>({...p,free_scans_per_day:+e.target.value}))} className="input-field w-full"/>
              </div>
              <div>
                <label className="block text-sm text-slate-400 mb-1">Pro Scans/Day</label>
                <input type="number" min={0} value={sysSettings.pro_scans_per_day} onChange={e=>setSysSettings(p=>({...p,pro_scans_per_day:+e.target.value}))} className="input-field w-full"/>
              </div>
            </div>
          </div>

          

          <div className="grid grid-cols-2 gap-3">
            {[['SMTP',sysSettings.smtp_configured],['Groq AI',sysSettings.groq_configured]].map(([k,v])=>(
              <div key={k} className={`p-3 rounded-lg border text-center ${v?'border-green-500/20 bg-green-500/5':'border-red-500/20 bg-red-500/5'}`}>
                <p className="text-xs text-slate-400">{k}</p>
                <p className={`text-xs font-semibold mt-0.5 ${v?'text-green-400':'text-red-400'}`}>{v?'✓ OK':'✗ Missing'}</p>
              </div>
            ))}
          </div>
          <button onClick={saveSettings} className="btn-primary w-full">Save Settings</button>
        </div>
      )}

      {/* ── Scan Detail Modal ── */}
      {scanDetail && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4" onClick={()=>setScanDetail(null)}>
          <div className="bg-slate-900 border border-slate-700 rounded-xl p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto" onClick={e=>e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-bold text-slate-100 truncate">{scanDetail.target_url}</h3>
              <button onClick={()=>setScanDetail(null)} className="text-slate-500 hover:text-slate-200 text-xl">✕</button>
            </div>
            <div className="grid grid-cols-2 gap-3 mb-4 text-sm">
              <div className="card p-3"><p className="text-slate-500 text-xs">Risk Score</p><p className={`text-2xl font-bold ${riskColor(scanDetail.risk_score)}`}>{scanDetail.risk_score?.toFixed(0)??'—'}</p></div>
              <div className="card p-3"><p className="text-slate-500 text-xs">Severity</p><p className="text-lg font-bold text-slate-200 capitalize">{scanDetail.overall_severity??'—'}</p></div>
            </div>
            {scanDetail.summary && <p className="text-sm text-slate-400 mb-4 p-3 bg-slate-800 rounded-lg">{scanDetail.summary}</p>}
            {(scanDetail.vulnerabilities||[]).length>0 && (
              <div className="space-y-2">
                <p className="text-xs text-slate-500 uppercase font-semibold">Vulnerabilities ({scanDetail.vulnerabilities.length})</p>
                {scanDetail.vulnerabilities.map((v,i)=>(
                  <div key={i} className="p-3 bg-slate-800 rounded-lg border border-slate-700">
                    <p className="text-sm font-semibold text-slate-200">{v.name} <span className={`text-xs ml-1 ${v.severity==='critical'?'text-red-400':v.severity==='high'?'text-orange-400':v.severity==='medium'?'text-yellow-400':'text-green-400'}`}>[{v.severity}]</span></p>
                    <p className="text-xs text-slate-400 mt-1">{v.description}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
