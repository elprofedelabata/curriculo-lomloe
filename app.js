const REPOSITORY_URL = "https://github.com/elprofedelabata/curriculo-lomloe";
const STAGE_NAMES = {
  infantil: "Educación Infantil",
  primaria: "Educación Primaria",
  eso: "Educación Secundaria Obligatoria",
  bachillerato: "Bachillerato",
  cfgb: "Ciclos Formativos de Grado Básico",
};
const STAGE_SHORT_NAMES = {
  infantil: "Infantil",
  primaria: "Primaria",
  eso: "ESO",
  bachillerato: "Bachillerato",
  cfgb: "CFGB",
};

const main = document.querySelector("#contenido");
const errorDialog = document.querySelector("#error-dialog");
const errorMessage = document.querySelector("#error-message");
const page = document.body.dataset.page || "home";
const requestedSource = new URLSearchParams(location.search).get("src");

const viewerState = {
  data: null,
  development: null,
  view: "competencias",
  query: "",
};

boot().catch(showError);

async function boot() {
  const catalog = await fetchJson("catalogo.json");
  if (requestedSource) {
    const data = await fetchJson(requestedSource);
    renderMatterPage(catalog, data, null);
    return;
  }
  if (page === "stage") {
    renderStagePage(catalog, document.body.dataset.territorio, document.body.dataset.etapa);
    return;
  }
  if (page === "matter") {
    const meta = catalog.materias.find((item) =>
      item.territorio === document.body.dataset.territorio
      && item.etapa === document.body.dataset.etapa
      && item.slug === document.body.dataset.materia
    );
    if (!meta) throw new Error("La materia solicitada no aparece en el catálogo publicado.");
    const data = await fetchJson(meta.jsonPath);
    renderMatterPage(catalog, data, meta);
    return;
  }
  renderHomePage(catalog);
}

async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`No se pudo descargar ${url} (HTTP ${response.status}).`);
  return response.json();
}

