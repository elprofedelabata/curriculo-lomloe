import { access, readFile } from "node:fs/promises";
import { resolve } from "node:path";

const root = resolve(import.meta.dirname, "..");
const dist = resolve(root, "dist");
const catalog = JSON.parse(await readFile(resolve(dist, "catalogo.json"), "utf8"));
const failures = [];

check(catalog.version === "1.0.0", "Versión inesperada del catálogo.");
check(catalog.progreso.length === 17, `Se esperaban 17 comunidades y hay ${catalog.progreso.length}.`);
check(catalog.etapas.length === 2, `Se esperaban 2 etapas publicadas y hay ${catalog.etapas.length}.`);
check(catalog.materias.length === 88, `Se esperaban 88 materias y hay ${catalog.materias.length}.`);
check(catalog.materias.filter((item) => item.etapa === "eso").length === 30, "El catálogo de ESO no contiene 30 materias.");
check(catalog.materias.filter((item) => item.etapa === "bachillerato").length === 58, "El catálogo de Bachillerato no contiene 58 materias.");
check(catalog.incidencias.length === 35, `Se esperaban 35 incidencias y hay ${catalog.incidencias.length}.`);
check(catalog.incidencias.every((item) => item.revisada), "Hay incidencias sin revisar en el catálogo publicado.");
check(new Set(catalog.materias.map((item) => item.id)).size === catalog.materias.length, "Hay ID de materia duplicados.");
check(new Set(catalog.incidencias.map((item) => item.id)).size === catalog.incidencias.length, "Hay ID de incidencia duplicados.");

await exists("index.html");
await exists("app.js");
await exists("styles.css");
await exists("schemas/materia.schema.json");
await exists("sitemap.xml");
await exists("robots.txt");
await exists(".nojekyll");

for (const stage of catalog.etapas) {
  await exists(`${stage.pagePath}index.html`);
  const html = await readFile(resolve(dist, stage.pagePath, "index.html"), "utf8");
  check(html.includes('data-page="stage"'), `La página ${stage.pagePath} no está marcada como etapa.`);
  check(html.includes('<base href="../../" />'), `Base incorrecta en ${stage.pagePath}.`);
}

for (const matter of catalog.materias) {
  await exists(matter.jsonPath);
  await exists(`${matter.pagePath}index.html`);
  const data = JSON.parse(await readFile(resolve(dist, matter.jsonPath), "utf8"));
  check(data.id === matter.id, `El ID de ${matter.jsonPath} no coincide con el catálogo.`);
  const html = await readFile(resolve(dist, matter.pagePath, "index.html"), "utf8");
  check(html.includes('data-page="matter"'), `La página ${matter.pagePath} no está marcada como materia.`);
  check(html.includes('<base href="../../../" />'), `Base incorrecta en ${matter.pagePath}.`);
  for (const incidentId of matter.incidencias) {
    check(catalog.incidencias.some((incident) => incident.id === incidentId), `Incidencia inexistente ${incidentId} en ${matter.id}.`);
  }
}

if (failures.length) {
  console.error(`Validación fallida con ${failures.length} problema(s):`);
  failures.forEach((failure) => console.error(`- ${failure}`));
  process.exit(1);
}

console.log(`Sitio válido: ${catalog.materias.length} materias, ${catalog.etapas.length} etapas, ${catalog.incidencias.length} incidencias y ${catalog.progreso.length} comunidades.`);

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