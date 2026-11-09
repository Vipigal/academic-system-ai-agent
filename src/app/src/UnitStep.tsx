import type { Institution, Offering } from "./students";

interface Props {
  institutions: Institution[];
  onPick: (offering: Offering) => void;
}

export function UnitStep({ institutions, onPick }: Props) {
  return (
    <>
      <div className="login-head">
        <div>
          <h1>Boas-vindas ;)</h1>
          <p className="lead">Escolha a unidade e a modalidade do aluno.</p>
        </div>
        <span className="chip dev">Ambiente de teste</span>
      </div>
      <div>
        {institutions.map((institution) => (
          <div key={institution.name} className="institution">
            <b>{institution.name}</b>
            <div className="offerings">
              {institution.offerings.map((offering) => (
                <button key={offering.brand} type="button" className="pill" onClick={() => onPick(offering)}>
                  {offering.modality}
                  <span>{offering.students.length}</span>
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>
    </>
  );
}
