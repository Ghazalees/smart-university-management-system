/** Renders the LoginPage workspace and coordinates its API-driven interactions. */

import { useState } from "react";
import { ArrowRight, BookOpenCheck, BrainCircuit, ShieldCheck } from "lucide-react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { useAppDispatch, useAppSelector } from "../app/hooks";
import { selectAuth, setSession } from "../app/authSlice";
import { useLoginMutation } from "../services/api";
import { Button, Input } from "../components/ui";
import { getErrorMessage } from "../app/formatters";

export function LoginPage() {
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [login, { isLoading }] = useLoginMutation();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const location = useLocation();
  const auth = useAppSelector(selectAuth);
  // Redirect authenticated users away from the public sign-in page.
  if (auth.accessToken && auth.user) return <Navigate to="/dashboard" replace />;

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    try {
      const response = await login({ identifier, password }).unwrap();
      dispatch(setSession(response.data));
      // Return users to the protected page that originally requested authentication.
      const destination = (location.state as { from?: string } | null)?.from || "/dashboard";
      navigate(destination, { replace: true });
    } catch (reason) {
      setError(getErrorMessage(reason));
    }
  }

  return (
    <main className="login-page">
      <section className="login-visual">
        <div className="login-brand"><span><ShieldCheck /></span><strong>UniFlow</strong></div>
        <div className="login-copy">
          <p className="eyebrow">One trusted university workspace</p>
          <h1>Knowledge, requests and academics—beautifully connected.</h1>
          <p>A secure role-aware platform for students, professors and university operations.</p>
          <div className="feature-pills">
            <span><BrainCircuit /> Grounded AI answers</span>
            <span><BookOpenCheck /> Verified policies</span>
            <span><ShieldCheck /> Permission-first access</span>
          </div>
        </div>
        <div className="orb orb-one" /><div className="orb orb-two" />
      </section>
      <section className="login-panel">
        <form className="login-form" onSubmit={submit}>
          <div><p className="eyebrow">Welcome back</p><h2>Sign in to your campus</h2><p>Use your university username or email address.</p></div>
          {auth.sessionExpired ? <div className="inline-alert">Your session expired. Sign in again to continue securely.</div> : null}
          {error ? <div className="inline-alert">{error}</div> : null}
          <Input label="Username or email" value={identifier} onChange={(event) => setIdentifier(event.target.value)} autoComplete="username" required />
          <Input label="Password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="current-password" required />
          <Button type="submit" disabled={isLoading || !identifier || !password}>{isLoading ? "Signing in…" : "Sign in"}<ArrowRight /></Button>
        </form>
      </section>
    </main>
  );
}
