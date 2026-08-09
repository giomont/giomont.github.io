/**
 * worker.js
 * ---------
 * Proxy pequeño (Cloudflare Worker / val.town, gratis) que los botones de
 * actualización del index.html llaman por fetch. Este worker guarda el
 * token de GitHub como SECRETO (nunca queda visible en el HTML público) y
 * dispara el workflow "actualizar_wegweiser.yml" con el modo elegido:
 *   - "all"      -> noticias + las cuatro listas
 *   - "noticias" -> solo noticias.json
 *   - "listas"   -> arví + colombia + guía + básico (banco rotativo de 100)
 *
 * El modo se puede mandar como query param (?modo=listas) o en el body
 * JSON de un POST ({ "modo": "listas" }). Si no se manda nada, es "all".
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
const MODOS_VALIDOS = ["all", "noticias", "listas"];

export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") {
      return new Response(null, { headers: corsHeaders() });
    }

    let modo = "all";
    try {
      const reqUrl = new URL(request.url);
      const qModo = reqUrl.searchParams.get("modo");
      if (qModo) modo = qModo;
      if (request.method === "POST") {
        const body = await request.json().catch(() => null);
        if (body && body.modo) modo = body.modo;
      }
    } catch (e) {
      // si algo falla al leer el modo, seguimos con "all"
    }
    if (!MODOS_VALIDOS.includes(modo)) modo = "all";

    const dispatchUrl = `https://api.github.com/repos/${OWNER}/${REPO}/actions/workflows/${WORKFLOW_FILE}/dispatches`;

    const resp = await fetch(dispatchUrl, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${env.GITHUB_TOKEN}`,
        "Accept": "application/vnd.github+json",
        "User-Agent": "wegweiser-worker",
      },
      body: JSON.stringify({ ref: "main", inputs: { modo } }),
    });

    const ok = resp.status === 204;
    return new Response(
      JSON.stringify({ ok, status: resp.status, modo }),
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
