const DEFAULT_SOURCE = "./data/es-an/eso/materias/fisica-y-quimica.json";

const state = {
  data: null,
  course: null,
  view: "competencias",
  query: "",
};

const elements = {
  title: document.querySelector("#page-title"),
  territory: document.querySelector("#territory-label"),
  heroMeta: document.querySelector("#hero-meta"),
  stats: document.querySelector("#stats"),
  courseTabs: document.querySelector("#course-tabs"),
  search: document.querySelector("#search"),
  sourceCard: document.querySelector("#source-card"),
  loadState: document.querySelector("#load-state"),
  viewer: document.querySelector("#viewer"),
  viewEyebrow: document.querySelector("#view-eyebrow"),
  viewTitle: document.querySelector("#view-title"),
  resultCount: document.querySelector("#result-count"),
  cards: document.querySelector("#cards"),
  emptyState: document.querySelector("#empty-state"),
  fileInput: document.querySelector("#json-file"),
  dataId: document.querySelector("#data-id"),
  errorDialog: document.querySelector("#error-dialog"),
  errorMessage: document.querySelector("#error-message"),
};

const escapeHtml = (value = "") => String(value).replace(/[&<>'"]/g, (char) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;",
}[char]));

const getText = (value) => {
  if (typeof value === "string") return value;
  if (value && typeof value.es === "string") return value.es;
  return "";
};

function assertCurriculum(data) {
  const requiredArrays = ["competenciasEspecificas", "desarrollos", "fuentes"];
  if (!data || typeof data !== "object") throw new Error("El contenido no es un objeto JSON.");
  if (!data.id || !data.materia?.nombre?.es) throw new Error("Faltan los campos obligatorios «id» o «materia.nombre.es».");
  for (const key of requiredArrays) {
    if (!Array.isArray(data[key])) throw new Error(`El campo «${key}» debe ser una lista.`);
  }
  if (!data.desarrollos.length) throw new Error("El documento no contiene desarrollos por curso.");
}

function buildIndexes(data) {
  data._competencies = new Map(data.competenciasEspecificas.map((item) => [item.id, item]));
  data._courses = new Map(data.desarrollos.map((item) => [Number(item.curso), item]));
  data._knowledge = new Map();
  data._criteriaByKnowledge = new Map();

  for (const development of data.desarrollos) {
    for (const block of development.bloquesSaberes || []) {
      for (const knowledge of block.saberes || []) data._knowledge.set(knowledge.id, knowledge);
    }
    for (const criterion of development.criteriosEvaluacion || []) {
      for (const ref of criterion.saberesBasicosRefs || []) {
        const linked = data._criteriaByKnowledge.get(ref) || [];
        linked.push(criterion);
        data._criteriaByKnowledge.set(ref, linked);
      }
    }
  }
}

async function loadFromUrl(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`La descarga devolvió HTTP ${response.status}.`);
  return response.json();
}

function showError(error) {
  const fileHint = location.protocol === "file:"
    ? " Abre el proyecto mediante un servidor HTTP local; los navegadores bloquean fetch() desde file://."
    : "";
  elements.errorMessage.textContent = `${error.message}${fileHint}`;
  elements.loadState.textContent = "No se ha podido cargar el currículo.";
  if (typeof elements.errorDialog.showModal === "function") elements.errorDialog.showModal();
}

function setData(data) {
  assertCurriculum(data);
  buildIndexes(data);
  state.data = data;
  state.course = Number(data.desarrollos[0].curso);
  state.query = "";
  elements.search.value = "";
  renderShell();
  render();
  elements.loadState.hidden = true;
  elements.viewer.hidden = false;
}

