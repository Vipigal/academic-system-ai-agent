import { useState } from "react";

import { Chat } from "./Chat";
import { Login } from "./Login";
import type { DevStudent } from "./students";

interface Session {
  token: string;
  student: DevStudent;
}

export function App() {
  const [session, setSession] = useState<Session | null>(null);

  if (session === null) return <Login onLogin={(student, token) => setSession({ student, token })} />;
  return <Chat token={session.token} student={session.student} onExpired={() => setSession(null)} />;
}
