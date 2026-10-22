const REPOSITORY_URL = "https://github.com/elprofedelabata/curriculo-lomloe";

const grid = document.querySelector(".folder-grid");
const expansion = document.getElementById("community-stages");
const title = document.getElementById("community-stages-title");
const previewNote = expansion.querySelector(".preview-note");
const stageGrid = expansion.querySelector(".stage-grid");
const stageModal = document.getElementById("stage-modal");
const modalTitle = document.getElementById("stage-modal-title");
const modalClose = stageModal.querySelector(".stage-modal-close");
const modalContent = stageModal.querySelector(".stage-modal-content");
const stageButtons = [...stageGrid.querySelectorAll(".stage-card-button")];
const folders = [...grid.querySelectorAll(".folder-card")];
const toggles = [...grid.querySelectorAll(".folder-card-toggle")];

let activeCode = null;
let activeStage = null;
let modalTrigger = null;
let catalogPromise = null;
let currentView = null;
let renderToken = 0;
let skipCloseRouteUpdate = false;

function setExpanded(code) {
  expansion.hidden = true;
  activeCode = code;

  for (const toggle of toggles) {
    const folder = toggle.closest(".folder-card");
    const expanded = folder.dataset.community === code;
    const name = folder.querySelector(".folder-name").textContent;
    const preview = folder.classList.contains("folder-card--preview");
    toggle.setAttribute("aria-expanded", String(expanded));
    toggle.setAttribute(
      "aria-label",
      (expanded ? "Ocultar " : "Mostrar ") +
        (preview ? "maqueta de etapas de " : "etapas de ") + name
    );
    folder.classList.toggle("folder-card--open", expanded);
  }

  if (!code) return;

  const selected = folders.find((folder) => folder.dataset.community === code);
  const rowTop = selected.offsetTop;
  const lastInRow = folders.filter((folder) => folder.offsetTop === rowTop).at(-1);
  lastInRow.after(expansion);

  const gridBounds = grid.getBoundingClientRect();
  const folderBounds = selected.getBoundingClientRect();
  const left = ((folderBounds.left - gridBounds.left) / gridBounds.width) * 100;
  const right = ((folderBounds.right - gridBounds.left) / gridBounds.width) * 100;
  expansion.style.setProperty("--shadow-left", left + "%");
  expansion.style.setProperty("--shadow-right", right + "%");

  const name = selected.querySelector(".folder-name").textContent;
  const preview = selected.classList.contains("folder-card--preview");
  title.textContent = "Etapas educativas de " + name;
  stageGrid.setAttribute("aria-label", "Etapas educativas de " + name);
  previewNote.hidden = !preview;
  for (const button of stageButtons) button.disabled = preview;
  expansion.classList.toggle("community-expansion--preview", preview);
  expansion.hidden = false;
}

function loadCatalog() {
  if (!catalogPromise) {
    catalogPromise = fetch("./catalogo.json")
      .then((response) => {
        if (!response.ok) throw new Error("No se pudo cargar el catálogo (HTTP " + response.status + ").");
        return response.json();
      })
      .catch((error) => {
        catalogPromise = null;
        throw error;
      });
  }
  return catalogPromise;
}

function openStage(stageCode, matterSlug = null, updateRoute = true) {
  const selected = folders.find((folder) => folder.dataset.community === activeCode);
  const trigger = stageGrid.querySelector('[data-stage="' + stageCode + '"] .stage-card-button');
  if (!selected?.classList.contains("folder-card--available") || !trigger || trigger.disabled) return;

  activeStage = stageCode;
  modalTrigger = trigger;
  currentView = null;
  modalTitle.textContent = trigger.textContent.trim();
  modalContent.replaceChildren(create("p", "modal-message", "Cargando currículos…"));
  if (!stageModal.open) stageModal.showModal();
  if (updateRoute) writeStageRoute(stageCode, matterSlug);

  const token = ++renderToken;
  loadCatalog().then((catalog) => {
    if (token !== renderToken || !stageModal.open) return;
    renderStage(catalog, activeCode, stageCode, matterSlug);
  }).catch((error) => {
    if (token !== renderToken || !stageModal.open) return;
    modalContent.replaceChildren(create("p", "modal-message", error.message + " Cierra y vuelve a abrir la etapa para reintentar."));
  });
}

