import { useEffect, useState } from "react";

import { describeError, devLogin, listDevStudents } from "./api";
import { StudentStep } from "./StudentStep";
import { groupByInstitution, loginReference, type DevStudent, type Institution, type Offering } from "./students";
import { Topbar } from "./Topbar";
import { UnitStep } from "./UnitStep";

interface Props {
  onLogin: (student: DevStudent, token: string) => void;
}

export function Login({ onLogin }: Props) {
  const [institutions, setInstitutions] = useState<Institution[] | null>(null);
  const [offering, setOffering] = useState<Offering | null>(null);
  const [entering, setEntering] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setError(null);
    try {
      setInstitutions(groupByInstitution(await listDevStudents()));
    } catch (failure) {
      setError(describeError(failure));
    }
  }

  async function enter(student: DevStudent) {
    setEntering(student.studentId);
    setError(null);
    try {
      onLogin(student, await devLogin(loginReference(student)));
    } catch (failure) {
      setError(describeError(failure));
      setEntering(null);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  return (
    <div className="screen">
      <Topbar />
      <main className="login-wrap">
        <section className="card login">
          {institutions === null && !error && <p className="muted">Carregando alunos...</p>}
          {institutions !== null && offering === null && <UnitStep institutions={institutions} onPick={setOffering} />}
          {offering !== null && (
            <StudentStep
              offering={offering}
              entering={entering}
              onBack={() => setOffering(null)}
              onPick={(student) => void enter(student)}
            />
          )}
          {error && (
            <p role="alert" className="error">
              {error}{" "}
              {institutions === null && (
                <button type="button" className="link" onClick={() => void load()}>
                  Tentar de novo
                </button>
              )}
            </p>
          )}
        </section>
        <p className="disclaimer">
          Tela de teste para desenvolvimento: entra como qualquer aluno sem senha. Em produção ela não existe; o aluno chega
          pelo login institucional (SSO) e a API só aceita o token emitido por ele.
        </p>
      </main>
    </div>
  );
}
