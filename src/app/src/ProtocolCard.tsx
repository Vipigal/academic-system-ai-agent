import { useState } from "react";

import { confirmProposal, type Confirmation } from "./api";
import { recordOf, text } from "./guards";
import { confirmationError, parseProposal, refusalText, type Proposal } from "./proposal";

const NOT_IN_DATA = "As regras do serviço e os efeitos sobre cobranças não estão nos dados do assistente.";

interface Props {
  output: Record<string, unknown>;
  token: string;
  conversationId: string;
  busy: boolean;
}

export function ProtocolCard({ output, token, conversationId, busy }: Props) {
  if (output.status === "refused") return <RefusedCard data={output.data} />;
  const proposal = parseProposal(output);
  if (proposal === null) return null;
  return <ProposalCard proposal={proposal} token={token} conversationId={conversationId} busy={busy} />;
}

function RefusedCard({ data }: { data: unknown }) {
  const existing = text(data, "existing_protocol");
  return (
    <div className="proposal refused">
      <span className="kicker">Solicitação</span>
      <strong className="proposal-title">Não foi possível abrir o pedido</strong>
      <p>{text(recordOf(data, "service"), "title")}</p>
      <p>{refusalText(text(data, "reason"))}</p>
      {existing && <p>Protocolo existente: {existing}</p>}
    </div>
  );
}

interface ProposalProps {
  proposal: Proposal;
  token: string;
  conversationId: string;
  busy: boolean;
}

function ProposalCard({ proposal, token, conversationId, busy }: ProposalProps) {
  const [message, setMessage] = useState("");
  const [word, setWord] = useState("");
  const [running, setRunning] = useState(false);
  const [done, setDone] = useState<Confirmation | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { confirmation } = proposal;
  const filled = (!proposal.requiresMessage || message.trim() !== "") && (!confirmation || word.trim() !== "");

  async function confirm() {
    setRunning(true);
    setError(null);
    try {
      const request = { proposalToken: proposal.token, conversationId, message, confirmationWord: word };
      setDone(await confirmProposal(token, request));
    } catch (failure) {
      setError(confirmationError(failure));
    }
    setRunning(false);
  }

  return (
    <div className={`proposal ${done ? "confirmed" : ""}`}>
      <span className="kicker">{done ? "Protocolo aberto" : "Solicitação"}</span>
      <strong className="proposal-title">{proposal.title}</strong>
      <p className="muted">
        Matrícula {proposal.enrollment} · {proposal.course}
      </p>
      {proposal.subject && <p>Disciplina citada: {proposal.subject}</p>}
      {confirmation ? (
        <>
          <strong>{confirmation.question}</strong>
          <p>{confirmation.effect}</p>
          {confirmation.limit && <p>{confirmation.limit}</p>}
          <p className="muted small">{NOT_IN_DATA}</p>
        </>
      ) : (
        <p>{proposal.effect}</p>
      )}
      {!proposal.requiresMessage && proposal.requestText && (
        <p>
          Texto do pedido: <q>{proposal.requestText}</q>
        </p>
      )}
      {done ? (
        <p role="status" className="success">
          Nº {done.protocolNumber}
        </p>
      ) : (
        <>
          {proposal.requiresMessage && (
            <label className="proposal-field">
              Escreva o seu pedido
              <textarea value={message} rows={4} onChange={(event) => setMessage(event.target.value)} />
            </label>
          )}
          {confirmation && (
            <label className="proposal-field">
              Digite {confirmation.word} para confirmar
              <input value={word} onChange={(event) => setWord(event.target.value)} autoComplete="off" />
            </label>
          )}
          <button
            type="button"
            className="btn primary"
            disabled={!filled || running || busy}
            onClick={() => void confirm()}
          >
            {running ? "Confirmando..." : "Confirmar"}
          </button>
        </>
      )}
      {error && <p role="alert" className="error">{error}</p>}
    </div>
  );
}
