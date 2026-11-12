import { useState, type FormEvent } from "react";
import { ApiProblem, isSessionProblem, signIn, type SessionInfo } from "./attendance-api";

type Props = {
  csrfToken: string;
  onSignIn: (session: SessionInfo) => void;
  onSessionProblem: () => void;
};

export function LoginForm({ csrfToken, onSignIn, onSessionProblem }: Props) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      onSignIn(await signIn(csrfToken, username, password));
    } catch (cause) {
      if (isSessionProblem(cause)) {
        onSessionProblem();
      } else {
        setError(cause instanceof ApiProblem ? cause.message : "No se pudo iniciar sesión. Inténtalo otra vez.");
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="login-shell">
      <section className="login-card" aria-labelledby="login-title">
        <p className="product-name">Sistema de Asistencia</p>
        <h1 id="login-title">Iniciar sesión</h1>
        <form className="login-form" onSubmit={submit}>
          <label htmlFor="usuario">Usuario</label>
          <input id="usuario" name="usuario" autoComplete="username" required
            maxLength={80} value={username} onChange={(event) => setUsername(event.target.value)} />
          <label htmlFor="contrasena">Contraseña</label>
          <input id="contrasena" name="contrasena" type="password"
            autoComplete="current-password" required maxLength={256}
            value={password} onChange={(event) => setPassword(event.target.value)} />
          {error && <p className="form-error" role="alert">{error}</p>}
          <button disabled={busy} type="submit">
            {busy ? "Ingresando…" : "Ingresar"}
          </button>
        </form>
      </section>
    </main>
  );
}