function renderHomePage(catalog) {
  const published = catalog.etapas.filter((item) => item.estado === "completo");
  const totalMatters = catalog.materias.length;

  main.innerHTML = `
    <section class="hero hero-home">
      <div class="hero-glow" aria-hidden="true"></div>
      <div class="hero-copy">
        <p class="eyebrow">Datos educativos abiertos y trazables</p>
        <h1>El currículo LOMLOE, listo para usar.</h1>
        <p class="hero-description">Currículos oficiales convertidos a JSON, cotejados con su normativa y publicados con sus decisiones de revisión.</p>
        <div class="hero-actions">
          <a class="button button-light" href="es-an/eso/">Explorar Andalucía · ESO</a>
          <a class="button button-outline-light" href="${REPOSITORY_URL}">Ver repositorio ↗</a>
        </div>
      </div>
      <div class="hero-seal" aria-hidden="true"><span>${totalMatters}</span><small>currículos<br>publicados</small></div>
    </section>

    ${statsStrip([
      [totalMatters, "currículos revisados"],
      [published.length, "etapas completas"],
      [catalog.incidencias.length, "decisiones documentadas"],
      [catalog.progreso.length, "comunidades objetivo"],
    ])}

    <section class="section" aria-labelledby="published-title">
      <div class="section-heading split-heading">
        <div><p class="eyebrow">Disponible ahora</p><h2 id="published-title">Colecciones publicadas</h2></div>
        <p>La estructura crecerá comunidad a comunidad sin cambiar la forma de consumir los datos.</p>
      </div>
      <div class="stage-grid">${published.map(stageCard).join("")}</div>
    </section>

    <section class="section section-soft" aria-labelledby="search-title">
      <div class="section-heading"><p class="eyebrow">Buscar en lo publicado</p><h2 id="search-title">Encuentra una materia</h2></div>
      <label class="large-search" for="global-search"><span aria-hidden="true">⌕</span><input id="global-search" type="search" placeholder="Ej.: Física, Lengua, Computación…" autocomplete="off" /></label>
      <div class="matter-grid compact-grid" id="global-results"></div>
    </section>

    <section class="section" id="progreso" aria-labelledby="progress-title">
      <div class="section-heading split-heading">
        <div><p class="eyebrow">Hoja de ruta</p><h2 id="progress-title">Progreso por comunidad y etapa</h2></div>
        <div class="legend" aria-label="Leyenda"><span><i class="status-dot complete"></i>Completo</span><span><i class="status-dot sources"></i>Fuentes</span><span><i class="status-dot active"></i>En curso</span><span><i class="status-dot pending"></i>Pendiente</span></div>
      </div>
      <div class="table-wrap"><table class="progress-table"><thead><tr><th>Comunidad autónoma</th>${Object.keys(STAGE_SHORT_NAMES).map((key) => `<th>${STAGE_SHORT_NAMES[key]}</th>`).join("")}</tr></thead><tbody>${catalog.progreso.map((territory) => progressRow(catalog, territory)).join("")}</tbody></table></div>
      <p class="table-note">CFGB forma parte del alcance inicial. El resto de enseñanzas de Formación Profesional se estudiará en una fase posterior.</p>
    </section>

    <section class="section principles" aria-labelledby="principles-title">
      <div class="section-heading"><p class="eyebrow">Qué ofrece el proyecto</p><h2 id="principles-title">Datos, contexto y decisiones</h2></div>
      <div class="feature-grid">
        ${feature("01", "JSON reutilizable", "Archivos independientes, documentados mediante un esquema común y accesibles por URL.")}
        ${feature("02", "Trazabilidad", "Cada elemento conserva su fuente y las páginas de la publicación oficial de las que procede.")}
        ${feature("03", "Revisión transparente", "Las discrepancias y normalizaciones se publican junto con la decisión aplicada.")}
        ${feature("04", "Lectura humana", "El visor permite recorrer competencias, criterios y saberes sin trabajar directamente con el JSON.")}
      </div>
    </section>
  `;

  const search = document.querySelector("#global-search");
  const results = document.querySelector("#global-results");
  const update = () => {
    const query = normalized(search.value);
    const filtered = catalog.materias.filter((matter) => !query || matchesMatter(matter, query)).slice(0, query ? 24 : 8);
    results.innerHTML = filtered.map((matter) => matterCard(matter, true)).join("");
  };
  search.addEventListener("input", update);
  update();
}
function renderStagePage(catalog, territoryCode, stageCode) {
  const stage = catalog.etapas.find((item) => item.territorio === territoryCode && item.codigo === stageCode);
  if (!stage) throw new Error("La etapa solicitada todavía no está publicada.");
  const matters = catalog.materias.filter((item) => item.territorio === territoryCode && item.etapa === stageCode);
  const incidents = catalog.incidencias.filter((item) => item.territorio === territoryCode && item.etapa === stageCode);
  const sources = catalog.documentosNormativos.filter((item) => item.etapas.includes(stageCode));
  const courses = [...new Set(matters.flatMap((matter) => matter.cursos.map((course) => course.curso)))].sort();

  main.innerHTML = `
    ${breadcrumb([["Inicio", "./"], [stage.territorioNombre, "./"], [STAGE_SHORT_NAMES[stageCode]]])}
    <section class="hero hero-collection">
      <div class="hero-glow" aria-hidden="true"></div>
      <div class="hero-copy">
        <p class="eyebrow">Colección completa y revisada</p>
        <h1>${escapeHtml(stage.territorioNombre)} · ${escapeHtml(STAGE_SHORT_NAMES[stageCode])}</h1>
        <p class="hero-description">Currículos de ${escapeHtml(stage.nombre)} estructurados a partir de los anexos oficiales y listos para consulta o reutilización.</p>
        <div class="hero-meta"><span class="meta-chip">Revisión ${formatDate(stage.ultimaRevision)}</span><span class="meta-chip">JSON Schema validado</span></div>
      </div>
    </section>
    ${statsStrip([[stage.materias, "materias publicadas"], [incidents.length, "incidencias revisadas"], [sources.length, "documentos normativos"], ["100 %", "JSON validados"]])}

    <section class="section" aria-labelledby="catalog-title">
      <div class="section-heading split-heading"><div><p class="eyebrow">Catálogo</p><h2 id="catalog-title">Materias publicadas</h2></div><p>Cada ficha abre el currículo navegable y ofrece acceso directo al JSON.</p></div>
      <div class="filter-bar">
        <label class="search-box grow" for="matter-search"><span aria-hidden="true">⌕</span><input id="matter-search" type="search" placeholder="Buscar materia…" /></label>
        <label class="select-box">Curso<select id="course-filter"><option value="">Todos</option>${courses.map((course) => `<option value="${course}">${courseLabel(stageCode, course)}</option>`).join("")}</select></label>
        <label class="select-box">Anexo<select id="annex-filter"><option value="">Todos</option><option value="II">II</option><option value="III">III</option></select></label>
      </div>
      <p class="filter-count" id="filter-count"></p>
      <div class="matter-grid" id="matter-list"></div>
    </section>

    <section class="section section-soft" id="incidencias" aria-labelledby="incidents-title">
      <div class="section-heading split-heading"><div><p class="eyebrow">Revisión transparente</p><h2 id="incidents-title">Informe de incidencias</h2></div><p>${incidents.length} decisiones contrastadas con la normativa oficial. Todas figuran como revisadas.</p></div>
      <div class="incident-list">${incidents.map((incident) => incidentCard(incident, true)).join("")}</div>
      <a class="text-link" href="${REPOSITORY_URL}/blob/main/INCIDENCIAS.md">Consultar el registro completo en GitHub ↗</a>
    </section>

    <section class="section" id="fuentes" aria-labelledby="sources-title">
      <div class="section-heading split-heading"><div><p class="eyebrow">Procedencia</p><h2 id="sources-title">Normativa oficial</h2></div><p>La publicación oficial es siempre la referencia jurídicamente válida.</p></div>
      <div class="source-grid">${sources.map(sourceCard).join("")}</div>
    </section>

    <section class="section reuse-panel" aria-labelledby="reuse-title">
      <div><p class="eyebrow">Para aplicaciones</p><h2 id="reuse-title">Consumo directo por URL</h2><p>Los archivos se sirven junto al visualizador y no requieren autenticación.</p></div>
      <pre><code>const datos = await fetch(
  "${location.origin}${location.pathname.replace(/es-an\/.+$/, "")}data/es-an/${stageCode}/materias/${matters[0].slug}.json"
).then(r =&gt; r.json());</code></pre>
    </section>
  `;

  const search = document.querySelector("#matter-search");
  const courseFilter = document.querySelector("#course-filter");
  const annexFilter = document.querySelector("#annex-filter");
  const list = document.querySelector("#matter-list");
  const count = document.querySelector("#filter-count");
  const update = () => {
    const query = normalized(search.value);
    const course = Number(courseFilter.value || 0);
    const annex = annexFilter.value;
    const filtered = matters.filter((matter) =>
      (!query || matchesMatter(matter, query))
      && (!course || matter.cursos.some((item) => item.curso === course))
      && (!annex || matter.anexos.includes(annex))
    );
    count.textContent = `${filtered.length} ${filtered.length === 1 ? "materia" : "materias"}`;
    list.innerHTML = filtered.length ? filtered.map((matter) => matterCard(matter)).join("") : emptyResult("No hay materias que coincidan con los filtros.");
  };
  [search, courseFilter, annexFilter].forEach((control) => control.addEventListener("input", update));
  update();
}
function renderMatterPage(catalog, data, meta) {
  assertCurriculum(data);
  buildIndexes(data);
  viewerState.data = data;
  viewerState.development = developmentKey(data.desarrollos[0]);
  viewerState.view = "competencias";
  viewerState.query = "";

  const stageName = STAGE_NAMES[data.etapa] || data.etapa;
  const territoryName = catalog.territorios.find((item) => item.codigo === data.territorio)?.nombre || data.territorio;
  const incidents = meta ? catalog.incidencias.filter((item) => meta.incidencias.includes(item.id)) : [];
  const criteriaCount = data.desarrollos.reduce((total, item) => total + (item.criteriosEvaluacion?.length || 0), 0);
  const knowledgeCount = data.desarrollos.reduce((total, item) => total + collectKnowledge(item).length, 0);
  const jsonPath = meta?.jsonPath || requestedSource;
  const reportTitle = encodeURIComponent(`Revisión: ${data.materia.nombre.es}`);
  const reportBody = encodeURIComponent(`Materia: ${data.id}\nPágina: ${location.href}\n\nDescribe aquí el posible error:`);

  document.title = `${data.materia.nombre.es} · ${STAGE_SHORT_NAMES[data.etapa] || stageName} | Currículo LOMLOE`;
  main.innerHTML = `
    ${breadcrumb([["Inicio", "./"], [territoryName, "./"], [STAGE_SHORT_NAMES[data.etapa] || stageName, meta ? `es-an/${data.etapa}/` : "./"], [data.materia.nombre.es]])}
    <section class="hero hero-matter">
      <div class="hero-glow" aria-hidden="true"></div>
      <div class="hero-copy">
        <p class="eyebrow">${escapeHtml(territoryName)} · ${escapeHtml(stageName)}</p>
        <h1>${escapeHtml(data.materia.nombre.es)}</h1>
        <p class="hero-description">Consulta las competencias específicas, los criterios de evaluación y los saberes básicos tal como se publican en el JSON.</p>
        <div class="hero-meta"><span class="meta-chip">Esquema ${escapeHtml(data.schemaVersion)}</span><span class="meta-chip">${escapeHtml(data.revision?.estado || "Sin revisar")}</span><span class="meta-chip">Desde ${escapeHtml(data.vigencia?.aplicableDesdeCurso || "—")}</span></div>
        <div class="hero-actions">${jsonPath ? `<a class="button button-light" href="${escapeHtml(jsonPath)}" download>Descargar JSON</a>` : ""}<button class="button button-outline-light" id="copy-url" type="button">Copiar enlace</button></div>
      </div>
    </section>
    ${statsStrip([[data.competenciasEspecificas.length, "competencias específicas"], [criteriaCount, "criterios de evaluación"], [knowledgeCount, "saberes básicos"], [data.desarrollos.length, "desarrollos disponibles"]])}

    <nav class="section-nav" aria-label="Secciones de la materia"><a href="#explorar">Explorar</a><a href="#presentacion">Presentación</a><a href="#incidencias">Incidencias</a><a href="#fuentes">Fuentes y datos</a></nav>

    <section class="workspace" id="explorar" aria-label="Explorador curricular">
      <aside class="sidebar">
        <div class="sidebar-section"><p class="control-label">Curso</p><div class="course-tabs" id="course-tabs" role="tablist"></div></div>
        <div class="sidebar-section"><p class="control-label">Vista</p><div class="view-switch" role="group"><button class="view-button is-active" type="button" data-view="competencias"><span aria-hidden="true">⌁</span> Competencias</button><button class="view-button" type="button" data-view="saberes"><span aria-hidden="true">◫</span> Saberes básicos</button></div></div>
        <div class="sidebar-section"><label class="control-label" for="viewer-search">Buscar en el curso</label><label class="search-box"><span aria-hidden="true">⌕</span><input id="viewer-search" type="search" placeholder="Código o texto…" /></label></div>
        <div class="sidebar-section source-card" id="viewer-source"></div>
      </aside>
      <div class="content-panel"><div class="panel-heading"><div><p class="eyebrow" id="view-eyebrow"></p><h2 id="view-title"></h2></div><p class="result-count" id="result-count"></p></div><div id="cards" class="cards"></div><div id="empty-state" class="empty-state" hidden><span aria-hidden="true">∅</span><h3>No hay coincidencias</h3><p>Prueba con otro término o borra la búsqueda.</p></div></div>
    </section>

    <section class="section section-soft" id="presentacion" aria-labelledby="intro-title">
      <div class="section-heading"><p class="eyebrow">Presentación oficial</p><h2 id="intro-title">Finalidad y enfoque de la materia</h2></div>
      <div class="prose">${(data.introduccion?.es || []).map((paragraph) => `<p>${escapeHtml(paragraph)}</p>`).join("")}</div>
    </section>

    <section class="section" id="incidencias" aria-labelledby="matter-incidents-title">
      <div class="section-heading split-heading"><div><p class="eyebrow">Decisiones de revisión</p><h2 id="matter-incidents-title">Incidencias de esta materia</h2></div><p>${incidents.length ? `${incidents.length} ${incidents.length === 1 ? "incidencia documentada" : "incidencias documentadas"}.` : "No se registraron discrepancias específicas durante el cotejo."}</p></div>
      ${incidents.length ? `<div class="incident-list">${incidents.map((incident) => incidentCard(incident)).join("")}</div>` : `<div class="clean-state"><span>✓</span><div><strong>Sin incidencias específicas</strong><p>El archivo superó el cotejo sin decisiones excepcionales que documentar.</p></div></div>`}
    </section>

    <section class="section section-soft" id="fuentes" aria-labelledby="matter-sources-title">
      <div class="section-heading split-heading"><div><p class="eyebrow">Trazabilidad</p><h2 id="matter-sources-title">Fuentes y datos técnicos</h2></div><a class="text-link" href="${REPOSITORY_URL}/issues/new?title=${reportTitle}&body=${reportBody}">Informar de un posible error ↗</a></div>
      <div class="source-grid">${data.fuentes.map((source) => matterSourceCard(catalog, source)).join("")}</div>
      <div class="technical-grid"><article><span>ID estable</span><code>${escapeHtml(data.id)}</code></article><article><span>Versión del esquema</span><code>${escapeHtml(data.schemaVersion)}</code></article><article><span>Última revisión</span><strong>${formatDate(data.revision?.fechaUltimaRevision)}</strong></article><article><span>Método</span><p>${escapeHtml(data.revision?.metodo || "No indicado")}</p></article></div>
    </section>
  `;

  document.querySelector("#copy-url")?.addEventListener("click", async (event) => {
    await navigator.clipboard.writeText(location.href);
    event.currentTarget.textContent = "Enlace copiado";
  });
  attachViewerEvents();
  renderViewerShell();
  renderViewer();
}

