import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'
import Pennant from './Pennant'

const links = [
  { to: '/', label: 'Home' },
  { to: '/products', label: 'Products' },
  { to: '/about', label: 'About Us' },
]

const guestLinks = [
  { to: '/login', label: 'Log in' },
  { to: '/create-account', label: 'Create account' },
]

export default function NavBar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  async function onLogout() {
    await logout()
    navigate('/')
  }

  return (
    <header className="nav">
      <Link to="/" className="brand" aria-label="Campus Customs home">
        <Pennant />
        <span>
          <strong>Campus Customs</strong>
          <small>Yale apparel · 57 Broadway</small>
        </span>
      </Link>
      <nav>
        {[...links, ...(user ? [] : guestLinks)].map((l) => (
          <NavLink key={l.to} to={l.to} end={l.to === '/'}>
            {l.label}
          </NavLink>
        ))}
        {user && (
          <>
            <span className="greeting">Hi, {user.first_name}</span>
            <button className="link-btn" onClick={onLogout}>
              Log out
            </button>
          </>
        )}
      </nav>
    </header>
  )
}
