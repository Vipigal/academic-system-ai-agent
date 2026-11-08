import type { ReactNode } from "react";

interface Props {
  children?: ReactNode;
}

export function Topbar({ children }: Props) {
  return (
    <header className="topbar">
      <div className="brand">
        <div className="brand-mark" aria-hidden="true">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
            <path d="M4 4h16a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H9l-5 4v-4a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2Z" />
          </svg>
        </div>
        <div>
          Atendimento ao aluno
          <small>Agente acadêmico</small>
        </div>
      </div>
      {children}
    </header>
  );
}
