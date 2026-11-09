import { recordsOf, text, type JsonRecord } from "../guards";
import { dayKey } from "./format";

export enum ExamWindow {
  Open = "open",
  Closed = "closed",
  NotOpen = "not_open",
}

export interface Exam {
  code: string;
  name: string;
  kind: string;
  opensAt: string;
  closesAt: string;
  window: ExamWindow;
}

export interface MonthCursor {
  year: number;
  month: number;
}

export interface CalendarDay {
  key: string;
  day: number;
  inMonth: boolean;
}

function windowOf(value: string): ExamWindow {
  if (value === ExamWindow.Open) return ExamWindow.Open;
  if (value === ExamWindow.NotOpen) return ExamWindow.NotOpen;
  return ExamWindow.Closed;
}

function examOf(row: JsonRecord): Exam {
  return {
    code: text(row, "subject_code"),
    name: text(row, "subject_name"),
    kind: text(row, "kind"),
    opensAt: text(row, "opens_at"),
    closesAt: text(row, "closes_at"),
    window: windowOf(text(row, "window")),
  };
}

export function examsOf(output: JsonRecord): Exam[] {
  return recordsOf(output, "data")
    .map(examOf)
    .filter((exam) => exam.opensAt && exam.closesAt);
}

export function startDay(exam: Exam): string {
  return dayKey(new Date(exam.opensAt));
}

export function endDay(exam: Exam): string {
  return dayKey(new Date(exam.closesAt));
}

export function examsOn(exams: Exam[], key: string): Exam[] {
  return exams.filter((exam) => startDay(exam) <= key && key <= endDay(exam));
}

function cursorOf(key: string): MonthCursor {
  const [year, month] = key.split("-").map(Number);
  return { year: year ?? 1970, month: (month ?? 1) - 1 };
}

function earliest(exams: Exam[], day: (exam: Exam) => string): Exam | undefined {
  return [...exams].sort((left, right) => day(left).localeCompare(day(right)))[0];
}

function focusOf(exams: Exam[]): string | null {
  const open = earliest(exams.filter((exam) => exam.window === ExamWindow.Open), endDay);
  if (open) return endDay(open);
  const upcoming = earliest(exams.filter((exam) => exam.window === ExamWindow.NotOpen), startDay);
  if (upcoming) return startDay(upcoming);
  const last = latest(exams, endDay);
  return last ? endDay(last) : null;
}

function latest(exams: Exam[], day: (exam: Exam) => string): Exam | undefined {
  return [...exams].sort((left, right) => day(right).localeCompare(day(left)))[0];
}

export function initialMonth(exams: Exam[]): MonthCursor {
  return cursorOf(focusOf(exams) ?? dayKey(new Date()));
}

export function shiftMonth(cursor: MonthCursor, delta: number): MonthCursor {
  const moved = new Date(Date.UTC(cursor.year, cursor.month + delta, 1));
  return { year: moved.getUTCFullYear(), month: moved.getUTCMonth() };
}

export function monthLabel(cursor: MonthCursor): string {
  const label = new Intl.DateTimeFormat("pt-BR", { month: "long", year: "numeric", timeZone: "UTC" }).format(
    new Date(Date.UTC(cursor.year, cursor.month, 1)),
  );
  return label.charAt(0).toUpperCase() + label.slice(1);
}

export function monthDays(cursor: MonthCursor): CalendarDay[] {
  const first = new Date(Date.UTC(cursor.year, cursor.month, 1));
  const start = new Date(Date.UTC(cursor.year, cursor.month, 1 - first.getUTCDay()));
  const lastOfMonth = new Date(Date.UTC(cursor.year, cursor.month + 1, 0)).getUTCDate();
  const cells = Math.ceil((first.getUTCDay() + lastOfMonth) / 7) * 7;
  return Array.from({ length: cells }, (_, offset) => {
    const moment = new Date(start.getTime() + offset * 86_400_000);
    return {
      key: moment.toISOString().slice(0, 10),
      day: moment.getUTCDate(),
      inMonth: moment.getUTCMonth() === cursor.month,
    };
  });
}
