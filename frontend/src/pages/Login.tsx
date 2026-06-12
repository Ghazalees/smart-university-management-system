import { motion } from "framer-motion";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useLoginMutation } from "../states/api/authApi";

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [login, { isLoading, error }] = useLoginMutation();

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await login({ email, password }).unwrap();
      navigate("/dashboard");
    } catch (err) {
      console.error("Login error:", err);
    }
  };

  return (
    <section className="relative flex min-h-screen items-center justify-center bg-[#0a0a0a] px-6 text-foreground overflow-hidden">
      {/* --- THE YOUTUBE GLOW EFFECT --- */}
      <div className="absolute flex items-center justify-center pointer-events-none">
        {/* Main centered glow (Theme Color) */}
        <motion.div
          animate={{
            scale: [1, 1.1, 1],
            opacity: [0.3, 0.5, 0.3],
          }}
          transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
          className="absolute h-[400px] w-[400px] rounded-full bg-primary/40 blur-[100px]"
        />
        {/* Secondary offset glow (Accenting color) */}
        <motion.div
          animate={{
            scale: [1.2, 1, 1.2],
            opacity: [0.2, 0.4, 0.2],
          }}
          transition={{ duration: 10, repeat: Infinity, ease: "easeInOut" }}
          className="absolute h-[350px] w-[500px] -translate-x-20 rounded-full bg-purple-600/30 blur-[120px]"
        />
      </div>

      {/* --- LOGIN CONTAINER --- */}
      <div className="relative w-full max-w-md">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
          /* 
             Glassmorphism logic: 
             - bg-white/[0.03] for a dark "smoke" glass 
             - backdrop-blur-3xl for the heavy frosted look
             - border-white/10 for the thin edge
          */
          className="relative overflow-hidden rounded-[2rem] border border-white/10 bg-white/[0.03] p-10 shadow-2xl backdrop-blur-3xl"
        >
          {/* Subtle inner reflection flare */}
          <div className="absolute inset-0 bg-gradient-to-br from-white/[0.05] to-transparent pointer-events-none" />

          <div className="relative z-10">
            <h2 className="mb-2 text-center text-3xl font-bold tracking-tight text-white">
              Welcome Back
            </h2>
            <p className="mb-8 text-center text-sm text-muted-foreground">
              Please enter your details to sign in.
            </p>

            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <label className="mb-1.5 ml-1 block text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Email Address
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@company.com"
                  required
                  className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-white transition-all focus:border-primary/50 focus:bg-white/10 focus:outline-none focus:ring-4 focus:ring-primary/10"
                />
              </div>

              <div>
                <label className="mb-1.5 ml-1 block text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Password
                </label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-white transition-all focus:border-primary/50 focus:bg-white/10 focus:outline-none focus:ring-4 focus:ring-primary/10"
                />
              </div>

              <div className="flex justify-end">
                <Link
                  to="/forgot-password"
                  size="sm"
                  className="text-xs text-primary hover:text-primary/80 transition-colors"
                >
                  Forgot Password?
                </Link>
              </div>

              {error && (
                <p className="text-center text-sm font-medium text-red-400">
                  Invalid email or password.
                </p>
              )}

              <motion.button
                type="submit"
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.98 }}
                disabled={isLoading}
                className="relative w-full overflow-hidden rounded-xl bg-primary px-4 py-3.5 font-bold text-white shadow-[0_0_20px_rgba(var(--primary-rgb),0.3)] transition-all hover:opacity-90 disabled:opacity-50"
              >
                {isLoading ? "Authenticating..." : "Sign In"}
              </motion.button>
            </form>

            <div className="my-8 flex items-center gap-4">
              <div className="h-px flex-1 bg-white/10" />
              <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-muted-foreground/60">
                Secure Login
              </span>
              <div className="h-px flex-1 bg-white/10" />
            </div>

            <p className="text-center text-sm text-muted-foreground">
              New here?{" "}
              <Link
                to="/signup"
                className="font-bold text-white hover:text-primary transition-colors"
              >
                Create an account
              </Link>
            </p>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
