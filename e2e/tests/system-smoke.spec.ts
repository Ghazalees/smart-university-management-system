import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";
import { LoginPage } from "../pages/login.page.js";
import { authenticate, dismissOnboarding, signOut } from "../support/auth.js";
import { demoCredentials } from "../support/credentials.js";

async function expectNoCriticalAccessibilityViolations(page: Page): Promise<void> {
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  const critical = results.violations.filter((violation) => violation.impact === "critical");
  expect(critical, JSON.stringify(critical, null, 2)).toEqual([]);
}

test.describe("system smoke and release checks", () => {
  test("@smoke gateway and backend health endpoints respond", async ({ request }) => {
    const gateway = await request.get("/gateway-health");
    expect(gateway.ok()).toBeTruthy();
    expect((await gateway.text()).trim()).toBe("ok");

    const backend = await request.get("/api/v1/health");
    expect(backend.ok()).toBeTruthy();
  });

  test("@smoke login is branded, secure, and free of demo credentials", async ({ page }) => {
    const login = new LoginPage(page);
    await login.open();

    await expect(page).toHaveTitle("UniFlow");
    await expect(page.getByText("Development demo", { exact: true })).toHaveCount(0);
    await expect(page.getByText(/student\s*\/\s*Student123!/i)).toHaveCount(0);
    await expect(page.getByLabel("Username or email")).toBeVisible();
    await expect(page.getByLabel("Password")).toHaveAttribute("type", "password");
    await expectNoCriticalAccessibilityViolations(page);
  });

  test("@smoke invalid credentials are rejected without leaving login", async ({ page }) => {
    const login = new LoginPage(page);
    await login.open();
    await login.signIn({ username: "unknown-user", password: "WrongPassword123!" });

    await expect(page).toHaveURL(/\/login$/);
    await expect(page.getByRole("alert")).toBeVisible();
  });

  test("@smoke protected routes redirect guests", async ({ page }) => {
    await page.goto("/academics/grades");
    await expect(page).toHaveURL(/\/login$/);
    await expect(
      page.getByRole("heading", { name: "Sign in to your campus" }),
    ).toBeVisible();
  });

  test("@smoke a valid professor session can sign in and sign out", async ({ page }) => {
    const login = new LoginPage(page);
    await login.open();
    await login.signIn(demoCredentials.professor);
    await expect(page).toHaveURL(/\/dashboard$/);
    await dismissOnboarding(page);

    await expect(page.getByRole("navigation", { name: "Primary navigation" })).toBeVisible();
    await page.goto("/academics/grades");
    await expect(page.getByRole("button", { name: "Record grade" })).toBeVisible();

    await signOut(page);
    await page.goto("/academics/grades");
    await expect(page).toHaveURL(/\/login$/);
  });

  test("@smoke authenticated dashboard has no critical accessibility violations", async ({ page, request }) => {
    await authenticate(page, request, "student");
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    await expectNoCriticalAccessibilityViolations(page);
  });

  test("@mobile login and primary navigation remain usable without horizontal overflow", async ({ page, request }) => {
    await page.goto("/login");
    const loginOverflow = await page.evaluate(
      () => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
    );
    expect(loginOverflow).toBeFalsy();
    await expect(page.getByRole("heading", { name: "Sign in to your campus" })).toBeVisible();

    await authenticate(page, request, "student");
    await page.getByRole("button", { name: "Open navigation" }).click();
    await expect(page.getByRole("link", { name: "Knowledge" })).toBeVisible();
    await page.getByRole("button", { name: "Close navigation" }).click();

    const dashboardOverflow = await page.evaluate(
      () => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
    );
    expect(dashboardOverflow).toBeFalsy();
  });
});