function renderShell() {
  const data = state.data;
  const criterionCount = data.desarrollos.reduce((total, item) => total + (item.criteriosEvaluacion?.length || 0), 0);
  const knowledgeCount = data.desarrollos.reduce((total, item) => total + (item.bloquesSaberes || []).reduce((sum, block) => sum + (block.saberes?.length || 0), 0), 0);
  const source = data.fuentes[0];
  const status = data.revision?.estado || "sin revisar";

  elements.title.textContent = data.materia.nombre.es;
  elements.territory.textContent = `${territoryName(data.territorio)} · ${stageName(data.etapa)}`;
  elements.heroMeta.innerHTML = [
    `Esquema ${data.schemaVersion || "—"}`,
    `Datos ${status}`,
    `Vigente desde ${data.vigencia?.aplicableDesdeCurso || "—"}`,
  ].map((item) => `<span class="meta-chip">${escapeHtml(item)}</span>`).join("");

  elements.stats.innerHTML = [
    [data.competenciasEspecificas.length, "competencias específicas"],
    [criterionCount, "criterios de evaluación"],
    [knowledgeCount, "saberes básicos"],
    [data.desarrollos.length, "cursos disponibles"],
  ].map(([value, label]) => `<div class="stat"><strong>${value}</strong><span>${label}</span></div>`).join("");

  elements.courseTabs.innerHTML = data.desarrollos.map((item) => `
    <button class="course-tab${Number(item.curso) === state.course ? " is-active" : ""}" type="button"
      role="tab" aria-selected="${Number(item.curso) === state.course}" data-course="${item.curso}">
      ${item.curso}.º
    </button>`).join("");

  elements.sourceCard.innerHTML = `
    <strong>Fuente normativa</strong>
    ${escapeHtml(source?.publicacion || "Fuente no indicada")} ${source?.numero ? `n.º ${escapeHtml(source.numero)}` : ""}<br>
    ${source?.fechaPublicacion ? formatDate(source.fechaPublicacion) : ""}
    ${source?.urlOficial ? `<br><a href="${escapeHtml(source.urlOficial)}" target="_blank" rel="noreferrer">Consultar documento oficial ↗</a>` : ""}`;
  elements.dataId.textContent = data.id;
}

function render() {
  document.querySelectorAll(".course-tab").forEach((button) => {
    const active = Number(button.dataset.course) === state.course;
    button.classList.toggle("is-active", active);
    button.setAttribute("aria-selected", String(active));
  });
  document.querySelectorAll(".view-button").forEach((button) => {
    button.classList.toggle("is-active", button.dataset.view === state.view);
  });

  if (state.view === "competencias") renderCompetencies();
  else renderKnowledge();
}

function renderCompetencies() {
  const development = state.data._courses.get(state.course);
  const criteriaByCompetency = new Map();
  for (const criterion of development.criteriosEvaluacion || []) {
    const linked = criteriaByCompetency.get(criterion.competenciaEspecificaRef) || [];
    linked.push(criterion);
    criteriaByCompetency.set(criterion.competenciaEspecificaRef, linked);
  }

  const query = normalized(state.query);
  const cards = state.data.competenciasEspecificas.map((competency) => {
    const criteria = criteriaByCompetency.get(competency.id) || [];
    const matchingCriteria = query ? criteria.filter((item) => matchesCriterion(item, query)) : criteria;
    const competencyMatches = matches([competency.codigoOficial, getText(competency.enunciado), ...(competency.descriptoresOperativosRefs || [])], query);
    if (query && !competencyMatches && !matchingCriteria.length) return null;
    return competencyCard(competency, competencyMatches ? criteria : matchingCriteria, Boolean(query));
  }).filter(Boolean);

  elements.viewEyebrow.textContent = `${state.course}.º ESO · Vista relacional`;
  elements.viewTitle.textContent = "Competencias y criterios";
  elements.resultCount.textContent = `${cards.length} ${cards.length === 1 ? "competencia" : "competencias"}`;
  elements.cards.innerHTML = cards.join("");
  toggleEmpty(cards.length);
}

function competencyCard(competency, criteria, open) {
  return `<details class="competency-card" ${open ? "open" : ""}>
    <summary>
      <span class="code-badge">CE ${escapeHtml(competency.codigoOficial)}</span>
      <span class="summary-copy">
        <strong>${escapeHtml(getText(competency.enunciado))}</strong>
        <small>${criteria.length} ${criteria.length === 1 ? "criterio vinculado" : "criterios vinculados"}</small>
      </span>
      <span class="chevron" aria-hidden="true">⌄</span>
    </summary>
    <div class="card-body">
      <ul class="descriptor-list" aria-label="Descriptores operativos">
        ${(competency.descriptoresOperativosRefs || []).map((ref) => `<li>${escapeHtml(ref)}</li>`).join("")}
      </ul>
      <div class="criteria-list">
        ${criteria.map(criterionCard).join("")}
      </div>
    </div>
  </details>`;
}

function criterionCard(criterion) {
  const refs = (criterion.saberesBasicosRefs || []).map((ref) => {
    const resolved = state.data._knowledge.has(ref);
    return `<li class="ref-pill" title="${resolved ? "Referencia resuelta" : "Referencia no encontrada"}">${escapeHtml(ref)}${resolved ? "" : " ⚠"}</li>`;
  }).join("");
  const pages = criterion.procedencia?.paginas || [];
  return `<article class="criterion">
    <div class="criterion-heading">
      <span class="criterion-code">Criterio ${escapeHtml(criterion.codigoOficial)}</span>
      <span class="criterion-page">${pages.length ? `p. ${pages.join("–")}` : ""}</span>
    </div>
    <p>${escapeHtml(getText(criterion.texto))}</p>
    <span class="refs-label">Saberes relacionados</span>
    <ul class="ref-list">${refs}</ul>
  </article>`;
}

