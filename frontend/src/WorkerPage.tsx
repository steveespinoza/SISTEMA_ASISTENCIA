import { useEffect, useState } from "react";
import {
  ApiProblem,
  getAttendance,
  isSessionProblem,
  markAttendance,
  type AttendanceView,
  type MarkAttempt,
  type MarkResult,
  type Shift,
} from "./attendance-api";
import { getPendingMark, savePendingMark } from "./pending-mark";
import { companyTimeFormatter } from "./shift-format";
import { ShiftDetails } from "./ShiftDetails";

type Props = {
  username: string;
  csrfToken: string;
  onSessionProblem: () => void;
};

function History({ shifts, formatter }: { shifts: Shift[]; formatter: Intl.DateTimeFormat }) {
  return (
    <section className="history-section" aria-labelledby="history-title">
      <h2 id="history-title">Historial</h2>
      {shifts.length === 0 ? <p className="summary">Todavía no hay jornadas registradas.</p> : (
        <ul className="shift-list">
          {shifts.map((shift) => (
            <li className="shift-card" key={shift.id}>
              <div className="shift-title">
                <strong>{shift.sede}</strong>
                <span className="shift-state">{shift.salida ? "Cerrada" : "Abierta"}</span>
              </div>
              <ShiftDetails shift={shift} formatter={formatter} />
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export function WorkerPage({ username, csrfToken, onSessionProblem }: Props) {
  const [view, setView] = useState<AttendanceView | null>(null);
  const [pending, setPending] = useState(() => getPendingMark(username));
  const [confirmation, setConfirmation] = useState<MarkResult | null>(null);
  const [actionError, setActionError] = useState("");
  const [loadError, setLoadError] = useState("");
  const [refresh, setRefresh] = useState(0);
  const [busy, setBusy] = useState(false);
  const [timezone, setTimezone] = useState<string>();

  useEffect(() => {
    const controller = new AbortController();
    void getAttendance(controller.signal).then((data) => {
      if (!controller.signal.aborted) {
        setTimezone(data.zona_horaria);
        setView(data);
      }
    }).catch((error: unknown) => {
      if (controller.signal.aborted) return;
      if (isSessionProblem(error)) {
        onSessionProblem();
      } else {
        setLoadError(error instanceof ApiProblem ? error.message : "No se pudo cargar tu asistencia.");
      }
    });
    return () => controller.abort();
  }, [onSessionProblem, refresh]);

  function reload() {
    setLoadError("");
    setView(null);
    setRefresh((value) => value + 1);
  }

  function remember(attempt: MarkAttempt | null) {
    savePendingMark(username, attempt);
    setPending(attempt);
  }

  async function submitMark() {
    if (!view || busy || (!view.activo && !pending)) return;
    const openShift = view.jornada_abierta;
    const attempt: MarkAttempt = pending ?? {
      operacion: openShift ? "salida" : "entrada",
      clave_reintento: crypto.randomUUID(),
      jornada_id: openShift?.id,
    };
    remember(attempt);
    setBusy(true);
    setActionError("");
    setConfirmation(null);
    try {
      const result = await markAttendance(csrfToken, attempt);
      remember(null);
      setConfirmation(result);
      reload();
    } catch (error) {
      if (isSessionProblem(error)) {
        onSessionProblem();
      } else if (error instanceof ApiProblem && error.code &&
        ["request_rejected", "worker_forbidden", "attendance_conflict"].includes(error.code)) {
        remember(null);
        setActionError(error.message);
        reload();
      } else {
        setActionError("No pudimos confirmar la marcación. Vuelve a intentar la misma solicitud.");
      }
    } finally {
      setBusy(false);
    }
  }

  const formatter = companyTimeFormatter(timezone);
  const confirmationTime = confirmation?.operacion === "salida"
    ? confirmation.jornada.salida
    : confirmation?.jornada.entrada;

  return (
    <main className="attendance-content">
      <h1>Mi asistencia</h1>
      {confirmation && confirmationTime && (
        <p className="confirmation" role="status">
          {confirmation.operacion === "entrada" ? "Entrada registrada" : "Salida registrada"}
          {" · "}{formatter.format(new Date(confirmationTime))}
        </p>
      )}
      {actionError && <p className="form-error" role="alert">{actionError}</p>}
      {loadError && (
        <div className="load-error">
          <p className="form-error" role="alert">{loadError}</p>
          <button type="button" className="secondary-button" onClick={reload}>Volver a cargar</button>
        </div>
      )}
      {!view && !loadError && <p className="summary" role="status">Cargando asistencia…</p>}
      {view && (
        <>
          <section className="attendance-card" aria-labelledby="shift-title">
            <div>
              <p className="worker-name">{view.nombre}</p>
              <h2 id="shift-title">{view.jornada_abierta ? "Jornada abierta" : "Sin jornada abierta"}</h2>
              <p className="site-name">{view.jornada_abierta?.sede ?? view.sede}</p>
            </div>
            {!view.activo && <p className="form-error">Trabajador desactivado.</p>}
            {pending && !busy && !actionError && (
              <p className="summary" role="status">Tienes una marcación pendiente de confirmar.</p>
            )}
            {(view.activo || pending) && (
              <button type="button" onClick={submitMark} disabled={busy}>
                {busy ? "Enviando…" : pending ? "Reintentar " + pending.operacion :
                  view.jornada_abierta ? "Registrar salida" : "Registrar entrada"}
              </button>
            )}
          </section>
          <History shifts={view.jornadas} formatter={formatter} />
        </>
      )}
    </main>
  );
}
