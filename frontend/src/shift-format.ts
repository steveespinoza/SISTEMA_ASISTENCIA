export function companyTimeFormatter(timeZone?: string) {
  return new Intl.DateTimeFormat("es-PE", {
    timeZone,
    dateStyle: "medium",
    timeStyle: "short",
    hourCycle: "h23",
  });
}
export const shiftStateLabel = {
  abierta: "Abierta",
  cerrada: "Cerrada",
  sin_salida: "Sin salida",
};
