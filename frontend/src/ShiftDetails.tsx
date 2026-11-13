import type { Shift } from "./attendance-api";

function durationLabel(seconds: number): string {
  if (seconds < 60) return seconds + " s";
  const minutes = Math.floor(seconds / 60);
  return Math.floor(minutes / 60) + " h " + (minutes % 60) + " min";
}

export function ShiftDetails({ shift, formatter }: { shift: Shift; formatter: Intl.DateTimeFormat }) {
  return (
    <dl className="shift-details">
      <div>
        <dt>Entrada</dt>
        <dd>{formatter.format(new Date(shift.entrada))}</dd>
        {shift.tiene_foto_entrada && <dd><a href={`/api/asistencia/jornadas/${shift.id}/fotos/entrada`}
          target="_blank" rel="noreferrer">Ver foto de entrada</a></dd>}
      </div>
      {shift.estado !== "sin_salida" && (
        <div>
          <dt>Salida</dt>
          <dd>{shift.salida ? formatter.format(new Date(shift.salida)) : "Pendiente"}</dd>
          {shift.tiene_foto_salida && <dd><a href={`/api/asistencia/jornadas/${shift.id}/fotos/salida`}
            target="_blank" rel="noreferrer">Ver foto de salida</a></dd>}
        </div>
      )}
      {shift.duracion_segundos !== null && (
        <div><dt>Duración</dt><dd>{durationLabel(shift.duracion_segundos)}</dd></div>
      )}
    </dl>
  );
}
