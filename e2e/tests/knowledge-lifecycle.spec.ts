import path from "node:path";
import { fileURLToPath } from "node:url";
import { expect, test } from "@playwright/test";
import { authenticate } from "../support/auth.js";
import { newAppContext } from "../support/context.js";
import { uniqueId } from "../support/ids.js";

const fixturePath = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "../fixtures/aurora-scholarship-policy.docx",
);

test.describe("knowledge document lifecycle", () => {
  test("unsupported file types are rejected with a controlled validation message", async ({ page, request }) => {
    await authenticate(page, request, "staff");
    await page.goto("/documents");
    await page.getByRole("button", { name: "Upload file" }).click();

    const dialog = page.getByRole("dialog", { name: "Upload a file to knowledge" });
    await dialog.locator('input[type="file"]').setInputFiles({
      name: "unsafe.exe",
      mimeType: "application/octet-stream",
      buffer: Buffer.from("not an accepted knowledge document"),
    });
    await dialog.getByRole("button", { name: "Upload and index" }).click();

    await expect(page.getByText(/Unsupported file type/i)).toBeVisible();
    await expect(dialog).toBeVisible();
  });

  test("DOCX upload, revision history, and grounded AI retrieval work end to end", async ({ browser, request }) => {
    const suffix = uniqueId("aurora");
    const title = `Aurora Scholarship Policy ${suffix}`;
    const revisionSummary = `Clarified portal submission ${suffix}`;

    const staffContext = await newAppContext(browser);
    const staffPage = await staffContext.newPage();
    await authenticate(staffPage, request, "staff");
    await staffPage.goto("/documents");
    await expect(staffPage.getByRole("heading", { name: "Knowledge governance" })).toBeVisible();

    await test.step("upload and index a governed DOCX file", async () => {
      await staffPage.getByRole("button", { name: "Upload file" }).click();
      const uploadDialog = staffPage.getByRole("dialog", { name: "Upload a file to knowledge" });
      await uploadDialog.locator('input[type="file"]').setInputFiles(fixturePath);
      await uploadDialog.getByLabel("Knowledge title").fill(title);
      await uploadDialog.getByLabel("Type").selectOption("policy");
      await uploadDialog.getByLabel("Lifecycle status").selectOption("published");
      await uploadDialog.getByLabel("Access level").selectOption("authenticated");
      await uploadDialog.getByLabel("Tags").fill("aurora, scholarship, appeal");
      await uploadDialog.getByLabel("Version note").fill("Initial governed DOCX upload");
      await uploadDialog.getByRole("button", { name: "Upload and index" }).click();
      await expect(
        staffPage.getByText(`${title} was uploaded, indexed and added to knowledge`),
      ).toBeVisible();
    });

    await test.step("verify extracted content and create a traceable revision", async () => {
      const card = staffPage.locator(".document-card").filter({ hasText: title });
      await expect(card).toBeVisible();
      await card.getByRole("button", { name: "View" }).click();
      const detail = staffPage.getByRole("dialog", { name: title });
      await expect(detail.getByText("17 business days", { exact: false })).toBeVisible();
      await detail.getByRole("button", { name: "Create revision" }).click();

      const revisionDialog = staffPage.getByRole("dialog", { name: `Create revision — ${title}` });
      await revisionDialog.getByLabel("Change summary").fill(revisionSummary);
      const content = revisionDialog.getByLabel("Document content");
      await content.fill(`${await content.inputValue()}\n\nAppeals must reference the original decision notice.`);
      await revisionDialog.getByRole("button", { name: "Save revision" }).click();
      await expect(staffPage.getByText("Revision created successfully")).toBeVisible();

      const revisedCard = staffPage.locator(".document-card").filter({ hasText: title });
      await revisedCard.getByRole("button", { name: "View" }).click();
      const revisedDetail = staffPage.getByRole("dialog", { name: title });
      await expect(revisedDetail.getByText("v2", { exact: true })).toBeVisible();
      await expect(revisedDetail.getByText(revisionSummary, { exact: true })).toBeVisible();
    });
    await staffContext.close();

    await test.step("retrieve the answer as an authorized student with a visible source", async () => {
      const studentContext = await newAppContext(browser);
      const studentPage = await studentContext.newPage();
      await authenticate(studentPage, request, "student");
      await studentPage.goto("/questions");
      const question = `What is the Aurora Scholarship appeal deadline in ${title}?`;
      await studentPage.getByLabel("Ask a university question").fill(question);
      await studentPage.getByRole("button", { name: "Ask with sources" }).click();

      const responseCard = studentPage.locator(".question-card").filter({ hasText: question }).first();
      await expect(responseCard).toBeVisible();
      await expect(responseCard.locator(".answer-box")).toContainText("17 business days");
      await expect(responseCard.locator(".source-panel")).toContainText(title);
      await studentContext.close();
    });
  });
});
