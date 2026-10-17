import { createHash } from "node:crypto";
import { access, readFile } from "node:fs/promises";
import { resolve } from "node:path";

const root = resolve(import.meta.dirname, "..");
const dist = resolve(root, "dist");
const catalog = JSON.parse(await readFile(resolve(dist, "catalogo.json"), "utf8"));
const failures = [];

check(catalog.version === "1.5.0", "Versión inesperada del catálogo.");
check(catalog.territorios.length === 17, `Se esperaban 17 territorios y hay ${catalog.territorios.length}.`);
check(catalog.progreso.length === 17, `Se esperaban 17 comunidades y hay ${catalog.progreso.length}.`);
check(catalog.etapas.length === 10, `Se esperaban 10 etapas territoriales y hay ${catalog.etapas.length}.`);
check(catalog.materias.length === 157, `Se esperaban 157 materias y hay ${catalog.materias.length}.`);
check(catalog.materias.filter((item) => item.etapa === "infantil").length === 6, "El catálogo de Infantil no contiene 6 áreas territoriales.");
check(catalog.materias.filter((item) => item.territorio === "es-ar" && item.etapa === "infantil").length === 3, "El catálogo de Aragón no contiene sus 3 áreas de Infantil.");
check(catalog.materias.filter((item) => item.etapa === "primaria").length === 21, "El catálogo de Primaria no contiene 21 materias territoriales.");
check(catalog.materias.filter((item) => item.territorio === "es-ar" && item.etapa === "primaria").length === 14, "El catálogo de Aragón no contiene sus 14 currículos de Primaria.");
check(catalog.materias.filter((item) => item.etapa === "eso").length === 70, "El catálogo de ESO no contiene 70 materias territoriales.");
check(catalog.materias.filter((item) => item.territorio === "es-ar" && item.etapa === "eso").length === 38, "El catálogo de Aragón no contiene sus 38 currículos de ESO.");
check(catalog.materias.filter((item) => item.etapa === "bachillerato").length === 58, "El catálogo de Bachillerato no contiene 58 materias.");
check(catalog.materias.filter((item) => item.etapa === "cfgb").length === 2, "El catálogo de CFGB no contiene 2 ámbitos.");
check(catalog.incidencias.length === 117, `Se esperaban 117 incidencias y hay ${catalog.incidencias.length}.`);
check(catalog.incidencias.every((item) => typeof item.revisada === "boolean"), "Hay incidencias sin estado de revisión válido.");
check(new Set(catalog.materias.map((item) => item.id)).size === catalog.materias.length, "Hay ID de materia duplicados.");
check(new Set(catalog.incidencias.map((item) => item.id)).size === catalog.incidencias.length, "Hay ID de incidencia duplicados.");

for (const file of [
  "index.html",
  "styles.css",
  "site.js",
  "catalogo.json",
  "schemas/materia.schema.json",
  "sitemap.xml",
  "robots.txt",
  ".nojekyll",
]) {
  await exists(file);
}

