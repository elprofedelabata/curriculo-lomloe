import { createHash } from "node:crypto";
import { access, readFile } from "node:fs/promises";
import { resolve } from "node:path";

const root = resolve(import.meta.dirname, "..");
const dist = resolve(root, "dist");
const catalog = JSON.parse(await readFile(resolve(dist, "catalogo.json"), "utf8"));
const failures = [];

check(catalog.version === "1.7.0", "Versión inesperada del catálogo.");
check(catalog.territorios.length === 17, `Se esperaban 17 territorios y hay ${catalog.territorios.length}.`);
check(catalog.progreso.length === 17, `Se esperaban 17 comunidades y hay ${catalog.progreso.length}.`);
check(catalog.etapas.length === 25, `Se esperaban 25 etapas territoriales y hay ${catalog.etapas.length}.`);
check(catalog.materias.length === 410, `Se esperaban 410 materias y hay ${catalog.materias.length}.`);
check(catalog.materias.filter((item) => item.etapa === "infantil").length === 15, "El catálogo de Infantil no contiene 15 áreas territoriales.");
check(catalog.materias.filter((item) => item.territorio === "es-ar" && item.etapa === "infantil").length === 3, "El catálogo de Aragón no contiene sus 3 áreas de Infantil.");
check(catalog.materias.filter((item) => item.territorio === "es-as" && item.etapa === "infantil").length === 3, "El catálogo de Asturias no contiene sus 3 áreas de Infantil.");
check(catalog.materias.filter((item) => item.territorio === "es-ib" && item.etapa === "infantil" && item.revision?.estado === "revisado").length === 3, "El catálogo de Illes Balears no contiene sus 3 áreas de Infantil revisadas.");
check(catalog.materias.filter((item) => item.territorio === "es-cn" && item.etapa === "infantil" && item.revision?.estado === "borrador").length === 3, "El catálogo de Canarias no contiene sus 3 áreas de Infantil en borrador.");
check(catalog.incidencias.filter((item) => item.id.startsWith("CN-INF-") && !item.revisada).length === 0, "Las incidencias de Infantil de Canarias deben estar revisadas.");
check(catalog.incidencias.filter((item) => item.id.startsWith("CN-PRIM-") && !item.revisada).length === 0, "Las incidencias de Primaria de Canarias deben estar revisadas.");
const canaryGrowth = JSON.parse(await readFile(resolve(dist, "data/es-cn/infantil/materias/crecimiento-en-armonia.json"), "utf8"));
const canaryAffectiveSabers = canaryGrowth.desarrollos.find((item) => item.ciclo === 1)?.bloquesSaberes.find((item) => item.codigo === "B")?.saberes;
check(canaryAffectiveSabers?.map((item) => item.numeracionFuente).join(",") === "1,2,3", "La numeración del bloque afectivo canario debe estar normalizada como 1, 2, 3.");
const canaryExploration = JSON.parse(await readFile(resolve(dist, "data/es-cn/infantil/materias/descubrimiento-y-exploracion-del-entorno.json"), "utf8"));
const canaryScientificBlock = canaryExploration.desarrollos.find((item) => item.ciclo === 1)?.bloquesCompetenciales.find((item) => item.competenciaEspecificaRef === "ce-2");
check(canaryScientificBlock?.competenciasClaveRefs.includes("CPSAA") && !canaryScientificBlock.competenciasClaveRefs.includes("CPSSAA"), "La vinculación de DEE C2 debe usar CPSAA.");
check(catalog.incidencias.filter((item) => item.territorio === "es-ib" && !item.revisada).length === 0, "No deben quedar incidencias baleares pendientes de revisión.");
check(catalog.materias.filter((item) => item.etapa === "primaria").length === 48, "El catálogo de Primaria no contiene 48 materias territoriales.");
check(catalog.materias.filter((item) => item.territorio === "es-cn" && item.etapa === "primaria").length === 9, "El catálogo de Canarias no contiene sus 9 áreas de Primaria.");
check(catalog.materias.filter((item) => item.territorio === "es-ib" && item.etapa === "primaria" && item.revision?.estado === "revisado").length === 8, "El catálogo de Illes Balears no contiene sus 8 áreas de Primaria revisadas.");
const balearValues = catalog.materias.find((item) => item.id === "es-ib.primaria.educacio-en-valors-civics-i-etics");
check(balearValues?.ciclos.length === 1 && balearValues.ciclos[0].ciclo === 3 && balearValues.cursos.length === 0, "Educación en Valores debe figurar como área del tercer ciclo, no como obligatoria en ambos cursos.");
const balearValuesDocument = JSON.parse(await readFile(resolve(dist, "data/es-ib/primaria/materias/educacio-en-valors-civics-i-etics.json"), "utf8"));
const balearValuesDevelopments = balearValuesDocument.desarrollos;
check(balearValuesDevelopments.length === 1 && balearValuesDevelopments[0].ciclo === 3 && !("curso" in balearValuesDevelopments[0]), "Valores debe tener un solo desarrollo canónico del tercer ciclo.");
check(balearValuesDevelopments[0].criteriosEvaluacion.length === 11, "Faltan criterios de Valores del tercer ciclo.");
const balearValuesKnowledge = balearValuesDevelopments[0].bloquesSaberes.flatMap((block) => [
  ...(block.saberes || []),
  ...(block.apartados || []).flatMap((part) => part.saberes || []),
]);
check(balearValuesKnowledge.length === 42 && new Set(balearValuesKnowledge.map((item) => item.id)).size === 42, "Los 42 saberes de Valores deben conservarse sin duplicados.");
check(balearValuesKnowledge.filter((item) => item.cursoOrientativo?.includes(5)).length === 18 && balearValuesKnowledge.filter((item) => item.cursoOrientativo?.includes(6)).length === 24, "Las marcas orientativas de 5.º y 6.º no coinciden con la tabla.");
check(catalog.materias.filter((item) => item.territorio === "es-ar" && item.etapa === "primaria").length === 14, "El catálogo de Aragón no contiene sus 14 currículos de Primaria.");
check(catalog.materias.filter((item) => item.territorio === "es-as" && item.etapa === "primaria").length === 10, "El catálogo de Asturias no contiene sus 10 currículos de Primaria.");
check(catalog.materias.filter((item) => item.territorio === "es-as" && item.etapa === "eso").length === 24, "El catálogo de Asturias no contiene sus 24 currículos de ESO.");
check(catalog.materias.filter((item) => item.etapa === "eso").length === 121, "El catálogo de ESO no contiene 121 materias territoriales.");
check(catalog.materias.filter((item) => item.territorio === "es-ib" && item.etapa === "eso" && item.revision?.estado === "revisado").length === 27, "El catálogo de Illes Balears no contiene sus 27 materias de ESO revisadas.");
check(catalog.materias.filter((item) => item.territorio === "es-ar" && item.etapa === "eso").length === 38, "El catálogo de Aragón no contiene sus 38 currículos de ESO.");
check(catalog.materias.filter((item) => item.etapa === "bachillerato").length === 218, "El catálogo de Bachillerato no contiene 218 materias territoriales.");
check(catalog.materias.filter((item) => item.territorio === "es-ib" && item.etapa === "bachillerato" && item.revision?.estado === "revisado").length === 53, "El catálogo de Illes Balears no contiene sus 53 materias de Bachillerato revisadas.");
const activitatFisica = JSON.parse(await readFile(resolve(dist, "data/es-ib/bachillerato/materias/activitat-fisica-oci-i-salut.json"), "utf8"));
check(
  activitatFisica.introduccion.ca[0].includes("de la matèria d’Activitat Física, Oci i Salut") &&
    !activitatFisica.introduccion.ca[0].includes("de la matèria d’Educació Física"),
  "La introducción de Activitat Física, Oci i Salut conserva una referencia residual a Educació Física.",
);
for (const [slug, course, blockCode, prefix] of [
  ["cor-i-tecnica-vocal", 2, "C", "Gestió de l'ansietat escènica."],
  ["dibuix-tecnic", 2, "C", "Projectes en col·laboració."],
  ["dibuix-tecnic", 2, "C", "Plans de muntatge senzills."],
  ["dibuix-tecnic", 2, "D", "Aplicacions CAD."],
  ["historia-de-l-art", 2, "C", "La dona com a artista."],
  ["tecniques-d-expressio-graficoplastica", 2, "A", "Estratègies d’investigació,"],
]) {
  const document = JSON.parse(await readFile(resolve(dist, "data/es-ib/bachillerato/materias", slug + ".json"), "utf8"));
  const development = document.desarrollos.find((item) => item.curso === course);
  const block = development?.bloquesSaberes.find((item) => item.codigo === blockCode);
  const parts = block?.apartados?.filter((item) => item.nombre.ca.startsWith(prefix));
  check(
    parts?.length === 1 && parts[0].saberes.length === 1 &&
      parts[0].nombre.ca === parts[0].saberes[0].texto.ca,
    "La fila " + prefix + " debe tener apartado propio con un único saber idéntico.",
  );
}
for (const slug of ["projecte-empresarial", "treball-d-investigacio-analisi-i-creativitat"]) {
  const document = JSON.parse(await readFile(resolve(dist, "data/es-ib/bachillerato/materias", slug + ".json"), "utf8"));
  check(
    document.competenciasEspecificas.length > 0 &&
      document.competenciasEspecificas.every((item) => !("descripcion" in item) && item.descriptoresOperativosRefs.length > 0),
    "Las CE de " + slug + " deben conservar sus descriptores sin inventar una descripción narrativa.",
  );
}
const tecniquesExperimentals = JSON.parse(await readFile(resolve(dist, "data/es-ib/bachillerato/materias/tecniques-experimentals.json"), "utf8"));
check(
  tecniquesExperimentals.desarrollos[0].bloquesSaberes.length === 1 &&
    tecniquesExperimentals.desarrollos[0].bloquesSaberes[0].apartados.length === 10,
  "Tècniques Experimentals debe conservar sus diez epígrafes bajo un bloque interno.",
);
check(catalog.materias.filter((item) => item.territorio === "es-ar" && item.etapa === "bachillerato").length === 59, "El catálogo de Aragón no contiene sus 59 currículos de Bachillerato.");
check(catalog.materias.filter((item) => item.territorio === "es-as" && item.etapa === "bachillerato").length === 48, "El catálogo de Asturias no contiene sus 48 currículos desarrollados de Bachillerato.");
check(catalog.materias.filter((item) => item.etapa === "cfgb").length === 8, "El catálogo de CFGB no contiene 8 ámbitos territoriales.");
check(catalog.materias.filter((item) => item.territorio === "es-ar" && item.etapa === "cfgb").length === 2, "El catálogo de Aragón no contiene sus 2 ámbitos de CFGB.");
check(catalog.materias.filter((item) => item.territorio === "es-as" && item.etapa === "cfgb").length === 2, "El catálogo de Asturias no contiene sus 2 ámbitos de CFGB.");
check(catalog.materias.filter((item) => item.territorio === "es-ib" && item.etapa === "cfgb" && item.revision?.estado === "revisado").length === 2, "Faltan los dos ámbitos de CFGB revisados de Illes Balears.");
check(catalog.materias.filter((item) => item.territorio === "es-ar" && item.revision?.estado === "revisado").length === 116, "Los 116 JSON de Aragón deben constar como revisados.");
check(catalog.materias.filter((item) => item.territorio === "es-ib" && item.revision?.estado === "revisado").length === 93, "Los 93 JSON de Illes Balears deben constar como revisados.");
for (const [slug, criteria, sabers, blocks] of [
  ["ciencies-aplicades", 18, 55, 11],
  ["comunicacio-i-ciencies-socials", 23, 89, 4],
]) {
  const document = JSON.parse(await readFile(resolve(dist, "data/es-ib/cfgb/materias", slug + ".json"), "utf8"));
  check(document.competenciasEspecificas.length === 8, "CFGB balear debe contener ocho competencias específicas en " + slug + ".");
  check(document.vigencia.entradaEnVigor === null && document.vigencia.aplicableDesdeCurso === null, "No se deben inventar fechas de vigencia del PDF institucional.");
  check(document.fuentes[0].tipo === "otro" && !("numero" in document.fuentes[0]) && !("fechaPublicacion" in document.fuentes[0]), "El PDF institucional de CFGB no debe presentarse como publicación del BOIB.");
  check(document.desarrollos.length === 2 && document.desarrollos.every((item) => item.criteriosEvaluacion.length === criteria && item.bloquesSaberes.length === blocks), "Faltan criterios o bloques de CFGB en " + slug + ".");
  check(document.desarrollos.every((item) => item.bloquesSaberes.flatMap((block) => block.saberes || block.apartados.flatMap((part) => part.saberes)).length === sabers), "Faltan saberes de CFGB en " + slug + ".");
}
const balearSocial = JSON.parse(await readFile(resolve(dist, "data/es-ib/cfgb/materias/comunicacio-i-ciencies-socials.json"), "utf8"));
check(balearSocial.competenciasEspecificas[7].descriptoresOperativosRefs.includes("CCL5") && balearSocial.competenciasEspecificas[3].descriptoresOperativosRefs.includes("CCL3") && !balearSocial.competenciasEspecificas[3].descriptoresOperativosRefs.includes("CL3"), "Las dos incidencias de descriptores de CFGB no se reflejan como se documentó.");
check(catalog.incidencias.filter((item) => item.territorio === "es-ib" && item.etapa === "cfgb").length === 2, "Faltan las dos incidencias de CFGB de Illes Balears.");
check(catalog.materias.filter((item) => item.territorio === "es-as" && item.revision?.estado === "revisado").length === 87, "Los 87 JSON publicados de Asturias deben constar como revisados.");
check(catalog.optativasAbiertas.length === 3, "Faltan las tres fichas informativas de optativas abiertas.");
check(catalog.optativasAbiertas.every((item) => item.territorio === "es-as" && item.etapa === "bachillerato" && item.estado === "concrecion-docente"), "Las optativas abiertas tienen una clasificación incorrecta.");
check(catalog.optativasAbiertas.every((item) => item.fuente.id === "es-as-bachillerato-decreto-60-2022" && item.fuente.urlOficial && item.fuente.archivo), "Las optativas abiertas deben remitir al Decreto 60/2022.");
check(catalog.optativasAbiertas.every((item) => !catalog.materias.some((matter) => matter.id === item.id)), "Una optativa abierta se presenta indebidamente como currículo cerrado.");
check(catalog.etapas.find((item) => item.territorio === "es-as" && item.codigo === "bachillerato")?.optativasAbiertas === 3, "La etapa de Bachillerato de Asturias no refleja sus tres optativas abiertas.");
const asturiasProgress = catalog.progreso.find((item) => item.territorio === "es-as");
check(asturiasProgress?.etapas.bachillerato.estado === "completo" && asturiasProgress.etapas.bachillerato.etiqueta === "48/48", "Los 48 currículos estructurables de Bachillerato de Asturias deben figurar como completos.");
check(catalog.incidencias.length === 224, `Se esperaban 224 incidencias y hay ${catalog.incidencias.length}.`);
check(catalog.incidencias.every((item) => typeof item.revisada === "boolean"), "Hay incidencias sin estado de revisión válido.");
check(new Set(catalog.materias.map((item) => item.id)).size === catalog.materias.length, "Hay ID de materia duplicados.");
check(new Set(catalog.incidencias.map((item) => item.id)).size === catalog.incidencias.length, "Hay ID de incidencia duplicados.");

