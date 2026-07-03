/** Defines the shared toast notification context contract. */

import { createContext } from "react";

export interface ToastContextValue {
  show: (text: string, tone?: "success" | "error") => void;
}

export const ToastContext = createContext<ToastContextValue | null>(null);
