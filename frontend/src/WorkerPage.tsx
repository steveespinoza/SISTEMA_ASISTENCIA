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
import { companyTimeFormatter, shiftStateLabel } from "./shift-format";
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
                <span className="shift-state">{shiftStateLabel[shift.estado]}</span>
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
  const [photo, setPhoto] = useState<{ file: File; preview: string } | null>(null);
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

  useEffect(() => {
    if (!view) return;
    const timer = window.setTimeout(() => {
      setView(null);
      setConfirmation(null);
      setRefresh((value) => value + 1);
    }, Math.max(100, view.actualizar_en_ms));
    return () => window.clearTimeout(timer);
  }, [view]);

  useEffect(() => {
    if (!photo) return;
    return () => URL.revokeObjectURL(photo.preview);
  }, [photo]);

  function reload() {
    setLoadError("");
    setView(null);
    setRefresh((value) => value + 1);
  }

  function remember(attempt: MarkAttempt | null) {
    savePendingMark(username, attempt);
    setPending(attempt);
  }

  const canMark = view?.activo && (!view.jornada_hoy || view.jornada_abierta !== null);

  async function submitMark() {
    if (!view || busy || (!pending && !canMark)) return;
    if (view.requiere_foto && !pending && !photo) return;
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
      const result = await markAttendance(csrfToken, attempt, view.requiere_foto ? photo?.file ?? null : null);
      remember(null);
      setPhoto(null);
      setConfirmation(result);
      reload();
    } catch (error) {
      if (isSessionProblem(error)) {
        onSessionProblem();
      } else if (error instanceof ApiProblem && error.code &&
        ["request_rejected", "worker_forbidden", "attendance_conflict"].includes(error.code)) {
        remember(null);
        setPhoto(null);
        setActionError(error.message);
        reload();
      } else if (error instanceof ApiProblem && error.code === "photo_required") {
        setActionError("La marcación sigue pendiente. Agrega la foto y vuelve a intentar.");
      } else if (error instanceof ApiProblem && error.code === "invalid_photo") {
        setPhoto(null);
        setActionError(error.message);
      } else if (error instanceof ApiProblem && error.code === "photo_storage_unavailable") {
        setActionError(error.message);
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
              <h2 id="shift-title">{view.jornada_abierta ? "Jornada abierta" :
                view.jornada_hoy ? "Asistencia de hoy registrada" : "Sin jornada abierta"}</h2>
              <p className="site-name">{view.jornada_hoy?.sede ?? view.sede}</p>
            </div>
            {!view.activo && <p className="form-error">Trabajador desactivado.</p>}
            {pending && !busy && !actionError && (
              <p className="summary" role="status">Tienes una marcación pendiente de confirmar.</p>
            )}
            {view.requiere_foto && (pending || canMark) && (
              <div className="mark-photo">
                <label htmlFor="mark-photo">Foto de {pending?.operacion ?? (view.jornada_abierta ? "salida" : "entrada")}</label>
                <input
                  id="mark-photo"
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  capture="user"
                  disabled={busy}
                  onChange={(event) => {
                    const selected = event.currentTarget.files?.[0];
                    if (!selected) return;
                    event.currentTarget.value = "";
                    if (selected.size > 12 * 1024 * 1024) {
                      setPhoto(null);
                      setActionError("La foto supera el límite de 12 MB.");
                      return;
                    }
                    setPhoto({ file: selected, preview: URL.createObjectURL(selected) });
                    setActionError("");
                  }}
                />
                {photo && <img src={photo.preview} alt="Vista previa de la foto de marcación" />}
              </div>
            )}
            {(pending || canMark) && (
              <button type="button" onClick={submitMark}
                disabled={busy || (view.requiere_foto && !pending && !photo)}>
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
