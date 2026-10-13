import { access, readFile } from "node:fs/promises";
import { resolve } from "node:path";

const root = resolve(import.meta.dirname, "..");
const dist = resolve(root, "dist");
const catalog = JSON.parse(await readFile(resolve(dist, "catalogo.json"), "utf8"));
const failures = [];

check(catalog.version === "1.4.0", "Versión inesperada del catálogo.");
check(catalog.territorios.length === 17, `Se esperaban 17 territorios y hay ${catalog.territorios.length}.`);
check(catalog.progreso.length === 17, `Se esperaban 17 comunidades y hay ${catalog.progreso.length}.`);
check(catalog.etapas.length === 5, `Se esperaban 5 etapas publicadas y hay ${catalog.etapas.length}.`);
check(catalog.materias.length === 100, `Se esperaban 100 materias y hay ${catalog.materias.length}.`);
check(catalog.materias.filter((item) => item.etapa === "infantil").length === 3, "El catálogo de Infantil no contiene 3 áreas.");
check(catalog.materias.filter((item) => item.etapa === "primaria").length === 7, "El catálogo de Primaria no contiene 7 materias.");
check(catalog.materias.filter((item) => item.etapa === "eso").length === 30, "El catálogo de ESO no contiene 30 materias.");
check(catalog.materias.filter((item) => item.etapa === "bachillerato").length === 58, "El catálogo de Bachillerato no contiene 58 materias.");
check(catalog.materias.filter((item) => item.etapa === "cfgb").length === 2, "El catálogo de CFGB no contiene 2 ámbitos.");
check(catalog.incidencias.length === 78, `Se esperaban 78 incidencias y hay ${catalog.incidencias.length}.`);
check(catalog.incidencias.every((item) => typeof item.revisada === "boolean"), "Hay incidencias sin estado de revisión válido.");
check(new Set(catalog.materias.map((item) => item.id)).size === catalog.materias.length, "Hay ID de materia duplicados.");
check(new Set(catalog.incidencias.map((item) => item.id)).size === catalog.incidencias.length, "Hay ID de incidencia duplicados.");

for (const file of [
  "index.html",
  "app.js",
  "styles.css",
  "catalogo.json",
  "schemas/materia.schema.json",
  "sitemap.xml",
  "robots.txt",
  ".nojekyll",
]) {
  await exists(file);
}

const html = await readFile(resolve(dist, "index.html"), "utf8");
check(html.includes('id="explorar"') || html.includes('href="#explorar"'), "La portada no enlaza el explorador.");
check(html.includes('src="./app.js"'), "La portada no carga la aplicación.");
check(!html.includes('data-page="'), "La portada conserva atributos del antiguo sistema multipágina.");

const sitemap = await readFile(resolve(dist, "sitemap.xml"), "utf8");
check((sitemap.match(/<url>/g) || []).length === 1, "El sitemap debe contener solo la aplicación principal.");

for (const stage of catalog.etapas) {
  check(
    stage.appPath === `?territorio=${stage.territorio}&etapa=${stage.codigo}#explorar`,
    `Ruta de aplicación incorrecta para ${stage.territorio}.${stage.codigo}.`,
  );
  check(!("pagePath" in stage), `La etapa ${stage.codigo} conserva una ruta multipágina obsoleta.`);
}

for (const matter of catalog.materias) {
  await exists(matter.jsonPath);
  const data = JSON.parse(await readFile(resolve(dist, matter.jsonPath), "utf8"));
  check(data.id === matter.id, `El ID de ${matter.jsonPath} no coincide con el catálogo.`);
  check(
    matter.appPath === `?territorio=${matter.territorio}&etapa=${matter.etapa}&materia=${matter.slug}#explorar`,
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

console.log(`SPA válida: ${catalog.materias.length} materias, ${catalog.etapas.length} etapas publicadas, ${catalog.incidencias.length} incidencias y ${catalog.progreso.length} comunidades.`);

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
