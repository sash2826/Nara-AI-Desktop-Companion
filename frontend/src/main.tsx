import React from "react";
import ReactDOM from "react-dom/client";
import { getCurrentWindow } from "@tauri-apps/api/window";
import App from "./App";
import { OrbWindow } from "./windows/orb/OrbWindow";
import "./styles/globals.css";

// Determine which window we're running in before rendering.
// The orb WebviewWindow is created with label "orb" in lib.rs.
const windowLabel = getCurrentWindow().label;

// The global CSS sets body { background-color: hsl(var(--background)) } which
// paints the orb window black. Override html+body to transparent before React
// mounts so the Tauri transparent window actually shows through.
if (windowLabel === "orb") {
  const style = document.createElement("style");
  style.textContent = `
    html, body, #root {
      background: transparent !important;
      overflow: visible !important;
    }
  `;
  document.head.appendChild(style);
}

const root = document.getElementById("root") as HTMLElement;

ReactDOM.createRoot(root).render(
  <React.StrictMode>{windowLabel === "orb" ? <OrbWindow /> : <App />}</React.StrictMode>
);
