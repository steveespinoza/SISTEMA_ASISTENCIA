import type { MarkAttempt } from "./attendance-api";

const keyFor = (username: string) => "asistencia.marcacion-pendiente." + username;

export function getPendingMark(username: string): MarkAttempt | null {
  try {
    const value = JSON.parse(sessionStorage.getItem(keyFor(username)) ?? "null");
    if (
      value && (value.operacion === "entrada" || value.operacion === "salida") &&
      typeof value.clave_reintento === "string"
    ) {
      return value;
    }
  } catch {
    // Si el navegador bloquea el almacenamiento, la página conserva el reintento en memoria.
  }
  return null;
}

export function savePendingMark(username: string, attempt: MarkAttempt | null) {
  try {
    const key = keyFor(username);
    if (attempt) {
      sessionStorage.setItem(key, JSON.stringify(attempt));
    } else {
      sessionStorage.removeItem(key);
    }
  } catch {
    // El estado de la página permite reintentar mientras siga abierta.
  }
}
