import { expect, test } from "@playwright/test";
import { authenticate } from "../support/auth.js";
import { newAppContext } from "../support/context.js";
import type { DemoRole } from "../support/credentials.js";

interface RoleExpectation {
  role: DemoRole;
  visibleLinks: string[];
  hiddenLinks: string[];
}

const roleMatrix: RoleExpectation[] = [
  {
    role: "student",
    visibleLinks: ["Knowledge", "Classes", "Grades"],
    hiddenLinks: ["Users", "AI analytics"],
  },
  {
    role: "professor",
    visibleLinks: ["Knowledge", "Classes", "Grades"],
    hiddenLinks: ["Users"],
  },
  {
    role: "staff",
    visibleLinks: ["Knowledge", "Users", "AI analytics"],
    hiddenLinks: [],
  },
  {
    role: "president",
    visibleLinks: ["Knowledge", "Users", "AI analytics"],
    hiddenLinks: [],
  },
];

test.describe("role-based access decision table", () => {
  for (const scenario of roleMatrix) {
    test(`@smoke ${scenario.role} receives the expected navigation permissions`, async ({ browser, request }) => {
      const context = await newAppContext(browser);
      const page = await context.newPage();
      await authenticate(page, request, scenario.role);
      const navigation = page.getByRole("navigation", { name: "Primary navigation" });

      for (const link of scenario.visibleLinks) {
        await expect(navigation.getByRole("link", { name: link })).toBeVisible();
      }
      for (const link of scenario.hiddenLinks) {
        await expect(navigation.getByRole("link", { name: link })).toHaveCount(0);
      }

      await context.close();
    });
  }

  test("student cannot open the user-management route directly", async ({ page, request }) => {
    await authenticate(page, request, "student");
    await page.goto("/admin/users");

    await expect(page).toHaveURL(/\/403$/);
    await expect(
      page.getByRole("heading", { name: "This workspace is protected." }),
    ).toBeVisible();
  });

  test("professor receives grading actions but not user administration", async ({ page, request }) => {
    await authenticate(page, request, "professor");

    await page.goto("/academics/classes");
    await expect(page.getByRole("button", { name: "Edit class" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Class report" })).toBeVisible();

    await page.goto("/academics/grades");
    await expect(page.getByRole("button", { name: "Record grade" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Users" })).toHaveCount(0);
  });
});
