import { StrictMode } from "react";
import ReactDOM from "react-dom/client";

import App from "@/app/App";
import { AppProvider } from "@/providers";

import "@/index.css";

ReactDOM.createRoot(
  document.getElementById("root")!,
).render(
  <StrictMode>
    <AppProvider>
      <App />
    </AppProvider>
  </StrictMode>,
);