function renderViewerShell() {
  const data = viewerState.data;
  document.querySelector("#course-tabs").innerHTML = data.desarrollos.map((development) => {
    const key = developmentKey(development);
    const active = key === viewerState.development;
    const variant = development.variante?.codigo ? ` ${development.variante.codigo.toUpperCase()}` : "";
    return `<button class="course-tab${active ? " is-active" : ""}" type="button" role="tab" aria-selected="${active}" data-development="${escapeHtml(key)}" aria-label="${escapeHtml(developmentLabel(data, development))}">${development.curso}.º${escapeHtml(variant)}</button>`;
  }).join("");
  renderViewerSource();
}

function attachViewerEvents() {
  document.querySelector("#course-tabs").addEventListener("click", (event) => {
    const button = event.target.closest("[data-development]");
    if (!button) return;
    viewerState.development = button.dataset.development;
    renderViewerSource();
    renderViewer();
  });
  document.querySelector(".view-switch").addEventListener("click", (event) => {
    const button = event.target.closest("[data-view]");
    if (!button) return;
    viewerState.view = button.dataset.view;
    renderViewer();
  });
  document.querySelector("#viewer-search").addEventListener("input", (event) => {
    viewerState.query = event.target.value;
    renderViewer();
  });
}
function renderViewer() {
  document.querySelectorAll(".course-tab").forEach((button) => {
    const active = button.dataset.development === viewerState.development;
    button.classList.toggle("is-active", active);
    button.setAttribute("aria-selected", String(active));
  });
  document.querySelectorAll(".view-button").forEach((button) => button.classList.toggle("is-active", button.dataset.view === viewerState.view));
  if (viewerState.view === "competencias") renderCompetencies();
  else renderKnowledge();
}

