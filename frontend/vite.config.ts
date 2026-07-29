import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import tsconfigPaths from "vite-tsconfig-paths";
import path from "path";
import https from "node:https";
import type { IncomingMessage } from "node:http";

const host = process.env.TAURI_DEV_HOST;

/**
 * Why a custom middleware instead of server.proxy?
 *
 * Vite's http-proxy drops the response body when APIM returns
 * transfer-encoding: chunked with no content-type. response.text() returns ""
 * even though the status is 200. Node's native https.request has no such bug —
 * it collects every byte and we forward them with an explicit content-length,
 * giving the browser a well-formed HTTP response every time.
 *
 * Path matching note: server.middlewares.use(path, fn) strips the prefix before
 * calling fn, so req.url becomes "/" inside. We register without a path and
 * check req.url ourselves to avoid that pitfall.
 */
function buildApimMiddleware(apimEndpoint: string) {
  const parsed = new URL(apimEndpoint);

  return function apimMiddleware(
    req: IncomingMessage,
    res: { writeHead: Function; end: Function; headersSent: boolean },
    next: () => void
  ) {
    if (!req.url?.startsWith("/apim-proxy")) {
      next();
      return;
    }

    const reqChunks: Buffer[] = [];
    req.on("data", (c: Buffer) => reqChunks.push(c));
    req.on("end", () => {
      const reqBody = Buffer.concat(reqChunks);

      const apiKey = req.headers["api-key"];
      const forwardHeaders: Record<string, string> = {
        "content-type": "application/json",
        "content-length": String(reqBody.length),
      };
      if (typeof apiKey === "string") {
        forwardHeaders["api-key"] = apiKey;
      }

      const options: https.RequestOptions = {
        hostname: parsed.hostname,
        port: Number(parsed.port) || 443,
        path: parsed.pathname + parsed.search,
        method: "POST",
        headers: forwardHeaders,
      };

      const upstream = https.request(options, (upstreamRes: IncomingMessage) => {
        const resChunks: Buffer[] = [];
        upstreamRes.on("data", (c: Buffer) => resChunks.push(c));
        upstreamRes.on("end", () => {
          const body = Buffer.concat(resChunks);
          const status = upstreamRes.statusCode ?? 502;
          console.log(`[apim-proxy] ← ${status} ${body.length} bytes`);

          // Strip hop-by-hop headers that corrupt the browser's fetch body reader.
          // Mirrors the Python proxy: drop connection, transfer-encoding, content-encoding.
          const STRIP = new Set(["connection", "transfer-encoding", "content-encoding", "keep-alive"]);
          const responseHeaders: Record<string, string> = {
            "content-type": "application/json",
            "content-length": String(body.length),
            "access-control-allow-origin": "*",
          };
          for (const [k, v] of Object.entries(upstreamRes.headers)) {
            if (!STRIP.has(k.toLowerCase()) && typeof v === "string") {
              responseHeaders[k] = v;
            }
          }

          res.writeHead(status, responseHeaders);
          res.end(body);
        });
      });

      upstream.on("error", (err: Error) => {
        console.error("[apim-proxy] upstream error:", err.message);
        if (!res.headersSent) {
          res.writeHead(502, { "content-type": "application/json" });
        }
        res.end(JSON.stringify({ error: err.message }));
      });

      upstream.write(reqBody);
      upstream.end();
    });
  };
}

// https://vite.dev/config/
export default defineConfig(async ({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const apimEndpoint = env.VITE_APIM_ENDPOINT;

  if (apimEndpoint) {
    console.log(`[apim-proxy] /apim-proxy → ${new URL(apimEndpoint).origin}`);
  }

  return {
    plugins: [
      react(),
      tsconfigPaths(),
      apimEndpoint
        ? {
            name: "apim-proxy",
            configureServer(server: { middlewares: { use: Function } }) {
              server.middlewares.use(buildApimMiddleware(apimEndpoint));
            },
          }
        : null,
    ],

    test: {
      environment: "jsdom",
      globals: true,
      setupFiles: ["./src/tests/setup.ts"],
    },

    resolve: {
      alias: {
        "@": path.resolve(__dirname, "./src"),
      },
    },

    clearScreen: false,
    server: {
      port: 1420,
      strictPort: true,
      host: host || false,
      hmr: host
        ? {
            protocol: "ws",
            host,
            port: 1421,
          }
        : undefined,
      watch: {
        ignored: ["**/src-tauri/**"],
      },
    },
  };
});
