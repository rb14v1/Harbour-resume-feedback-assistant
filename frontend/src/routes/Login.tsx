import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      await login(email, password);
      navigate("/applications");
    } catch {
      setError("Invalid email or password.");
    }
  };

  return (
    <div style={{ fontFamily: "sans-serif", maxWidth: 360, margin: "4rem auto" }}>
      <h1>Resume & Cover Letter Feedback Assistant</h1>
      <form onSubmit={handleSubmit}>
        {error && <p style={{ color: "red" }}>{error}</p>}
        <div>
          <label>
            Email
            <br />
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </label>
        </div>
        <div>
          <label>
            Password
            <br />
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </label>
        </div>
        <button type="submit">Log in</button>
      </form>
      <p style={{ fontSize: "0.85rem", color: "#555" }}>
        Demo accounts: candidate@example.com / admin@example.com, password demo12345
      </p>
    </div>
  );
}
