export type User = {
  usuario: string;
  rol: "trabajador" | "administrador";
};

export type SessionInfo = {
  usuario: User | null;
  csrf_token: string;
};

export type Operation = "entrada" | "salida";

export type MarkAttempt = {
  operacion: Operation;
  clave_reintento: string;
  jornada_id?: string;
};

export type Shift = {
  id: string;
  sede: string;
  entrada: string;
  salida: string | null;
  tiene_foto_entrada?: boolean;
  tiene_foto_salida?: boolean;
  estado: "abierta" | "cerrada" | "sin_salida";
  duracion_segundos: number | null;
};

export type AttendanceView = {
  nombre: string;
  sede: string;
  activo: boolean;
  jornada_abierta: Shift | null;
  jornada_hoy: Shift | null;
  actualizar_en_ms: number;
  jornadas: Shift[];
  zona_horaria: string;
  requiere_foto: boolean;
};

export type MarkResult = {
  operacion: Operation;
  jornada: Shift;
};

export class ApiProblem extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly code?: string,
  ) {
    super(message);
  }
}

export async function requestJson<T>(path: string, options: RequestInit = {}, timeoutMs = 8000): Promise<T> {
  const timeout = AbortSignal.timeout(timeoutMs);
  const response = await fetch(path, {
    ...options,
    cache: "no-store",
    signal: options.signal ? AbortSignal.any([options.signal, timeout]) : timeout,
  });
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiProblem(
      body?.error ?? "El servicio no está disponible en este momento.",
      response.status,
      body?.codigo,
    );
  }
  if (body === null) {
    throw new Error("La respuesta del servidor está incompleta.");
  }
  return body as T;
}

export function sendJson<T>(
  path: string, csrfToken: string, payload?: object, method: "POST" | "PATCH" = "POST",
) {
  const headers: Record<string, string> = { "X-CSRF-Token": csrfToken };
  if (payload) {
    headers["Content-Type"] = "application/json";
  }
  return requestJson<T>(path, {
    method,
    headers,
    body: payload ? JSON.stringify(payload) : undefined,
  });
}

export function getSession(signal: AbortSignal) {
  return requestJson<SessionInfo>("/api/auth/sesion", { signal });
}

export function signIn(csrfToken: string, usuario: string, contrasena: string) {
  return sendJson<SessionInfo>("/api/auth/iniciar-sesion", csrfToken, { usuario, contrasena });
}

export function signOut(csrfToken: string) {
  return sendJson<SessionInfo>("/api/auth/cerrar-sesion", csrfToken);
}

export function getAttendance(signal: AbortSignal) {
  return requestJson<AttendanceView>("/api/asistencia", { signal });
}

export function markAttendance(csrfToken: string, attempt: MarkAttempt, photo: File | null) {
  if (photo) {
    const body = new FormData();
    body.set("operacion", attempt.operacion);
    body.set("clave_reintento", attempt.clave_reintento);
    if (attempt.jornada_id) body.set("jornada_id", attempt.jornada_id);
    body.set("foto", photo);
    return requestJson<MarkResult>("/api/asistencia/marcaciones", {
      method: "POST", headers: { "X-CSRF-Token": csrfToken }, body,
    }, 45_000);
  }
  return sendJson<MarkResult>("/api/asistencia/marcaciones", csrfToken, attempt);
}

export function isSessionProblem(error: unknown): boolean {
  return error instanceof ApiProblem && (
    error.code === "session_required" || error.code === "csrf_invalid"
  );
}
