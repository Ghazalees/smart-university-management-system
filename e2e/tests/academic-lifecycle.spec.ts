import { expect, test } from "@playwright/test";
import { authenticate } from "../support/auth.js";
import { newAppContext } from "../support/context.js";
import { getApi, postApi } from "../support/api.js";
import { uniqueId } from "../support/ids.js";

interface ApiUser {
  id: number;
  username: string;
  full_name: string;
}

interface AcademicClass {
  id: number;
  course_detail: { code: string; title: string };
}

test("student registration, enrollment, professor grading, and class reporting work end to end", async ({ browser, request }) => {
  const suffix = uniqueId("student").replaceAll("-", "").slice(-14);
  const username = `e2e${suffix}`.toLowerCase();
  const password = "E2eStudent123!";
  const firstName = "E2E";
  const lastName = `Student${suffix.slice(-5)}`;
  const fullName = `${firstName} ${lastName}`;
  const email = `${username}@example.test`;
  const studentNumber = `E2E-${suffix.toUpperCase()}`;
  const score = "91.50";
  const feedback = `Excellent architecture validation ${suffix}`;
  const location = `Engineering E2E-${suffix.slice(-4)}`;

  const staffContext = await newAppContext(browser);
  const staffPage = await staffContext.newPage();
  const staffSession = await authenticate(staffPage, request, "staff");
  await staffPage.goto("/admin/users");

  await test.step("register a student through the real administrative form", async () => {
    await staffPage.getByRole("button", { name: "New user" }).click();
    const dialog = staffPage.getByRole("dialog", { name: "Create university account" });
    await dialog.getByLabel("First name").fill(firstName);
    await dialog.getByLabel("Last name").fill(lastName);
    await dialog.getByLabel("Username").fill(username);
    await dialog.getByLabel("Email").fill(email);
    await dialog.getByLabel("Temporary password").fill(password);
    await dialog.getByLabel("Confirm password").fill(password);
    await dialog.getByLabel("Role").selectOption({ label: "Student" });
    await dialog.getByLabel("Student number").fill(studentNumber);
    await dialog.getByRole("button", { name: "Register student" }).click();
    await expect(staffPage.getByText("Student account registered successfully")).toBeVisible();
  });

  const users = await getApi<ApiUser[]>(
    request,
    `/api/v1/users?search=${encodeURIComponent(username)}`,
    staffSession,
  );
  const student = users.data.find((candidate) => candidate.username === username);
  expect(student).toBeDefined();

  await test.step("reject a duplicate student number as an invalid equivalence class", async () => {
    await staffPage.getByRole("button", { name: "New user" }).click();
    const dialog = staffPage.getByRole("dialog", { name: "Create university account" });
    await dialog.getByLabel("First name").fill("Duplicate");
    await dialog.getByLabel("Last name").fill("Number");
    await dialog.getByLabel("Username").fill(`${username}duplicate`);
    await dialog.getByLabel("Email").fill(`duplicate-${email}`);
    await dialog.getByLabel("Temporary password").fill(password);
    await dialog.getByLabel("Confirm password").fill(password);
    await dialog.getByLabel("Role").selectOption({ label: "Student" });
    await dialog.getByLabel("Student number").fill(studentNumber.toLowerCase());
    await dialog.getByRole("button", { name: "Register student" }).click();
    await expect(staffPage.getByText(/student number.*already/i)).toBeVisible();
    await dialog.getByRole("button", { name: "Cancel" }).click();
  });

  const classes = await getApi<AcademicClass[]>(request, "/api/v1/classes?page=1", staffSession);
  const targetClass = classes.data.find((item) => item.course_detail.code === "SE401");
  expect(targetClass).toBeDefined();
  await postApi(
    request,
    "/api/v1/enrollments",
    staffSession,
    { academic_class: targetClass!.id, student: student!.id },
  );
  await staffContext.close();

  const professorContext = await newAppContext(browser);
  const professorPage = await professorContext.newPage();
  await authenticate(professorPage, request, "professor");

  await test.step("professor edits the owned class without changing its owner", async () => {
    await professorPage.goto("/academics/classes");
    const classCard = professorPage.locator(".class-card").filter({ hasText: "Advanced Software Engineering" });
    await classCard.getByRole("button", { name: "Edit class" }).click();
    const dialog = professorPage.getByRole("dialog", { name: "Edit SE401 class" });
    await expect(dialog.getByLabel("Professor")).toHaveCount(0);
    await dialog.getByLabel("Room / location").fill(location);
    await dialog.getByRole("button", { name: "Save class changes" }).click();
    await expect(professorPage.getByText("Class updated successfully")).toBeVisible();
    await expect(classCard).toContainText(location);
  });

  await test.step("boundary validation rejects a score above 100 before submission", async () => {
    await professorPage.goto("/academics/grades");
    await professorPage.getByRole("button", { name: "Record grade" }).click();
    const dialog = professorPage.getByRole("dialog", { name: "Record a grade" });
    const forbiddenStudentDirectoryRequests: string[] = [];
    professorPage.on("request", (apiRequest) => {
      const url = apiRequest.url();
      if (url.includes("/api/v1/users") && url.includes("role=Student")) {
        forbiddenStudentDirectoryRequests.push(url);
      }
    });

    const enrollmentResponse = professorPage.waitForResponse((response) => {
      const url = response.url();
      return response.request().method() === "GET"
        && url.includes("/api/v1/enrollments")
        && url.includes(`class_id=${targetClass!.id}`)
        && response.ok();
    });
    await dialog.locator('select[name="academic_class"]').selectOption(String(targetClass!.id));
    await enrollmentResponse;

    const studentSelect = dialog.locator('select[name="student"]');
    await expect(studentSelect).toContainText(fullName);
    await studentSelect.selectOption(String(student!.id));
    const scoreInput = dialog.getByLabel("Score out of 100");
    await scoreInput.fill("100.01");
    expect(await scoreInput.evaluate((element: HTMLInputElement) => element.validity.rangeOverflow)).toBeTruthy();
    await dialog.getByRole("button", { name: "Save grade" }).click();
    await expect(dialog).toBeVisible();

    await scoreInput.fill(score);
    await dialog.getByLabel("Feedback").fill(feedback);
    await dialog.getByRole("button", { name: "Save grade" }).click();
    await expect(professorPage.getByText("Grade saved and student notified")).toBeVisible();
    expect(forbiddenStudentDirectoryRequests).toEqual([]);
  });

  await test.step("class report contains grades, ungraded students, statistics, and feedback", async () => {
    await professorPage.goto("/academics/classes");
    const classCard = professorPage.locator(".class-card").filter({ hasText: "Advanced Software Engineering" });
    await classCard.getByRole("button", { name: "Class report" }).click();
    const report = professorPage.getByRole("dialog", { name: "Class performance report" });
    const studentRow = report.locator("tbody tr").filter({ hasText: fullName });
    await expect(studentRow).toContainText("91.5");
    await expect(studentRow).toContainText("Graded");
    await expect(studentRow).toContainText(feedback);
    const studentsText = await report.locator(".report-stat").filter({ hasText: "Students" }).textContent();
    const gradedText = await report.locator(".report-stat").filter({ hasText: "Grades recorded" }).textContent();
    const ungradedText = await report.locator(".report-stat").filter({ hasText: "Without grade" }).textContent();
    expect(Number(studentsText?.match(/\d+/)?.[0])).toBeGreaterThanOrEqual(2);
    expect(Number(gradedText?.match(/\d+/)?.[0])).toBeGreaterThanOrEqual(1);
    expect(Number(ungradedText?.match(/\d+/)?.[0])).toBeGreaterThanOrEqual(1);
    await expect(report.locator(".report-stat").filter({ hasText: "Class average" })).toContainText("91.5");
    await expect(report.locator(".report-stat").filter({ hasText: "Lowest grade" })).toContainText("91.5");
    await expect(report.locator(".report-stat").filter({ hasText: "Highest grade" })).toContainText("91.5");
  });
  await professorContext.close();

  await test.step("student sees only the student's own grade and no class report action", async () => {
    const studentContext = await newAppContext(browser);
    const studentPage = await studentContext.newPage();
    await authenticate(studentPage, request, { username, password });
    await studentPage.goto("/academics/grades");
    const ownGrade = studentPage.locator(".grade-card").filter({ hasText: fullName });
    await expect(ownGrade).toContainText("91.5");
    await expect(ownGrade).toContainText(feedback);
    await studentPage.goto("/academics/classes");
    await expect(studentPage.getByRole("button", { name: "Class report" })).toHaveCount(0);
    await studentContext.close();
  });
});
