import { useState } from "react";

import { displayName, institutionName, matches, statusLabel, type DevStudent, type Offering } from "./students";

const ACTIVE = "ACTIVE";

interface Props {
  offering: Offering;
  entering: string | null;
  onBack: () => void;
  onPick: (student: DevStudent) => void;
}

export function StudentStep({ offering, entering, onBack, onPick }: Props) {
  const [query, setQuery] = useState("");
  const visible = offering.students.filter((student) => matches(student, query));
  const title = institutionName(offering.brand);

  return (
    <>
      <button type="button" className="back" onClick={onBack} disabled={entering !== null}>
        ← Trocar unidade
      </button>
      <div className="login-head">
        <div>
          <h1>
            {title} · {offering.modality}
          </h1>
          <p className="lead">{offering.students.length} alunos. Escolha um para entrar como ele.</p>
        </div>
        <span className="chip dev">Ambiente de teste</span>
      </div>
      <input
        className="search"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        placeholder="Buscar por nome ou RA"
        aria-label="Buscar aluno"
      />
      <ul className="students">
        {visible.length === 0 && <li className="muted empty-row">Nenhum aluno encontrado.</li>}
        {visible.map((student) => (
          <li key={student.studentId}>
            <button
              type="button"
              className="student"
              disabled={entering !== null}
              onClick={() => onPick(student)}
            >
              <span>
                <span className="name">{displayName(student.fullName)}</span>
                <span className="ra">
                  {entering === student.studentId ? "Entrando..." : `RA ${student.studentId}`}
                </span>
              </span>
              <span className={`chip ${student.status === ACTIVE ? "ok" : "warn"}`}>{statusLabel(student.status)}</span>
            </button>
          </li>
        ))}
      </ul>
    </>
  );
}
