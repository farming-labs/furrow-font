// Serves farmjs.dev on localhost with Graft in place of Geist Sans and Geist
// Mono, to see the fonts on a real site. Every request is forwarded to
// farmjs.dev; only the Geist font files are answered from site/public/fonts,
// read on each request so a rebuild shows up on reload. Only GET and HEAD.
import { readFile } from "node:fs/promises";
import { createServer } from "node:http";

const PORT = Number(process.env.PORT ?? 4318);
const UPSTREAM = "https://farmjs.dev";
const FONTS = new URL("../site/public/fonts/", import.meta.url);
const local = `http://localhost:${PORT}`;

createServer(async (req, res) => {
  try {
    if (req.method !== "GET" && req.method !== "HEAD") {
      res.writeHead(405, { allow: "GET, HEAD" });
      res.end();
      return;
    }
    const file = decodeURIComponent((req.url ?? "/").split("?")[0].split("/").pop() ?? "");
    if (/geist/i.test(file) && !/pixel/i.test(file) && /\.woff2$/i.test(file)) {
      const name = /mono/i.test(file) ? "GraftMono-Variable.woff2" : "Graft-Variable.woff2";
      res.writeHead(200, { "content-type": "font/woff2", "cache-control": "no-store" });
      res.end(await readFile(new URL(name, FONTS)));
      return;
    }
    const upstream = await fetch(UPSTREAM + req.url, {
      method: req.method,
      headers: { accept: req.headers.accept ?? "*/*", "accept-language": "en" },
      redirect: "manual",
    });
    const headers = {};
    for (const [key, value] of upstream.headers) {
      // fetch already decoded the body, so its length and encoding no longer apply.
      if (
        [
          "content-encoding",
          "content-length",
          "transfer-encoding",
          "strict-transport-security",
        ].includes(key)
      )
        continue;
      headers[key] = key === "location" ? value.replace(UPSTREAM, local) : value;
    }
    headers["cache-control"] = "no-store";
    const type = upstream.headers.get("content-type") ?? "";
    let body = Buffer.from(await upstream.arrayBuffer());
    // Keep absolute links on this host so navigation stays inside the preview.
    if (/text\/html|javascript|text\/css|json/.test(type)) {
      body = Buffer.from(body.toString("utf8").replaceAll(UPSTREAM, local));
    }
    res.writeHead(upstream.status, headers);
    res.end(body);
  } catch (error) {
    res.writeHead(502, { "content-type": "text/plain" });
    res.end(`Proxy error: ${error.message}`);
  }
}).listen(PORT, () => console.log(`farmjs.dev with Graft: ${local}`));