function renderStage(catalog, territoryCode, stageCode, matterSlug) {
  const stage = catalog.etapas.find((item) => item.territorio === territoryCode && item.codigo === stageCode);
  const matters = catalog.materias.filter((item) => item.territorio === territoryCode && item.etapa === stageCode);
  const openOptions = (catalog.optativasAbiertas || []).filter((item) => item.territorio === territoryCode && item.etapa === stageCode);
  const incidents = catalog.incidencias.filter((item) => item.territorio === territoryCode && item.etapa === stageCode);
  const documents = catalog.documentosNormativos.filter((item) =>
    item.etapas.includes(stageCode) && (item.territorio || "es-an") === territoryCode
  );

  modalTitle.textContent = stage?.nombre || modalTitle.textContent;
  const section = create("section", "modal-section");
  section.append(create("h3", "sr-only", stageCode === "cfgb" ? "Ámbitos" : stageCode === "infantil" ? "Áreas" : "Materias"));
  const list = create("div", "matter-list");
  section.append(list);
  list.replaceChildren(...matters.map((matter) => renderMatterCard(catalog, matter)));
  if (!matters.length) list.append(create("p", "modal-message", "Todavía no hay currículos publicados."));
  currentView = { matterSlug };
  const sections = [section];
  if (openOptions.length) sections.push(renderOpenOptions(openOptions, territoryCode));
  sections.push(renderDocuments(documents, territoryCode), renderIncidentsNote(incidents, territoryCode));
  modalContent.replaceChildren(...sections);

  if (matterSlug) {
    const selected = [...list.querySelectorAll(".matter-item")].find((item) => item.dataset.matter === matterSlug);
    if (selected) {
      selected.querySelector("details").open = true;
      requestAnimationFrame(() => selected.scrollIntoView({ block: "center" }));
    }
  }
}

function renderOpenOptions(options, territoryCode) {
  const section = create("section", "modal-section open-options");
  section.append(create("h3", "", "Optativas de desarrollo abierto"));
  section.append(create("p", "modal-muted", options[0].criterioRepresentacion));
  const list = create("div", "open-option-list");
  for (const option of options) {
    const card = create("article", "open-option");
    const heading = create("div", "open-option-heading");
    heading.append(create("h4", "", option.nombre), create("span", "open-option-status", "Concreción docente"));
    card.append(heading);
    card.append(create("p", "open-option-courses", option.cursos.map((course) => courseLabel(option.etapa, course)).join(" y ")));
    const links = create("div", "document-links");
    links.append(makeActionLink("Publicación oficial", option.fuente.urlOficial, "official"));
    if (option.fuente.archivo) {
      links.append(makeActionLink("PDF archivado", archiveUrl(territoryCode, option.fuente.archivo), "archive"));
    }
    card.append(links);
    list.append(card);
  }
  section.append(list);
  return section;
}

function renderMatterCard(catalog, matter) {
  const card = create("article", "matter-item");
  card.dataset.matter = matter.slug;
  const row = create("div", "matter-row");
  const heading = create("div", "matter-title");
  heading.append(create("span", "matter-code", matter.codigo), create("h4", "", matter.nombre));
  const jsonLink = makeLink("JSON", "./" + matter.jsonPath);
  jsonLink.className = "matter-json-link";
  jsonLink.prepend(createJsonIcon());
  row.append(heading, jsonLink);
  card.append(row);

  const details = create("details", "matter-details");
  details.append(create("summary", "", "Fuentes e incidencias"));
  const body = create("div", "matter-details-body");
  const courses = matter.ciclos?.length
    ? matter.ciclos.map((item) => cycleLabel(item.ciclo) + (item.caracter ? " (" + item.caracter + ")" : ""))
    : (matter.cursos || []).map((item) =>
        courseLabel(matter.etapa, item.curso) + (item.caracter ? " (" + item.caracter + ")" : "")
      );
  const metadata = [
    matter.anexos.length ? "Anexo " + matter.anexos.join(", ") : null,
    courses.join(", "),
  ].filter(Boolean).join(" · ");
  if (metadata) body.append(create("p", "matter-detail-meta", metadata));
  const columns = create("div", "matter-detail-columns");
  columns.append(renderMatterSources(catalog, matter), renderMatterIncidents(catalog, matter));
  body.append(columns);
  details.append(body);
  card.append(details);
  return card;
}
function renderMatterSources(catalog, matter) {
  const section = create("section", "matter-detail-section");
  section.append(create("h5", "", "Fuentes"));
  const sources = [...new Map(matter.fuentes.map((source) => [source.id, source])).values()];
  if (!sources.length) {
    section.append(create("p", "modal-muted", "No hay fuentes registradas."));
    return section;
  }
  const list = create("ul", "matter-source-list");
  for (const source of sources) {
    const item = create("li", "");
    const pages = source.paginasMateria
      ? " · págs. " + source.paginasMateria.desde + "–" + source.paginasMateria.hasta : "";
    item.append(create("p", "", "Anexo " + (source.anexo || "—") + pages));
    const actions = create("div", "matter-source-actions");
    actions.append(makeActionLink("Publicación oficial", source.urlOficial, "official"));
    const archive = catalog.documentosNormativos.find((document) =>
      document.id === source.id || document.urlOficial === source.urlOficial
    );
    if (archive?.archivo) {
      actions.append(makeActionLink("PDF archivado", archiveUrl(matter.territorio, archive.archivo), "archive"));
    }
    item.append(actions);
    list.append(item);
  }
  section.append(list);
  return section;
}