function renderKnowledge() {
  const development = state.data._courses.get(state.course);
  const query = normalized(state.query);
  const blocks = (development.bloquesSaberes || []).map((block) => {
    const knowledge = (block.saberes || []).filter((item) => matches([item.id, item.codigoOficial, getText(item.texto), getText(block.nombre)], query));
    if (!knowledge.length) return null;
    return knowledgeBlock(block, knowledge, Boolean(query));
  }).filter(Boolean);
  const itemCount = blocks.reduce((sum, item) => sum + item.count, 0);

  elements.viewEyebrow.textContent = `${state.course}.º ESO · Índice temático`;
  elements.viewTitle.textContent = "Saberes básicos";
  elements.resultCount.textContent = `${itemCount} ${itemCount === 1 ? "saber" : "saberes"}`;
  elements.cards.innerHTML = blocks.map((item) => item.html).join("");
  toggleEmpty(itemCount);
}

function knowledgeBlock(block, knowledge, open) {
  return {
    count: knowledge.length,
    html: `<details class="knowledge-block" ${open ? "open" : ""}>
      <summary>
        <span class="code-badge">${escapeHtml(block.codigo)}</span>
        <span class="summary-copy"><strong>${escapeHtml(getText(block.nombre))}</strong><small>${knowledge.length} saberes</small></span>
        <span class="chevron" aria-hidden="true">⌄</span>
      </summary>
      <div class="card-body">
        ${knowledge.map(knowledgeItem).join("")}
      </div>
    </details>`,
  };
}

function knowledgeItem(item) {
  const criteria = state.data._criteriaByKnowledge.get(item.id) || [];
  const courseCriteria = criteria.filter((criterion) => criterion.id.startsWith(`cri-${state.course}-`));
  const linked = courseCriteria.length
    ? courseCriteria.map((criterion) => `<strong>${escapeHtml(criterion.codigoOficial)}</strong>`).join(", ")
    : "ninguno";
  return `<article class="knowledge-item">
    <div class="knowledge-title">
      <code>${escapeHtml(item.codigoOficial || item.id)}</code>
      <p>${escapeHtml(getText(item.texto))}</p>
    </div>
    <div class="linked-criteria">Aparece en criterios: ${linked}</div>
  </article>`;
}

function matchesCriterion(criterion, query) {
  return matches([
    criterion.codigoOficial,
    getText(criterion.texto),
    ...(criterion.saberesBasicosRefs || []),
  ], query);
}

function matches(values, query) {
  if (!query) return true;
  return normalized(values.filter(Boolean).join(" ")).includes(query);
}

function normalized(value) {
  return String(value || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().trim();
}

function toggleEmpty(hasResults) {
  elements.cards.hidden = !hasResults;
  elements.emptyState.hidden = Boolean(hasResults);
}

function territoryName(code) {
  return ({ "es-an": "Andalucía" })[code] || code || "Territorio no indicado";
}

function stageName(code) {
  return ({ eso: "Educación Secundaria Obligatoria", bachillerato: "Bachillerato" })[code] || code || "Etapa no indicada";
}

function formatDate(value) {
  const date = new Date(`${value}T00:00:00`);
  return Number.isNaN(date.getTime()) ? value : new Intl.DateTimeFormat("es-ES", { dateStyle: "long" }).format(date);
}

elements.courseTabs.addEventListener("click", (event) => {
  const button = event.target.closest("[data-course]");
  if (!button) return;
  state.course = Number(button.dataset.course);
  render();
});

document.querySelector(".view-switch").addEventListener("click", (event) => {
  const button = event.target.closest("[data-view]");
  if (!button) return;
  state.view = button.dataset.view;
  render();
});

elements.search.addEventListener("input", (event) => {
  state.query = event.target.value;
  render();
});

elements.fileInput.addEventListener("change", async (event) => {
  const [file] = event.target.files;
  if (!file) return;
  try {
    setData(JSON.parse(await file.text()));
  } catch (error) {
    showError(error);
  } finally {
    event.target.value = "";
  }
});

const requestedSource = new URLSearchParams(location.search).get("src");
loadFromUrl(requestedSource || DEFAULT_SOURCE).then(setData).catch(showError);
