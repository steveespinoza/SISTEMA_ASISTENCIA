import { requestJson, sendJson } from "./attendance-api";

export type Site = { id: string; nombre: string };

export type WorkerDetails = { nombre: string; sede_id: string };
export type WorkerCredentials = { usuario: string; contrasena: string };
export type Worker = WorkerDetails & {
  id: string;
  usuario: string | null;
  activo: boolean;
};

export type Directory = { sedes: Site[]; trabajadores: Worker[] };

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
