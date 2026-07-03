export function uniqueId(prefix: string): string {
  const entropy = Math.random().toString(36).slice(2, 8);
  return `${prefix}-${Date.now()}-${entropy}`;
}
