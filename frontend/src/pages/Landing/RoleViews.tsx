import { motion } from "framer-motion";

const roles = [
  {
    title: "Students",
    description:
      "Track courses, manage requests, receive notifications, and access academic resources.",
  },
  {
    title: "Professors",
    description:
      "Manage courses, review student requests, and monitor class performance.",
  },
  {
    title: "Administrative Staff",
    description:
      "Handle approvals, documentation, and operational workflows efficiently.",
  },
  {
    title: "Deans & Administrators",
    description:
      "Monitor analytics, oversee departments, and maintain institutional oversight.",
  },
];

export default function RoleViews() {
  return (
    <section className="bg-background py-20">
      <div className="mx-auto max-w-6xl px-6">
        <motion.div
          initial={{ opacity: 0, y: 14 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          viewport={{ once: true }}
          className="text-center"
        >
          <h2 className="text-3xl font-semibold text-foreground sm:text-4xl">
            One platform for every role
          </h2>

          <p className="mx-auto mt-3 max-w-2xl text-sm text-muted-foreground">
            Each user gets a personalized dashboard tailored to their
            responsibilities within the university.
          </p>
        </motion.div>

        <div className="mt-14 grid gap-6 md:grid-cols-4">
          {roles.map((role, index) => (
            <motion.div
              key={role.title}
              initial={{ opacity: 0, y: 18 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              viewport={{ once: true }}
              className="rounded-lg border border-border bg-card p-6 shadow-soft hover:border-primary/40 transition"
            >
              <h3 className="text-sm font-semibold text-foreground">
                {role.title}
              </h3>

              <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
                {role.description}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
