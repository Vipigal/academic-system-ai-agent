import { useChat } from "@ai-sdk/react";
import { DefaultChatTransport } from "ai";
import { useEffect, useMemo, useRef, useState } from "react";

import { API_URL, createConversation, describeError, Unauthorized } from "./api";
import { MessageView } from "./MessageView";

interface Props {
  token: string;
  student: string;
  onExpired: () => void;
}

export function Chat({ token, student, onExpired }: Props) {
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [startError, setStartError] = useState<string | null>(null);

  async function start() {
    setConversationId(null);
    setStartError(null);
    try {
      setConversationId(await createConversation(token));
    } catch (failure) {
      if (failure instanceof Unauthorized) onExpired();
      else setStartError(describeError(failure));
    }
  }

  useEffect(() => {
    void start();
  }, []);

  return (
    <main className="page chat">
      <header className="row between">
        <strong>{student}</strong>
        <div className="row">
          <button type="button" className="secondary" onClick={() => void start()}>
            Nova conversa
          </button>
          <button type="button" className="secondary" onClick={onExpired}>
            Sair
          </button>
        </div>
      </header>
      {startError && <p role="alert" className="error">{startError}</p>}
      {conversationId === null && !startError && <p className="muted">Abrindo conversa...</p>}
      {conversationId !== null && (
        <Conversation key={conversationId} id={conversationId} token={token} onExpired={onExpired} />
      )}
    </main>
  );
}

interface ConversationProps {
  id: string;
  token: string;
  onExpired: () => void;
}

function Conversation({ id, token, onExpired }: ConversationProps) {
  const transport = useMemo(
    () => new DefaultChatTransport({ api: `${API_URL}/chat`, headers: { Authorization: `Bearer ${token}` } }),
    [token],
  );
  const { messages, sendMessage, status, error } = useChat({ id, transport });
  const [text, setText] = useState("");
  const bottom = useRef<HTMLDivElement>(null);
  const busy = status === "submitted" || status === "streaming";

  useEffect(() => {
    bottom.current?.scrollIntoView({ block: "end" });
  }, [messages, status]);

  useEffect(() => {
    if (error?.message.includes("401")) onExpired();
  }, [error]);

  return (
    <>
      <section className="messages" aria-live="polite">
        {messages.length === 0 && <p className="muted">Pergunte algo, por exemplo: "Quanto estou devendo hoje?"</p>}
        {messages.map((message) => (
          <MessageView key={message.id} message={message} token={token} />
        ))}
        {status === "submitted" && <p className="muted">Pensando...</p>}
        {error && (
          <p role="alert" className="error">
            Não consegui responder agora. Tente de novo em instantes.
          </p>
        )}
        <div ref={bottom} />
      </section>
      <form
        className="row"
        onSubmit={(event) => {
          event.preventDefault();
          if (!text.trim() || busy) return;
          void sendMessage({ text: text.trim() });
          setText("");
        }}
      >
        <input
          value={text}
          onChange={(event) => setText(event.target.value)}
          placeholder="Escreva sua pergunta"
          aria-label="Mensagem"
        />
        <button type="submit" disabled={busy || !text.trim()}>
          Enviar
        </button>
      </form>
    </>
  );
}
