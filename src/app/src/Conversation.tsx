import { useChat } from "@ai-sdk/react";
import { DefaultChatTransport } from "ai";
import { useEffect, useMemo, useRef, useState } from "react";

import { API_URL } from "./api";
import { MessageView } from "./MessageView";
import { firstName } from "./students";

const SUGGESTIONS = [
  "Quanto falta para eu me formar?",
  "Como está minha situação financeira?",
  "Quais provas online eu tenho?",
  "Qual o andamento dos meus protocolos?",
];

interface Props {
  id: string;
  token: string;
  greeting: string;
  onExpired: () => void;
}

export function Conversation({ id, token, greeting, onExpired }: Props) {
  const transport = useMemo(
    () => new DefaultChatTransport({ api: `${API_URL}/chat`, headers: { Authorization: `Bearer ${token}` } }),
    [token],
  );
  const { messages, sendMessage, status, error } = useChat({ id, transport });
  const [text, setText] = useState("");
  const bottom = useRef<HTMLDivElement>(null);
  const busy = status === "submitted" || status === "streaming";

  function send(value: string) {
    if (!value.trim() || busy) return;
    void sendMessage({ text: value.trim() });
    setText("");
  }

  useEffect(() => {
    bottom.current?.scrollIntoView({ block: "end" });
  }, [messages, status]);

  useEffect(() => {
    if (error?.message.includes("401")) onExpired();
  }, [error]);

  return (
    <>
      {messages.length === 0 ? (
        <div className="empty">
          <h1>Olá, {firstName(greeting)} ;)</h1>
          <p className="lead">Pergunte sobre sua vida acadêmica, financeiro, protocolos ou o ambiente virtual.</p>
          <div className="suggestions">
            {SUGGESTIONS.map((suggestion) => (
              <button key={suggestion} type="button" className="btn outline" onClick={() => send(suggestion)}>
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      ) : (
        <section className="messages" aria-live="polite">
          {messages.map((message, index) => (
            <MessageView
              key={message.id}
              message={message}
              context={{ token, conversationId: id, busy }}
              streaming={busy && index === messages.length - 1}
            />
          ))}
          {status === "submitted" && <p className="thinking">Pensando...</p>}
          {error && (
            <p role="alert" className="error">
              Não consegui responder agora. Tente de novo em instantes.
            </p>
          )}
          <div ref={bottom} />
        </section>
      )}
      <form
        className="composer"
        onSubmit={(event) => {
          event.preventDefault();
          send(text);
        }}
      >
        <input
          value={text}
          onChange={(event) => setText(event.target.value)}
          placeholder="Escreva sua mensagem"
          aria-label="Mensagem"
        />
        <button type="submit" className="btn gold" disabled={busy || !text.trim()}>
          Enviar
        </button>
      </form>
    </>
  );
}
