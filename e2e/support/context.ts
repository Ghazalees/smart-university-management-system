import type { Browser, BrowserContext } from "@playwright/test";

export function newAppContext(browser: Browser): Promise<BrowserContext> {
  return browser.newContext({
    baseURL: process.env.E2E_BASE_URL ?? "http://127.0.0.1:8088",
  });
}
