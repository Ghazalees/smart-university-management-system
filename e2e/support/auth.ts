import { expect, type APIRequestContext, type Page } from "@playwright/test";
import { loginApi, patchApi, type UserSession } from "./api.js";
import { demoCredentials, type Credentials, type DemoRole } from "./credentials.js";

export async function authenticate(
  page: Page,
  request: APIRequestContext,
  identity: DemoRole | Credentials,
): Promise<UserSession> {
  const credentials = typeof identity === "string" ? demoCredentials[identity] : identity;
  const session = await loginApi(request, credentials);

  // Mark onboarding complete through the public application API so it cannot cover later UI actions.
  await patchApi(
    request,
    "/api/v1/experience/preferences",
    session,
    { onboarding_completed: true },
  );

  // Seed the same persisted Redux session used by the production frontend.
  await page.addInitScript((value) => {
    window.localStorage.setItem(
      "smart-university-auth",
      JSON.stringify({
        user: value.user,
        accessToken: value.tokens.access,
        refreshToken: value.tokens.refresh,
      }),
    );
  }, session);

  await page.goto("/dashboard");
  await expect(page).toHaveURL(/\/dashboard$/);
  return session;
}

export async function dismissOnboarding(page: Page): Promise<void> {
  const tour = page.getByRole("dialog", { name: "Welcome tour" });
  try {
    await tour.waitFor({ state: "visible", timeout: 5_000 });
    await tour.getByRole("button", { name: "Skip tour" }).click();
    await expect(tour).toBeHidden();
  } catch {
    // Returning users do not receive the tour.
  }
}

export async function signOut(page: Page): Promise<void> {
  await page.getByRole("button", { name: "Log out" }).click();
  await expect(page).toHaveURL(/\/login$/);
}
