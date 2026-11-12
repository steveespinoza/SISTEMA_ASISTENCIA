import { useEffect, useState } from "react";
import { getSystemStatus, type SystemStatus } from "./system-status";

const messages = {
  checking: {
    summary: "Comprobando los servicios…",
    api: "Comprobando",
    database: "Comprobando",
  },
  online: {
    summary: "Los servicios están disponibles.",
    api: "Conectada",
    database: "Conectada",
  },
  "database-unavailable": {
    summary: "Comprueba que PostgreSQL esté en ejecución y vuelve a intentar.",
    api: "Conectada",
    database: "No disponible",
  },
  "api-unavailable": {
    summary: "Comprueba que la API esté en ejecución y vuelve a intentar.",
    api: "No disponible",
    database: "Sin comprobar",
  },
} satisfies Record<SystemStatus | "checking", Record<"summary" | "api" | "database", string>>;

export function App() {
  const [status, setStatus] = useState<SystemStatus | "checking">("checking");
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    void getSystemStatus(controller.signal).then((result) => {
      if (!controller.signal.aborted) {
        setStatus(result);
      }
    });
    return () => controller.abort();
  }, [attempt]);

  const message = messages[status];

  function checkAgain() {
    setStatus("checking");
    setAttempt((previous) => previous + 1);
  }

  return (
    <main className="system-panel">
      <header>
        <p className="product-name">Sistema de Asistencia</p>
        <h1>Estado del sistema</h1>
      </header>

      <div role="status">
        <p className="summary">{message.summary}</p>
        <dl className="services">
          <div>
            <dt>API</dt>
            <dd>{message.api}</dd>
          </div>
          <div>
            <dt>Base de datos</dt>
            <dd>{message.database}</dd>
          </div>
        </dl>
      </div>

      <button type="button" onClick={checkAgain} disabled={status === "checking"}>
        Volver a comprobar
      </button>
    </main>
  );
}