function renderCompetencies() {
  const development = viewerState.data._developments.get(viewerState.development);
  const criteriaByCompetency = new Map();
  for (const criterion of development.criteriosEvaluacion || []) {
    const linked = criteriaByCompetency.get(criterion.competenciaEspecificaRef) || [];
    linked.push(criterion);
    criteriaByCompetency.set(criterion.competenciaEspecificaRef, linked);
  }
  const query = normalized(viewerState.query);
  const cards = viewerState.data.competenciasEspecificas.map((competency) => {
    const criteria = criteriaByCompetency.get(competency.id) || [];
    const matchingCriteria = query ? criteria.filter((criterion) => matchesCriterion(criterion, query)) : criteria;
    const competencyMatches = matches([competency.codigoOficial, textOf(competency.enunciado), ...(competency.descriptoresOperativosRefs || [])], query);
    if (query && !competencyMatches && !matchingCriteria.length) return null;
    return competencyCard(competency, competencyMatches ? criteria : matchingCriteria, Boolean(query));
  }).filter(Boolean);
  document.querySelector("#view-eyebrow").textContent = `${developmentLabel(viewerState.data, development)} · Vista relacional`;
  document.querySelector("#view-title").textContent = "Competencias y criterios";
  document.querySelector("#result-count").textContent = `${cards.length} ${cards.length === 1 ? "competencia" : "competencias"}`;
  setViewerCards(cards.join(""), cards.length);
}

