import { numberOf, recordOf, recordsOf, text, type JsonRecord } from "../guards";
import { formatHours, titleCase } from "./format";
import { ProgressRing } from "./ProgressRing";

const COMPLETED = new Set(["approved", "exempt"]);
const IN_PROGRESS = "in_progress";

interface Progress {
  enrollment: string;
  completionPct: number;
  completedHours: number;
  totalHours: number;
  pending: JsonRecord[];
}

function progressOf(enrollment: string, totals: JsonRecord, subjects: JsonRecord[]): Progress {
  return {
    enrollment,
    completionPct: numberOf(totals, `${enrollment}.completion_pct`) ?? 0,
    completedHours: numberOf(totals, `${enrollment}.completed_hours`) ?? 0,
    totalHours: numberOf(totals, `${enrollment}.total_hours`) ?? 0,
    pending: subjects.filter(
      (subject) => text(subject, "enrollment") === enrollment && !COMPLETED.has(text(subject, "situation")),
    ),
  };
}

function institutionOf(enrollment: string): string {
  return enrollment.split(":")[0]?.replace("_EAD", " EAD") ?? "";
}

function enrollmentsIn(totals: JsonRecord): string[] {
  const suffix = ".completion_pct";
  return Object.keys(totals)
    .filter((key) => key.endsWith(suffix))
    .map((key) => key.slice(0, -suffix.length));
}

function bySemester(subjects: JsonRecord[]): [number, JsonRecord[]][] {
  const groups = new Map<number, JsonRecord[]>();
  for (const subject of subjects) {
    const semester = numberOf(subject, "semester") ?? 0;
    groups.set(semester, [...(groups.get(semester) ?? []), subject]);
  }
  return [...groups].sort(([left], [right]) => left - right);
}

function EnrollmentProgress({ progress, label }: { progress: Progress; label: string }) {
  return (
    <div className="progress">
      <div className="progress-head">
        <ProgressRing percent={progress.completionPct} />
        <div>
          <span className="kicker">Integralização{label ? ` · ${label}` : ""}</span>
          <p className="muted">
            {formatHours(progress.completedHours)} de {formatHours(progress.totalHours)}
          </p>
        </div>
      </div>
      {progress.pending.length > 0 && (
        <details className="widget-more">
          <summary>O que falta, por semestre</summary>
          {bySemester(progress.pending).map(([semester, subjects]) => (
            <div key={semester} className="semester">
              <span className="kicker">{semester}º semestre</span>
              <ul>
                {subjects.map((subject) => (
                  <li key={text(subject, "code")}>
                    {titleCase(text(subject, "name"))}
                    {text(subject, "situation") === IN_PROGRESS && <span className="chip ok">Cursando</span>}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </details>
      )}
    </div>
  );
}

export function ProgressWidget({ output }: { output: JsonRecord }) {
  const totals = recordOf(output, "totals") ?? {};
  const subjects = recordsOf(output, "data");
  const enrollments = enrollmentsIn(totals);
  if (enrollments.length === 0) return null;
  return (
    <div className="widget progress-widget">
      {enrollments.map((enrollment) => (
        <EnrollmentProgress
          key={enrollment}
          progress={progressOf(enrollment, totals, subjects)}
          label={enrollments.length > 1 ? institutionOf(enrollment) : ""}
        />
      ))}
    </div>
  );
}
