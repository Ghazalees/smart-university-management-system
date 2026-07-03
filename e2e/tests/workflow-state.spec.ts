import { expect, test } from "@playwright/test";
import { authenticate } from "../support/auth.js";
import { newAppContext } from "../support/context.js";
import { uniqueId } from "../support/ids.js";

function isoDate(daysFromNow: number): string {
  const date = new Date();
  date.setUTCDate(date.getUTCDate() + daysFromNow);
  return date.toISOString().slice(0, 10);
}

test("leave request follows the allowed pending-to-review-to-approved state transitions", async ({ browser, request }) => {
  const title = `E2E leave request ${uniqueId("leave")}`;

  const studentContext = await newAppContext(browser);
  const studentPage = await studentContext.newPage();
  await authenticate(studentPage, request, "student");
  await studentPage.goto("/workflows");

  await test.step("student submits a valid leave request", async () => {
    await studentPage.getByRole("button", { name: "New request" }).click();
    const dialog = studentPage.getByRole("dialog", { name: "Start a university request" });
    await dialog.getByLabel("Request type").selectOption({ label: "Leave request" });
    await dialog.getByLabel("Request title").fill(title);
    await dialog.getByLabel("Description and supporting details").fill(
      "Automated end-to-end validation of the governed leave approval workflow.",
    );
    await dialog.getByRole("button", { name: "Continue" }).click();
    await dialog.getByLabel("Start date").fill(isoDate(30));
    await dialog.getByLabel("End date").fill(isoDate(34));
    await dialog.getByRole("textbox", { name: /^Reason/ }).fill(
      "Academic conference participation and approved research travel.",
    );
    await dialog.getByRole("button", { name: "Submit request" }).click();
    await expect(studentPage.getByText("Request submitted for review")).toBeVisible();
    await expect(studentPage.locator("tbody tr").filter({ hasText: title })).toContainText("pending");
  });

  const staffContext = await newAppContext(browser);
  const staffPage = await staffContext.newPage();
  await authenticate(staffPage, request, "staff");
  await staffPage.goto("/workflows");
  await staffPage.getByPlaceholder("Search number, title or requester").fill(title);

  await test.step("staff starts review", async () => {
    let row = staffPage.locator("tbody tr").filter({ hasText: title });
    await expect(row).toBeVisible();
    await row.getByRole("button", { name: "View" }).click();
    const detail = staffPage.getByRole("dialog").filter({ hasText: title });
    await detail.getByRole("button", { name: "Start review" }).click();
    await expect(staffPage.getByText("Request status updated")).toBeVisible();
    row = staffPage.locator("tbody tr").filter({ hasText: title });
    await expect(row).toContainText("under review");
  });

  await test.step("staff approves the reviewed request", async () => {
    const row = staffPage.locator("tbody tr").filter({ hasText: title });
    await row.getByRole("button", { name: "View" }).click();
    const detail = staffPage.getByRole("dialog").filter({ hasText: title });
    await detail.getByRole("button", { name: "Approve" }).click();
    await expect(staffPage.getByText("Request status updated")).toBeVisible();
    await expect(staffPage.locator("tbody tr").filter({ hasText: title })).toContainText("approved");
  });
  await staffContext.close();

  await test.step("student sees the final approved state", async () => {
    await studentPage.reload();
    await studentPage.getByPlaceholder("Search number, title or requester").fill(title);
    await expect(studentPage.locator("tbody tr").filter({ hasText: title })).toContainText("approved");
  });
  await studentContext.close();
});
