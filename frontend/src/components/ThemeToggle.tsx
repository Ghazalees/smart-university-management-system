"use client";

import { useEffect, useState } from "react";
import { useTheme } from "next-themes";
import { Button } from "@heroui/react";
import { Sun, Moon } from "lucide-react";

export const ThemeToggle = () => {
  const [mounted, setMounted] = useState(false);
  const { theme, setTheme } = useTheme();

  // Prevents the hydration mismatch error by waiting for the client mount
  useEffect(() => {
    setMounted(true);
  }, []);

  // Structural skeleton matching the button layout during SSR
  if (!mounted) {
    return (
      <Button isIconOnly variant="light" aria-label="Loading theme wrapper">
        <div className="w-5 h-5 rounded-full bg-default-200 animate-pulse" />
      </Button>
    );
  }

  const isDark = theme === "dark";

  return (
    <Button
      isIconOnly
      variant="light"
      onPress={() => setTheme(isDark ? "light" : "dark")}
      aria-label={`Switch to ${isDark ? "light" : "dark"} mode`}
    >
      {isDark ? (
        <Sun
          size={20}
          className="text-warning transition-transform hover:rotate-45"
        />
      ) : (
        <Moon
          size={20}
          className="text-default-700 transition-transform hover:-rotate-12"
        />
      )}
    </Button>
  );
};
