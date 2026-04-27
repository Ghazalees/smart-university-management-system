import { motion } from "framer-motion";

const steps = [
  {
    title: "Connect Your Campus",
    description:
      "Import students, professors, and departments to create a centralized university directory.",
  },
  {
    title: "Define Roles & Permissions",
    description:
      "Assign roles like student, professor, staff, or dean with secure role‑based access control.",
  },
  {
    title: "Automate Workflows",
    description:
      "Handle course enrollments, approvals, requests, and administrative tasks automatically.",
  },
  {
    title: "Monitor with Smart Insights",
    description:
      "Use dashboards and analytics to understand campus activity and improve decision making.",
  },
];

export default function HowItWorks() {
  return (
    <section className="bg-muted/40 py-20">
      <div className="mx-auto max-w-6xl px-6">
        <motion.div
          initial={{ opacity: 0, y: 14 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          viewport={{ once: true }}
          className="text-center"
        >
          <h2 className="text-3xl font-semibold text-foreground sm:text-4xl">
            How it works
          </h2>
          <p className="mx-auto mt-3 max-w-2xl text-sm text-muted-foreground">
            A simple workflow designed to streamline academic operations across
            your entire university.
          </p>
        </motion.div>

        <div className="mt-14 grid gap-8 md:grid-cols-4">
          {steps.map((step, index) => (
            <motion.div
              key={step.title}
              initial={{ opacity: 0, y: 18 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              viewport={{ once: true }}
              className="relative rounded-lg border border-border bg-card p-6 shadow-soft"
            >
              <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-full bg-primary text-sm font-semibold text-primary-foreground">
                {index + 1}
              </div>

              <h3 className="text-sm font-semibold text-foreground">
                {step.title}
              </h3>

              <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
                {step.description}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
