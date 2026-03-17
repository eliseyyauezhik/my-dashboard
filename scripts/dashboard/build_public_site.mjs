import { cp, mkdir, readFile, rm, writeFile } from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const workspaceRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
const defaultOutputDir = path.join(workspaceRoot, ".output", "public");

const staticFiles = ["index.html", "app.js", "style.css", "mindmap.html", "mindmap.js", "mindmap.css"];
const dataFiles = ["dashboard_data.json", "telegram_intelligence.json", "idea_inbox.json", "mindmap.json"];
const pathKeyPattern = /(?:^|_)(?:path|paths|sourcepath|localpath|filepath)$/i;
const windowsPathPattern = /(?:file:\/\/\/)?[a-zA-Z]:(?:[\\/][^"\\/\r\n<>]+)+/g;
const cloudflareHeaders = `/*
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  X-Frame-Options: DENY
  Permissions-Policy: camera=(), microphone=(), geolocation=()
  X-Robots-Tag: noindex, nofollow, noarchive

/index.html
  Cache-Control: public, max-age=0, must-revalidate

/mindmap.html
  Cache-Control: public, max-age=0, must-revalidate

/data/*
  Cache-Control: public, max-age=60, must-revalidate

/*.js
  Cache-Control: public, max-age=300, must-revalidate

/*.css
  Cache-Control: public, max-age=300, must-revalidate
`;
const cloudflareRedirects = `/dashboard    /index.html    301
/mindmap      /mindmap.html  301
`;
const robotsTxt = `User-agent: *
Disallow: /
`;

function parseArgs(argv) {
  const args = { outputDir: defaultOutputDir };
  for (let index = 0; index < argv.length; index += 1) {
    if (argv[index] === "--output-dir" && argv[index + 1]) {
      args.outputDir = path.resolve(argv[index + 1]);
      index += 1;
    }
  }
  return args;
}

function sanitizeString(value) {
  return value.replace(windowsPathPattern, "[hidden local path]");
}

function sanitizeValue(value, parentKey = "") {
  if (Array.isArray(value)) {
    if (pathKeyPattern.test(parentKey)) {
      return value.map(() => "[hidden local path]");
    }
    return value.map((item) => sanitizeValue(item, parentKey));
  }

  if (value && typeof value === "object") {
    const sanitized = {};
    for (const [key, nestedValue] of Object.entries(value)) {
      if (pathKeyPattern.test(key)) {
        if (Array.isArray(nestedValue)) {
          sanitized[key] = nestedValue.map(() => "[hidden local path]");
        } else if (typeof nestedValue === "string" && nestedValue) {
          sanitized[key] = "[hidden local path]";
        } else {
          sanitized[key] = nestedValue;
        }
        continue;
      }
      sanitized[key] = sanitizeValue(nestedValue, key);
    }
    return sanitized;
  }

  if (typeof value === "string") {
    return sanitizeString(value);
  }

  return value;
}

async function copyStaticFiles(outputDir) {
  for (const file of staticFiles) {
    await cp(path.join(workspaceRoot, file), path.join(outputDir, file), { force: true });
  }
}

async function sanitizeDataFiles(outputDir) {
  const outputDataDir = path.join(outputDir, "data");
  await mkdir(outputDataDir, { recursive: true });

  for (const file of dataFiles) {
    const sourcePath = path.join(workspaceRoot, "data", file);
    const content = await readFile(sourcePath, "utf8");
    const parsed = JSON.parse(content);
    const sanitized = sanitizeValue(parsed);
    await writeFile(path.join(outputDataDir, file), `${JSON.stringify(sanitized, null, 2)}\n`, "utf8");
  }
}

async function writePlatformFiles(outputDir) {
  await writeFile(path.join(outputDir, "_headers"), cloudflareHeaders, "utf8");
  await writeFile(path.join(outputDir, "_redirects"), cloudflareRedirects, "utf8");
  await writeFile(path.join(outputDir, "robots.txt"), robotsTxt, "utf8");
}

async function main() {
  const { outputDir } = parseArgs(process.argv.slice(2));
  await rm(outputDir, { recursive: true, force: true });
  await mkdir(outputDir, { recursive: true });
  await copyStaticFiles(outputDir);
  await sanitizeDataFiles(outputDir);
  await writePlatformFiles(outputDir);
  await writeFile(path.join(outputDir, ".nojekyll"), "", "utf8");
  process.stdout.write(`PUBLIC_SITE_READY ${outputDir}\n`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
