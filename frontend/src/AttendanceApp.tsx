import { useCallback, useEffect, useState } from "react";
import { getSession, isSessionProblem, signOut, type SessionInfo } from "./attendance-api";
import { LoginForm } from "./LoginForm";
import { WorkerPage } from "./WorkerPage";

export function AttendanceApp() {
  const [session, setSession] = useState<SessionInfo | null>(null);
  const [sessionError, setSessionError] = useState("");
  const [attempt, setAttempt] = useState(0);
  const [loggingOut, setLoggingOut] = useState(false);

  const reloadSession = useCallback(() => {
    setSession(null);
    setSessionError("");
    setAttempt((value) => value + 1);
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    void getSession(controller.signal).then((data) => {
      if (!controller.signal.aborted) setSession(data);
    }).catch(() => {
      if (!controller.signal.aborted) setSessionError("No se pudo conectar con el servicio.");
    });
    return () => controller.abort();
  }, [attempt]);

  async function logout() {
    if (!session) return;
    setSessionError("");
    setLoggingOut(true);
    try {
      setSession(await signOut(session.csrf_token));
    } catch (error) {
      if (isSessionProblem(error)) {
        reloadSession();
      } else {
        setSessionError("No se pudo cerrar sesión. Inténtalo otra vez.");
      }
    } finally {
      setLoggingOut(false);
    }
  }

  if (!session) {
    return (
      <main className="login-shell">
        <section className="login-card">
          <h1>Sistema de Asistencia</h1>
          <p className={sessionError ? "form-error" : "summary"} role="status">
            {sessionError || "Cargando sesión…"}
          </p>
          {sessionError && <button type="button" onClick={reloadSession}>Volver a intentar</button>}
        </section>
      </main>
    );
  }

  if (!session.usuario) {
    return <LoginForm csrfToken={session.csrf_token} onSignIn={setSession} onSessionProblem={reloadSession} />;
  }

  return (
    <>
      <header className="app-header">
        <div className="app-header-content">
          <p className="product-name">Sistema de Asistencia</p>
          <button type="button" className="secondary-button" onClick={logout} disabled={loggingOut}>
            {loggingOut ? "Cerrando sesión…" : "Cerrar sesión"}
          </button>
        </div>
      </header>
      {sessionError && <p className="attendance-content form-error" role="alert">{sessionError}</p>}
      {session.usuario.rol === "trabajador" ? (
        <WorkerPage key={session.usuario.usuario} username={session.usuario.usuario}
          csrfToken={session.csrf_token} onSessionProblem={reloadSession} />
      ) : (
        <main className="attendance-content">
          <h1>Administración</h1>
          <p className="summary">La gestión administrativa está en preparación.</p>
        </main>
      )}
    </>
  );
}
