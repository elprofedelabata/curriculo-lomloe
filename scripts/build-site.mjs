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

const template = await readFile(resolve(root, "index.html"), "utf8");
const readme = await readFile(resolve(root, "README.md"), "utf8");
const incidentMarkdown = await readFile(resolve(root, "INCIDENCIAS.md"), "utf8");
const sourceCatalog = JSON.parse(await readFile(resolve(root, "sources/es-an/normativa/catalogo.json"), "utf8"));

const incidents = parseIncidents(incidentMarkdown);
const matters = [];

for (const stage of ["eso", "bachillerato"]) {
  const directory = resolve(root, `data/es-an/${stage}/materias`);
  const files = (await readdir(directory)).filter((file) => file.endsWith(".json")).sort();
  for (const file of files) {
    const document = JSON.parse(await readFile(resolve(directory, file), "utf8"));
    const slug = basename(file, ".json");
    const jsonPath = `data/es-an/${stage}/materias/${file}`;
    const matterIncidents = incidents.filter((incident) => incident.jsonPath === jsonPath);
    const criteriaCount = document.desarrollos.reduce(
      (total, development) => total + (development.criteriosEvaluacion?.length || 0),
      0,
    );
    const knowledgeCount = document.desarrollos.reduce(
      (total, development) => total + collectKnowledge(development).length,
      0,
    );

    matters.push({
      id: document.id,
      slug,
      territorio: document.territorio,
      etapa: stage,
      nombre: document.materia.nombre.es,
      codigo: document.materia.codigo,
      cursos: document.materia.cursos,
      schemaVersion: document.schemaVersion,
      vigencia: document.vigencia,
      revision: document.revision,
      jsonPath,
      pagePath: `es-an/${stage}/${slug}/`,
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

const stages = ["eso", "bachillerato"].map((stage) => {
  const stageMatters = matters.filter((matter) => matter.etapa === stage);
  const stageIncidents = incidents.filter((incident) => incident.etapa === stage);
  const revisions = stageMatters.map((matter) => matter.revision?.fechaUltimaRevision).filter(Boolean).sort();
  return {
    territorio: "es-an",
    territorioNombre: "Andalucía",
    codigo: stage,
    nombre: stageNames[stage],
    estado: "completo",
    pagePath: `es-an/${stage}/`,
    materias: stageMatters.length,
    incidencias: stageIncidents.length,
    fuentes: sourceCatalog.documentos.filter((source) => source.etapas.includes(stage)).length,
    ultimaRevision: revisions.at(-1) || sourceCatalog.fechaActualizacion,
  };
});

const catalog = {
  version: "1.0.0",
  proyecto: {
    nombre: "Currículo LOMLOE en JSON",
    repositorio: repoUrl,
    sitio: siteUrl,
    descripcion: "Currículos oficiales estructurados, revisados y listos para reutilizar.",
  },
  territorios: [{ codigo: sourceCatalog.territorio, nombre: sourceCatalog.nombre }],
  etapas: stages,
  materias: matters.sort((a, b) => a.nombre.localeCompare(b.nombre, "es")),
  incidencias: incidents,
  documentosNormativos: sourceCatalog.documentos,
  progreso: parseProgress(readme),
};

await rm(dist, { recursive: true, force: true });
await mkdir(dist, { recursive: true });

for (const file of ["styles.css", "app.js"]) {
  await cp(resolve(root, file), resolve(dist, file));
}
await cp(resolve(root, "data"), resolve(dist, "data"), { recursive: true });
await cp(resolve(root, "schemas"), resolve(dist, "schemas"), { recursive: true });

await writeFile(resolve(dist, "catalogo.json"), `${JSON.stringify(catalog, null, 2)}\n`);
await writeFile(resolve(dist, ".nojekyll"), "");
await writeFile(resolve(dist, "robots.txt"), `User-agent: *\nAllow: /\nSitemap: ${siteUrl}/sitemap.xml\n`);

await writePage("index.html", pageHtml({ type: "home", base: "./" }));

for (const stage of stages) {
  await writePage(
    `${stage.pagePath}index.html`,
    pageHtml({
      type: "stage",
      base: "../../",
      territorio: stage.territorio,
      etapa: stage.codigo,
      title: `${stage.territorioNombre} · ${stage.nombre} | Currículo LOMLOE`,
      description: `${stage.materias} currículos de ${stage.nombre} de ${stage.territorioNombre}, con fuentes, incidencias y descarga en JSON.`,
    }),
  );
}

for (const matter of matters) {
  await writePage(
    `${matter.pagePath}index.html`,
    pageHtml({
      type: "matter",
      base: "../../../",
      territorio: matter.territorio,
      etapa: matter.etapa,
      materia: matter.slug,
      title: `${matter.nombre} · ${stageNames[matter.etapa]} | Currículo LOMLOE`,
      description: `Currículo de ${matter.nombre} de ${stageNames[matter.etapa]} en Andalucía: competencias, criterios, saberes, incidencias y JSON.`,
    }),
  );
}

const routes = ["", ...stages.map((stage) => stage.pagePath), ...matters.map((matter) => matter.pagePath)];
const sitemap = [
  '<?xml version="1.0" encoding="UTF-8"?>',
  '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
  ...routes.map((route) => `  <url><loc>${siteUrl}/${route}</loc></url>`),
  "</urlset>",
  "",
].join("\n");
await writeFile(resolve(dist, "sitemap.xml"), sitemap);

console.log(`Sitio preparado: ${matters.length} materias, ${stages.length} etapas y ${incidents.length} incidencias.`);

function collectKnowledge(development) {
  return (development.bloquesSaberes || []).flatMap((block) => [
    ...(block.saberes || []),
    ...(block.apartados || []).flatMap((section) => section.saberes || []),
  ]);
}

function parseIncidents(markdown) {
  const pattern = /^\| \[(?<review>[^\]]*)\] \| (?<id>(?:BACH|ESO)-\d{3}) \| \[(?<matter>[^\]]+)\]\((?<path>[^)]+)\) \| (?<issue>.*?) \| (?<decision>.*?) \|$/;
  return markdown.split(/\r?\n/).flatMap((line) => {
    const match = line.match(pattern);
    if (!match) return [];
    const jsonPath = match.groups.path.replaceAll("\\", "/");
    const pathMatch = jsonPath.match(/^data\/es-an\/(?<stage>eso|bachillerato)\/materias\/(?<slug>[^/]+)\.json$/);
    if (!pathMatch) throw new Error(`Ruta de incidencia no reconocida: ${jsonPath}`);
    return [{
      id: match.groups.id,
      revisada: match.groups.review.trim().toUpperCase() === "X",
      materia: match.groups.matter,
      materiaSlug: pathMatch.groups.slug,
      territorio: "es-an",
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
  if (value.startsWith("📚")) return { estado: "fuentes", etiqueta: "Fuentes recopiladas" };
  if (value.startsWith("🚧")) return { estado: "en-curso", etiqueta: "En curso" };
  return { estado: "pendiente", etiqueta: "Pendiente" };
}

function pageHtml({ type, base, territorio = "", etapa = "", materia = "", title, description }) {
  const attributes = [
    `data-page="${type}"`,
    territorio && `data-territorio="${territorio}"`,
    etapa && `data-etapa="${etapa}"`,
    materia && `data-materia="${materia}"`,
  ].filter(Boolean).join(" ");

  let html = template
    .replace('<base href="./" />', `<base href="${base}" />`)
    .replace('<body data-page="home">', `<body ${attributes}>`);
  if (title) html = html.replace("<title>Currículo LOMLOE en JSON</title>", `<title>${escapeHtml(title)}</title>`);
  if (description) {
    html = html.replace(
      "Currículos LOMLOE estructurados en JSON, documentados y listos para reutilizar.",
      escapeHtml(description),
    );
  }
  return html;
}

async function writePage(relativePath, content) {
  const target = resolve(dist, relativePath);
  await mkdir(resolve(target, ".."), { recursive: true });
  await writeFile(target, content);
}

function escapeHtml(value) {
  return String(value).replace(/[&<>\"]/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '\"': "&quot;",
  })[character]);
}