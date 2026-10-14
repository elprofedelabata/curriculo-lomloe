import { createHash } from "node:crypto";
import { cp, mkdir, readdir, readFile, rm, writeFile } from "node:fs/promises";
import { basename, join, relative, resolve } from "node:path";

const root = resolve(import.meta.dirname, "..");
const dist = resolve(root, "dist");
const repoUrl = "https://github.com/elprofedelabata/curriculo-lomloe";
const siteUrl = "https://elprofedelabata.github.io/curriculo-lomloe";

const stageNames = {
  infantil: "Educación Infantil",
  primaria: "Educación Primaria",
  eso: "Educación Secundaria Obligatoria",
  bachillerato: "Bachillerato",
  cfgb: "Ciclos Formativos de Grado Básico",
};

const communityCodes = new Map([
  ["Andalucía", "es-an"],
  ["Aragón", "es-ar"],
  ["Principado de Asturias", "es-as"],
  ["Illes Balears", "es-ib"],
  ["Canarias", "es-cn"],
  ["Cantabria", "es-cb"],
  ["Castilla-La Mancha", "es-cm"],
  ["Castilla y León", "es-cl"],
  ["Cataluña", "es-ct"],
  ["Comunitat Valenciana", "es-vc"],
  ["Extremadura", "es-ex"],
  ["Galicia", "es-ga"],
  ["Comunidad de Madrid", "es-md"],
  ["Región de Murcia", "es-mc"],
  ["Comunidad Foral de Navarra", "es-nc"],
  ["País Vasco", "es-pv"],
  ["La Rioja", "es-ri"],
]);

const readme = await readFile(resolve(root, "README.md"), "utf8");
const incidentFiles = (await readdir(resolve(root, "incidencias"), { withFileTypes: true }))
  .filter((entry) => entry.isFile() && /^es-[a-z]{2}\.md$/.test(entry.name))
  .map((entry) => entry.name)
  .sort();
const incidentMarkdowns = await Promise.all(
  incidentFiles.map((filename) => readFile(resolve(root, "incidencias", filename), "utf8")),
);
const stageCodes = ["infantil", "primaria", "eso", "bachillerato", "cfgb"];
const progress = parseProgress(readme);
const incidents = incidentMarkdowns.flatMap(parseIncidents);
const matters = [];
const sourceCatalogs = new Map();

const territoryDirectories = (await readdir(resolve(root, "data"), { withFileTypes: true }))
  .filter((entry) => entry.isDirectory() && /^es-[a-z]{2}$/.test(entry.name))
  .map((entry) => entry.name)
  .sort();

for (const territoryCode of territoryDirectories) {
  const sourceCatalogPath = resolve(root, `sources/${territoryCode}/normativa/catalogo.json`);
  try {
    sourceCatalogs.set(territoryCode, JSON.parse(await readFile(sourceCatalogPath, "utf8")));
  } catch (error) {
    if (error.code !== "ENOENT") throw error;
  }

  for (const stage of stageCodes) {
    const directory = resolve(root, `data/${territoryCode}/${stage}/materias`);
    let files;
    try {
      files = (await readdir(directory)).filter((file) => file.endsWith(".json")).sort();
    } catch (error) {
      if (error.code === "ENOENT") continue;
      throw error;
    }

    for (const file of files) {
      const document = JSON.parse(await readFile(resolve(directory, file), "utf8"));
      const slug = basename(file, ".json");
      const jsonPath = `data/${territoryCode}/${stage}/materias/${file}`;
      const matterIncidents = incidents.filter((incident) => incident.jsonPath === jsonPath);
      const criteriaCount = document.desarrollos.reduce(
        (total, development) => total + (development.criteriosEvaluacion?.length || 0),
        0,
      );
      const knowledgeCount = new Set(
        document.desarrollos.flatMap((development) => collectKnowledge(development).map((knowledge) => knowledge.id)),
      ).size;

      matters.push({
        id: document.id,
        slug,
        territorio: document.territorio,
        etapa: stage,
        nombre: document.materia.nombre.es,
        codigo: document.materia.codigo,
        cursos: document.materia.cursos || [],
        ciclos: document.materia.ciclos || [],
        schemaVersion: document.schemaVersion,
        vigencia: document.vigencia,
        revision: document.revision,
        jsonPath,
        appPath: `?territorio=${document.territorio}&etapa=${stage}&materia=${slug}#${document.territorio}`,
        anexos: [...new Set(document.fuentes.map((source) => source.anexo).filter(Boolean))],
        fuentes: document.fuentes.map((source) => ({
          id: source.id,
          titulo: source.titulo,
          publicacion: source.publicacion,
          numero: source.numero,
          fechaPublicacion: source.fechaPublicacion,
          urlOficial: source.urlOficial,
          urlVerificacion: source.urlVerificacion,
          anexo: source.anexo,
          paginasMateria: source.paginasMateria,
        })),
        incidencias: matterIncidents.map((incident) => incident.id),
        estadisticas: {
          competencias: document.competenciasEspecificas.length,
          criterios: criteriaCount,
          saberes: knowledgeCount,
          desarrollos: document.desarrollos.length,
        },
      });
    }
  }
}

