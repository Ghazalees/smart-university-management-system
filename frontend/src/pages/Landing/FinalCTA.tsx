import { motion } from "framer-motion";
import { Link } from "react-router-dom";

export default function FinalCTA() {
  return (
    <section className="border-t border-border bg-muted/60 py-16">
      <div className="mx-auto flex max-w-5xl flex-col items-center justify-between gap-6 px-6 text-center md:flex-row md:text-left">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          viewport={{ once: true }}
        >
          <h3 className="text-xl font-semibold text-foreground">
            Ready to simplify your university operations?
          </h3>

          <p className="mt-2 text-sm text-muted-foreground">
            Bring students, professors, and administrators together in one smart
            platform.
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 12 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          viewport={{ once: true }}
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.96 }}
        >
          <Link
            to="/login"
            className="inline-flex items-center justify-center rounded-md bg-primary px-6 py-3 text-sm font-medium text-primary-foreground shadow-strong hover:opacity-90"
          >
            Get Started
          </Link>
        </motion.div>
      </div>
    </section>
  );
}