for (const file of [
  "index.html",
  "styles.css",
  "site.js",
  "catalogo.json",
  "schemas/materia.schema.json",
  "schemas/optativas-abiertas.schema.json",
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
check(siteJs.includes("renderOpenOptions(openOptions, territoryCode)") && siteJs.includes('"Optativas de desarrollo abierto"'), "El modal de Bachillerato debe mostrar las fichas informativas separadas.");
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
check(css.includes(".open-option-list") && css.includes(".open-option-status"), "Faltan los estilos de las optativas con desarrollo abierto.");
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
check(html.includes('<li class="folder-card folder-card--available" data-community="es-as">'), "Asturias no aparece como disponible.");
check(html.includes('<li class="folder-card folder-card--available" data-community="es-ib">'), "Illes Balears no aparece como disponible.");
for (const code of ["es-cn"]) {
  check(html.includes('<li class="folder-card folder-card--preview" data-community="' + code + '">'), 'Falta la carpeta temporal ' + code + '.');
}
check((html.match(/folder-card--preview/g) || []).length === 1, "Debe haber una carpeta temporal.");
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

for (const option of catalog.optativasAbiertas) {
  await exists(option.fichaPath);
  const ficha = JSON.parse(await readFile(resolve(dist, option.fichaPath), "utf8"));
  check(ficha.$schema === "../../../schemas/optativas-abiertas.schema.json" && ficha.fuenteId === option.fuente.id, "La ficha informativa no remite a su esquema y fuente correctos.");
  check(ficha.optativas.some((item) => item.id === option.id), "La ficha informativa no contiene " + option.id + ".");
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