const stages = [...sourceCatalogs.entries()].flatMap(([territoryCode, sourceCatalog]) => {
  const territoryProgress = progress.find((territory) => territory.territorio === territoryCode);
  return stageCodes.map((stage) => {
    const stageMatters = matters.filter((matter) => matter.territorio === territoryCode && matter.etapa === stage);
    const stageIncidents = incidents.filter((incident) => incident.territorio === territoryCode && incident.etapa === stage);
    const revisions = stageMatters.map((matter) => matter.revision?.fechaUltimaRevision).filter(Boolean).sort();
    return {
      territorio: territoryCode,
      territorioNombre: territoryProgress?.nombre || sourceCatalog.nombre || territoryCode,
      codigo: stage,
      nombre: stageNames[stage],
      estado: territoryProgress?.etapas[stage]?.estado || "pendiente",
      appPath: `?territorio=${territoryCode}&etapa=${stage}#${territoryCode}`,
      materias: stageMatters.length,
      incidencias: stageIncidents.length,
      fuentes: sourceCatalog.documentos.filter((source) => source.etapas.includes(stage)).length,
      ultimaRevision: revisions.at(-1) || sourceCatalog.fechaActualizacion,
    };
  });
});

const sourceDocuments = [...sourceCatalogs.entries()].flatMap(([territoryCode, sourceCatalog]) =>
  sourceCatalog.documentos.map((document) => ({ territorio: document.territorio || territoryCode, ...document })),
);
const catalog = {
  version: "1.5.0",
  proyecto: {
    nombre: "Currículo LOMLOE en JSON",
    repositorio: repoUrl,
    sitio: siteUrl,
    descripcion: "Currículos oficiales estructurados, trazables y listos para reutilizar.",
  },
  territorios: parseProgress(readme).map((territory) => ({ codigo: territory.territorio, nombre: territory.nombre })),
  etapas: stages,
  materias: matters.sort((a, b) => a.nombre.localeCompare(b.nombre, "es")),
  incidencias: incidents,
  documentosNormativos: sourceDocuments,
  progreso: progress,
};

await rm(dist, { recursive: true, force: true });
await mkdir(dist, { recursive: true });

for (const file of ["index.html", "styles.css", "site.js"]) {
  await cp(resolve(root, file), resolve(dist, file));
}

const scriptHash = createHash("sha256")
  .update(await readFile(resolve(root, "site.js")))
  .digest("hex")
  .slice(0, 12);
const styleHash = createHash("sha256")
  .update(await readFile(resolve(root, "styles.css")))
  .digest("hex")
  .slice(0, 12);
