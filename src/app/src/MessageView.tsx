import type { UIMessage } from "ai";
import type { ComponentType } from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { isRecord, type JsonRecord } from "./guards";
import { ProtocolCard } from "./ProtocolCard";
import { ToolCallState, ToolCallView, type ToolCall } from "./ToolCallView";
import { TOOL_WIDGETS, type WidgetProps } from "./widgets/registry";

const PROPOSE_TOOL = "propose_protocol";
const OK = "ok";
const REMARK_PLUGINS = [remarkGfm];

type Part = UIMessage["parts"][number];

function toolName(part: Part): string | null {
  if (part.type === "dynamic-tool") return part.toolName;
  if (part.type.startsWith("tool-")) return part.type.slice("tool-".length);
  return null;
}

function stateOf(part: Part): ToolCallState {
  if (!("state" in part)) return ToolCallState.Running;
  if (part.state === "output-error") return ToolCallState.Failed;
  if (part.state === "output-available") return ToolCallState.Done;
  return ToolCallState.Running;
}

function toolCallOf(part: Part, name: string): ToolCall {
  return {
    name,
    state: stateOf(part),
    input: "input" in part ? part.input : undefined,
    output: "output" in part ? part.output : undefined,
    errorText: "errorText" in part && typeof part.errorText === "string" ? part.errorText : "",
  };
}

function RobotIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <rect x="4" y="8" width="16" height="12" rx="3" />
      <path d="M12 8V4M9 14h.01M15 14h.01M2 13v3M22 13v3" />
      <circle cx="12" cy="3.5" r="1" fill="currentColor" />
    </svg>
  );
}

interface CardContext {
  token: string;
  conversationId: string;
  busy: boolean;
}

interface PartProps {
  part: Part;
  role: UIMessage["role"];
  context: CardContext;
}

function PartView({ part, role, context }: PartProps) {
  if (part.type === "text") {
    if (!part.text.trim()) return null;
    if (role === "user") return <div className="row user"><div className="bubble user">{part.text}</div></div>;
    return (
      <div className="row assistant">
        <div className="avatar" aria-label="Assistente">
          <RobotIcon />
        </div>
        <div className="bubble assistant markdown">
          <Markdown remarkPlugins={REMARK_PLUGINS}>{part.text}</Markdown>
        </div>
      </div>
    );
  }
  const name = toolName(part);
  if (name === null) return null;
  const call = toolCallOf(part, name);
  return (
    <>
      <ToolCallView call={call} />
      {name === PROPOSE_TOOL && isRecord(call.output) && <ProtocolCard output={call.output} {...context} />}
    </>
  );
}

interface ReadyWidget {
  key: string;
  Widget: ComponentType<WidgetProps>;
  output: JsonRecord;
}

function asksForUi(call: ToolCall): boolean {
  return isRecord(call.input) && call.input.show_ui === true;
}

function widgetsOf(parts: Part[]): ReadyWidget[] {
  const requested = parts.flatMap((part, index) => {
    const name = toolName(part);
    const Widget = name === null ? undefined : TOOL_WIDGETS[name];
    if (name === null || !Widget) return [];
    const call = toolCallOf(part, name);
    if (!asksForUi(call) || call.state !== ToolCallState.Done || !isRecord(call.output) || call.output.status !== OK) return [];
    return [{ key: `${name}-${index}`, Widget, output: call.output }];
  });
  return requested.slice(-1);
}

interface Props {
  message: UIMessage;
  context: CardContext;
  streaming: boolean;
}

export function MessageView({ message, context, streaming }: Props) {
  const widgets = streaming ? [] : widgetsOf(message.parts);
  return (
    <div className="turn">
      {message.parts.map((part, index) => (
        <PartView key={index} part={part} role={message.role} context={context} />
      ))}
      {widgets.length > 0 && (
        <div className="widgets">
          {widgets.map(({ key, Widget, output }) => (
            <Widget key={key} output={output} />
          ))}
        </div>
      )}
    </div>
  );
}
