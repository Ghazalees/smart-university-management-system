import { motion } from "framer-motion";
import { Link } from "react-router-dom";

export default function Hero() {
  return (
    <section className="relative overflow-hidden bg-background pb-24 pt-16 text-foreground">
      {/* Background glow / gradient */}
      <div className="pointer-events-none absolute inset-0 -z-10">
        <div className="absolute left-1/2 top-[-10%] h-72 w-72 -translate-x-1/2 rounded-full bg-primary/25 blur-[140px]" />
        <div className="absolute bottom-0 left-0 h-64 w-64 rounded-full bg-secondary/10 blur-[120px]" />
      </div>

      <div className="mx-auto flex max-w-6xl flex-col items-center gap-12 px-6 md:flex-row md:items-start md:justify-between">
        {/* Left: Text + CTAs + Stats */}
        <motion.div
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          className="max-w-xl text-center md:text-left"
        >
          {/* Eyebrow / badge */}
          <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-border bg-muted/60 px-3 py-1 text-xs font-medium text-muted-foreground backdrop-blur">
            <span className="inline-flex h-2 w-2 rounded-full bg-emerald-400" />
            Smart University Management Platform
          </div>

          {/* Headline */}
          <h1 className="text-balance text-4xl font-semibold tracking-tight sm:text-5xl lg:text-6xl">
            Run your entire campus
            <span className="text-primary"> from one smart hub.</span>
          </h1>

          {/* Description */}
          <p className="mt-4 text-balance text-sm text-muted-foreground sm:text-base">
            Centralize users, courses, requests, and approvals in a single
            dashboard. Built for students, professors, and administrators to
            move faster with fewer emails and spreadsheets.
          </p>

          {/* CTAs */}
          <div className="mt-8 flex flex-wrap items-center justify-center gap-3 md:justify-start">
            <motion.div whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.96 }}>
              <Link
                to="/login"
                className="inline-flex items-center justify-center rounded-md bg-primary px-6 py-3 text-sm font-medium text-primary-foreground shadow-strong transition hover:opacity-90"
              >
                Get Started
              </Link>
            </motion.div>

            <motion.button
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.96 }}
              type="button"
              className="inline-flex items-center justify-center rounded-md border border-border bg-background/70 px-5 py-3 text-sm font-medium text-foreground shadow-soft backdrop-blur hover:bg-muted"
            >
              View Demo Dashboard
            </motion.button>
          </div>

          {/* Roles row */}
          <div className="mt-6 flex flex-wrap items-center justify-center gap-2 text-xs md:justify-start">
            <span className="text-muted-foreground">Built for:</span>
            <span className="rounded-full bg-muted px-3 py-1 text-foreground">
              Students
            </span>
            <span className="rounded-full bg-muted px-3 py-1 text-foreground">
              Professors
            </span>
            <span className="rounded-full bg-muted px-3 py-1 text-foreground">
              Department Staff
            </span>
            <span className="rounded-full bg-muted px-3 py-1 text-foreground">
              Deans & Admins
            </span>
          </div>

          {/* Stats row */}
          <div className="mt-8 flex flex-wrap items-center justify-center gap-6 border-t border-border pt-6 text-left text-sm md:justify-start">
            <div>
              <div className="text-lg font-semibold text-foreground">12k+</div>
              <div className="text-xs text-muted-foreground">
                Students managed
              </div>
            </div>
            <div>
              <div className="text-lg font-semibold text-foreground">350+</div>
              <div className="text-xs text-muted-foreground">
                Active courses
              </div>
            </div>
            <div>
              <div className="text-lg font-semibold text-foreground">5k+</div>
              <div className="text-xs text-muted-foreground">
                Requests automated
              </div>
            </div>
          </div>
        </motion.div>

        {/* Right: Dashboard Preview */}
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, ease: "easeOut", delay: 0.1 }}
          className="w-full max-w-md"
        >
          <div className="rounded-xl border border-border bg-card/80 p-4 shadow-soft backdrop-blur-lg">
            {/* Top bar */}
            <div className="mb-4 flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <span className="h-2.5 w-2.5 rounded-full bg-red-400" />
                <span className="h-2.5 w-2.5 rounded-full bg-amber-300" />
                <span className="h-2.5 w-2.5 rounded-full bg-emerald-400" />
              </div>
              <span className="text-xs font-medium text-muted-foreground">
                Smart Campus Overview
              </span>
            </div>

            <div className="flex gap-4">
              {/* Sidebar mock */}
              <div className="flex w-24 flex-col gap-2">
                <div className="h-8 rounded-md bg-muted" />
                <div className="h-8 rounded-md bg-muted/80" />
                <div className="h-8 rounded-md bg-muted/60" />
                <div className="h-8 rounded-md bg-muted/40" />
              </div>

              {/* Main content mock */}
              <div className="flex-1 space-y-3">
                {/* Stat cards */}
                <div className="grid grid-cols-3 gap-2">
                  <div className="rounded-md bg-muted/70 p-2">
                    <div className="h-2 w-10 rounded bg-foreground/70" />
                    <div className="mt-2 h-3 w-8 rounded bg-foreground/40" />
                  </div>
                  <div className="rounded-md bg-muted/70 p-2">
                    <div className="h-2 w-10 rounded bg-foreground/70" />
                    <div className="mt-2 h-3 w-8 rounded bg-foreground/40" />
                  </div>
                  <div className="rounded-md bg-muted/70 p-2">
                    <div className="h-2 w-10 rounded bg-foreground/70" />
                    <div className="mt-2 h-3 w-8 rounded bg-foreground/40" />
                  </div>
                </div>

                {/* Chart mock */}
                <div className="rounded-lg bg-muted/60 p-3">
                  <div className="mb-2 flex items-center justify-between">
                    <div className="h-3 w-20 rounded bg-foreground/70" />
                    <div className="h-2 w-10 rounded bg-foreground/40" />
                  </div>
                  <div className="flex items-end gap-1">
                    <div className="h-8 flex-1 rounded bg-primary/70" />
                    <div className="h-12 flex-1 rounded bg-primary/50" />
                    <div className="h-6 flex-1 rounded bg-primary/30" />
                    <div className="h-10 flex-1 rounded bg-primary/60" />
                    <div className="h-5 flex-1 rounded bg-primary/40" />
                  </div>
                </div>

                {/* Activity list mock */}
                <div className="space-y-2 rounded-lg bg-muted/70 p-3">
                  <div className="flex items-center justify-between">
                    <div className="h-2.5 w-24 rounded bg-foreground/70" />
                    <div className="h-2 w-10 rounded bg-foreground/30" />
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="h-2.5 w-20 rounded bg-foreground/60" />
                    <div className="h-2 w-8 rounded bg-foreground/30" />
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="h-2.5 w-28 rounded bg-foreground/50" />
                    <div className="h-2 w-12 rounded bg-foreground/30" />
                  </div>
                </div>
              </div>
            </div>

            {/* Bottom hint */}
            <div className="mt-4 flex items-center justify-between text-[11px] text-muted-foreground">
              <span>Role-based views for every user</span>
              <span>Live requests • Smart alerts</span>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
