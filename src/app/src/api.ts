import { isRecord } from "./guards";
import { parseStudents, type DevStudent } from "./students";

export const API_URL: string = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

export class ApiError extends Error {
  readonly status: number;
  readonly detail: string;

  constructor(status: number, detail = "") {
    super(`HTTP ${status}`);
    this.status = status;
    this.detail = detail;
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
  if (!response.ok) throw new ApiError(response.status, await detailOf(response));
  return response.json();
}

async function detailOf(response: Response): Promise<string> {
  try {
    const payload: unknown = await response.json();
    return isRecord(payload) && typeof payload.detail === "string" ? payload.detail : "";
  } catch {
    return "";
  }
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

export interface ConfirmationRequest {
  proposalToken: string;
  conversationId: string;
  message: string;
  confirmationWord: string;
}

export async function confirmProposal(token: string, request: ConfirmationRequest): Promise<Confirmation> {
  const payload = await post("/protocols/proposals/confirm", token, {
    token: request.proposalToken,
    conversation_id: request.conversationId,
    message: request.message,
    confirmation_word: request.confirmationWord,
  });
  return {
    protocolNumber: stringField(payload, "protocol_number"),
    slaDueAt: stringField(payload, "sla_due_at"),
  };
}

export function describeError(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 404) return "Esta proposta não vale mais. Peça de novo ao assistente.";
    if (error.status === 409) return "Já existe um pedido em andamento para este serviço.";
    if (error.status === 422) return "A API recusou o pedido.";
    return `A API respondeu com erro (${error.status}).`;
  }
  return "Não consegui falar com a API. Verifique se ela está no ar.";
}
