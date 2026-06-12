import { motion } from "framer-motion";

const features = [
  {
    title: "User & Role Management",
    description:
      "Manage students, professors, staff, and administration from a single centralized platform.",
  },
  {
    title: "Course Management",
    description:
      "Organize courses, assignments, and academic data with an intuitive interface.",
  },
  {
    title: "Requests & Approvals",
    description:
      "Submit and track academic or administrative requests with streamlined approval workflows.",
  },
  {
    title: "Smart Notifications",
    description:
      "Stay informed with real-time notifications for important updates and deadlines.",
  },
  {
    title: "Analytics Dashboard",
    description:
      "Gain insights into academic performance and institutional data through analytics tools.",
  },
  {
    title: "Centralized Document Hub",
    description:
      "Store, manage, and share official documents, forms, and policies in one secure location.",
  },
];

export default function Features() {
  return (
    <section className="bg-background px-6 py-24 text-foreground">
      <div className="mx-auto max-w-6xl text-center">
        <h2 className="mb-6 text-3xl font-bold sm:text-4xl">
          Everything Your University Needs
        </h2>

        <p className="mx-auto mb-16 max-w-2xl text-muted-foreground">
          A unified platform designed to simplify academic management and
          administrative workflows.
        </p>

        <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
          {features.map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 15 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{
                once: true,
                margin: "-50px",
              }}
              transition={{
                duration: 0.6,
                delay: index * 0.1,
                ease: "easeOut",
              }}
              className="rounded-lg border border-white/10 bg-white/5 p-6 backdrop-blur-md transition-colors hover:border-primary/50"
            >
              <h3 className="mb-2 text-lg font-semibold">{feature.title}</h3>
              <p className="text-sm text-muted-foreground">
                {feature.description}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