function renderMatterIncidents(catalog, matter) {
  const section = create("section", "matter-detail-section");
  section.append(create("h5", "", "Incidencias"));
  const incidents = catalog.incidencias.filter((item) => matter.incidencias.includes(item.id));
  if (!incidents.length) {
    section.append(create("p", "modal-muted", "No hay incidencias registradas para esta materia."));
    return section;
  }
  for (const incident of incidents) {
    const item = create("div", "matter-incident");
    item.append(create("strong", "", incident.id + " · " + (incident.revisada ? "Revisada" : "Pendiente")));
    item.append(create("p", "", incident.incidencia));
    item.append(create("p", "", "Decisión: " + incident.decision));
    section.append(item);
  }
  return section;
}

function renderDocuments(documents, territoryCode) {
  const section = create("section", "modal-section modal-documents");
  section.append(create("h3", "", "Documentos normativos"));
  if (!documents.length) {
    section.append(create("p", "modal-muted", "No hay documentos normativos recopilados para esta etapa."));
    return section;
  }
  const list = create("ul", "document-list");
  for (const document of documents) {
    const item = create("li", "document-item");
    item.append(create("strong", "", document.titulo));
    const links = create("div", "document-links");
    links.append(makeActionLink("Publicación oficial", document.urlOficial, "official"));
    if (document.archivo) links.append(makeActionLink("PDF archivado", archiveUrl(territoryCode, document.archivo), "archive"));
    item.append(links);
    list.append(item);
  }
  section.append(list);
  return section;
}

function renderIncidentsNote(incidents, territoryCode) {
  const section = create("section", "modal-section modal-incidents");
  section.append(create("h3", "", "Registro de incidencias"));
  section.append(create("p", "modal-muted",
    incidents.length
      ? "Las decisiones de revisión de esta etapa están documentadas en el registro de la comunidad."
      : "No hay incidencias registradas para esta etapa."
  ));
  section.append(makeActionLink("Consultar incidencias", REPOSITORY_URL + "/blob/main/incidencias/" + territoryCode + ".md", "incidents"));
  return section;
}

function makeActionLink(label, href, iconKind) {
  const link = makeLink(label, href);
  link.className = "modal-action-link";
  link.prepend(createActionIcon(iconKind));
  return link;
}

function createActionIcon(kind) {
  const namespace = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(namespace, "svg");
  svg.setAttribute("viewBox", "0 0 24 24");
  svg.setAttribute("fill", "none");
  svg.setAttribute("stroke", "currentColor");
  svg.setAttribute("stroke-width", "1.8");
  svg.setAttribute("stroke-linecap", "round");
  svg.setAttribute("stroke-linejoin", "round");
  svg.setAttribute("aria-hidden", "true");
  svg.setAttribute("focusable", "false");
  const paths = {
    official: "M14 4h6v6M20 4l-9 9M18 13v5a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h5",
    archive: "M7 2.5h7l4.5 4.5V20a1.5 1.5 0 0 1-1.5 1.5H7A1.5 1.5 0 0 1 5.5 20V4A1.5 1.5 0 0 1 7 2.5ZM14 2.5V7h4.5M9 12h6M9 16h6",
    incidents: "M8 4H5a1 1 0 0 0-1 1v15a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1V5a1 1 0 0 0-1-1h-3M9 3h6v3H9zM8 11h1m3 0h5M8 16h1m3 0h5",
  };
  const path = document.createElementNS(namespace, "path");
  path.setAttribute("d", paths[kind]);
  svg.append(path);
  return svg;
}

function makeLink(label, href) {
  const link = create("a", "", label);
  link.href = href;
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  return link;
}

