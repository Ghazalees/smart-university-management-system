import { useState } from "react";
import { Link } from "react-router-dom";
import * as Icons from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@nextui-org/react";
import { Menu, X } from "lucide-react";

export const Sidebar = ({ navItems }) => {
  const [isOpen, setIsOpen] = useState(true);

  return (
    <motion.aside
      initial={false}
      animate={{ width: isOpen ? 256 : 80 }}
      className="border-r border-divider h-screen p-4 flex flex-col bg-content1/20"
    >
      {/* Header Area */}
      <div className="mb-8 flex items-center justify-between h-8 overflow-hidden">
        <AnimatePresence mode="wait">
          {isOpen ? (
            <motion.span
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="font-bold text-xl whitespace-nowrap"
            >
              MySchool
            </motion.span>
          ) : null}
        </AnimatePresence>

        <Button
          isIconOnly
          variant="light"
          onPress={() => setIsOpen(!isOpen)}
          className="shrink-0"
        >
          <AnimatePresence mode="wait">
            {isOpen ? (
              <motion.div
                key="x"
                initial={{ opacity: 0, rotate: -90 }}
                animate={{ opacity: 1, rotate: 0 }}
                exit={{ opacity: 0, rotate: 90 }}
              >
                <X size={20} />
              </motion.div>
            ) : (
              <motion.div
                key="menu"
                initial={{ opacity: 0, rotate: 90 }}
                animate={{ opacity: 1, rotate: 0 }}
                exit={{ opacity: 0, rotate: -90 }}
              >
                <Menu size={20} />
              </motion.div>
            )}
          </AnimatePresence>
        </Button>
      </div>

      {/* Navigation */}
      <nav className="flex flex-col gap-2">
        {navItems.map((item) => {
          const IconComponent = Icons[item.icon as keyof typeof Icons];
          return (
            <motion.div key={item.path} whileHover={{ x: 5 }}>
              <Link
                to={item.path}
                className="flex items-center gap-3 p-3 rounded-lg hover:bg-content1 transition-colors"
              >
                <IconComponent size={20} className="shrink-0" />
                <AnimatePresence>
                  {isOpen && (
                    <motion.span
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      className="whitespace-nowrap"
                    >
                      {item.name}
                    </motion.span>
                  )}
                </AnimatePresence>
              </Link>
            </motion.div>
          );
        })}
      </nav>
    </motion.aside>
  );
};
