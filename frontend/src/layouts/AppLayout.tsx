import { Link, Outlet } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export default function AppLayout() {
  const { user, logout } = useAuth();
  return (
    <div style={{ fontFamily: "sans-serif", margin: "1rem" }}>
      <header style={{ display: "flex", justifyContent: "space-between", marginBottom: "1rem" }}>
        <nav>
          <Link to="/applications" style={{ marginRight: "1rem" }}>
            My Applications
          </Link>
        </nav>
        <div>
          {user?.email} ({user?.role}) <button onClick={logout}>Logout</button>
        </div>
      </header>
      <Outlet />
    </div>
  );
}