function archiveUrl(territoryCode, filename) {
  return REPOSITORY_URL + "/blob/main/sources/" + territoryCode + "/normativa/" + filename;
}

function create(tag, className, value) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (value !== undefined) element.textContent = value;
  return element;
}

function createJsonIcon() {
  const namespace = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(namespace, "svg");
  svg.setAttribute("viewBox", "0 0 24 24");
  svg.setAttribute("fill", "none");
  svg.setAttribute("stroke", "currentColor");
  svg.setAttribute("stroke-width", "1.6");
  svg.setAttribute("stroke-linecap", "round");
  svg.setAttribute("stroke-linejoin", "round");
  svg.setAttribute("aria-hidden", "true");
  svg.setAttribute("focusable", "false");
  const path = document.createElementNS(namespace, "path");
  path.setAttribute("d", "M7 2.5h7l4.5 4.5V20a1.5 1.5 0 0 1-1.5 1.5H7A1.5 1.5 0 0 1 5.5 20V4A1.5 1.5 0 0 1 7 2.5ZM14 2.5V7h4.5M10 11l-2 2 2 2m4-4 2 2-2 2");
  svg.append(path);
  return svg;
}

function cycleLabel(cycle) {
  if (cycle === 1) return "Primer ciclo";
  if (cycle === 2) return "Segundo ciclo";
  return cycle + ".º ciclo";
}

function courseLabel(stage, course) {
  if (stage === "eso") return course + ".º ESO";
  if (stage === "bachillerato") return course + ".º Bachillerato";
  if (stage === "cfgb") return course + ".º CFGB";
  return course + ".º";
}


function writeStageRoute(stageCode, matterSlug) {
  const url = new URL(window.location.href);
  url.searchParams.set("territorio", activeCode);
  url.searchParams.set("etapa", stageCode);
  if (matterSlug) url.searchParams.set("materia", matterSlug);
  else url.searchParams.delete("materia");
  url.hash = activeCode;
  history.pushState({ stageModal: true }, "", url);
}

function clearStageRoute() {
  const url = new URL(window.location.href);
  url.searchParams.delete("territorio");
  url.searchParams.delete("etapa");
  url.searchParams.delete("materia");
  url.hash = activeCode || "";
  history.replaceState(null, "", url);
}

function readRoute() {
  const params = new URLSearchParams(window.location.search);
  const requestedCode = params.get("territorio") || window.location.hash.slice(1);
  const selected = folders.find((folder) => folder.dataset.community === requestedCode);
  const code = selected?.querySelector(".folder-card-toggle") ? requestedCode : null;
  const stage = params.get("etapa");
  const matter = params.get("materia");
  return { code, stage, matter };
}

function syncFromLocation() {
  const route = readRoute();
  setExpanded(route.code);
  const available = folders.find((folder) => folder.dataset.community === route.code)
    ?.classList.contains("folder-card--available");
  const validStage = stageGrid.querySelector('[data-stage="' + route.stage + '"]');
  if (available && validStage) {
    if (!stageModal.open || activeStage !== route.stage || currentView?.matterSlug !== route.matter) {
      openStage(route.stage, route.matter, false);
    }
  } else if (stageModal.open) {
    skipCloseRouteUpdate = true;
    stageModal.close();
  }
}

for (const toggle of toggles) {
  toggle.addEventListener("click", () => {
    const code = toggle.closest(".folder-card").dataset.community;
    setExpanded(activeCode === code ? null : code);
    const url = new URL(window.location.href);
    url.search = "";
    url.hash = activeCode || "";
    history.replaceState(null, "", url);
  });
}

for (const button of stageButtons) {
  button.addEventListener("click", () => {
    const stageCode = button.closest(".stage-card").dataset.stage;
    openStage(stageCode);
  });
}

modalClose.addEventListener("click", () => stageModal.close());
stageModal.addEventListener("click", (event) => {
  if (event.target === stageModal) stageModal.close();
});
stageModal.addEventListener("close", () => {
  ++renderToken;
  currentView = null;
  activeStage = null;
  if (skipCloseRouteUpdate) skipCloseRouteUpdate = false;
  else clearStageRoute();
  if (modalTrigger && !modalTrigger.disabled && !expansion.hidden) modalTrigger.focus();
});

window.addEventListener("resize", () => {
  if (activeCode) setExpanded(activeCode);
});
window.addEventListener("popstate", syncFromLocation);
window.addEventListener("hashchange", syncFromLocation);

syncFromLocation();
