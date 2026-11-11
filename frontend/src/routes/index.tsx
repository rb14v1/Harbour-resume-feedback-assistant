import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import ApplicationDetail from "../features/applications/ApplicationDetail";
import ApplicationList from "../features/applications/ApplicationList";
import AppLayout from "../layouts/AppLayout";
import Login from "./Login";

function RequireAuth({ children }: { children: JSX.Element }) {
  const { user, loading } = useAuth();
  if (loading) return <p>Loading...</p>;
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

export default function AppRoutes() {
  const { user, loading } = useAuth();

  if (loading) return <p>Loading...</p>;

  return (
    <Routes>
      <Route path="/login" element={user ? <Navigate to="/applications" replace /> : <Login />} />
      <Route
        element={
          <RequireAuth>
            <AppLayout />
          </RequireAuth>
        }
      >
        <Route path="/applications" element={<ApplicationList />} />
        <Route path="/applications/:id" element={<ApplicationDetail />} />
      </Route>
      <Route path="*" element={<Navigate to={user ? "/applications" : "/login"} replace />} />
    </Routes>
  );
}