function renderKnowledge() {
  const development = viewerState.data._developments.get(viewerState.development);
  const query = normalized(viewerState.query);
  const groups = knowledgeGroups(development).map((group) => {
    const items = group.items.filter((item) => matches([item.id, item.codigoOficial, textOf(item.texto), group.name], query));
    return items.length ? knowledgeGroup(group, items, Boolean(query)) : null;
  }).filter(Boolean);
  const count = groups.reduce((total, group) => total + group.count, 0);
  document.querySelector("#view-eyebrow").textContent = `${developmentLabel(viewerState.data, development)} · Índice temático`;
  document.querySelector("#view-title").textContent = "Saberes básicos";
  document.querySelector("#result-count").textContent = `${count} ${count === 1 ? "saber" : "saberes"}`;
  setViewerCards(groups.map((group) => group.html).join(""), count);
}

function setViewerCards(html, count) {
  const cards = document.querySelector("#cards");
  const empty = document.querySelector("#empty-state");
  cards.innerHTML = html;
  cards.hidden = !count;
  empty.hidden = Boolean(count);
}

function competencyCard(competency, criteria, open) {
  return `<details class="competency-card" ${open ? "open" : ""}><summary><span class="code-badge">CE ${escapeHtml(competency.codigoOficial)}</span><span class="summary-copy"><strong>${escapeHtml(textOf(competency.enunciado))}</strong><small>${criteria.length} ${criteria.length === 1 ? "criterio vinculado" : "criterios vinculados"}</small></span><span class="chevron" aria-hidden="true">⌄</span></summary><div class="card-body"><ul class="descriptor-list">${(competency.descriptoresOperativosRefs || []).map((ref) => `<li>${escapeHtml(ref)}</li>`).join("")}</ul><div class="criteria-list">${criteria.map(criterionCard).join("")}</div></div></details>`;
}

