import { useState } from 'react'
import { User, Mail, Shield, Zap, Save, Loader2, Calendar } from 'lucide-react'
import { format } from 'date-fns'
import toast from 'react-hot-toast'
import { useForm } from 'react-hook-form'
import useAuthStore from '../store/authStore'
import { userAPI } from '../utils/api'
import clsx from 'clsx'
export default function Profile() {
  const { user, updateUser } = useAuthStore()
  const [saving, setSaving] = useState(false)

  const { register, handleSubmit, formState: { isDirty } } = useForm({
    defaultValues: { full_name: user?.full_name || '' },
  })

  const onSave = async (values) => {
    setSaving(true)
    try {
      const { data } = await userAPI.updateProfile({ full_name: values.full_name })
      updateUser(data)
      toast.success('Profile updated!')
    } catch {
      toast.error('Failed to save changes')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-slate-100 mb-6">Profile & Account</h1>

      {/* Account info card */}
      <div className="card p-6 mb-4">
        <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4">Account Details</h2>

        <form onSubmit={handleSubmit(onSave)} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1.5">Full Name</label>
            <div className="relative">
              <User size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
              <input
                {...register('full_name')}
                className="input-field pl-10"
                placeholder="Your full name"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1.5">Email</label>
            <div className="relative">
              <Mail size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
              <input
                value={user?.email || ''}
                disabled
                className="input-field pl-10 opacity-60 cursor-not-allowed"
              />
            </div>
            <p className="text-xs text-slate-500 mt-1">Email cannot be changed</p>
          </div>

          <button
            type="submit"
            disabled={saving || !isDirty}
            className="btn-primary flex items-center gap-2"
          >
            {saving ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
            Save Changes
          </button>
        </form>
      </div>

      {/* Plan card */}
      <div className="card p-6 mb-4">
        <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4">Subscription</h2>
        <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg flex items-center justify-center bg-green-500/10">
              <Zap size={20} className="text-green-400" />
            </div>
            <div>
              <p className="font-semibold text-slate-100">Free Plan</p>
              <p className="text-sm text-slate-400">Unlimited scans · All features</p>
            </div>
          </div>
      </div>

      {/* Usage stats */}
      <div className="card p-6">
        <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4">Usage Statistics</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {[
            { label: 'Total Scans',  value: user?.total_scans ?? 0, icon: Shield },
            { label: 'Scans Today',  value: user?.scans_today ?? 0,  icon: Zap },
            { label: 'Member Since', value: user?.created_at ? format(new Date(user.created_at), 'MMM yyyy') : '—', icon: Calendar },
          ].map(({ label, value, icon: Icon }) => (
            <div key={label} className="bg-slate-800/50 rounded-lg p-4 text-center">
              <Icon size={18} className="text-blue-400 mx-auto mb-2" />
              <p className="text-xl font-bold text-slate-100">{value}</p>
              <p className="text-xs text-slate-500 mt-0.5">{label}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