const html = await readFile(resolve(dist, "index.html"), "utf8");
check(html.includes('id="contenido"'), "La portada no contiene el área principal.");
check(html.includes('class="folder-grid"'), "La portada no contiene la cuadrícula de comunidades.");
check(/<script src="\.\/site\.js\?v=[a-f0-9]{12}" defer><\/script>/.test(html), "Falta una versión explícita del script del desplegable.");
check((html.match(/aria-controls="community-stages"/g) || []).length === 5, "Las cinco carpetas interactivas deben tener un control desplegable accesible.");
check(html.includes('<li class="community-expansion" id="community-stages" hidden>'), "Falta el panel desplegable compartido.");
check(html.includes('class="preview-note" hidden'), "Las maquetas deben avisar de que aún no tienen datos.");
check(!html.includes('folder-toggle-icon'), "La carpeta no debe mostrar una flecha de desplegable.");
check(!html.includes('id="community-view"'), "La vista separada de Andalucía debe haberse retirado.");
check(html.indexOf('data-community="es-cn"') < html.indexOf('id="community-stages"') && html.indexOf('id="community-stages"') < html.indexOf('data-community="es-cb"'), "El panel de prueba debe partir de la primera fila.");
const stageCards = [...html.matchAll(/<li class="stage-card" data-stage="([a-z]+)"><button class="stage-card-button" type="button" aria-haspopup="dialog"><span>([^<]+)<\/span><\/button><\/li>/g)];
check(stageCards.length === 5, "El interior de Andalucía debe mostrar cinco etapas.");
check(html.includes('<dialog class="stage-modal" id="stage-modal" aria-labelledby="stage-modal-title">'), "Falta el modal de las etapas.");
check(html.includes('<div class="stage-modal-content"></div>'), "Falta el contenedor dinámico del modal.");
check(new Set(stageCards.map((match) => match[1])).size === 5, "Hay etapas duplicadas en el interior.");
for (const stage of catalog.etapas) {
  const label = { eso: "ESO", cfgb: "CFGB" }[stage.codigo] || stage.nombre;
  check(stageCards.some((match) => match[1] === stage.codigo && match[2] === label), `Falta la etapa ${label} en el interior.`);
}
const siteJs = await readFile(resolve(dist, "site.js"), "utf8");
const scriptHash = createHash("sha256").update(siteJs).digest("hex").slice(0, 12);
check(html.includes('src="./site.js?v=' + scriptHash + '"'), "El HTML no apunta a la versión actual del script.");
check(siteJs.includes('lastInRow.after(expansion)') && siteJs.includes('aria-expanded'), "El panel no sigue la fila de la carpeta seleccionada.");
check(siteJs.includes('stageModal.showModal()') && siteJs.includes('stageModal.close()'), "Las subcarpetas no abren y cierran el modal.");
check(siteJs.includes('button.disabled = preview'), "Las subcarpetas de maqueta deben permanecer inactivas.");
check(siteJs.includes('fetch("./catalogo.json")') && siteJs.includes('renderMatterCard') && siteJs.includes('renderDocuments'), "El modal debe obtener y listar los datos del catálogo.");
check(siteJs.includes('writeStageRoute') && siteJs.includes('syncFromLocation'), "Faltan las rutas compartibles de las etapas.");
check(siteJs.includes('create("span", "matter-code", matter.codigo)') && siteJs.includes('jsonLink.prepend(createJsonIcon())'), "Cada materia debe mostrar su abreviatura y el icono SVG del JSON.");
check(siteJs.includes('makeActionLink("Publicación oficial"') && siteJs.includes('makeActionLink("PDF archivado"') && siteJs.includes('makeActionLink("Consultar incidencias"'), "Normativa e incidencias deben enlazarse como botones con iconos.");
check(siteJs.includes('"/blob/main/incidencias/" + territoryCode + ".md"'), "El modal debe enlazar el registro de incidencias de la comunidad seleccionada.");
check(siteJs.includes('actions.append(makeActionLink("Publicación oficial"') && siteJs.includes('actions.append(makeActionLink("PDF archivado"'), "Las fuentes desplegables deben usar los mismos botones con iconos.");
const css = await readFile(resolve(dist, "styles.css"), "utf8");
const styleHash = createHash("sha256").update(css).digest("hex").slice(0, 12);
check(html.includes('href="./styles.css?v=' + styleHash + '"'), "El HTML no apunta a la versión actual del CSS.");
for (const stage of catalog.etapas) {
  check(css.includes('.stage-card[data-stage="' + stage.codigo + '"]'), "Falta el icono de la etapa " + stage.codigo + ".");
  await exists("assets/stages/" + stage.codigo + ".svg");
}
check(css.includes(".community-expansion:not(.community-expansion--preview) .stage-card:hover") && css.includes(".stage-card:hover::after"), "Falta el hover de las subcarpetas reales.");
check(css.includes(".stage-card-button:focus-visible") && css.includes(".stage-modal::backdrop"), "Faltan los estilos accesibles del modal.");
check(css.includes(".matter-list") && css.includes(".matter-detail-columns") && !css.includes(".matter-search"), "La lista de materias debe ser compacta y sin buscador.");
check(css.includes(".matter-details[open] {") && css.includes("background: #f5f9f5;") && css.includes("margin: 5px 0 13px 14px;"), "El desplegable de cada materia debe tener fondo y sangría.");
check(css.includes(".matter-code {") && css.includes(".matter-json-link svg {"), "Faltan los estilos de la abreviatura o del icono JSON.");
const badgeCss = css.match(/\.matter-code \{([^}]+)\}/)?.[1] || "";
const jsonButtonCss = css.match(/\.matter-json-link \{([^}]+)\}/)?.[1] || "";
check(badgeCss.includes("color: #fff;") && jsonButtonCss.includes("color: #fff;"), "La abreviatura y el botón JSON deben conservar texto blanco.");
const secondaryButtonCss = css.match(/\.modal-action-link \{([^}]+)\}/)?.[1] || "";
check(css.includes(".modal-action-link svg {") && css.includes(".matter-source-actions {") && secondaryButtonCss.includes("background: #4e7659;") && secondaryButtonCss.includes("color: #fff;"), "Falta el estilo secundario con SVG y texto blanco.");
check(css.includes(":is(.folder-card--available, .folder-card--preview):not(.folder-card--open):hover"), "Falta el efecto hover de las carpetas interactivas.");
check(css.includes(".folder-card--preview.folder-card--open") && css.includes(".folder-card--preview.folder-card--open::after"), "La carpeta abierta debe mantener el estado hover.");
check(css.includes(".community-expansion {") && css.includes("grid-column: 1 / -1;"), "El panel de etapas no ocupa una fila propia de la cuadrícula.");
check(css.includes("--shadow-left") && css.includes("--shadow-right"), "La sombra no sigue la carpeta seleccionada.");
check(css.includes(".folder-card--open .folder-card-toggle::before") && !css.includes(".folder-card--open .folder-card-toggle::after"), "La carpeta abierta debe mostrar una hoja sin la solapa anterior.");
check(css.includes("transform: translateY(45px) rotate(-2deg) scale(.95)") && css.includes("transition: opacity .22s ease, transform .34s") && css.includes("@media (prefers-reduced-motion: reduce)"), "Falta la animación accesible de apertura del folio.");
check(css.includes(".folder-card--disabled::after") && css.includes("grayscale(1)"), "Falta la escala de grises de las carpetas vacías.");
const folderCodes = [...html.matchAll(/<li class="folder-card folder-card--(?:available|preview|disabled)" data-community="(es-[a-z]{2})">/g)]
  .map((match) => match[1]);
