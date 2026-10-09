const REPOSITORY_URL = "https://github.com/elprofedelabata/curriculo-lomloe";
const STAGES = [
  ["infantil", "Infantil"],
  ["primaria", "Primaria"],
  ["eso", "ESO"],
  ["bachillerato", "Bachillerato"],
  ["cfgb", "CFGB"],
];
const STAGE_LONG_NAMES = {
  infantil: "Educación Infantil",
  primaria: "Educación Primaria",
  eso: "Educación Secundaria Obligatoria",
  bachillerato: "Bachillerato",
  cfgb: "Ciclos Formativos de Grado Básico",
};

const main = document.querySelector("#contenido");
const params = new URLSearchParams(location.search);
const state = {
  territory: params.get("territorio") || "es-an",
  stage: params.get("etapa") || null,
  matter: params.get("materia") || null,
  query: "",
};

boot().catch(showError);

async function boot() {
  const response = await fetch("catalogo.json");
  if (!response.ok) throw new Error(`No se pudo cargar el catálogo (HTTP ${response.status}).`);
  const catalog = await response.json();

  if (!catalog.progreso.some((item) => item.territorio === state.territory)) {
    state.territory = "es-an";
  }
  if (state.stage && !STAGES.some(([code]) => code === state.stage)) {
    state.stage = null;
  }

  renderShell(catalog);
  bindEvents(catalog);
  renderSelection(catalog);

  if (state.matter) {
    requestAnimationFrame(() => {
      document.querySelector(`[data-matter="${cssEscape(state.matter)}"]`)?.scrollIntoView({ block: "center" });
    });
  }
}

function renderShell(catalog) {
  const completed = catalog.progreso.reduce(
    (total, territory) => total + Object.values(territory.etapas).filter((stage) => stage.estado === "completo").length,
    0,
  );

  main.innerHTML = `
    <section class="hero">
      <div>
        <p class="eyebrow">Proyecto abierto</p>
        <h1>El currículo LOMLOE,<br><span>enlaces claros y JSON directo.</span></h1>
        <p>Selecciona una comunidad y una etapa. Encontrarás cada currículo junto a su fuente oficial, sus incidencias y el archivo listo para usar.</p>
      </div>
      <dl aria-label="Resumen del proyecto">
        <div><dt>${catalog.progreso.length}</dt><dd>comunidades</dd></div>
        <div><dt>${catalog.materias.length}</dt><dd>currículos</dd></div>
        <div><dt>${completed}</dt><dd>etapas completas</dd></div>
      </dl>
    </section>

    <section class="explorer" id="explorar">
      <div class="section-heading">
        <p class="step">1</p>
        <div>
          <h2>Elige una comunidad</h2>
          <p>El estado de cada una se irá actualizando a medida que incorporemos sus currículos.</p>
        </div>
      </div>
      <div class="community-grid" id="community-list">
        ${catalog.progreso.map((territory) => communityButton(catalog, territory)).join("")}
      </div>

      <div id="selection"></div>
    </section>

    <section class="project-section" id="proyecto">
      <div class="section-heading">
        <p class="step">i</p>
        <div>
          <h2>Qué acompaña a cada currículo</h2>
          <p>Los datos no se publican aislados: conservamos su procedencia y explicamos las decisiones de revisión.</p>
        </div>
      </div>
      <div class="project-cards">
        <article><strong>JSON reutilizable</strong><p>Un archivo estable por materia, accesible sin cuenta ni autenticación.</p></article>
        <article><strong>Fuente oficial</strong><p>Enlace al boletín, páginas exactas y copia del PDF usado en la extracción.</p></article>
        <article><strong>Revisión transparente</strong><p>Las discrepancias detectadas y su resolución se documentan públicamente.</p></article>
      </div>
      <div class="project-links">
        <a href="catalogo.json">Catálogo completo en JSON ↗</a>
        <a href="schemas/materia.schema.json">Esquema de los datos ↗</a>
        <a href="${REPOSITORY_URL}/blob/main/INCIDENCIAS.md">Registro de incidencias ↗</a>
        <a href="${REPOSITORY_URL}">Repositorio en GitHub ↗</a>
      </div>
    </section>
  `;
}

