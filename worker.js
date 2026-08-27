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
 * También soporta una segunda acción, usada por el botón "✨ 3 frases
 * nuevas" del juego de vocabulario: POST { "accion": "agregarFrase",
 * "banco": "arvi"|"colombia"|"guia"|"basico", "frase": "...", "categoria": "..." }
 * Esto edita generar.py directamente (agrega la frase al banco fuente),
 * para que quede en el ciclo de rotación para siempre, no solo en el JSON
 * del día (que se sobreescribe en cada corrida).
 *
 * Setup (una sola vez):
 *   1. dash.cloudflare.com -> Workers -> Create Worker -> pegar este código.
 *   2. Settings -> Variables -> agregar secreto: GITHUB_TOKEN
 *      (Personal Access Token con permiso "repo" / "Actions: write" y
 *      "Contents: write" — este último es necesario para el endpoint
 *      "agregarFrase" que edita generar.py directamente)
 *   3. Copiar la URL del worker (algo como
 *      https://wegweiser-trigger.tu-usuario.workers.dev)
 *   4. Poner esa URL en el botón del index.html (ver snippet_boton.html)
 */

const OWNER = "giomont";
const REPO = "giomont.github.io";
const WORKFLOW_FILE = "actualizar_wegweiser.yml";
const GENERAR_PATH = "generar.py";
const MODOS_VALIDOS = ["all", "noticias", "listas"];

// Bancos a los que se les puede agregar una frase nueva desde el juego de
// vocabulario. "tupla:true" significa que la lista guarda (texto, categoría)
// en vez de solo el texto (así es GUIA_PHRASES).
const BANCOS = {
  arvi:     { const_name: "ARVI_PHRASES",           tupla: false },
  colombia: { const_name: "COLOMBIA_PHRASES",       tupla: false },
  guia:     { const_name: "GUIA_PHRASES",           tupla: true  },
  basico:   { const_name: "ALEMAN_BASICO_PHRASES",  tupla: false },
};

export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") {
      return new Response(null, { headers: corsHeaders() });
    }

    let body = null;
    if (request.method === "POST") {
      body = await request.json().catch(() => null);
    }

    // ---- Acción 2: agregar una frase generada por el jugador al banco ----
    if (body && body.accion === "agregarFrase") {
      return manejarAgregarFrase(body, env);
    }

    // ---- Acción 1 (default): disparar el workflow de regeneración ----
    let modo = "all";
    try {
      const reqUrl = new URL(request.url);
      const qModo = reqUrl.searchParams.get("modo");
      if (qModo) modo = qModo;
      if (body && body.modo) modo = body.modo;
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

// ---------------------------------------------------------------------------
// Agregar frase: lee generar.py, inserta la frase nueva justo antes del `]`
// que cierra el banco correspondiente, y commitea el archivo actualizado.
// Así, la próxima vez que corra generar.py (manual, cron o botón ☁️🔄), la
// frase entra al ciclo de rotación como una más del banco de 100+.
// ---------------------------------------------------------------------------
async function manejarAgregarFrase(body, env) {
  const { banco, frase, categoria } = body;
  const cfg = BANCOS[banco];
  if (!cfg || !frase || typeof frase !== "string") {
    return jsonResp({ ok: false, error: "Banco o frase inválidos." }, 400);
  }

  const contentsUrl = `https://api.github.com/repos/${OWNER}/${REPO}/contents/${GENERAR_PATH}`;
  const ghHeaders = {
    "Authorization": `Bearer ${env.GITHUB_TOKEN}`,
    "Accept": "application/vnd.github+json",
    "User-Agent": "wegweiser-worker",
  };

  try {
    // 1) Leer generar.py actual (contenido + sha, necesarios para el PUT)
    const getResp = await fetch(contentsUrl + "?ref=main", { headers: ghHeaders });
    if (!getResp.ok) {
      return jsonResp({ ok: false, error: `No se pudo leer generar.py (status ${getResp.status})` }, 502);
    }
    const fileData = await getResp.json();
    const texto = b64DecodeUnicode(fileData.content);

    // 2) Ubicar el banco (p.ej. "ARVI_PHRASES = [ ... \n]") e insertar la
    //    frase nueva justo antes del "]" que lo cierra.
    const inicioMarcador = `${cfg.const_name} = [`;
    const inicioIdx = texto.indexOf(inicioMarcador);
    if (inicioIdx === -1) {
      return jsonResp({ ok: false, error: `No se encontró ${cfg.const_name} en generar.py` }, 500);
    }
    const cierreIdx = texto.indexOf("\n]", inicioIdx);
    if (cierreIdx === -1) {
      return jsonResp({ ok: false, error: `No se encontró el cierre de ${cfg.const_name}` }, 500);
    }

    const fraseEscapada = frase.replace(/\\/g, "\\\\").replace(/"/g, '\\"');
    const lineaNueva = cfg.tupla
      ? `    ("${fraseEscapada}", "${(categoria || "Vokabular").replace(/"/g, '\\"')}"),\n`
      : `    "${fraseEscapada}",\n`;

    const nuevoTexto = texto.slice(0, cierreIdx + 1) + lineaNueva + texto.slice(cierreIdx + 1);

    // 3) Commitear el archivo actualizado.
    const putResp = await fetch(contentsUrl, {
      method: "PUT",
      headers: { ...ghHeaders, "Content-Type": "application/json" },
      body: JSON.stringify({
        message: `Agregar frase al banco ${banco} desde el juego de vocabulario`,
        content: b64EncodeUnicode(nuevoTexto),
        sha: fileData.sha,
        branch: "main",
      }),
    });

    if (!putResp.ok) {
      const err = await putResp.text();
      return jsonResp({ ok: false, error: `No se pudo commitear (status ${putResp.status}): ${err}` }, 502);
    }

    return jsonResp({ ok: true, banco });
  } catch (e) {
    return jsonResp({ ok: false, error: String(e) }, 500);
  }
}

function jsonResp(obj, status) {
  return new Response(JSON.stringify(obj), {
    status: status || 200,
    headers: { ...corsHeaders(), "Content-Type": "application/json" },
  });
}

// Base64 <-> UTF-8 (atob/btoa nativos solo manejan Latin1; esto permite
// que letras como ä ö ü é ñ sobrevivan el viaje ida y vuelta).
function b64DecodeUnicode(str) {
  return decodeURIComponent(
    atob(str)
      .split("")
      .map((c) => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
      .join("")
  );
}

function b64EncodeUnicode(str) {
  return btoa(
    encodeURIComponent(str).replace(/%([0-9A-F]{2})/g, (match, p1) =>
      String.fromCharCode("0x" + p1)
    )
  );
}

function corsHeaders() {
  return {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
  };
}
