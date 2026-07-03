export type DemoRole = "student" | "professor" | "staff" | "president";

export interface Credentials {
  username: string;
  password: string;
}

export const demoCredentials: Record<DemoRole, Credentials> = {
  student: {
    username: process.env.E2E_STUDENT_USERNAME ?? "student",
    password: process.env.E2E_STUDENT_PASSWORD ?? "Student123!",
  },
  professor: {
    username: process.env.E2E_PROFESSOR_USERNAME ?? "professor",
    password: process.env.E2E_PROFESSOR_PASSWORD ?? "Professor123!",
  },
  staff: {
    username: process.env.E2E_STAFF_USERNAME ?? "staff",
    password: process.env.E2E_STAFF_PASSWORD ?? "Staff123!",
  },
  president: {
    username: process.env.E2E_PRESIDENT_USERNAME ?? "president",
    password: process.env.E2E_PRESIDENT_PASSWORD ?? "President123!",
  },
};
