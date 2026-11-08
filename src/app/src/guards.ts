export type JsonRecord = Record<string, unknown>;

export function isRecord(value: unknown): value is JsonRecord {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function text(source: unknown, key: string): string {
  return isRecord(source) && typeof source[key] === "string" ? source[key] : "";
}

export function numberOf(source: unknown, key: string): number | null {
  if (!isRecord(source)) return null;
  const value = source[key];
  if (typeof value === "number") return value;
  if (typeof value === "string" && value.trim() !== "" && Number.isFinite(Number(value))) return Number(value);
  return null;
}

export function recordOf(source: unknown, key: string): JsonRecord | null {
  return isRecord(source) && isRecord(source[key]) ? source[key] : null;
}

export function recordsOf(source: unknown, key: string): JsonRecord[] {
  if (!isRecord(source)) return [];
  const value = source[key];
  return Array.isArray(value) ? value.filter(isRecord) : [];
}

export function flag(source: unknown, key: string): boolean {
  return isRecord(source) && source[key] === true;
}