check(folderCodes.length === catalog.territorios.length, "La portada no muestra las 17 carpetas.");
check(new Set(folderCodes).size === catalog.territorios.length, "Hay carpetas de comunidad duplicadas.");
check(html.includes('<li class="folder-card folder-card--available" data-community="es-an">'), "Andalucía no aparece como disponible.");
check(html.includes('<li class="folder-card folder-card--available" data-community="es-ar">'), "Aragón no aparece como disponible.");
for (const code of ["es-as", "es-ib", "es-cn"]) {
  check(html.includes('<li class="folder-card folder-card--preview" data-community="' + code + '">'), 'Falta la carpeta temporal ' + code + '.');
}
check((html.match(/folder-card--preview/g) || []).length === 3, "Debe haber tres carpetas temporales.");
check((html.match(/folder-card--disabled/g) || []).length === 12, "Las 12 carpetas restantes deben estar deshabilitadas.");
check(!html.includes('es-an ·'), "La carpeta de Andalucía debe mostrar solo su código.");
for (const territory of catalog.territorios) {
  check(folderCodes.includes(territory.codigo), `Falta la carpeta de ${territory.nombre}.`);
  check(html.includes(`<span class="folder-name">${territory.nombre}</span>`), `Falta el nombre de ${territory.nombre}.`);
  check(css.includes(`data-community="${territory.codigo}"`), `Falta el estilo de bandera de ${territory.nombre}.`);
  await exists(`assets/flags/${territory.codigo}.png`);
}
await exists("assets/flags/README.md");

const sitemap = await readFile(resolve(dist, "sitemap.xml"), "utf8");
check((sitemap.match(/<url>/g) || []).length === 1, "El sitemap debe contener solo la aplicación principal.");

for (const stage of catalog.etapas) {
  check(
    stage.appPath === `?territorio=${stage.territorio}&etapa=${stage.codigo}#${stage.territorio}`,
    `Ruta de aplicación incorrecta para ${stage.territorio}.${stage.codigo}.`,
  );
  check(!("pagePath" in stage), `La etapa ${stage.codigo} conserva una ruta multipágina obsoleta.`);
}

for (const matter of catalog.materias) {
  await exists(matter.jsonPath);
  const data = JSON.parse(await readFile(resolve(dist, matter.jsonPath), "utf8"));
  check(data.id === matter.id, `El ID de ${matter.jsonPath} no coincide con el catálogo.`);
  check(
    matter.appPath === `?territorio=${matter.territorio}&etapa=${matter.etapa}&materia=${matter.slug}#${matter.territorio}`,
    `Ruta de aplicación incorrecta para ${matter.id}.`,
  );
  check(!("pagePath" in matter), `La materia ${matter.id} conserva una ruta multipágina obsoleta.`);

  for (const incidentId of matter.incidencias) {
    check(
      catalog.incidencias.some((incident) => incident.id === incidentId),
      `Incidencia inexistente ${incidentId} en ${matter.id}.`,
    );
  }
}

if (failures.length) {
  console.error(`Validación fallida con ${failures.length} problema(s):`);
  failures.forEach((failure) => console.error(`- ${failure}`));
  process.exit(1);
}

console.log(`Sitio estático válido: ${catalog.materias.length} materias, ${catalog.etapas.length} etapas publicadas, ${catalog.incidencias.length} incidencias y ${catalog.progreso.length} comunidades.`);

function check(condition, message) {
  if (!condition) failures.push(message);
}

async function exists(relativePath) {
  try {
    await access(resolve(dist, relativePath));
  } catch {
    failures.push(`Falta ${relativePath}.`);
  }
}
