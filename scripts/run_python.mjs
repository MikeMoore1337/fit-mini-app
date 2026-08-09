import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const localPython =
  process.platform === "win32"
    ? resolve(root, ".venv", "Scripts", "python.exe")
    : resolve(root, ".venv", "bin", "python");

const candidates = [];
if (process.env.PYTHON) candidates.push([process.env.PYTHON, []]);
if (existsSync(localPython)) candidates.push([localPython, []]);
if (process.platform === "win32") candidates.push(["py", ["-3"]]);
candidates.push(["python3", []], ["python", []]);

const scriptArguments = process.argv.slice(2);
for (const [command, prefixArguments] of candidates) {
  const result = spawnSync(command, [...prefixArguments, ...scriptArguments], {
    stdio: "inherit",
    shell: false,
  });
  if (result.error?.code === "ENOENT") continue;
  if (result.error) {
    console.error(
      `Failed to start Python via ${command}: ${result.error.message}`,
    );
    process.exit(1);
  }
  process.exit(result.status ?? 1);
}

console.error(
  "Python 3 was not found. Create .venv or set the PYTHON environment variable.",
);
process.exit(1);
