import { motion } from "framer-motion";
import { Link } from "react-router-dom";

export default function Login() {
  return (
    <section className="relative flex min-h-screen items-center justify-center bg-background px-6 text-foreground">
      {/* Background glow */}
      <div className="absolute inset-0 -z-10 overflow-hidden">
        <div className="absolute left-1/2 top-1/4 h-64 w-64 -translate-x-1/2 rounded-full bg-primary/30 blur-[120px]" />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
        className="w-full max-w-md rounded-lg border border-white/10 bg-white/5 p-8 shadow-soft backdrop-blur-xl"
      >
        <h2 className="mb-6 text-center text-3xl font-semibold">
          Welcome Back
        </h2>

        {/* Email */}
        <div className="mb-4">
          <label className="mb-1 block text-sm text-muted-foreground">
            Email
          </label>
          <input
            type="email"
            placeholder="example@domain.com"
            className="w-full rounded-md border border-white/20 bg-white/10 px-4 py-2 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>

        {/* Password */}
        <div className="mb-4">
          <label className="mb-1 block text-sm text-muted-foreground">
            Password
          </label>
          <input
            type="password"
            placeholder="••••••••"
            className="w-full rounded-md border border-white/20 bg-white/10 px-4 py-2 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>

        {/* Forgot password */}
        <div className="mb-6 text-right">
          <Link
            to="/forgot-password"
            className="text-sm text-primary hover:underline"
          >
            Forgot Password?
          </Link>
        </div>

        {/* Login button */}
        <motion.button
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.96 }}
          className="w-full rounded-md bg-primary py-3 font-medium text-white shadow-strong transition hover:opacity-90"
        >
          Login
        </motion.button>

        {/* Divider */}
        <div className="my-6 flex items-center gap-3">
          <div className="h-px flex-1 bg-white/10" />
          <span className="text-sm text-muted-foreground">OR</span>
          <div className="h-px flex-1 bg-white/10" />
        </div>

        {/* Signup */}
        <p className="text-center text-sm text-muted-foreground">
          Don’t have an account?{" "}
          <Link to="/signup" className="text-primary hover:underline">
            Create one
          </Link>
        </p>
      </motion.div>
    </section>
  );
}
