import { Link } from 'react-router-dom'
import Pennant from './Pennant'

export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer-inner">
        <div className="footer-brand">
          <Pennant size={44} />
          <div>
            <strong>Campus Customs</strong>
            <p>Officially licensed Yale apparel, a short walk from Old Campus.</p>
          </div>
        </div>
        <div>
          <h4>Shop</h4>
          <Link to="/products?cat=Hoodies">Hoodies</Link>
          <Link to="/products?cat=Crewnecks">Crewnecks</Link>
          <Link to="/products?cat=T-shirts+%26+tops">Tees</Link>
          <Link to="/products?cat=Quarter-zips">Quarter-zips</Link>
        </div>
        <div>
          <h4>Visit</h4>
          <p>57 Broadway</p>
          <p>New Haven, CT</p>
          <Link to="/about">About us</Link>
        </div>
      </div>
      <p className="footer-fine">© Campus Customs · Boola Boola</p>
    </footer>
  )
}
