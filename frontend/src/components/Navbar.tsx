import { Link, useLocation } from "react-router-dom";

export default function Navbar() {
  const location = useLocation();

  function isActive(path: string) {
    if (path === "/") return location.pathname === "/";
    return location.pathname.startsWith(path);
  }

  return (
    <nav className="navbar">
      <div className="nav-brand">
        <Link to="/">
          <span className="brand-icon">◈</span> FinSight Lite
        </Link>
      </div>
      <div className="nav-links">
        <Link to="/" className={isActive("/") ? "active" : ""}>
          Dashboard
        </Link>
        <Link to="/transactions" className={isActive("/transactions") ? "active" : ""}>
          Transactions
        </Link>
      </div>
    </nav>
  );
}
