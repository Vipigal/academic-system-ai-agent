import { useState } from "react";

import { Chat } from "./Chat";
import { Login } from "./Login";

export function App() {
  const [token, setToken] = useState<string | null>(null);
  const [student, setStudent] = useState("");

  if (token === null) {
    return (
      <Login
        onLogin={(value, login) => {
          setStudent(value);
          setToken(login);
        }}
      />
    );
  }
  return <Chat token={token} student={student} onExpired={() => setToken(null)} />;
}
