/** Provides the reusable ErrorBoundary interface component and accessibility behavior. */

import { Component, type ErrorInfo, type ReactNode } from "react";
import { AlertTriangle } from "lucide-react";

export class ErrorBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  componentDidCatch(error: Error, info: ErrorInfo) { console.error("Application error", error, info); }
  render() {
    if (this.state.failed) {
      return <main className="fatal-error"><AlertTriangle /><h1>Something went wrong</h1><p>The interface encountered an unexpected problem.</p><button className="button button-primary" onClick={() => window.location.reload()}>Reload application</button></main>;
    }
    return this.props.children;
  }
}
