import { useEffect, useState, type FormEvent } from "react";
import { AdminHistory } from "./AdminHistory";
import {
  createWorker,
  deactivateWorker,
  editWorker,
  getDirectory,
  saveSite,
  type Directory,
  type Site,
  type Worker,
  type WorkerCredentials,
  type WorkerDetails,
} from "./admin-api";
import { ApiProblem, isSessionProblem } from "./attendance-api";
import "./admin.css";

type Feedback = { kind: "error" | "success"; message: string; workerId?: string };
type Panel = "trabajadores" | "sedes" | "historial";

function upsert<T extends { id: string; nombre: string }>(items: T[], item: T): T[] {
  return [...items.filter(({ id }) => id !== item.id), item].sort(
    (first, second) => first.nombre.localeCompare(second.nombre, "es-PE"),
  );
}

function FeedbackMessage({ feedback }: { feedback: Feedback | null }) {
  if (!feedback) return null;
  return feedback.kind === "error"
    ? <p role="alert" className="form-error">{feedback.message}</p>
    : <p role="status" className="confirmation">{feedback.message}</p>;
}

function SitePanel({ sites, saving, onSave }: {
  sites: Site[];
  saving: boolean;
  onSave: (name: string, id?: string) => Promise<boolean>;
}) {
  const [editing, setEditing] = useState<Site | null>(null);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const name = String(new FormData(form).get("nombre"));
    if (await onSave(name, editing?.id)) {
      form.reset();
      setEditing(null);
    }
  }

  return (
    <div className="admin-grid">
      <form className="admin-panel admin-form" key={editing?.id ?? "new"} onSubmit={submit}>
        <h2>{editing ? "Editar sede" : "Nueva sede"}</h2>
        <label htmlFor="site-name">Nombre de la sede</label>
        <input id="site-name" name="nombre" defaultValue={editing?.nombre} autoFocus={!!editing}
          required maxLength={120} />
        <div className="admin-actions">
          <button disabled={saving}>{editing ? "Guardar sede" : "Crear sede"}</button>
          {editing && <button type="button" className="secondary-button" disabled={saving}
            onClick={() => setEditing(null)}>Cancelar</button>}
        </div>
      </form>
      <section className="admin-panel" aria-labelledby="site-list-title">
        <h2 id="site-list-title">Sedes registradas</h2>
        {sites.length === 0 ? <p className="summary">Aún no hay sedes registradas.</p> : (
          <ul className="directory-list">
            {sites.map((site) => (
              <li key={site.id}>
                <strong>{site.nombre}</strong>
                <button type="button" className="secondary-button" disabled={saving}
                  aria-label={"Editar sede " + site.nombre} onClick={() => setEditing(site)}>Editar</button>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}

function WorkerPanel({ directory, saving, feedback, onSave, onDeactivate, onOpenSites }: {
  directory: Directory;
  saving: boolean;
  feedback: Feedback | null;
  onSave: (save: (token: string) => Promise<Worker>, message: string) => Promise<boolean>;
  onDeactivate: (worker: Worker) => Promise<boolean>;
  onOpenSites: () => void;
}) {
  const [editing, setEditing] = useState<Worker | null>(null);
  const [confirmId, setConfirmId] = useState<string | null>(null);
  const siteNames = new Map(directory.sedes.map((site) => [site.id, site.nombre]));

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const fields = new FormData(form);
    const details: WorkerDetails = {
      nombre: String(fields.get("nombre")),
      sede_id: String(fields.get("sede_id")),
    };
    const workerId = editing?.id;
    let saved: boolean;
    if (workerId) {
      saved = await onSave((token) => editWorker(token, workerId, details), "Trabajador actualizado.");
    } else {
      const credentials: WorkerCredentials = {
        usuario: String(fields.get("usuario")),
        contrasena: String(fields.get("contrasena")),
      };
      saved = await onSave((token) => createWorker(token, { ...details, ...credentials }), "Trabajador registrado.");
    }
    if (saved) {
      form.reset();
      setEditing(null);
    }
  }

  async function confirmDeactivation(worker: Worker) {
    if (await onDeactivate(worker)) setConfirmId(null);
  }

  return (
    <div className="admin-grid">
      {directory.sedes.length === 0 ? (
        <section className="admin-panel" aria-labelledby="new-worker-title">
          <h2 id="new-worker-title">Nuevo trabajador</h2>
          <p className="summary">Crea una sede antes de registrar al primer trabajador.</p>
          <button type="button" onClick={onOpenSites}>Ir a sedes</button>
        </section>
      ) : (
        <form className="admin-panel admin-form" key={editing?.id ?? "new"} onSubmit={submit}>
          <h2>{editing ? "Editar trabajador" : "Nuevo trabajador"}</h2>
          <label htmlFor="worker-name">Nombre del trabajador</label>
          <input id="worker-name" name="nombre" defaultValue={editing?.nombre} autoFocus={!!editing}
            required maxLength={120} />
          <label htmlFor="worker-site">Sede</label>
          <select id="worker-site" name="sede_id" defaultValue={editing?.sede_id ?? ""} required>
            <option value="" disabled>Selecciona una sede</option>
            {directory.sedes.map((site) => <option key={site.id} value={site.id}>{site.nombre}</option>)}
          </select>
          {!editing && (
            <>
              <label htmlFor="worker-username">Usuario de acceso</label>
              <input id="worker-username" name="usuario" autoCapitalize="none" autoComplete="off"
                required maxLength={80} />
              <label htmlFor="worker-password">Contraseña inicial</label>
              <input id="worker-password" name="contrasena" type="password" autoComplete="new-password"
                required minLength={8} maxLength={256} />
            </>
          )}
          <div className="admin-actions">
            <button disabled={saving}>{editing ? "Guardar trabajador" : "Registrar trabajador"}</button>
            {editing && <button type="button" className="secondary-button" disabled={saving}
              onClick={() => setEditing(null)}>Cancelar</button>}
          </div>
        </form>
      )}
      <section className="admin-panel" aria-labelledby="worker-list-title">
        <h2 id="worker-list-title">Trabajadores registrados</h2>
        {directory.trabajadores.length === 0 ? <p className="summary">Aún no hay trabajadores registrados.</p> : (
          <ul className="directory-list">
            {directory.trabajadores.map((worker) => (
              <li key={worker.id}>
                <div>
                  <strong>{worker.nombre}</strong>
                  <p>{siteNames.get(worker.sede_id)} · {worker.usuario ?? "Sin cuenta"}</p>
                  <span className="directory-state">{worker.activo ? "Activo" : "Desactivado"}</span>
                </div>
                <div className="admin-actions">
                  <button type="button" className="secondary-button" disabled={saving}
                    aria-label={"Editar trabajador " + worker.nombre}
                    onClick={() => setEditing(worker)}>Editar</button>
                  {worker.activo && confirmId !== worker.id && (
                    <button type="button" className="secondary-button" disabled={saving}
                      aria-label={"Desactivar a " + worker.nombre}
                      onClick={() => setConfirmId(worker.id)}>Desactivar</button>
                  )}
                </div>
                {worker.activo && confirmId === worker.id && (
                  <div className="deactivation-prompt">
                    <p>¿Desactivar a {worker.nombre}? Su historial se conservará.</p>
                    <div className="admin-actions">
                      <button type="button" disabled={saving} onClick={() => void confirmDeactivation(worker)}>
                        Confirmar desactivación
                      </button>
                      <button type="button" className="secondary-button" disabled={saving}
                        onClick={() => setConfirmId(null)}>Cancelar</button>
                    </div>
                  </div>
                )}
                {feedback?.workerId === worker.id && (feedback.kind === "success" || confirmId === worker.id) &&
                  <FeedbackMessage feedback={feedback} />}
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}

export function AdminPage({ csrfToken, onSessionProblem }: {
  csrfToken: string;
  onSessionProblem: () => void;
}) {
  const [panel, setPanel] = useState<Panel>("trabajadores");
  const [directory, setDirectory] = useState<Directory | null>(null);
  const [loadError, setLoadError] = useState("");
  const [attempt, setAttempt] = useState(0);
  const [saving, setSaving] = useState(false);
  const [feedback, setFeedback] = useState<Feedback | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    void getDirectory(controller.signal).then((data) => {
      if (!controller.signal.aborted) setDirectory(data);
    }).catch((error: unknown) => {
      if (controller.signal.aborted) return;
      if (isSessionProblem(error)) onSessionProblem();
      else setLoadError(error instanceof ApiProblem ? error.message : "No se pudo cargar la administración.");
    });
    return () => controller.abort();
  }, [attempt, onSessionProblem]);

  function openPanel(next: Panel) {
    if (next === panel) return;
    setFeedback(null);
    setPanel(next);
  }

  async function save<T>(
    action: () => Promise<T>, apply: (data: Directory, item: T) => Directory, message: string, workerId?: string,
  ) {
    if (saving) return false;
    setSaving(true);
    setFeedback(null);
    try {
      const item = await action();
      setDirectory((data) => data && apply(data, item));
      setFeedback({ kind: "success", message, workerId });
      return true;
    } catch (error) {
      if (isSessionProblem(error)) {
        onSessionProblem();
      } else {
        setFeedback({
          kind: "error",
          workerId,
          message: error instanceof ApiProblem
            ? error.message
            : "No se pudo confirmar el cambio. Actualiza la página para comprobarlo.",
        });
      }
      return false;
    } finally {
      setSaving(false);
    }
  }

  function saveWorker(action: (token: string) => Promise<Worker>, message: string, workerId?: string) {
    return save(() => action(csrfToken), (data, worker) => ({
      ...data, trabajadores: upsert(data.trabajadores, worker),
    }), message, workerId);
  }

  return (
    <main className="attendance-content admin-content">
      <h1>Administración</h1>
      {loadError && (
        <>
          <p role="alert" className="form-error">{loadError}</p>
          <button type="button" className="secondary-button" onClick={() => {
            setLoadError("");
            setAttempt((value) => value + 1);
          }}>Volver a cargar</button>
        </>
      )}
      {!directory && !loadError && <p role="status" className="summary">Cargando administración…</p>}
      {directory && (
        <>
          <nav className="admin-nav" aria-label="Gestión administrativa">
            <button type="button" className="secondary-button" disabled={saving}
              aria-pressed={panel === "trabajadores"} onClick={() => openPanel("trabajadores")}>Trabajadores</button>
            <button type="button" className="secondary-button" disabled={saving}
              aria-pressed={panel === "sedes"} onClick={() => openPanel("sedes")}>Sedes</button>
            <button type="button" className="secondary-button" disabled={saving}
              aria-pressed={panel === "historial"} onClick={() => openPanel("historial")}>Historial</button>
          </nav>
          <FeedbackMessage feedback={feedback?.workerId ? null : feedback} />
          {panel === "sedes" && (
            <SitePanel sites={directory.sedes} saving={saving} onSave={(name, id) => save(
              () => saveSite(csrfToken, name, id),
              (data, site) => ({ ...data, sedes: upsert(data.sedes, site) }),
              id ? "Sede actualizada." : "Sede registrada.",
            )} />
          )}
          {panel === "trabajadores" && (
            <WorkerPanel directory={directory} saving={saving} feedback={feedback} onSave={saveWorker}
              onDeactivate={(worker) => saveWorker(
                (token) => deactivateWorker(token, worker.id), "Trabajador desactivado.", worker.id,
              )}
              onOpenSites={() => openPanel("sedes")} />
          )}
          {panel === "historial" && <AdminHistory directory={directory} onSessionProblem={onSessionProblem} />}
        </>
      )}
    </main>
  );
}
