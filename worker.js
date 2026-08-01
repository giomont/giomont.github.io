/**
 * worker.js
 * ---------
 * Proxy pequeño (Cloudflare Worker, gratis) que el botón "Actualizar
 * (giomont.github.io)" del index.html llama por fetch. Este worker
 * guarda el token de GitHub como SECRETO (nunca queda visible en el
 * HTML público) y dispara el workflow "actualizar_wegweiser.yml".
 *
 * Setup (una sola vez):
 *   1. dash.cloudflare.com -> Workers -> Create Worker -> pegar este código.
 *   2. Settings -> Variables -> agregar secreto: GITHUB_TOKEN
 *      (Personal Access Token con permiso "repo" / "Actions: write")
 *   3. Copiar la URL del worker (algo como
 *      https://wegweiser-trigger.tu-usuario.workers.dev)
 *   4. Poner esa URL en el botón del index.html (ver snippet_boton.html)
 */

const OWNER = "giomont";
const REPO = "giomont.github.io";
const WORKFLOW_FILE = "actualizar_wegweiser.yml";

export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") {
      return new Response(null, { headers: corsHeaders() });
    }

    const url = `https://api.github.com/repos/${OWNER}/${REPO}/actions/workflows/${WORKFLOW_FILE}/dispatches`;

    const resp = await fetch(url, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${env.GITHUB_TOKEN}`,
        "Accept": "application/vnd.github+json",
        "User-Agent": "wegweiser-worker",
      },
      body: JSON.stringify({ ref: "main" }),
    });

    const ok = resp.status === 204;
    return new Response(
      JSON.stringify({ ok, status: resp.status }),
      { headers: { ...corsHeaders(), "Content-Type": "application/json" } }
    );
  },
};

function corsHeaders() {
  return {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
  };
}
