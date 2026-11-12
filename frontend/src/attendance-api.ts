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
  duracion_segundos: number | null;
};

export type AttendanceView = {
  nombre: string;
  sede: string;
  activo: boolean;
  jornada_abierta: Shift | null;
  jornadas: Shift[];
  zona_horaria: string;
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

export async function requestJson<T>(path: string, options: RequestInit = {}): Promise<T> {
  const timeout = AbortSignal.timeout(8000);
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

export function markAttendance(csrfToken: string, attempt: MarkAttempt) {
  return sendJson<MarkResult>("/api/asistencia/marcaciones", csrfToken, attempt);
}

export function isSessionProblem(error: unknown): boolean {
  return error instanceof ApiProblem && (
    error.code === "session_required" || error.code === "csrf_invalid"
  );
}
