import { requestJson, sendJson, type Shift } from "./attendance-api";

export type Site = { id: string; nombre: string };

export type WorkerDetails = { nombre: string; sede_id: string };
export type WorkerCredentials = { usuario: string; contrasena: string };
export type Worker = WorkerDetails & {
  id: string;
  usuario: string | null;
  activo: boolean;
};

export type Directory = { sedes: Site[]; trabajadores: Worker[] };

export type HistoryQuery = {
  desde: string;
  hasta: string;
  trabajador_id: string;
  sede_id: string;
  pagina: number;
};

export type HistoryPage = {
  jornadas: (Shift & { trabajador: string; trabajador_id: string; sede_id: string })[];
  pagina: number;
  hay_siguiente: boolean;
  zona_horaria: string;
};

export function getHistory(query: HistoryQuery, signal: AbortSignal) {
  const params = new URLSearchParams({
    desde: query.desde,
    hasta: query.hasta,
    pagina: String(query.pagina),
  });
  if (query.trabajador_id) params.set("trabajador_id", query.trabajador_id);
  if (query.sede_id) params.set("sede_id", query.sede_id);
  return requestJson<HistoryPage>("/api/admin/jornadas?" + params, { signal });
}

export function getDirectory(signal: AbortSignal) {
  return requestJson<Directory>("/api/admin", { signal });
}

export function saveSite(token: string, nombre: string, id?: string) {
  return id
    ? sendJson<Site>("/api/admin/sedes/" + id, token, { nombre }, "PATCH")
    : sendJson<Site>("/api/admin/sedes", token, { nombre });
}

export function createWorker(token: string, details: WorkerDetails & WorkerCredentials) {
  return sendJson<Worker>("/api/admin/trabajadores", token, details);
}

export function editWorker(token: string, id: string, details: WorkerDetails) {
  return sendJson<Worker>("/api/admin/trabajadores/" + id, token, details, "PATCH");
}

export function deactivateWorker(token: string, id: string) {
  return sendJson<Worker>("/api/admin/trabajadores/" + id + "/desactivar", token);
}
