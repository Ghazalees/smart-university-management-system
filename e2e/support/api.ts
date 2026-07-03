import { expect, type APIRequestContext } from "@playwright/test";
import type { Credentials } from "./credentials.js";

export interface UserSession {
  user: Record<string, unknown> & { id: number; username: string };
  tokens: { access: string; refresh: string };
}

export interface ApiEnvelope<T> {
  data: T;
  message?: string;
  pagination?: { count: number; pages: number; page: number };
}

export async function loginApi(
  request: APIRequestContext,
  credentials: Credentials,
): Promise<UserSession> {
  const response = await request.post("/api/v1/auth/login", {
    data: { identifier: credentials.username, password: credentials.password },
  });
  expect(response.ok(), await response.text()).toBeTruthy();
  const body = (await response.json()) as ApiEnvelope<UserSession>;
  return body.data;
}

export function authHeaders(session: UserSession): Record<string, string> {
  return { Authorization: `Bearer ${session.tokens.access}` };
}

export async function getApi<T>(
  request: APIRequestContext,
  path: string,
  session: UserSession,
): Promise<ApiEnvelope<T>> {
  const response = await request.get(path, { headers: authHeaders(session) });
  expect(response.ok(), await response.text()).toBeTruthy();
  return (await response.json()) as ApiEnvelope<T>;
}

export async function postApi<T>(
  request: APIRequestContext,
  path: string,
  session: UserSession,
  data: unknown,
): Promise<ApiEnvelope<T>> {
  const response = await request.post(path, {
    headers: authHeaders(session),
    data,
  });
  expect(response.ok(), await response.text()).toBeTruthy();
  return (await response.json()) as ApiEnvelope<T>;
}

export async function patchApi<T>(
  request: APIRequestContext,
  path: string,
  session: UserSession,
  data: unknown,
): Promise<ApiEnvelope<T>> {
  const response = await request.patch(path, {
    headers: authHeaders(session),
    data,
  });
  expect(response.ok(), await response.text()).toBeTruthy();
  return (await response.json()) as ApiEnvelope<T>;
}
