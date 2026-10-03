import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { AuthProvider } from './auth'
import NavBar from './components/NavBar'
import AnnouncementBar from './components/AnnouncementBar'
import Footer from './components/Footer'
import ChatWidget from './components/ChatWidget'
import ChatResultsPanel from './components/ChatResultsPanel'
import { ChatResultsProvider } from './chatResults'
import Home from './pages/Home'
import Products from './pages/Products'
import ProductDetail from './pages/ProductDetail'
import About from './pages/About'
import Login from './pages/Login'
import CreateAccount from './pages/CreateAccount'

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <ChatResultsProvider>
          <AnnouncementBar />
          <NavBar />
          <main className="page">
            <ChatResultsPanel />
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/products" element={<Products />} />
              <Route path="/products/:id" element={<ProductDetail />} />
              <Route path="/about" element={<About />} />
              <Route path="/login" element={<Login />} />
              <Route path="/create-account" element={<CreateAccount />} />
              <Route path="*" element={<p className="status">Page not found.</p>} />
            </Routes>
          </main>
          <Footer />
          <ChatWidget />
        </ChatResultsProvider>
      </BrowserRouter>
    </AuthProvider>
  )
}
