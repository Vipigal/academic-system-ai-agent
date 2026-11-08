import { useState } from "react";

import type { JsonRecord } from "../guards";
import {
  endDay,
  ExamWindow,
  examsOf,
  examsOn,
  initialMonth,
  monthDays,
  monthLabel,
  shiftMonth,
  type CalendarDay,
  type Exam,
} from "./calendar";
import { titleCase } from "./format";

const WEEKDAYS = ["D", "S", "T", "Q", "Q", "S", "S"];
const KIND_LABELS: Record<string, string> = { av1: "AV1", av2: "AV2", practice_test: "Simulado" };
const WINDOW_LABELS: Record<ExamWindow, string> = {
  [ExamWindow.Open]: "Aberta",
  [ExamWindow.NotOpen]: "Ainda não abriu",
  [ExamWindow.Closed]: "Encerrada",
};

function dayClass(day: CalendarDay, exams: Exam[], selected: string | null): string {
  const covering = examsOn(exams, day.key);
  const classes = ["day"];
  if (!day.inMonth) classes.push("outside");
  if (covering.length > 0) classes.push(`has-${covering[0]?.window ?? ExamWindow.Closed}`);
  if (covering.some((exam) => endDay(exam) === day.key)) classes.push("deadline");
  if (day.key === selected) classes.push("selected");
  return classes.join(" ");
}

function ExamDetail({ exam }: { exam: Exam }) {
  return (
    <li className="exam">
      <span>
        <b>{KIND_LABELS[exam.kind] ?? exam.kind}</b> {titleCase(exam.name)}
      </span>
      <span className={`chip window-${exam.window}`}>{WINDOW_LABELS[exam.window]}</span>
    </li>
  );
}

export function ExamCalendar({ output }: { output: JsonRecord }) {
  const exams = examsOf(output);
  const [cursor, setCursor] = useState(() => initialMonth(exams));
  const [selected, setSelected] = useState<string | null>(null);
  if (exams.length === 0) return null;
  const chosen = selected === null ? [] : examsOn(exams, selected);

  return (
    <div className="widget calendar">
      <div className="calendar-head">
        <button type="button" className="nav" aria-label="Mês anterior" onClick={() => setCursor(shiftMonth(cursor, -1))}>
          ‹
        </button>
        <strong className="widget-title">{monthLabel(cursor)}</strong>
        <button type="button" className="nav" aria-label="Próximo mês" onClick={() => setCursor(shiftMonth(cursor, 1))}>
          ›
        </button>
      </div>
      <div className="calendar-grid">
        {WEEKDAYS.map((weekday, index) => (
          <span key={index} className="weekday">
            {weekday}
          </span>
        ))}
        {monthDays(cursor).map((day) => (
          <button key={day.key} type="button" className={dayClass(day, exams, selected)} onClick={() => setSelected(day.key)}>
            {day.day}
          </button>
        ))}
      </div>
      <div className="legend">
        <span className="legend-item has-open">Aberta</span>
        <span className="legend-item has-not_open">Ainda não abriu</span>
        <span className="legend-item has-closed">Encerrada</span>
        <span className="legend-item deadline">Prazo final</span>
      </div>
      {selected !== null && (
        <ul className="exams">
          {chosen.length === 0 ? <li className="muted">Nenhuma prova neste dia.</li> : chosen.map((exam) => <ExamDetail key={`${exam.code}-${exam.kind}`} exam={exam} />)}
        </ul>
      )}
      {selected === null && <p className="muted small">Toque num dia marcado para ver as provas.</p>}
    </div>
  );
}
