import { useState, type ChangeEvent, type FormEvent } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { signup } from '../api'
import { useAuth } from '../auth'

export default function CreateAccount() {
  const { user, setUser } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ first_name: '', last_name: '', email: '', password: '', confirm: '' })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  if (user) return <Navigate to="/" replace />

  const update = (field: keyof typeof form) => (e: ChangeEvent<HTMLInputElement>) =>
    setForm({ ...form, [field]: e.target.value })

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    if (form.password !== form.confirm) {
      setError('Passwords do not match.')
      return
    }
    setBusy(true)
    try {
      const { confirm: _, ...body } = form
      setUser(await signup(body))
      navigate('/')
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <form className="auth" onSubmit={onSubmit}>
      <h1>Create account</h1>
      <label>
        First name
        <input value={form.first_name} onChange={update('first_name')} required autoComplete="given-name" />
      </label>
      <label>
        Last name
        <input value={form.last_name} onChange={update('last_name')} required autoComplete="family-name" />
      </label>
      <label>
        Email
        <input type="email" value={form.email} onChange={update('email')} required autoComplete="email" />
      </label>
      <label>
        Password
        <input
          type="password"
          value={form.password}
          onChange={update('password')}
          required
          minLength={8}
          autoComplete="new-password"
        />
      </label>
      <label>
        Confirm password
        <input
          type="password"
          value={form.confirm}
          onChange={update('confirm')}
          required
          autoComplete="new-password"
        />
      </label>
      {error && <p className="error">{error}</p>}
      <button type="submit" className="btn" disabled={busy}>
        {busy ? 'Creating account…' : 'Create account'}
      </button>
      <p className="muted">
        Already have an account? <Link to="/login">Log in</Link>
      </p>
    </form>
  )
}