function criterionCard(criterion) {
  const refs = (criterion.saberesBasicosRefs || []).map((ref) => `<li class="ref-pill" title="${viewerState.data._knowledge.has(ref) ? "Referencia resuelta" : "Referencia no encontrada"}">${escapeHtml(ref)}${viewerState.data._knowledge.has(ref) ? "" : " ⚠"}</li>`).join("");
  const pages = criterion.procedencia?.paginas || [];
  return `<article class="criterion"><div class="criterion-heading"><span class="criterion-code">Criterio ${escapeHtml(criterion.codigoOficial)}</span><span class="criterion-page">${pages.length ? `p. ${pages.join("–")}` : ""}</span></div><p>${escapeHtml(textOf(criterion.texto))}</p><span class="refs-label">Saberes relacionados</span><ul class="ref-list">${refs}</ul></article>`;
}

function knowledgeGroup(group, items, open) {
  return {
    count: items.length,
    html: `<details class="knowledge-block" ${open ? "open" : ""}><summary><span class="code-badge">${escapeHtml(group.code)}</span><span class="summary-copy"><strong>${escapeHtml(group.name)}</strong><small>${items.length} saberes</small></span><span class="chevron" aria-hidden="true">⌄</span></summary><div class="card-body">${items.map(knowledgeItem).join("")}</div></details>`,
  };
}

function knowledgeItem(item) {
  const criteria = viewerState.data._criteriaByKnowledge.get(item.id) || [];
  const activeIds = new Set((viewerState.data._developments.get(viewerState.development)?.criteriosEvaluacion || []).map((criterion) => criterion.id));
  const active = criteria.filter((criterion) => activeIds.has(criterion.id));
  return `<article class="knowledge-item"><div class="knowledge-title"><code>${escapeHtml(item.codigoOficial || item.id)}</code><p>${escapeHtml(textOf(item.texto))}</p></div><div class="linked-criteria">Aparece en criterios: ${active.length ? active.map((criterion) => `<strong>${escapeHtml(criterion.codigoOficial)}</strong>`).join(", ") : "ninguno"}</div></article>`;
}

function renderViewerSource() {
  const development = viewerState.data._developments.get(viewerState.development);
  const sourceId = development.criteriosEvaluacion?.[0]?.procedencia?.fuenteRef;
  const source = viewerState.data.fuentes.find((item) => item.id === sourceId) || viewerState.data.fuentes[0];
  document.querySelector("#viewer-source").innerHTML = `<strong>Fuente normativa</strong>${escapeHtml(source?.publicacion || "Fuente no indicada")} ${source?.numero ? `n.º ${escapeHtml(source.numero)}` : ""}<br>${source?.fechaPublicacion ? formatDate(source.fechaPublicacion) : ""}${source?.urlOficial ? `<br><a href="${escapeHtml(source.urlOficial)}">Consultar documento oficial ↗</a>` : ""}`;
}

function buildIndexes(data) {
  data._developments = new Map(data.desarrollos.map((item) => [developmentKey(item), item]));
  data._knowledge = new Map();
  data._criteriaByKnowledge = new Map();
  for (const development of data.desarrollos) {
    for (const knowledge of collectKnowledge(development)) data._knowledge.set(knowledge.id, knowledge);
    for (const criterion of development.criteriosEvaluacion || []) {
      for (const ref of criterion.saberesBasicosRefs || []) {
        const linked = data._criteriaByKnowledge.get(ref) || [];
        linked.push(criterion);
        data._criteriaByKnowledge.set(ref, linked);
      }
    }
  }
}

