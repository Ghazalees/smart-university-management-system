import { motion } from "framer-motion";
import { Link } from "react-router-dom";

export default function Signup() {
  return (
    <section className="relative flex min-h-screen items-center justify-center bg-background p-6 text-foreground">
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
          Create Account
        </h2>

        {/* First Name */}
        <div className="mb-4">
          <label className="mb-1 block text-sm text-muted-foreground">
            First Name
          </label>
          <input
            type="text"
            placeholder="John"
            className="w-full rounded-md border border-white/20 bg-white/10 px-4 py-2 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>

        {/* Last Name */}
        <div className="mb-4">
          <label className="mb-1 block text-sm text-muted-foreground">
            Last Name
          </label>
          <input
            type="text"
            placeholder="Doe"
            className="w-full rounded-md border border-white/20 bg-white/10 px-4 py-2 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>

        {/* Email */}
        <div className="mb-4">
          <label className="mb-1 block text-sm text-muted-foreground">
            University Email
          </label>
          <input
            type="email"
            placeholder="student@university.edu"
            className="w-full rounded-md border border-white/20 bg-white/10 px-4 py-2 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>

        {/* University ID */}
        <div className="mb-4">
          <label className="mb-1 block text-sm text-muted-foreground">
            University ID
          </label>
          <input
            type="text"
            placeholder="202400123"
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

        {/* Confirm Password */}
        <div className="mb-6">
          <label className="mb-1 block text-sm text-muted-foreground">
            Confirm Password
          </label>
          <input
            type="password"
            placeholder="••••••••"
            className="w-full rounded-md border border-white/20 bg-white/10 px-4 py-2 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>

        {/* Signup button */}
        <motion.button
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.96 }}
          className="w-full rounded-md bg-primary py-3 font-medium text-white shadow-strong transition hover:opacity-90"
        >
          Create Account
        </motion.button>

        {/* Login link */}
        <p className="mt-6 text-center text-sm text-muted-foreground">
          Already have an account?{" "}
          <Link to="/login" className="text-primary hover:underline">
            Login
          </Link>
        </p>
      </motion.div>
    </section>
  );
}
