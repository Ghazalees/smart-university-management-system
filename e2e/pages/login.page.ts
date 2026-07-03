import { expect, type Page } from "@playwright/test";
import type { Credentials } from "../support/credentials.js";

export class LoginPage {
  constructor(private readonly page: Page) {}

  async open(): Promise<void> {
    await this.page.goto("/login");
    await expect(
      this.page.getByRole("heading", { name: "Sign in to your campus" }),
    ).toBeVisible();
  }

  async signIn(credentials: Credentials): Promise<void> {
    await this.page.getByLabel("Username or email").fill(credentials.username);
    await this.page.getByLabel("Password").fill(credentials.password);
    await this.page.getByRole("button", { name: "Sign in" }).click();
  }
}
