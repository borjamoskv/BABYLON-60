// C5-REAL EXERGY CERTIFIED
"use strict";
const node_fs = require("node:fs");
const node_os = require("node:os");
const path = require("node:path");
const node_child_process = require("node:child_process");
function getDisclaimerBinaryPath() {
  {
    const contentsPath = path.dirname(process.resourcesPath);
    return path.join(contentsPath, "Helpers", "disclaimer");
  }
}
function getUntrustedLaunchOptions(options) {
  const disclaimerPath = getDisclaimerBinaryPath();
  return {
    cmd: disclaimerPath,
    args: [options.cmd, ...options.args]
  };
}
function abortRejection(signal, cmd) {
  return signal.reason instanceof Error ? signal.reason : new DOMException(`spawnAsync(${cmd}) aborted`, "AbortError");
}
async function spawnAsync(cmd, args = [], options = {}) {
  var _a;
  const untrusted = getUntrustedLaunchOptions({ cmd, args });
  try {
    return await spawnAsyncDirect(untrusted.cmd, untrusted.args, options);
  } catch (error) {
    if (((_a = options.signal) == null ? void 0 : _a.aborted) && (error === options.signal.reason || error instanceof Error && error.name === "AbortError")) {
      if (untrusted.cmd !== cmd && error !== options.signal.reason) {
        throw new DOMException(
          `spawnAsync(${cmd}) aborted (via disclaimer)`,
          "AbortError"
        );
      }
      throw error;
    }
    if (untrusted.cmd !== cmd && error instanceof Error) {
      const isEnoent = error.message.includes("ENOENT");
      if (isEnoent) {
        throw new Error(
          `Failed to spawn ${cmd} (disclaimer binary not found): ${error.message}`
        );
      }
      throw new Error(
        `Failed to spawn ${cmd} (via disclaimer): ${error.message}`
      );
    }
    throw error;
  }
}
const DEFAULT_MAX_BUFFER = 16 * 1024 * 1024;
function spawnAsyncDirect(cmd, args = [], options = {}) {
  const {
    ignoreExitCode,
    maxBuffer = DEFAULT_MAX_BUFFER,
    stdin,
    destroyStdioOnExit,
    hardTimeoutMs,
    signal,
    ...spawnOptions
  } = options;
  if (signal == null ? void 0 : signal.aborted) {
    return Promise.reject(abortRejection(signal, cmd));
  }
  return new Promise((resolve, reject) => {
    var _a, _b;
    const proc = node_child_process.spawn(cmd, args, {
      ...spawnOptions,
      stdio: [stdin !== void 0 ? "pipe" : "ignore", "pipe", "pipe"]
    });
    if (stdin !== void 0 && proc.stdin) {
      proc.stdin.on("error", () => void 0);
      proc.stdin.write(stdin);
      proc.stdin.end();
    }
    const stdout = [];
    const stderr = [];
    let totalBytes = 0;
    let killed = false;
    const onData = (chunks) => (data) => {
      totalBytes += data.length;
      if (totalBytes > maxBuffer) {
        killed = true;
        proc.kill();
        return;
      }
      chunks.push(data);
    };
    (_a = proc.stdout) == null ? void 0 : _a.on("data", onData(stdout));
    (_b = proc.stderr) == null ? void 0 : _b.on("data", onData(stderr));
    const pgid = process.platform !== "win32" && spawnOptions.detached && typeof proc.pid === "number" ? proc.pid : void 0;
    const killGroup = (sig) => {
      if (pgid !== void 0) {
        try {
          process.kill(-pgid, sig);
          return;
        } catch {
        }
      }
      proc.kill(sig);
    };
    let aborted = false;
    const onAbort = () => {
      const childExited = proc.exitCode !== null || proc.signalCode !== null;
      if (!childExited) {
        aborted = true;
        proc.kill(spawnOptions.killSignal);
      }
      if (pgid !== void 0) {
        killGroup("SIGTERM");
      }
      setTimeout(() => {
        var _a2, _b2;
        killGroup("SIGKILL");
        if (!childExited) {
          (_a2 = proc.stdout) == null ? void 0 : _a2.destroy();
          (_b2 = proc.stderr) == null ? void 0 : _b2.destroy();
        }
      }, 1e3).unref();
    };
    signal == null ? void 0 : signal.addEventListener("abort", onAbort, { once: true });
    let hardTimer;
    let hardKilled = false;
    if (hardTimeoutMs) {
      hardTimer = setTimeout(() => {
        var _a2, _b2;
        hardKilled = true;
        killGroup("SIGKILL");
        (_a2 = proc.stdout) == null ? void 0 : _a2.destroy();
        (_b2 = proc.stderr) == null ? void 0 : _b2.destroy();
      }, hardTimeoutMs);
    }
    proc.on("error", (error) => {
      if (hardTimer) {
        clearTimeout(hardTimer);
      }
      signal == null ? void 0 : signal.removeEventListener("abort", onAbort);
      reject(new Error(`Failed to spawn ${cmd}: ${error.message}`));
    });
    let exitGraceTimer;
    proc.on("exit", () => {
      if (proc.killed && pgid !== void 0) {
        killGroup("SIGTERM");
        setTimeout(() => killGroup("SIGKILL"), 1e3).unref();
      }
      if (!proc.killed && !destroyStdioOnExit) {
        return;
      }
      exitGraceTimer = setTimeout(() => {
        var _a2, _b2;
        (_a2 = proc.stdout) == null ? void 0 : _a2.destroy();
        (_b2 = proc.stderr) == null ? void 0 : _b2.destroy();
      }, 1e3);
    });
    proc.on("close", (code) => {
      if (exitGraceTimer) {
        clearTimeout(exitGraceTimer);
      }
      if (hardTimer) {
        clearTimeout(hardTimer);
      }
      signal == null ? void 0 : signal.removeEventListener("abort", onAbort);
      if (aborted && signal) {
        reject(abortRejection(signal, cmd));
        return;
      }
      if (killed) {
        reject(
          new Error(
            `${cmd} output exceeded maxBuffer limit (${maxBuffer} bytes)`
          )
        );
        return;
      }
      const stderrBuffer = Buffer.concat(stderr);
      const stderrStr = stderrBuffer.toString();
      const stdoutBuffer = Buffer.concat(stdout);
      const result = {
        stdout: stdoutBuffer.toString(),
        stdoutBuffer,
        stderrBuffer,
        stderr: hardKilled ? `${stderrStr}${stderrStr ? "\n" : ""}killed after ${hardTimeoutMs}ms hard deadline` : stderrStr,
        code
      };
      if (!ignoreExitCode && code !== 0) {
        const error = new Error(
          `${cmd} exited with code ${code}: ${result.stderr || result.stdout}`
        );
        error.result = result;
        reject(error);
        return;
      }
      resolve(result);
    });
  });
}
const SHELL_TIMEOUT_MS = 4e3;
const PATH_SENTINEL = "___CLAUDE_PATH_EXTRACT___";
const PROBE_ONLY_ENV = {
  // Disable auto-update prompts from tools like oh-my-zsh
  DISABLE_AUTO_UPDATE: "true",
  ZSH_DISABLE_COMPFIX: "true",
  // Lets rc files skip slow init for the env-probe shell —
  // VS Code's VSCODE_RESOLVING_ENVIRONMENT pattern.
  CLAUDE_DESKTOP_RESOLVING_ENVIRONMENT: "1"
};
const PROBE_SESSION_VARS = ["PWD", "OLDPWD", "SHLVL", "_"];
const COMMON_SHELLS = [
  {
    path: "/bin/zsh",
    hints: [path.resolve(node_os.homedir(), ".zshrc")]
  },
  { path: "/bin/bash", hints: [path.resolve(node_os.homedir(), ".bashrc")] },
  { path: "/bin/sh" }
];
function getSafeShell() {
  var _a;
  const envShell = process.env.SHELL;
  if ((envShell == null ? void 0 : envShell.startsWith("/")) && node_fs.existsSync(envShell)) {
    return envShell;
  }
  for (const shell of COMMON_SHELLS) {
    if (node_fs.existsSync(shell.path) && ((_a = shell.hints) == null ? void 0 : _a.some((hint) => node_fs.existsSync(hint)))) {
      return shell.path;
    }
  }
  for (const shell of COMMON_SHELLS) {
    if (node_fs.existsSync(shell.path)) {
      return shell.path;
    }
  }
  return "/bin/sh";
}
async function extractPathFromShell() {
  var _a;
  if (process.platform === "win32") {
    return process.env.PATH || "";
  }
  const shell = getSafeShell();
  const { stdout } = await spawnAsync(
    shell,
    [
      "-l",
      "-i",
      "-c",
      `/bin/sh -c 'printf "%s%s\\n" "${PATH_SENTINEL}" "$PATH"'`
    ],
    {
      timeout: SHELL_TIMEOUT_MS,
      env: {
        HOME: process.env.HOME,
        PATH: process.env.PATH,
        SHELL: process.env.SHELL,
        USER: process.env.USER,
        ...PROBE_ONLY_ENV
      }
    }
  );
  const match = stdout.match(new RegExp(`${PATH_SENTINEL}(.*)$`, "m"));
  return ((_a = match == null ? void 0 : match[1]) == null ? void 0 : _a.trim()) || process.env.PATH || "";
}
const ENV_SENTINEL = "___CLAUDE_ENV_EXTRACT___";
async function extractShellEnvironment() {
  if (process.platform === "win32") {
    const result2 = {};
    for (const [key, value] of Object.entries(process.env)) {
      if (value !== void 0) {
        result2[key] = value;
      }
    }
    return result2;
  }
  const shell = getSafeShell();
  const { stdout } = await spawnAsync(
    shell,
    ["-l", "-i", "-c", `echo "${ENV_SENTINEL}"; env`],
    {
      timeout: SHELL_TIMEOUT_MS,
      env: {
        HOME: process.env.HOME,
        PATH: process.env.PATH,
        SHELL: process.env.SHELL,
        USER: process.env.USER,
        ...PROBE_ONLY_ENV
      }
    }
  );
  const sentinelIdx = stdout.indexOf(ENV_SENTINEL);
  if (sentinelIdx === -1) {
    return { PATH: process.env.PATH || "" };
  }
  const result = parseEnvDump(
    stdout.slice(sentinelIdx + ENV_SENTINEL.length + 1).trim()
  );
  if (!result.PATH) {
    result.PATH = process.env.PATH || "";
  }
  return result;
}
function parseEnvDump(envOutput) {
  const result = {};
  let currentKey = null;
  let currentValue = null;
  const flush = () => {
    if (currentKey !== null && currentValue !== null) {
      result[currentKey] = currentValue;
    }
  };
  for (const line of envOutput.split("\n")) {
    const eqIdx = line.indexOf("=");
    if (eqIdx > 0 && /^[A-Za-z_][A-Za-z0-9_]*$/.test(line.slice(0, eqIdx))) {
      flush();
      currentKey = line.slice(0, eqIdx);
      currentValue = line.slice(eqIdx + 1);
    } else if (eqIdx > 0) {
      flush();
      currentKey = null;
      currentValue = null;
    } else if (currentKey !== null && currentValue !== null) {
      currentValue += "\n" + line;
    }
  }
  flush();
  for (const [key, injected] of Object.entries(PROBE_ONLY_ENV)) {
    if (result[key] === injected) {
      delete result[key];
    }
  }
  for (const key of PROBE_SESSION_VARS) {
    delete result[key];
  }
  return result;
}
function postToParent(port, message) {
  try {
    port.postMessage(message);
  } catch {
  }
}
process.parentPort.once("message", (e) => {
  var _a;
  if (e.data.type !== "init" || !((_a = e.ports) == null ? void 0 : _a[0])) {
    process.exit(1);
  }
  const port = e.ports[0];
  port.on("message", async (event) => {
    if (event.data.type === "getPath") {
      try {
        if (process.platform === "win32") {
          postToParent(port, { type: "result", path: process.env.PATH || "" });
          return;
        }
        const path2 = await extractPathFromShell();
        postToParent(port, { type: "result", path: path2 });
      } catch (error) {
        const message = error instanceof Error ? error.message : "Unknown error";
        postToParent(port, { type: "error", message });
      }
    } else if (event.data.type === "getEnvironment") {
      try {
        const env = await extractShellEnvironment();
        postToParent(port, { type: "envResult", env });
      } catch (error) {
        const message = error instanceof Error ? error.message : "Unknown error";
        postToParent(port, { type: "error", message });
      }
    }
  });
  port.start();
});
process.on("SIGTERM", () => process.exit(0));
process.on("SIGINT", () => process.exit(0));