function bindEvents(catalog) {
  main.addEventListener("click", (event) => {
    const community = event.target.closest("[data-territory]");
    if (community) {
      state.territory = community.dataset.territory;
      state.stage = null;
      state.matter = null;
      state.query = "";
      updateUrl();
      renderSelection(catalog);
      document.querySelector("#stages")?.scrollIntoView({ behavior: "smooth", block: "start" });
      return;
    }

    const stage = event.target.closest("[data-stage]");
    if (stage) {
      state.stage = stage.dataset.stage;
      state.matter = null;
      state.query = "";
      updateUrl();
      renderSelection(catalog);
      document.querySelector("#results")?.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  });

  main.addEventListener("input", (event) => {
    if (event.target.matches("[data-role='matter-search']")) {
      state.query = event.target.value;
      renderMatterList(catalog);
    }
  });
}

function renderSelection(catalog) {
  document.querySelectorAll("[data-territory]").forEach((button) => {
    const selected = button.dataset.territory === state.territory;
    button.classList.toggle("is-selected", selected);
    button.setAttribute("aria-pressed", String(selected));
  });

  const territory = catalog.progreso.find((item) => item.territorio === state.territory);
  const container = document.querySelector("#selection");
  if (!territory) {
    container.innerHTML = "";
    return;
  }

  container.innerHTML = `
    <section class="stage-section" id="stages">
      <div class="section-heading compact">
        <p class="step">2</p>
        <div>
          <p class="overline">${escapeHtml(territory.nombre)}</p>
          <h2>Elige una etapa</h2>
        </div>
      </div>
      <div class="stage-grid">
        ${STAGES.map(([code, label]) => stageButton(catalog, territory, code, label)).join("")}
      </div>
    </section>
    <section class="results-section" id="results" aria-live="polite"></section>
  `;

  if (!state.stage) {
    document.querySelector("#results").innerHTML = `
      <div class="prompt">
        <span aria-hidden="true">↑</span>
        <p>Selecciona una etapa para ver sus currículos y documentos.</p>
      </div>
    `;
    return;
  }

  renderResults(catalog, territory);
}

function renderResults(catalog, territory) {
  const progress = territory.etapas[state.stage];
  const matters = catalog.materias.filter(
    (item) => item.territorio === territory.territorio && item.etapa === state.stage,
  );
  const documents = stageDocuments(catalog, territory.territorio, state.stage);
  const incidents = catalog.incidencias.filter(
    (item) => item.territorio === territory.territorio && item.etapa === state.stage,
  );
  const stageName = STAGE_LONG_NAMES[state.stage];

  document.querySelector("#results").innerHTML = `
    <div class="results-heading">
      <div>
        <p class="overline">${escapeHtml(territory.nombre)}</p>
        <h2>${escapeHtml(stageName)}</h2>
        <p>${resultDescription(progress, matters, documents)}</p>
      </div>
      ${matters.length ? `<div class="result-total"><strong>${matters.length}</strong><span>materias</span></div>` : ""}
    </div>

    ${matters.length ? `
      <div class="list-toolbar">
        <label>
          <span class="sr-only">Buscar una materia</span>
          <input data-role="matter-search" type="search" placeholder="Buscar materia…" value="${escapeHtml(state.query)}" autocomplete="off">
        </label>
        <span id="match-count"></span>
      </div>
      <div class="curriculum-list" id="matter-list"></div>
    ` : emptyStage(progress)}

    ${documents.length ? `
      <section class="documents">
        <div class="subheading">
          <h3>Documentos oficiales</h3>
          <p>Normativa recopilada para esta etapa.</p>
        </div>
        <div class="document-list">${documents.map((document) => documentCard(document, territory.territorio)).join("")}</div>
      </section>
    ` : ""}

    ${incidents.length ? `
      <p class="stage-note">
        Esta etapa tiene ${incidents.length} ${incidents.length === 1 ? "incidencia revisada" : "incidencias revisadas"}.
        <a href="${REPOSITORY_URL}/blob/main/INCIDENCIAS.md">Ver el informe completo ↗</a>
      </p>
    ` : ""}
  `;

  renderMatterList(catalog);
}

function renderMatterList(catalog) {
  const list = document.querySelector("#matter-list");
  if (!list) return;

  const query = normalize(state.query);
  const matters = catalog.materias.filter((item) =>
    item.territorio === state.territory
    && item.etapa === state.stage
    && (!query || normalize(`${item.nombre} ${item.codigo || ""}`).includes(query))
  );
  const count = document.querySelector("#match-count");
  count.textContent = `${matters.length} ${matters.length === 1 ? "resultado" : "resultados"}`;
  list.innerHTML = matters.length
    ? matters.map((matter) => matterCard(catalog, matter)).join("")
    : `<div class="empty-search">No hay materias que coincidan con la búsqueda.</div>`;
}

function communityButton(catalog, territory) {
  const count = catalog.materias.filter((item) => item.territorio === territory.territorio).length;
  const hasSources = Object.values(territory.etapas).some((item) => item.estado === "fuentes");
  const status = count
    ? `<span class="available">${count} currículos</span>`
    : hasSources
      ? `<span class="with-sources">Fuentes recopiladas</span>`
      : `<span>Pendiente</span>`;

  return `
    <button class="community-button" type="button" data-territory="${territory.territorio}" aria-pressed="false">
      <strong>${escapeHtml(territory.nombre)}</strong>
      ${status}
    </button>
  `;
}

function stageButton(catalog, territory, code, label) {
  const progress = territory.etapas[code] || { estado: "pendiente", etiqueta: "Pendiente" };
  const count = catalog.materias.filter(
    (item) => item.territorio === territory.territorio && item.etapa === code,
  ).length;
  const selected = state.stage === code;
  const detail = count ? `${count} materias` : progress.etiqueta;

  return `
    <button class="stage-button ${selected ? "is-selected" : ""}" type="button" data-stage="${code}" aria-pressed="${selected}">
      <strong>${escapeHtml(label)}</strong>
      <span class="status ${progress.estado}"><i></i>${escapeHtml(detail)}</span>
    </button>
  `;
}

function matterCard(catalog, matter) {
  const incidents = catalog.incidencias.filter((item) => matter.incidencias.includes(item.id));
  const sources = uniqueBy(matter.fuentes, "id");
  const courses = matter.cursos.map((item) => {
    const character = item.caracter ? ` · ${item.caracter}` : "";
    return `<span>${courseLabel(matter.etapa, item.curso)}${escapeHtml(character)}</span>`;
  }).join("");
  const opened = state.matter === matter.slug ? " open" : "";

  return `
    <article class="curriculum-item" data-matter="${escapeHtml(matter.slug)}">
      <div class="curriculum-row">
        <div>
          <p class="matter-code">${escapeHtml(matter.codigo || "Materia")} · Anexo ${escapeHtml(matter.anexos.join(", ") || "—")}</p>
          <h3>${escapeHtml(matter.nombre)}</h3>
          <div class="chips">${courses}</div>
        </div>
        <a class="json-link" href="${escapeHtml(matter.jsonPath)}">JSON <span>↗</span></a>
      </div>
      <details${opened}>
        <summary>Información, fuentes e incidencias <span aria-hidden="true">⌄</span></summary>
        <div class="matter-details">
          <dl class="metrics">
            <div><dt>${matter.estadisticas.competencias}</dt><dd>competencias</dd></div>
            <div><dt>${matter.estadisticas.criterios}</dt><dd>criterios</dd></div>
            <div><dt>${matter.estadisticas.saberes}</dt><dd>saberes</dd></div>
            <div><dt>${escapeHtml(matter.revision?.estado || "—")}</dt><dd>revisión</dd></div>
          </dl>
          <div class="matter-columns">
            <div>
              <h4>Fuentes</h4>
              <ul class="plain-list">${sources.map((source) => matterSource(catalog, source, matter.territorio)).join("")}</ul>
            </div>
            <div>
              <h4>Incidencias</h4>
              ${incidents.length
                ? `<div class="incident-list">${incidents.map(incidentCard).join("")}</div>`
                : `<p class="muted">No se registraron incidencias específicas.</p>`}
            </div>
          </div>
          <div class="data-path">
            <span>Ruta directa</span>
            <code>${escapeHtml(matter.jsonPath)}</code>
          </div>
        </div>
      </details>
    </article>
  `;
}

function matterSource(catalog, source, territoryCode) {
  const document = catalog.documentosNormativos.find((item) => item.id === source.id || item.urlOficial === source.urlOficial);
  const pages = source.paginasMateria
    ? ` · págs. ${source.paginasMateria.desde}–${source.paginasMateria.hasta}`
    : "";
  const archive = document?.archivo
    ? `<a href="${REPOSITORY_URL}/blob/main/sources/${territoryCode}/normativa/${escapeHtml(document.archivo)}">PDF archivado</a>`
    : "";

  return `
    <li>
      <p>Anexo ${escapeHtml(source.anexo || "—")}${pages}</p>
      <div><a href="${escapeHtml(source.urlOficial)}">Publicación oficial ↗</a>${archive}</div>
    </li>
  `;
}

function incidentCard(incident) {
  return `
    <article class="incident">
      <strong>${escapeHtml(incident.id)}</strong>
      <p>${escapeHtml(incident.incidencia)}</p>
      <p><b>Decisión:</b> ${escapeHtml(incident.decision)}</p>
    </article>
  `;
}

function documentCard(document, territoryCode) {
  const archiveUrl = `${REPOSITORY_URL}/blob/main/sources/${territoryCode}/normativa/${document.archivo}`;
  return `
    <article class="document-card">
      <div>
        <span>${escapeHtml(document.tipo.replaceAll("-", " "))}</span>
        <h4>${escapeHtml(document.titulo)}</h4>
        <p>BOJA ${escapeHtml(document.boja)} · ${formatDate(document.fechaPublicacion)}</p>
      </div>
      <div>
        <a href="${escapeHtml(document.urlOficial)}">Oficial ↗</a>
        <a href="${archiveUrl}">PDF archivado ↗</a>
      </div>
    </article>
  `;
}

function emptyStage(progress) {
  const message = progress?.estado === "fuentes"
    ? "Ya hemos recopilado la normativa. La conversión a JSON todavía está pendiente."
    : "Esta etapa forma parte de la hoja de ruta, pero aún no tiene datos publicados.";
  return `
    <div class="empty-stage">
      <span aria-hidden="true">○</span>
      <div><strong>${escapeHtml(progress?.etiqueta || "Pendiente")}</strong><p>${message}</p></div>
    </div>
  `;
}

function resultDescription(progress, matters, documents) {
  if (matters.length) {
    return `${matters.length} currículos revisados, con acceso directo al JSON y a su documentación.`;
  }
  if (progress?.estado === "fuentes" && documents.length) {
    return `${documents.length} documentos oficiales recopilados; los archivos JSON están pendientes.`;
  }
  return "Todavía no hay currículos publicados para esta selección.";
}

function stageDocuments(catalog, territoryCode, stageCode) {
  if (territoryCode !== "es-an") return [];
  return catalog.documentosNormativos.filter((document) => document.etapas.includes(stageCode));
}

function updateUrl() {
  const next = new URLSearchParams();
  if (state.territory) next.set("territorio", state.territory);
  if (state.stage) next.set("etapa", state.stage);
  const query = next.toString();
  history.replaceState(null, "", `${location.pathname}${query ? `?${query}` : ""}#explorar`);
}

function uniqueBy(items, key) {
  return [...new Map(items.map((item) => [item[key], item])).values()];
}

function courseLabel(stage, course) {
  if (stage === "eso") return `${course}.º ESO`;
  if (stage === "bachillerato") return `${course}.º Bachillerato`;
  return `${course}.º`;
}

function normalize(value) {
  return String(value || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().trim();
}

function formatDate(value) {
  if (!value) return "Fecha no indicada";
  return new Intl.DateTimeFormat("es-ES", { day: "numeric", month: "short", year: "numeric" })
    .format(new Date(`${value}T12:00:00`));
}

function cssEscape(value) {
  return window.CSS?.escape ? CSS.escape(value) : String(value).replace(/[^a-zA-Z0-9_-]/g, "");
}

function escapeHtml(value = "") {
  return String(value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;",
  })[character]);
}

function showError(error) {
  console.error(error);
  main.innerHTML = `
    <div class="fatal-error">
      <span aria-hidden="true">!</span>
      <h1>No se pudo abrir el catálogo</h1>
      <p>${escapeHtml(error.message)}</p>
      <button type="button" onclick="location.reload()">Reintentar</button>
    </div>
  `;
}
