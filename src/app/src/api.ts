import { isRecord } from "./guards";
import { parseStudents, type DevStudent } from "./students";

export const API_URL: string = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

export class ApiError extends Error {
  readonly status: number;

  constructor(status: number) {
    super(`HTTP ${status}`);
    this.status = status;
  }
}

export class Unauthorized extends Error {}

async function post(path: string, token: string | null, body?: object): Promise<unknown> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;
  const response = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (response.status === 401 && token) throw new Unauthorized();
  if (!response.ok) throw new ApiError(response.status);
  return response.json();
}

function stringField(payload: unknown, key: string): string {
  if (isRecord(payload) && typeof payload[key] === "string") return payload[key];
  throw new ApiError(502);
}

export async function devLogin(student: string): Promise<string> {
  return stringField(await post("/auth/dev-login", null, { student }), "access_token");
}

export async function listDevStudents(): Promise<DevStudent[]> {
  const response = await fetch(`${API_URL}/auth/dev-students`);
  if (!response.ok) throw new ApiError(response.status);
  return parseStudents(await response.json());
}

export async function createConversation(token: string): Promise<string> {
  return stringField(await post("/conversations", token), "id");
}

export interface Confirmation {
  protocolNumber: string;
  slaDueAt: string;
}

export async function confirmProposal(token: string, proposalToken: string): Promise<Confirmation> {
  const payload = await post("/protocols/proposals/confirm", token, { token: proposalToken });
  return {
    protocolNumber: stringField(payload, "protocol_number"),
    slaDueAt: stringField(payload, "sla_due_at"),
  };
}

export function describeError(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 404) return "Esta proposta não vale mais. Peça de novo ao assistente.";
    if (error.status === 409) return "Já existe um pedido em andamento para este serviço.";
    if (error.status === 422) return "Este serviço tem taxa e não pode ser aberto pelo assistente.";
    return `A API respondeu com erro (${error.status}).`;
  }
  return "Não consegui falar com a API. Verifique se ela está no ar.";
}
