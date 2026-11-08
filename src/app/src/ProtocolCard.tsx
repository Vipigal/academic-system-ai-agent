import { useState } from "react";

import { confirmProposal, describeError, type Confirmation } from "./api";
import { isRecord, text } from "./guards";

const REFUSALS: Record<string, string> = {
  service_has_fee: "Este serviço tem taxa e não pode ser aberto pelo assistente.",
  service_inactive: "Este serviço não está disponível.",
  empty_message: "É preciso descrever o pedido.",
  duplicate_in_progress: "Já existe um pedido em andamento para este serviço.",
};

interface Props {
  output: Record<string, unknown>;
  token: string;
}

export function ProtocolCard({ output, token }: Props) {
  const [running, setRunning] = useState(false);
  const [done, setDone] = useState<Confirmation | null>(null);
  const [error, setError] = useState<string | null>(null);
  const data = output.data;
  const proposalToken = text(output.client_only, "token");

  if (output.status === "refused") {
    const existing = text(data, "existing_protocol");
    return (
      <div className="proposal refused">
        <span className="kicker">Solicitação</span>
        <strong className="proposal-title">Não foi possível abrir o pedido</strong>
        <p>{REFUSALS[text(data, "reason")] ?? "O pedido foi recusado."}</p>
        {existing && <p>Protocolo existente: {existing}</p>}
      </div>
    );
  }
  if (output.status !== "ok" || !proposalToken) return null;

  async function confirm() {
    setRunning(true);
    setError(null);
    try {
      setDone(await confirmProposal(token, proposalToken));
    } catch (failure) {
      setError(describeError(failure));
      setRunning(false);
    }
  }

  return (
    <div className={`proposal ${done ? "confirmed" : ""}`}>
      <span className="kicker">{done ? "Protocolo aberto" : "Solicitação"}</span>
      <strong className="proposal-title">{text(isRecord(data) ? data.service : null, "name")}</strong>
      <p className="muted">
        Matrícula {text(data, "enrollment")} · {text(data, "course_name")}
      </p>
      <p>{text(data, "message")}</p>
      {done ? (
        <p role="status" className="success">
          Nº {done.protocolNumber}
        </p>
      ) : (
        <button type="button" className="btn primary" disabled={running} onClick={() => void confirm()}>
          {running ? "Confirmando..." : "Confirmar"}
        </button>
      )}
      {error && <p role="alert" className="error">{error}</p>}
    </div>
  );
}
