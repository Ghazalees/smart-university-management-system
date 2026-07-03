import { spawn } from "node:child_process";
import process from "node:process";
import { fileURLToPath } from "node:url";

const e2eDirectory = fileURLToPath(new URL("..", import.meta.url));
const frontendDirectory = fileURLToPath(new URL("../../frontend/", import.meta.url));
const projectName = process.env.E2E_COMPOSE_PROJECT ?? "uniflow-e2e";
const port = process.env.E2E_PORT ?? "8088";
const baseURL = process.env.E2E_BASE_URL ?? `http://127.0.0.1:${port}`;
const keepStack = process.env.E2E_KEEP_STACK === "1";
const skipFrontendBuild = process.env.E2E_SKIP_FRONTEND_BUILD === "1";
const compose = [
  "compose",
  "-p",
  projectName,
  "-f",
  "../docker-compose.yml",
  "-f",
  "docker-compose.e2e.yml",
];
const environment = {
  ...process.env,
  HTTP_PORT: port,
  AUTO_MIGRATE: "1",
  AUTO_SEED_SYSTEM: "1",
  AUTO_SEED_DEMO: "1",
  E2E_BASE_URL: baseURL,
};

function run(command, args, options = {}) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, {
      cwd: options.cwd ?? e2eDirectory,
      env: environment,
      stdio: options.capture ? ["ignore", "pipe", "pipe"] : "inherit",
      shell: process.platform === "win32",
    });

    let output = "";
    if (options.capture) {
      child.stdout.on("data", (chunk) => { output += chunk; });
      child.stderr.on("data", (chunk) => { output += chunk; });
    }

    child.on("error", reject);
    child.on("close", (code) => {
      if (code === 0 || options.allowFailure) resolve({ code, output });
      else reject(new Error(`${command} ${args.join(" ")} exited with code ${code}`));
    });
  });
}

async function buildFrontend() {
  if (skipFrontendBuild) {
    console.log("Skipping the frontend build because E2E_SKIP_FRONTEND_BUILD=1.");
    return;
  }

  // The runtime image serves frontend/dist, so always build from the current source.
  await run("npm", ["ci"], { cwd: frontendDirectory });
  await run("npm", ["run", "build"], { cwd: frontendDirectory });
}

async function waitForHealth() {
  const deadline = Date.now() + 180_000;
  while (Date.now() < deadline) {
    try {
      const [gateway, backend] = await Promise.all([
        fetch(`${baseURL}/gateway-health`),
        fetch(`${baseURL}/api/v1/health`),
      ]);
      if (gateway.ok && backend.ok) return;
    } catch {
      // Containers may still be building or starting; retry until the deadline.
    }
    await new Promise((resolve) => setTimeout(resolve, 2_000));
  }
  throw new Error(`UniFlow did not become healthy at ${baseURL} within 180 seconds.`);
}

let failed = false;
try {
  await buildFrontend();
  await run("docker", [...compose, "down", "-v", "--remove-orphans"], { allowFailure: true });
  await run("docker", [...compose, "up", "--build", "-d"]);
  await waitForHealth();
  await run("npx", ["playwright", "test"]);
} catch (error) {
  failed = true;
  console.error(error instanceof Error ? error.message : error);
  const logs = await run(
    "docker",
    [...compose, "logs", "--no-color", "--tail", "300"],
    { capture: true, allowFailure: true },
  );
  console.error("\n--- Docker logs ---\n");
  console.error(logs.output);
} finally {
  if (keepStack) {
    console.log(`E2E stack left running at ${baseURL} (E2E_KEEP_STACK=1).`);
  } else {
    await run("docker", [...compose, "down", "-v", "--remove-orphans"], { allowFailure: true });
  }
}

if (failed) process.exitCode = 1;
