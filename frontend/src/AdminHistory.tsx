import { useEffect, useState, type FormEvent } from "react";
import { getHistory, type Directory, type HistoryPage, type HistoryQuery } from "./admin-api";
import { ApiProblem, isSessionProblem } from "./attendance-api";
import { companyTimeFormatter } from "./shift-format";
import { ShiftDetails } from "./ShiftDetails";

const periodFormatter = new Intl.DateTimeFormat("es-PE", { dateStyle: "medium", timeZone: "UTC" });

function workerLabel(name: string, username?: string | null): string {
  return username ? name + " (" + username + ")" : name;
}

type SearchResult =
  | { query: HistoryQuery; data: HistoryPage; error?: never }
  | { query: HistoryQuery; error: string; data?: never };

export function AdminHistory({ directory, onSessionProblem }: {
  directory: Directory;
  onSessionProblem: () => void;
}) {
  const [query, setQuery] = useState<HistoryQuery | null>(null);
  const [result, setResult] = useState<SearchResult | null>(null);
  const [formError, setFormError] = useState("");

  useEffect(() => {
    if (!query) return;
    const controller = new AbortController();
    void getHistory(query, controller.signal).then((data) => {
      if (!controller.signal.aborted) setResult({ query, data });
    }).catch((error: unknown) => {
      if (controller.signal.aborted) return;
      if (isSessionProblem(error)) {
        onSessionProblem();
      } else {
        setResult({
          query,
          error: error instanceof ApiProblem ? error.message : "No se pudo cargar el historial.",
        });
      }
    });
    return () => controller.abort();
  }, [query, onSessionProblem]);

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const fields = new FormData(event.currentTarget);
    const desde = String(fields.get("desde"));
    const hasta = String(fields.get("hasta"));
    if (desde > hasta) {
      setFormError("La fecha final debe ser igual o posterior a la fecha inicial.");
      return;
    }
    setFormError("");
    setQuery({
      desde, hasta, pagina: 1,
      trabajador_id: String(fields.get("trabajador_id")),
      sede_id: String(fields.get("sede_id")),
    });
  }

  const current = result && result.query === query ? result : null;
  const workers = new Map(directory.trabajadores.map((worker) => [worker.id, worker]));
  const selectedWorker = query?.trabajador_id ? workers.get(query.trabajador_id) : null;
  const selectedSite = query?.sede_id
    ? directory.sedes.find((site) => site.id === query.sede_id)?.nombre
    : "Todas las sedes";
  const formatter = current?.data ? companyTimeFormatter(current.data.zona_horaria) : null;

  return (
    <section className="admin-history" aria-labelledby="admin-history-title">
      <form className="admin-panel admin-form" onSubmit={submit} onChange={() => setFormError("")}>
        <h2 id="admin-history-title">Historial de asistencia</h2>
        <div className="history-filters">
          <div>
            <label htmlFor="history-from">Entrada desde</label>
            <input id="history-from" name="desde" type="date" min="0001-01-01" max="9999-12-30" required />
          </div>
          <div>
            <label htmlFor="history-to">Entrada hasta</label>
            <input id="history-to" name="hasta" type="date" min="0001-01-01" max="9999-12-30" required />
          </div>
          <div>
            <label htmlFor="history-worker">Trabajador</label>
            <select id="history-worker" name="trabajador_id">
              <option value="">Todos los trabajadores</option>
              {directory.trabajadores.map((worker) => (
                <option key={worker.id} value={worker.id}>{workerLabel(worker.nombre, worker.usuario)}</option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="history-site">Sede</label>
            <select id="history-site" name="sede_id">
              <option value="">Todas las sedes</option>
              {directory.sedes.map((site) => <option key={site.id} value={site.id}>{site.nombre}</option>)}
            </select>
          </div>
        </div>
        {formError && <p className="form-error" role="alert">{formError}</p>}
        <div className="admin-actions"><button>Consultar jornadas</button></div>
      </form>
      {!query && <p className="summary">Selecciona un período para consultar las jornadas.</p>}
      {query && (
        <>
          <p className="summary history-period">
            Entradas del {periodFormatter.format(new Date(query.desde))} al {periodFormatter.format(new Date(query.hasta))}
            {" · "}{selectedWorker ? workerLabel(selectedWorker.nombre, selectedWorker.usuario) : "Todos los trabajadores"}
            {" · "}{selectedSite}
            {current?.data && <> · {current.data.zona_horaria}</>}
          </p>
          {!current && <p className="summary" role="status">Cargando jornadas…</p>}
          {current?.error && (
            <>
              <p className="form-error" role="alert">{current.error}</p>
              <button type="button" className="secondary-button" onClick={() => setQuery({ ...query })}>
                Volver a intentar
              </button>
            </>
          )}
          {current?.data && formatter && (
            <>
              {current.data.jornadas.length === 0 ? (
                <p className="summary" role="status">No hay jornadas que coincidan con los filtros.</p>
              ) : (
                <ul className="shift-list">
                  {current.data.jornadas.map((shift) => (
                    <li className="shift-card" key={shift.id}>
                      <div className="shift-title">
                        <div>
                          <strong>{workerLabel(shift.trabajador, workers.get(shift.trabajador_id)?.usuario)}</strong>
                          <p className="site-name">{shift.sede}</p>
                        </div>
                        <span className="shift-state">{shift.salida ? "Cerrada" : "Abierta"}</span>
                      </div>
                      <ShiftDetails shift={shift} formatter={formatter} />
                    </li>
                  ))}
                </ul>
              )}
              {(query.pagina > 1 || current.data.hay_siguiente) && (
                <nav className="history-pagination" aria-label="Páginas de jornadas">
                  <button type="button" className="secondary-button" disabled={query.pagina === 1}
                    onClick={() => setQuery({ ...query, pagina: query.pagina - 1 })}>Anterior</button>
                  <span role="status">Página {query.pagina}</span>
                  <button type="button" className="secondary-button" disabled={!current.data.hay_siguiente}
                    onClick={() => setQuery({ ...query, pagina: query.pagina + 1 })}>Siguiente</button>
                </nav>
              )}
            </>
          )}
        </>
      )}
    </section>
  );
}
