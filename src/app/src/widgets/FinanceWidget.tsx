import { flag, numberOf, recordOf, recordsOf, text, type JsonRecord } from "../guards";
import { daysBetween, formatCompetence, formatDayMonth, formatMoney, formatRate } from "./format";

const DUE_SOON_DAYS = 7;

function DebtAlert({ debt }: { debt: JsonRecord }) {
  if ((numberOf(debt, "overdue_invoices") ?? 0) === 0) return <div className="alert ok">Nada em atraso</div>;
  return (
    <div className="alert danger">
      <strong>{formatMoney(numberOf(debt, "total_reais") ?? 0)} em atraso</strong>
      <ul className="invoice-rows">
        {recordsOf(debt, "items").map((item) => (
          <li key={text(item, "invoice_id")}>
            <span>{formatCompetence(text(item, "competence"))}</span>
            <span>venceu {formatDayMonth(text(item, "due_date"))}</span>
            <span>{formatMoney((numberOf(item, "principal_reais") ?? 0) + (numberOf(item, "late_charge_reais") ?? 0))}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function NextInvoice({ invoice, referenceDate }: { invoice: JsonRecord; referenceDate: string }) {
  const dueDate = text(invoice, "due_date");
  const soon = daysBetween(referenceDate, dueDate) <= DUE_SOON_DAYS;
  return (
    <span className={`chip ${soon ? "soon" : "neutral"}`}>
      Próxima {formatDayMonth(dueDate)} · {formatMoney(numberOf(invoice, "amount_reais") ?? 0)}
    </span>
  );
}

function Contract({ contract }: { contract: JsonRecord }) {
  const debt = recordOf(contract, "debt") ?? {};
  const next = recordOf(contract, "next_invoice");
  const scholarships = recordsOf(contract, "scholarships").filter((scholarship) => flag(scholarship, "is_active"));
  return (
    <div className="contract">
      <DebtAlert debt={debt} />
      <div className="chips">
        {next && <NextInvoice invoice={next} referenceDate={text(debt, "reference_date")} />}
        {scholarships.map((scholarship, index) => (
          <span key={index} className="chip ok">
            Bolsa {formatRate(numberOf(scholarship, "rate") ?? 0)}
          </span>
        ))}
      </div>
    </div>
  );
}

export function FinanceWidget({ output }: { output: JsonRecord }) {
  const contracts = recordsOf(output, "data");
  if (contracts.length === 0) return null;
  return (
    <div className="widget finance">
      {contracts.map((contract, index) => (
        <Contract key={index} contract={contract} />
      ))}
    </div>
  );
}