function assertCurriculum(data) {
  if (!data || typeof data !== "object") throw new Error("El contenido no es un objeto JSON.");
  if (!data.id || !data.materia?.nombre?.es) throw new Error("Faltan los campos obligatorios del currículo.");
  for (const key of ["competenciasEspecificas", "desarrollos", "fuentes"]) {
    if (!Array.isArray(data[key])) throw new Error(`El campo «${key}» debe ser una lista.`);
  }
}

function collectKnowledge(development) {
  return knowledgeGroups(development).flatMap((group) => group.items);
}

function knowledgeGroups(development) {
  return (development.bloquesSaberes || []).flatMap((block) => {
    if (block.saberes) return [{ code: block.codigo, name: textOf(block.nombre), items: block.saberes }];
    return (block.apartados || []).map((section) => ({ code: `${block.codigo}.${section.codigo}`, name: `${textOf(block.nombre)} · ${textOf(section.nombre)}`, items: section.saberes || [] }));
  });
}
function stageCard(stage) {
  return `<article class="stage-card"><div><span class="status-badge">Completo y revisado</span><p class="eyebrow">${escapeHtml(stage.territorioNombre)}</p><h3>${escapeHtml(STAGE_SHORT_NAMES[stage.codigo])}</h3><p>${stage.materias} materias · ${stage.incidencias} incidencias documentadas</p></div><a class="card-link" href="${escapeHtml(stage.pagePath)}">Explorar colección <span>→</span></a></article>`;
}

function matterCard(matter, compact = false) {
  const courses = matter.cursos.map((course) => `${course.curso}.º`).join(", ");
  return `<article class="matter-card${compact ? " is-compact" : ""}"><div class="matter-top"><span class="code-badge">${escapeHtml(matter.codigo)}</span><span class="review-mark">✓ Revisado</span></div><h3><a href="${escapeHtml(matter.pagePath)}">${escapeHtml(matter.nombre)}</a></h3><p>${escapeHtml(STAGE_SHORT_NAMES[matter.etapa])} · ${escapeHtml(courses)}${matter.anexos.length ? ` · Anexo ${escapeHtml(matter.anexos.join(", "))}` : ""}</p><div class="matter-metrics"><span>${matter.estadisticas.criterios} criterios</span><span>${matter.estadisticas.saberes} saberes</span>${matter.incidencias.length ? `<span>${matter.incidencias.length} inc.</span>` : ""}</div><div class="matter-actions"><a href="${escapeHtml(matter.pagePath)}">Explorar</a><a href="${escapeHtml(matter.jsonPath)}" download>JSON ↓</a></div></article>`;
}

function progressRow(catalog, territory) {
  return `<tr><th scope="row">${escapeHtml(territory.nombre)}</th>${Object.entries(territory.etapas).map(([stageCode, status]) => {
    const published = catalog.etapas.find((item) => item.territorio === territory.territorio && item.codigo === stageCode);
    const content = `<span class="progress-status ${status.estado}"><i></i><span>${escapeHtml(status.etiqueta)}</span></span>`;
    return `<td>${published ? `<a href="${escapeHtml(published.pagePath)}">${content}</a>` : content}</td>`;
  }).join("")}</tr>`;
}

function incidentCard(incident, showMatter = false) {
  const matter = showMatter ? `<a href="es-an/${incident.etapa}/${incident.materiaSlug}/">${escapeHtml(incident.materia)}</a>` : "";
  return `<article class="incident-card"><div class="incident-id"><span>${escapeHtml(incident.id)}</span><small>Revisada</small></div><div>${matter ? `<h3>${matter}</h3>` : ""}<p>${formatInline(incident.incidencia)}</p><div class="decision"><strong>Decisión aplicada</strong><p>${formatInline(incident.decision)}</p></div></div></article>`;
}

function sourceCard(source) {
  const archived = `${REPOSITORY_URL}/blob/main/sources/es-an/normativa/${source.archivo}`;
  return `<article class="norm-card"><div class="norm-meta"><span>${escapeHtml(source.tipo.replaceAll("-", " "))}</span><span>BOJA ${escapeHtml(source.boja)}</span><span>${formatDate(source.fechaPublicacion)}</span></div><h3>${escapeHtml(source.titulo)}</h3>${source.notas ? `<p>${escapeHtml(source.notas)}</p>` : ""}<dl><div><dt>Páginas</dt><dd>${source.paginas}</dd></div><div><dt>SHA-256</dt><dd><code title="${escapeHtml(source.sha256)}">${escapeHtml(source.sha256.slice(0, 12))}…</code></dd></div></dl><div class="card-actions"><a href="${escapeHtml(source.urlOficial)}">Publicación oficial ↗</a><a href="${escapeHtml(archived)}">Copia archivada ↗</a></div></article>`;
}

