import { useState } from "react";

import { describeError, devLogin } from "./api";

const SHORTCUTS = ["UniAraucaria_EAD:013161", "UniMontanhas:070017", "UniSaoPaulo:181722", "UniMontanhas:070114"];

interface Props {
  onLogin: (student: string, token: string) => void;
}

export function Login({ onLogin }: Props) {
  const [student, setStudent] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function enter(value: string) {
    setLoading(true);
    setError(null);
    try {
      onLogin(value, await devLogin(value));
    } catch (failure) {
      setError(describeError(failure));
      setLoading(false);
    }
  }

  return (
    <main className="page">
      <h1>Atendimento ao aluno</h1>
      <form
        onSubmit={(event) => {
          event.preventDefault();
          if (student.trim()) void enter(student.trim());
        }}
      >
        <label htmlFor="student">Aluno (marca:RA)</label>
        <div className="row">
          <input
            id="student"
            value={student}
            onChange={(event) => setStudent(event.target.value)}
            placeholder="UniAraucaria_EAD:013161"
            disabled={loading}
          />
          <button type="submit" disabled={loading || !student.trim()}>
            {loading ? "Entrando..." : "Entrar"}
          </button>
        </div>
      </form>
      <div className="shortcuts">
        {SHORTCUTS.map((value) => (
          <button key={value} type="button" className="secondary" disabled={loading} onClick={() => void enter(value)}>
            {value}
          </button>
        ))}
      </div>
      {error && <p role="alert" className="error">{error}</p>}
    </main>
  );
}