const indexPath = resolve(dist, "index.html");
const indexHtml = await readFile(indexPath, "utf8");
const scriptTag = '<script src="./site.js" defer></script>';
const styleTag = '<link rel="stylesheet" href="./styles.css" />';
if (!indexHtml.includes(scriptTag) || !indexHtml.includes(styleTag)) {
  throw new Error("No se encontraron los recursos de la página en index.html.");
}
await writeFile(
  indexPath,
  indexHtml
    .replace(scriptTag, '<script src="./site.js?v=' + scriptHash + '" defer></script>')
    .replace(styleTag, '<link rel="stylesheet" href="./styles.css?v=' + styleHash + '" />'),
);
await cp(resolve(root, "assets"), resolve(dist, "assets"), { recursive: true });
await cp(resolve(root, "data"), resolve(dist, "data"), { recursive: true });
await cp(resolve(root, "schemas"), resolve(dist, "schemas"), { recursive: true });

await writeFile(resolve(dist, "catalogo.json"), `${JSON.stringify(catalog, null, 2)}\n`);
await writeFile(resolve(dist, ".nojekyll"), "");
await writeFile(resolve(dist, "robots.txt"), `User-agent: *\nAllow: /\nSitemap: ${siteUrl}/sitemap.xml\n`);

const sitemap = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n  <url><loc>${siteUrl}/</loc></url>\n</urlset>\n`;
await writeFile(resolve(dist, "sitemap.xml"), sitemap);

console.log(`Sitio estático preparado: ${matters.length} materias, ${stages.length} etapas publicadas y ${incidents.length} incidencias.`);

function collectKnowledge(development) {
  return (development.bloquesSaberes || []).flatMap((block) => [
    ...(block.saberes || []),
    ...(block.apartados || []).flatMap((section) => section.saberes || []),
  ]);
}

function parseIncidents(markdown) {
  const pattern = /^\| \[(?<review>[^\]]*)\] \| (?<id>[A-Z]+(?:-[A-Z]+)*-\d{3}) \| \[(?<matter>[^\]]+)\]\((?<path>[^)]+)\) \| (?<issue>.*?) \| (?<decision>.*?) \|$/;
  return markdown.split(/\r?\n/).flatMap((line) => {
    const match = line.match(pattern);
    if (!match) return [];
    const jsonPath = match.groups.path.replaceAll("\\", "/").replace(/^(\.\.\/)+/, "");
    const pathMatch = jsonPath.match(/^data\/(?<territory>es-[a-z]{2})\/(?<stage>infantil|primaria|eso|bachillerato|cfgb)\/materias\/(?<slug>[^/]+)\.json$/);
    if (!pathMatch) throw new Error(`Ruta de incidencia no reconocida: ${jsonPath}`);
    return [{
      id: match.groups.id,
      revisada: match.groups.review.trim().toUpperCase() === "X",
      materia: match.groups.matter,
      materiaSlug: pathMatch.groups.slug,
      territorio: pathMatch.groups.territory,
      etapa: pathMatch.groups.stage,
      jsonPath,
      incidencia: match.groups.issue,
      decision: match.groups.decision,
    }];
  });
}

function parseProgress(markdown) {
  const stageCodes = ["infantil", "primaria", "eso", "bachillerato", "cfgb"];
  return markdown.split(/\r?\n/).flatMap((line) => {
    if (!line.startsWith("| ")) return [];
    const cells = line.split("|").slice(1, -1).map((cell) => cell.trim());
    if (cells.length !== 6 || !communityCodes.has(cells[0])) return [];
    return [{
      territorio: communityCodes.get(cells[0]),
      nombre: cells[0],
      etapas: Object.fromEntries(stageCodes.map((stage, index) => [stage, progressStatus(cells[index + 1])])),
    }];
  });
}

function progressStatus(value) {
  if (value.startsWith("✅")) return { estado: "completo", etiqueta: value.replace(/^✅\s*/, "") };
  if (value.startsWith("📝")) return { estado: "en-revision", etiqueta: `${value.replace(/^📝\s*/, "")} en revisión` };
  if (value.startsWith("📚")) return { estado: "fuentes", etiqueta: "Fuentes recopiladas" };
  if (value.startsWith("🚧")) return { estado: "en-curso", etiqueta: "En curso" };
  return { estado: "pendiente", etiqueta: "Pendiente" };
}