function matterSourceCard(catalog, source) {
  const archivedSource = catalog.documentosNormativos.find((item) => item.cve === source.cve && item.urlOficial === source.urlOficial)
    || catalog.documentosNormativos.find((item) => item.cve === source.cve);
  const archived = archivedSource ? `${REPOSITORY_URL}/blob/main/sources/es-an/normativa/${archivedSource.archivo}` : "";
  const pages = source.paginasMateria ? `${source.paginasMateria.desde}–${source.paginasMateria.hasta}` : "No indicadas";
  return `<article class="norm-card"><div class="norm-meta"><span>Anexo ${escapeHtml(source.anexo || "—")}</span><span>BOJA ${escapeHtml(source.numero || "—")}</span><span>${formatDate(source.fechaPublicacion)}</span></div><h3>${escapeHtml(source.titulo)}</h3><dl><div><dt>Páginas de la materia</dt><dd>${escapeHtml(pages)}</dd></div><div><dt>CVE</dt><dd><code>${escapeHtml(source.cve)}</code></dd></div></dl><div class="card-actions"><a href="${escapeHtml(source.urlOficial)}">Documento oficial ↗</a>${archived ? `<a href="${escapeHtml(archived)}">Copia archivada ↗</a>` : ""}</div></article>`;
}

function statsStrip(items) {
  return `<section class="stats" aria-label="Resumen">${items.map(([value, label]) => `<div class="stat"><strong>${escapeHtml(value)}</strong><span>${escapeHtml(label)}</span></div>`).join("")}</section>`;
}

function feature(number, title, body) {
  return `<article><span>${number}</span><h3>${escapeHtml(title)}</h3><p>${escapeHtml(body)}</p></article>`;
}

function breadcrumb(items) {
  return `<nav class="breadcrumb" aria-label="Migas de pan">${items.map(([label, href]) => href ? `<a href="${escapeHtml(href)}">${escapeHtml(label)}</a><span aria-hidden="true">/</span>` : `<span aria-current="page">${escapeHtml(label)}</span>`).join("")}</nav>`;
}

function emptyResult(message) {
  return `<div class="empty-result"><span aria-hidden="true">∅</span><p>${escapeHtml(message)}</p></div>`;
}

function developmentKey(development) {
  return `${Number(development.curso)}:${development.variante?.codigo || ""}`;
}

function developmentLabel(data, development) {
  const variant = textOf(development.variante?.nombre);
  return `${courseLabel(data.etapa, development.curso)}${variant ? ` · ${variant}` : ""}`;
}

function courseLabel(stage, course) {
  if (stage === "eso") return `${course}.º ESO`;
  if (stage === "bachillerato") return `${course}.º Bachillerato`;
  return `${course}.º`;
}

function matchesMatter(matter, query) {
  return matches([matter.nombre, matter.codigo, STAGE_NAMES[matter.etapa], ...matter.cursos.map((course) => course.curso)], query);
}

function matchesCriterion(criterion, query) {
  return matches([criterion.codigoOficial, textOf(criterion.texto), ...(criterion.saberesBasicosRefs || [])], query);
}

function matches(values, query) {
  if (!query) return true;
  return normalized(values.filter(Boolean).join(" ")).includes(query);
}

function normalized(value) {
  return String(value || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().trim();
}

function textOf(value) {
  if (typeof value === "string") return value;
  return value?.es || "";
}

function formatDate(value) {
  if (!value) return "No indicada";
  const date = new Date(`${value}T00:00:00`);
  return Number.isNaN(date.getTime()) ? value : new Intl.DateTimeFormat("es-ES", { dateStyle: "long" }).format(date);
}

function formatInline(value) {
  return escapeHtml(value).replace(/`([^`]+)`/g, "<code>$1</code>");
}

function escapeHtml(value = "") {
  return String(value).replace(/[&<>'"]/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '\"': "&quot;" })[character]);
}

function showError(error) {
  console.error(error);
  main.innerHTML = `<section class="fatal-error"><span>!</span><h1>No se pudo preparar esta página</h1><p>${escapeHtml(error.message)}</p><a class="button" href="./">Volver al inicio</a></section>`;
  errorMessage.textContent = error.message;
  if (typeof errorDialog?.showModal === "function") errorDialog.showModal();
}