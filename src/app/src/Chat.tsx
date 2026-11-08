import { useEffect, useState } from "react";

import { createConversation, describeError, Unauthorized } from "./api";
import { Conversation } from "./Conversation";
import { displayName, type DevStudent } from "./students";
import { Topbar } from "./Topbar";

interface Props {
  token: string;
  student: DevStudent;
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
    <div className="screen">
      <Topbar>
        <div className="who">
          <span className="who-name">{displayName(student.fullName)}</span>
          <span className="chip on-navy">
            {student.brand} · {student.studentId}
          </span>
          <button type="button" className="btn ghost-light" onClick={onExpired}>
            Sair
          </button>
        </div>
      </Topbar>
      <main className="chat-wrap">
        <section className="card chat">
          <div className="chat-head">
            <span className="title">Atendimento</span>
            <button type="button" className="btn outline small" onClick={() => void start()}>
              Nova conversa
            </button>
          </div>
          {startError && (
            <p role="alert" className="error notice">
              {startError}
            </p>
          )}
          {conversationId === null && !startError && <p className="muted notice">Abrindo conversa...</p>}
          {conversationId !== null && (
            <Conversation
              key={conversationId}
              id={conversationId}
              token={token}
              greeting={student.fullName}
              onExpired={onExpired}
            />
          )}
        </section>
      </main>
    </div>
  );
}
