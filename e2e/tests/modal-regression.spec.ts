import { expect, test, type Page } from "@playwright/test";
import { authenticate } from "../support/auth.js";

async function openRequestModal(page: Page) {
  await page.goto("/workflows");
  await page.getByRole("button", { name: "New request" }).click();
  const dialog = page.getByRole("dialog", { name: "Start a university request" });
  await expect(dialog).toBeVisible();
  return dialog;
}

test.describe("modal regression coverage", () => {
  test.beforeEach(async ({ page, request }) => {
    await authenticate(page, request, "student");
  });

  test("controlled fields preserve focus while the modal rerenders", async ({ page }) => {
    const dialog = await openRequestModal(page);
    const title = dialog.getByLabel("Request title");
    // Programmatic focus avoids coupling the regression check to modal entrance motion.
    await title.focus();
    await title.pressSequentially("Focused request title", { delay: 15 });

    await expect(title).toHaveValue("Focused request title");
    await expect(title).toBeFocused();
  });

  test("modal closes through Escape and the explicit close button", async ({ page }) => {
    let dialog = await openRequestModal(page);
    await page.keyboard.press("Escape");
    await expect(dialog).toBeHidden();

    dialog = await openRequestModal(page);
    await dialog.getByRole("button", { name: "Close Start a university request" }).click();
    await expect(dialog).toBeHidden();
  });

  test("backdrop click closes the modal, inner click does not, and scrolling is restored", async ({ page }) => {
    const dialog = await openRequestModal(page);
    await dialog.getByLabel("Request title").fill("Backdrop safety check");
    await dialog.locator(".form-grid").click();
    await expect(dialog).toBeVisible();

    await page.locator(".modal-backdrop").click({ position: { x: 4, y: 4 } });
    await expect(dialog).toBeHidden();
    await expect.poll(() => page.evaluate(() => document.body.style.overflow)).not.toBe("hidden");
  });
});
