import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "@fontsource-variable/inter";
import { App as SystemStatus } from "./App";
import { AttendanceApp } from "./AttendanceApp";
import "./styles.css";
import "./attendance.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    {window.location.pathname === "/estado" ? <SystemStatus /> : <AttendanceApp />}
  </StrictMode>,
);
