import type { UIMessage } from "ai";

import { isRecord } from "./api";
import { ProtocolCard } from "./ProtocolCard";

const PROPOSE_TOOL = "propose_protocol";

type Part = UIMessage["parts"][number];

function toolName(part: Part): string | null {
  if (part.type === "dynamic-tool") return part.toolName;
  if (part.type.startsWith("tool-")) return part.type.slice("tool-".length);
  return null;
}

function outputOf(part: Part): unknown {
  return "output" in part ? part.output : undefined;
}

interface Props {
  message: UIMessage;
  token: string;
}

export function MessageView({ message, token }: Props) {
  return (
    <div className={`bubble ${message.role}`}>
      {message.parts.map((part, index) => {
        if (part.type === "text") return <p key={index} className="text">{part.text}</p>;
        const name = toolName(part);
        if (name === null) return null;
        const output = outputOf(part);
        if (name === PROPOSE_TOOL && isRecord(output)) {
          return <ProtocolCard key={index} output={output} token={token} />;
        }
        return (
          <p key={index} className="tool">
            Consultando: {name}
          </p>
        );
      })}
    </div>
  );
}
