import { isRecord } from "./guards";
import { toolLabel } from "./toolLabels";

export enum ToolCallState {
  Running = "running",
  Done = "done",
  Failed = "failed",
}

const CLIENT_ONLY = "client_only";

const VERBS: Record<ToolCallState, string> = {
  [ToolCallState.Running]: "Consultando",
  [ToolCallState.Done]: "Consultou",
  [ToolCallState.Failed]: "Falhou ao consultar",
};

export interface ToolCall {
  name: string;
  state: ToolCallState;
  input: unknown;
  output: unknown;
  errorText: string;
}

function formatted(value: unknown): string {
  if (value === undefined) return "—";
  if (typeof value === "string") return value;
  return JSON.stringify(value, null, 2);
}

function seenByModel(output: unknown): unknown {
  if (!isRecord(output) || !(CLIENT_ONLY in output)) return output;
  return Object.fromEntries(Object.entries(output).filter(([key]) => key !== CLIENT_ONLY));
}

function hasClientOnly(output: unknown): boolean {
  return isRecord(output) && CLIENT_ONLY in output;
}

interface Props {
  call: ToolCall;
}

export function ToolCallView({ call }: Props) {
  return (
    <details className={`tool ${call.state}`}>
      <summary>
        {VERBS[call.state]} {toolLabel(call.name)}
      </summary>
      <div className="tool-debug">
        <code className="tool-name">{call.name}</code>
        <span className="kicker">Input</span>
        <pre>{formatted(call.input)}</pre>
        <span className="kicker">{call.state === ToolCallState.Failed ? "Erro" : "Output"}</span>
        <pre>{call.state === ToolCallState.Failed ? call.errorText : formatted(seenByModel(call.output))}</pre>
        {hasClientOnly(call.output) && (
          <span className="muted small">
            <code>client_only</code> omitido: vai só para o front, fora do que o modelo recebe.
          </span>
        )}
      </div>
    </details>
  );
}
