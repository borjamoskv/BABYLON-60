"use strict";
var __defProp = Object.defineProperty;
var __knownSymbol = (name, symbol) => (symbol = Symbol[name]) ? symbol : Symbol.for("Symbol." + name);
var __typeError = (msg) => {
  throw TypeError(msg);
};
var __defNormalProp = (obj, key, value) => key in obj ? __defProp(obj, key, { enumerable: true, configurable: true, writable: true, value }) : obj[key] = value;
var __publicField = (obj, key, value) => __defNormalProp(obj, typeof key !== "symbol" ? key + "" : key, value);
var __accessCheck = (obj, member, msg) => member.has(obj) || __typeError("Cannot " + msg);
var __privateGet = (obj, member, getter) => (__accessCheck(obj, member, "read from private field"), getter ? getter.call(obj) : member.get(obj));
var __privateAdd = (obj, member, value) => member.has(obj) ? __typeError("Cannot add the same private member more than once") : member instanceof WeakSet ? member.add(obj) : member.set(obj, value);
var __privateSet = (obj, member, value, setter) => (__accessCheck(obj, member, "write to private field"), setter ? setter.call(obj, value) : member.set(obj, value), value);
var __privateMethod = (obj, member, method) => (__accessCheck(obj, member, "access private method"), method);
var __privateWrapper = (obj, member, setter, getter) => ({
  set _(value) {
    __privateSet(obj, member, value, setter);
  },
  get _() {
    return __privateGet(obj, member, getter);
  }
});
var __using = (stack, value, async) => {
  if (value != null) {
    if (typeof value !== "object" && typeof value !== "function") __typeError("Object expected");
    var dispose, inner;
    if (async) dispose = value[__knownSymbol("asyncDispose")];
    if (dispose === void 0) {
      dispose = value[__knownSymbol("dispose")];
      if (async) inner = dispose;
    }
    if (typeof dispose !== "function") __typeError("Object not disposable");
    if (inner) dispose = function() {
      try {
        inner.call(this);
      } catch (e) {
        return Promise.reject(e);
      }
    };
    stack.push([async, dispose, value]);
  } else if (async) {
    stack.push([async]);
  }
  return value;
};
var __callDispose = (stack, error, hasError) => {
  var E = typeof SuppressedError === "function" ? SuppressedError : function(e, s, m, _) {
    return _ = Error(m), _.name = "SuppressedError", _.error = e, _.suppressed = s, _;
  };
  var fail = (e) => error = hasError ? new E(e, error, "An error was suppressed during disposal") : (hasError = true, e);
  var next = (it) => {
    while (it = stack.pop()) {
      try {
        var result = it[1] && it[1].call(it[2]);
        if (it[0]) return Promise.resolve(result).then(next, (e) => (fail(e), next()));
      } catch (e) {
        fail(e);
      }
    }
    if (hasError) throw error;
  };
  return next();
};
var _queue, _carryoverConcurrencyCount, _isIntervalIgnored, _intervalCount, _intervalCap, _interval, _intervalEnd, _intervalId, _timeoutId, _queue2, _queueClass, _pending, _concurrency, _isPaused, _throwOnTimeout, _PQueue_instances, doesIntervalAllowAnother_get, doesConcurrentAllowAnother_get, next_fn, onResumeInterval_fn, isIntervalPaused_get, tryToStartAnother_fn, initializeIntervalIfNeeded_fn, onInterval_fn, processQueue_fn, throwOnAbort_fn, onEvent_fn, _fd, _tier, _closed, _SafeFile_instances, requireMaxBytes_fn, _canonical, _tier2, _allowUnc, _rootFd, _removeOnDispose, _disposed, _inflight, _drained, _SafeRoot_instances, assertLive_fn, requireMaxBytes_fn2, resolveLeaf_fn, lexicalLeaf_fn, withRootFd_fn, assertNotSymlinkLeaf_fn, renameTmp_fn, _a2;
Object.defineProperty(exports, Symbol.toStringTag, { value: "Module" });
const os = require("node:os");
const fs = require("node:fs");
const path = require("node:path");
const fs$1 = require("node:fs/promises");
const promises = require("node:stream/promises");
const module$1 = require("module");
const promises$1 = require("node:timers/promises");
require("node:util");
function _interopNamespaceDefault(e) {
  const n = Object.create(null, { [Symbol.toStringTag]: { value: "Module" } });
  if (e) {
    for (const k in e) {
      if (k !== "default") {
        const d = Object.getOwnPropertyDescriptor(e, k);
        Object.defineProperty(n, k, d.get ? d : {
          enumerable: true,
          get: () => e[k]
        });
      }
    }
  }
  n.default = e;
  return Object.freeze(n);
}
const path__namespace = /* @__PURE__ */ _interopNamespaceDefault(path);
const fs__namespace = /* @__PURE__ */ _interopNamespaceDefault(fs$1);
let source = () => ({ appPath: "", homedir: os.homedir() });
let cached;
function setScrubEnvSource(next) {
  source = next;
  cached = void 0;
}
function getScrubEnv() {
  return cached ?? (cached = source());
}
const UUID_RE$1 = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const _registryServerUuids = /* @__PURE__ */ new Set();
function noteRegistryServerUuids(uuids) {
  for (const u of uuids) {
    if (UUID_RE$1.test(u)) {
      _registryServerUuids.add(u);
    }
  }
}
function isRegistryServerUuid(s) {
  return UUID_RE$1.test(s) && _registryServerUuids.has(s);
}
const SYNTHETIC_MODEL = "<synthetic>";
const COLD_SCAN_DAYS = 182;
const MAX_LINE_LEN = 16 * 1024 * 1024;
const MAX_TRANSCRIPT_BYTES = 1024 * 1024 * 1024;
const STAT_BATCH_SIZE = 20;
const BATCH_SIZE = 8;
function toDateString(d) {
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${d.getFullYear()}-${m}-${day}`;
}
async function loadCliStatsCache(claudeConfigDir) {
  const cachePath = path.join(claudeConfigDir, "stats-cache.json");
  try {
    const raw = await fs.promises.readFile(cachePath, "utf-8");
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed.dailyActivity) ? parsed : null;
  } catch {
    return null;
  }
}
async function mapBatched(items, batchSize, fn) {
  const out = [];
  for (let i = 0; i < items.length; i += batchSize) {
    out.push(
      ...await Promise.all(items.slice(i, i + batchSize).map((x) => fn(x)))
    );
  }
  return out;
}
async function getAllSessionFiles(claudeConfigDir) {
  const projectsDir = path.join(claudeConfigDir, "projects");
  let projectEntries;
  try {
    projectEntries = await fs.promises.readdir(projectsDir, { withFileTypes: true });
  } catch {
    return [];
  }
  const projectDirs = projectEntries.filter((d) => d.isDirectory()).map((d) => path.join(projectsDir, d.name));
  const projectResults = await mapBatched(
    projectDirs,
    STAT_BATCH_SIZE,
    async (projectDir) => {
      try {
        const entries = await fs.promises.readdir(projectDir, { withFileTypes: true });
        const mainFiles = entries.filter((e) => e.isFile() && e.name.endsWith(".jsonl")).map((e) => path.join(projectDir, e.name));
        const sessionDirs = entries.filter((e) => e.isDirectory());
        const subagentResults = await mapBatched(
          sessionDirs,
          STAT_BATCH_SIZE,
          async (sd) => {
            const subDir = path.join(projectDir, sd.name, "subagents");
            try {
              const subs = await fs.promises.readdir(subDir, { withFileTypes: true });
              return subs.filter(
                (s) => s.isFile() && s.name.endsWith(".jsonl") && s.name.startsWith("agent-")
              ).map((s) => path.join(subDir, s.name));
            } catch {
              return [];
            }
          }
        );
        return [...mainFiles, ...subagentResults.flat()];
      } catch {
        return [];
      }
    }
  );
  return projectResults.flat();
}
async function* boundedLines(file, maxLen, onSkip) {
  const stream = fs.createReadStream(file, { encoding: "utf-8" });
  let buf = "";
  let discarding = false;
  let pendingCR = false;
  try {
    for await (let chunk of stream) {
      if (pendingCR && chunk[0] === "\n") {
        chunk = chunk.slice(1);
      }
      pendingCR = chunk.at(-1) === "\r";
      if (chunk.includes("\r")) {
        chunk = chunk.replace(/\r\n?/g, "\n");
      }
      let pos = 0;
      while (pos < chunk.length) {
        const nl = chunk.indexOf("\n", pos);
        const end = nl === -1 ? chunk.length : nl;
        if (discarding) {
          if (nl === -1) {
            break;
          }
          discarding = false;
          pos = nl + 1;
          continue;
        }
        buf += chunk.slice(pos, end);
        pos = end + 1;
        if (nl === -1) {
          if (buf.length > maxLen) {
            buf = "";
            discarding = true;
            onSkip == null ? void 0 : onSkip();
          }
          break;
        }
        if (buf.length > maxLen) {
          onSkip == null ? void 0 : onSkip();
        } else if (buf) {
          yield buf;
        }
        buf = "";
      }
    }
    if (buf && !discarding) {
      if (buf.length > maxLen) {
        onSkip == null ? void 0 : onSkip();
      } else {
        yield buf;
      }
    }
  } finally {
    stream.destroy();
  }
}
async function foldTranscript(file, isSubagentFile, fromDate, onSkip) {
  var _a3, _b2, _c;
  let firstTs = null;
  let messageCount = 0;
  let toolCallCount = 0;
  const usageByModel = /* @__PURE__ */ Object.create(null);
  for await (const line of boundedLines(file, MAX_LINE_LEN, onSkip)) {
    let e;
    try {
      e = JSON.parse(line);
    } catch {
      continue;
    }
    if (e === null || typeof e !== "object") {
      continue;
    }
    if (e.type !== "user" && e.type !== "assistant") {
      continue;
    }
    if (!isSubagentFile && e.isSidechain) {
      continue;
    }
    if (firstTs === null) {
      if (!e.timestamp || isNaN(new Date(e.timestamp).getTime())) {
        return null;
      }
      firstTs = e.timestamp;
      if (toDateString(new Date(firstTs)) < fromDate) {
        return null;
      }
    }
    messageCount++;
    if (e.type !== "assistant") {
      continue;
    }
    const content = (_a3 = e.message) == null ? void 0 : _a3.content;
    if (Array.isArray(content)) {
      for (const block of content) {
        if ((block == null ? void 0 : block.type) === "tool_use") {
          toolCallCount++;
        }
      }
    }
    const usage = (_b2 = e.message) == null ? void 0 : _b2.usage;
    const model = ((_c = e.message) == null ? void 0 : _c.model) ?? "unknown";
    if (!usage || model === SYNTHETIC_MODEL) {
      continue;
    }
    const mu = usageByModel[model] ?? (usageByModel[model] = {
      inputTokens: 0,
      outputTokens: 0,
      cacheReadInputTokens: 0,
      cacheCreationInputTokens: 0
    });
    mu.inputTokens += usage.input_tokens ?? 0;
    mu.outputTokens += usage.output_tokens ?? 0;
    mu.cacheReadInputTokens += usage.cache_read_input_tokens ?? 0;
    mu.cacheCreationInputTokens += usage.cache_creation_input_tokens ?? 0;
  }
  if (firstTs === null) {
    return null;
  }
  return { firstTs, messageCount, toolCallCount, usageByModel };
}
function calculateStreaks(activeDates) {
  if (activeDates.size === 0) {
    return { currentStreak: 0, longestStreak: 0 };
  }
  const checkDate = /* @__PURE__ */ new Date();
  checkDate.setHours(0, 0, 0, 0);
  let currentStreak = 0;
  while (activeDates.has(toDateString(checkDate))) {
    currentStreak++;
    checkDate.setDate(checkDate.getDate() - 1);
  }
  const sorted = Array.from(activeDates).sort();
  let longestStreak = 1;
  let temp = 1;
  for (let i = 1; i < sorted.length; i++) {
    const prev = new Date(sorted[i - 1]);
    const curr = new Date(sorted[i]);
    const dayDiff = Math.round(
      (curr.getTime() - prev.getTime()) / (1e3 * 60 * 60 * 24)
    );
    if (dayDiff === 1) {
      temp++;
    } else {
      longestStreak = Math.max(longestStreak, temp);
      temp = 1;
    }
  }
  longestStreak = Math.max(longestStreak, temp);
  return { currentStreak, longestStreak };
}
function dayAfter(date) {
  const d = /* @__PURE__ */ new Date(`${date}T00:00:00`);
  d.setDate(d.getDate() + 1);
  return toDateString(d);
}
async function computeCodeStats(claudeConfigDir) {
  const cache = await loadCliStatsCache(claudeConfigDir);
  const fromDate = (cache == null ? void 0 : cache.lastComputedDate) ? dayAfter(cache.lastComputedDate) : toDateString(new Date(Date.now() - COLD_SCAN_DAYS * 24 * 60 * 60 * 1e3));
  const fromMs = (/* @__PURE__ */ new Date(`${fromDate}T00:00:00`)).getTime();
  const sessionFiles = await getAllSessionFiles(claudeConfigDir);
  const dailyActivityMap = /* @__PURE__ */ new Map();
  for (const d of (cache == null ? void 0 : cache.dailyActivity) ?? []) {
    if (d.date < fromDate) {
      dailyActivityMap.set(d.date, { ...d });
    }
  }
  const dailyModelTokensMap = /* @__PURE__ */ new Map();
  for (const d of (cache == null ? void 0 : cache.dailyModelTokens) ?? []) {
    if (d.date < fromDate) {
      dailyModelTokensMap.set(d.date, { ...d.tokensByModel });
    }
  }
  const modelUsage = /* @__PURE__ */ Object.create(null);
  for (const [model, u] of Object.entries((cache == null ? void 0 : cache.modelUsage) ?? {})) {
    modelUsage[model] = {
      inputTokens: u.inputTokens ?? 0,
      outputTokens: u.outputTokens ?? 0,
      cacheReadInputTokens: u.cacheReadInputTokens ?? 0,
      cacheCreationInputTokens: u.cacheCreationInputTokens ?? 0
    };
  }
  const hourCounts = /* @__PURE__ */ new Map();
  for (const [h, c] of Object.entries((cache == null ? void 0 : cache.hourCounts) ?? {})) {
    hourCounts.set(Number(h), c);
  }
  let totalSessions = (cache == null ? void 0 : cache.totalSessions) ?? 0;
  let totalMessages = (cache == null ? void 0 : cache.totalMessages) ?? 0;
  let firstSessionDate = (cache == null ? void 0 : cache.firstSessionDate) ?? null;
  let lastSessionDate = null;
  const candidateFiles = [];
  let skippedOversizedFiles = 0;
  await mapBatched(sessionFiles, STAT_BATCH_SIZE, async (file) => {
    try {
      const st = await fs.promises.stat(file);
      if (st.mtimeMs < fromMs) {
        return;
      }
      if (st.size > MAX_TRANSCRIPT_BYTES) {
        skippedOversizedFiles++;
        return;
      }
      candidateFiles.push(file);
    } catch {
    }
  });
  let totalSkippedLines = 0;
  let fileErrors = 0;
  for (let i = 0; i < candidateFiles.length; i += BATCH_SIZE) {
    const batch = candidateFiles.slice(i, i + BATCH_SIZE);
    const results = await Promise.all(
      batch.map(async (file) => {
        const isSubagentFile = file.includes(`${path.sep}subagents${path.sep}`);
        try {
          return {
            isSubagentFile,
            summary: await foldTranscript(
              file,
              isSubagentFile,
              fromDate,
              () => {
                totalSkippedLines++;
              }
            )
          };
        } catch {
          fileErrors++;
          return { isSubagentFile, summary: null };
        }
      })
    );
    for (const { isSubagentFile, summary } of results) {
      if (!summary) {
        continue;
      }
      const firstTs = new Date(summary.firstTs);
      const dateKey = toDateString(firstTs);
      if (!isSubagentFile) {
        const dayActivity2 = dailyActivityMap.get(dateKey) ?? {
          date: dateKey,
          messageCount: 0,
          sessionCount: 0,
          toolCallCount: 0
        };
        totalSessions++;
        totalMessages += summary.messageCount;
        dayActivity2.sessionCount++;
        dayActivity2.messageCount += summary.messageCount;
        dailyActivityMap.set(dateKey, dayActivity2);
        const hour = firstTs.getHours();
        hourCounts.set(hour, (hourCounts.get(hour) ?? 0) + 1);
        if (!firstSessionDate || summary.firstTs < firstSessionDate) {
          firstSessionDate = summary.firstTs;
        }
        if (!lastSessionDate || summary.firstTs > lastSessionDate) {
          lastSessionDate = summary.firstTs;
        }
      }
      const dayActivity = dailyActivityMap.get(dateKey);
      if (dayActivity) {
        dayActivity.toolCallCount += summary.toolCallCount;
      }
      for (const [model, u] of Object.entries(summary.usageByModel)) {
        const mu = modelUsage[model] ?? (modelUsage[model] = {
          inputTokens: 0,
          outputTokens: 0,
          cacheReadInputTokens: 0,
          cacheCreationInputTokens: 0
        });
        mu.inputTokens += u.inputTokens;
        mu.outputTokens += u.outputTokens;
        mu.cacheReadInputTokens += u.cacheReadInputTokens;
        mu.cacheCreationInputTokens += u.cacheCreationInputTokens;
        const total = u.inputTokens + u.outputTokens;
        if (total > 0) {
          const day = dailyModelTokensMap.get(dateKey) ?? /* @__PURE__ */ Object.create(null);
          day[model] = (day[model] ?? 0) + total;
          dailyModelTokensMap.set(dateKey, day);
        }
      }
    }
  }
  const dailyActivity = Array.from(dailyActivityMap.values()).sort(
    (a, b) => a.date.localeCompare(b.date)
  );
  const dailyModelTokens = Array.from(dailyModelTokensMap.entries()).map(([date, tokensByModel]) => ({ date, tokensByModel })).sort((a, b) => a.date.localeCompare(b.date));
  const activeDates = new Set(dailyActivity.map((d) => d.date));
  let peakActivityHour = null;
  let peakCount = 0;
  for (const [hour, count] of hourCounts) {
    if (count > peakCount) {
      peakCount = count;
      peakActivityHour = hour;
    }
  }
  return {
    payload: {
      totalSessions,
      totalMessages,
      activeDays: activeDates.size,
      firstSessionDate,
      lastSessionDate,
      peakActivityHour,
      streaks: calculateStreaks(activeDates),
      dailyActivity,
      dailyModelTokens,
      modelUsage
    },
    diag: {
      fromDate,
      totalFiles: sessionFiles.length,
      scannedFiles: candidateFiles.length,
      skippedOversizedFiles,
      skippedOversizedLines: totalSkippedLines,
      fileErrors
    }
  };
}
const MAX_REPORTED_FAILURES = 50;
const LARGE_FILE_BYTES = 8 * 1024 * 1024;
const COPY_MODE = fs.constants.COPYFILE_FICLONE;
const inFlightWrites = {
  entries: /* @__PURE__ */ new Set(),
  sweeping: false
};
async function sweepInFlightWrites() {
  inFlightWrites.sweeping = true;
  const entries = [...inFlightWrites.entries];
  inFlightWrites.entries.clear();
  await Promise.all(
    entries.map((e) => fs__namespace.unlink(e.dest).catch(() => void 0))
  );
}
async function copyFiles(srcDir, destDir, files, options = {}) {
  var _a3;
  const result = {
    copiedCount: 0,
    skippedCount: 0,
    failedCount: 0,
    failed: []
  };
  for (const relativePath of files) {
    if (((_a3 = options.signal) == null ? void 0 : _a3.aborted) || inFlightWrites.sweeping) {
      return result;
    }
    const srcPath = path__namespace.join(srcDir, relativePath);
    const destPath = path__namespace.join(destDir, relativePath);
    const write = { dest: destPath };
    let destForfeit = false;
    let fh;
    try {
      await fs__namespace.mkdir(path__namespace.dirname(destPath), { recursive: true });
      if (options.skipExisting) {
        const srcStat = await fs__namespace.stat(srcPath);
        if (inFlightWrites.sweeping) {
          return result;
        }
        inFlightWrites.entries.add(write);
        fh = await fs__namespace.open(destPath, "wx", 384);
        destForfeit = true;
        if (inFlightWrites.sweeping) {
          await fh.close();
          await fs__namespace.unlink(destPath).catch(() => void 0);
          return result;
        }
        if (options.signal && srcStat.size > LARGE_FILE_BYTES) {
          await promises.pipeline(fs.createReadStream(srcPath), fh.createWriteStream(), {
            signal: options.signal
          });
        } else {
          await fh.close();
          if (inFlightWrites.sweeping) {
            await fs__namespace.unlink(destPath).catch(() => void 0);
            return result;
          }
          await fs__namespace.copyFile(srcPath, destPath, COPY_MODE);
        }
        await fs__namespace.chmod(destPath, srcStat.mode & 511).catch(() => void 0);
      } else {
        const srcStat = options.signal ? await fs__namespace.stat(srcPath).catch(() => null) : null;
        if (inFlightWrites.sweeping) {
          return result;
        }
        if (srcStat && srcStat.size > LARGE_FILE_BYTES) {
          fh = await fs__namespace.open(destPath, "w", 384);
          destForfeit = true;
          inFlightWrites.entries.add(write);
          if (inFlightWrites.sweeping) {
            await fh.close();
            await fs__namespace.unlink(destPath).catch(() => void 0);
            return result;
          }
          await promises.pipeline(fs.createReadStream(srcPath), fh.createWriteStream(), {
            signal: options.signal
          });
          await fs__namespace.chmod(destPath, srcStat.mode & 511).catch(() => void 0);
        } else {
          inFlightWrites.entries.add(write);
          await fs__namespace.copyFile(srcPath, destPath, COPY_MODE);
        }
      }
      result.copiedCount++;
    } catch (err2) {
      const e = err2;
      if (options.skipExisting && (e == null ? void 0 : e.code) === "EEXIST") {
        result.skippedCount++;
        continue;
      }
      await (fh == null ? void 0 : fh.close().catch(() => void 0));
      if ((e == null ? void 0 : e.name) === "AbortError") {
        if (inFlightWrites.entries.has(write)) {
          await fs__namespace.unlink(destPath).catch(() => void 0);
        }
        return result;
      }
      if (destForfeit && inFlightWrites.entries.has(write)) {
        await fs__namespace.unlink(destPath).catch(() => void 0);
      }
      result.failedCount++;
      if (result.failed.length < MAX_REPORTED_FAILURES) {
        result.failed.push({
          file: relativePath,
          error: err2 instanceof Error ? err2.message : "Unknown error"
        });
      }
    } finally {
      inFlightWrites.entries.delete(write);
    }
  }
  return result;
}
const GB_HASHED_KEY_PREFIX = "__gb__";
function fasthashDjb2(name) {
  if (name.startsWith(GB_HASHED_KEY_PREFIX)) {
    return name.slice(GB_HASHED_KEY_PREFIX.length);
  }
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = (hash << 5) - hash + name.charCodeAt(i);
    hash = hash & hash;
  }
  return ((hash & 4294967295) >>> 0).toString();
}
const SECURITY_SENSITIVE_FEATURES = [
  // Safe-prompt hash allowlist — suppresses the prompt-injection warning.
  "claudeai_safe_prompt_hashes",
  // Chalk (Claude for Education) telemetry collection gate. Default-off and
  // flipped only after the Sec-Eng launch-gate review: the flag is the
  // control between deployed code and collection
  // of education-identifier telemetry, so a forced-ON override in a victim
  // browser would start collection before the gate clears. Consent and
  // nonessential-telemetry gates still stack, but the launch-gate decision
  // itself must not be client-forceable.
  "proj-chalk-telemetry",
  // Chalk K-12 legal-document links ({tos, dpa} URLs) rendered as hrefs
  // behind the trusted "K-12 Terms of Service" / "Student Data Processing
  // Addendum" labels in the teacher verification modal
  // (useChalkK12LegalLinks.ts). A forced value in a victim browser would
  // make those trusted labels a phishing vector — and URL-originated
  // overrides outlive the crafted link (persisted in gb_url_overrides
  // until ?n=1 or a panel clear). The reader's schema also host-pins the
  // URLs to anthropic.com; this entry makes that defense in depth.
  "proj-chalk-k12-legal-links",
  // --- MCP tool approval / consent ---
  // Forcing OFF removes the approval requirement for MCP tools marked
  // destructiveHint (api/sync/mcp.ts).
  "disable_destructive_mcp_tools_by_default",
  // Cowork always-allow admin clamp — part of the Cowork prompt-injection
  // safeguard (api/sync/mcp.ts).
  "cowork_show_tool_permissioning_always_allow",
  // Forcing OFF removes per-call consent for consumer-health MCPs
  // (api/consent.ts).
  "sensitive_mcps_per_call_consent",
  // A forced {"<toolId>":"always_allow"} value makes the approval resolver
  // return approvalRequired:false for arbitrary tool IDs (api/sync/mcp.ts).
  "yukon_silver_tool_perms",
  // Per-server/per-tool approval config with wildcard matching; a forced
  // wildcard-"always" auto-approves MCP tools (useToolApprovalConfig.ts).
  "mcp_tool_approval_config",
  // Lists PHI-sensitive MCP servers; a forced-empty value makes
  // requiresHealthConsent() false (useHealthDataConsent.ts).
  "sensitive_mcp_tools",
  // Forcing ON constructs the MCP client with schema validation skipped
  // (components/mcp/helpers.ts).
  "claude_ai_mcp_skip_schema_validation",
  // --- MCP-app iframe capabilities ---
  // Forcing ON grants MCP-app iframes the direct-send-as-user capability
  // (McpAppToolUseCell.tsx).
  "apps_mcp_apps_experimental_flags",
  // --- Redacted strings (apps_redacted_strings_*) ---
  // useRedactedStrings spreads ALL apps_redacted_strings_* feature
  // values into one codename-keyed record, so any sibling can supply
  // another's codename via spread key conflict. Two sinks reach real
  // consequences today: fiddlehead's Slack-install URL goes to
  // window.open (api/sync/fiddlehead.ts), and fenugreek's self-hosted
  // install/worker commands render in a copy-button shell-command block
  // (apps/console/.../InstallationInstructions.tsx) — forced values are
  // copy-paste RCE on operator infrastructure. Until useRedactedStrings
  // key-scopes its merge (follow-up), every sibling is listed.
  "apps_redacted_strings_cilantro",
  "apps_redacted_strings_cubeb",
  "apps_redacted_strings_fennel",
  "apps_redacted_strings_fenugreek",
  "apps_redacted_strings_fiddlehead",
  "apps_redacted_strings_glass",
  "apps_redacted_strings_kunefeh",
  "apps_redacted_strings_parsley",
  "apps_redacted_strings_poppy",
  "apps_redacted_strings_seltzer",
  "apps_redacted_strings_sesame",
  "apps_redacted_strings_shiso",
  "apps_redacted_strings_workbench",
  // --- Cowork / CCR permission modes ---
  // Forcing ON offers "act without asking" unsupervised modes; on consumer
  // tier the gate is the only control (useCoworkUnsupervisedMode.ts).
  "cowork_bypass_permissions_mode",
  "cowork_auto_permission_mode",
  // Forcing ON enables auto permission mode in CCR remote sessions ahead
  // of rollout (useAutoPermissionModeAvailable.ts).
  "ccr_auto_permission_mode",
  // Chooses which policy path decides bypass/auto availability; forcing
  // flips the decision path (useResolvedClaudeCodeSettings.ts).
  "claudeai_permission_modes_managed_settings",
  // Forcing OFF disables org skill/plugin disablement at cowork session
  // spawn (useStartCoworkSession.tsx).
  "enforce_org_skill_disablement_main",
  // Forcing OFF returns the "no restrictions" sentinel for org CLI-exec
  // policies at cowork session spawn — and per api/cli-exec-policies.ts,
  // CLI exec has no backend backstop: desktop main is the only
  // enforcement point.
  "cowork_argonaut_org_policies_main",
  // --- Sandbox network egress ---
  // The defaults behind `org/account explicit setting ?? flag`: forcing ON
  // (or the without_spotlight variant) turns sandbox egress on for
  // accounts that never opted in; forcing the hosts template to
  // full_egress removes the host restriction — an exfiltration channel for
  // prompt-injected sessions (hooks/wiggle/useWiggle.ts).
  "claudeai_default_wiggle_egress_enabled",
  "claudeai_default_wiggle_egress_enabled_without_spotlight",
  "claudeai_default_wiggle_egress_hosts_template",
  // --- Rendering kill-switches ---
  // Kill-switch for Mermaid rendering of message content — the ramp-down
  // lever during a sanitizer incident; a forced-ON victim would stay
  // exposed through exactly the incident the flag exists to mitigate
  // (packages/chat/components/md/UIElements.tsx).
  "claude_ai_markdown_mermaid_render",
  // --- Auth / verification enforcement ---
  // Forcing OFF disables the client-side age-verification redirect
  // (withCurrentAccountRequired.tsx).
  "claude_ai_age_verification_hoc_gate",
  // A forced {"minimumAge":0} value trivializes the age check
  // (utils/country.ts).
  "onboarding_age_verification",
  // OR'd with the config opt-in; the code comment says this legacy gate
  // "remains the only way to opt OUT" — forcing it OFF downgrades signup
  // age verification to a self-attest checkbox (utils/country.ts).
  "use_birthday_for_age_verification",
  // Forcing OFF skips device-binding key enrollment and per-message event
  // signing (trustedDevices.ts, clientEventSigner.ts).
  "ccr_per_message_attestation_web",
  // Forcing OFF downgrades bound-session signing from the enclave key
  // (creg_) to the td-v1 WebCrypto key (registryDevice.ts,
  // clientEventSigner.ts) — the XSS-forgeable arm. Forcing ON activates
  // enclave registration + device-bind outside the rollout.
  "trusted_device_self_attestation",
  // Kill-switch for cowork safety banners; forcing OFF suppresses safety
  // UX in cowork sessions (CoworkSafetyBanner.tsx).
  "cowork_safety_banners",
  // --- Managed-config (MDM) enforcement ---
  // Serves the 3P managed-config key disableFeatureDiscovery (forced via the
  // synthetic bootstrap). The key's contract is admin-enforced and
  // non-user-reversible; a client-side force would let users re-enable the
  // announcement UI their org suppressed (useFeatureDiscoveryDisabled.ts).
  "ccd_disable_feature_discovery"
];
new Set(
  SECURITY_SENSITIVE_FEATURES.map(fasthashDjb2)
);
const AUTO_CLONE_MARKETPLACE_NAMES = /* @__PURE__ */ new Set([
  "claude-code-marketplace",
  "claude-code-plugins",
  "claude-plugins-official",
  "anthropic-marketplace",
  "anthropic-plugins",
  "agent-skills",
  "life-sciences",
  "knowledge-work-plugins"
]);
const ALLOWED_OFFICIAL_MARKETPLACE_NAMES = /* @__PURE__ */ new Set([
  ...AUTO_CLONE_MARKETPLACE_NAMES,
  // Backend-sync-only default marketplace (documents et al.). Private source
  // repo, served exclusively through the backend marketplace pipeline —
  // deliberately absent from AUTO_CLONE_MARKETPLACE_NAMES.
  "first-party-plugins"
]);
new Set(
  [...AUTO_CLONE_MARKETPLACE_NAMES].map((name) => `anthropics/${name}`)
);
/* @__PURE__ */ new Set([
  ...ALLOWED_OFFICIAL_MARKETPLACE_NAMES,
  "local-desktop-app-uploads"
]);
function isOfficialMarketplacePlugin(id) {
  const atIndex = id.lastIndexOf("@");
  if (atIndex <= 0) {
    return false;
  }
  return ALLOWED_OFFICIAL_MARKETPLACE_NAMES.has(id.slice(atIndex + 1));
}
function redactPluginId(id) {
  return isOfficialMarketplacePlugin(id) ? id : "<plugin>@other";
}
const OFFICIAL_PLUGIN_TOOL_SHAPE = /^[a-zA-Z0-9_.*-]{1,64}$/;
const PLUGIN_ID_HASH_SALT = "claude-plugin-telemetry-v1";
const saltedHash = (s) => fasthashDjb2(PLUGIN_ID_HASH_SALT + s);
const analyticsNameHash = fasthashDjb2;
const redactBedrockArnAccountId = (s) => s.replace(/^(arn:aws[^:]*:bedrock:[^:]*:)\d+(:)/, "$1***$2");
function redactMcpServerUrl(url) {
  if (!url) {
    return url;
  }
  let parsed;
  try {
    parsed = new URL(url);
  } catch {
    return void 0;
  }
  if (!parsed.hostname) {
    return void 0;
  }
  const port = parsed.port ? `:${parsed.port}` : "";
  return `${parsed.protocol}//${parsed.hostname}${port}${parsed.pathname}`;
}
const KNOWN_BUILTIN_TOOL_NAMES = /* @__PURE__ */ new Set([
  "AskUserQuestion",
  "Bash",
  "BashOutput",
  "Edit",
  "ExitPlanMode",
  "Glob",
  "Grep",
  "JavaScript",
  "KillBash",
  "MultiEdit",
  "NotebookEdit",
  "Read",
  "REPL",
  "SendUserMessage",
  "Skill",
  "Task",
  "TaskCreate",
  "TaskGet",
  "TaskList",
  "TaskStop",
  "TaskUpdate",
  "Tmux",
  "TodoWrite",
  "ToolSearch",
  "WebFetch",
  "WebSearch",
  "Workflow",
  "Write",
  // Diagnostic sentinel, not an SDK tool: emitters fall back to it when the
  // real tool name is unavailable (e.g. SessionDataProvider's pending-request
  // store miss). A code constant — keeping it legible preserves the
  // store-miss dashboards.
  "unknown"
]);
const COMPUTER_SENTINEL_ACTIONS = /* @__PURE__ */ new Set([
  "request_access",
  "request_teach_access"
]);
const BROWSER_SENTINEL_ACTIONS = /* @__PURE__ */ new Set([
  "browser_batch",
  "click",
  "computer",
  "domain_transition",
  "execute_javascript",
  "file_upload",
  "find",
  "form_input",
  "get_page_text",
  "gif_creator",
  "javascript_tool",
  "list_connected_browsers",
  "navigate",
  "plan_approval",
  "read_console_messages",
  "read_network_requests",
  "read_page",
  "read_page_content",
  "remote_mcp",
  "resize_window",
  "select_browser",
  "shortcuts_execute",
  "shortcuts_list",
  "submit_credentials",
  "switch_browser",
  "tabs_close_mcp",
  "tabs_context_mcp",
  "tabs_create_mcp",
  "type",
  "unknown",
  "upload_image"
]);
function redactToolName(toolName, hashFn = saltedHash) {
  if (toolName.startsWith("mcp__")) {
    const parts = toolName.split("__");
    const server = parts[1] ?? "";
    const tool = parts.slice(2).join("__");
    return `mcp__${hashFn(server)}__${hashFn(tool)}`;
  }
  if (toolName.startsWith("plugin-shim:")) {
    const parts = toolName.split(":");
    const plugin = parts[1] ?? "";
    const cli = parts[2] ?? "";
    const op = parts.slice(3).join(":");
    return `plugin-shim:${hashFn(plugin)}:${hashFn(cli)}:${hashFn(op)}`;
  }
  if (toolName.startsWith("webfetch:")) {
    const hostname = toolName.slice("webfetch:".length);
    return `webfetch:${hashFn(hostname)}`;
  }
  const colonIndex = toolName.indexOf(":");
  if (colonIndex !== -1) {
    const prefix = toolName.slice(0, colonIndex);
    const suffix = toolName.slice(colonIndex + 1);
    const sentinelActions = prefix === "computer" ? COMPUTER_SENTINEL_ACTIONS : prefix === "browser" ? BROWSER_SENTINEL_ACTIONS : void 0;
    if (sentinelActions == null ? void 0 : sentinelActions.has(suffix)) {
      return toolName;
    }
    return `${hashFn(prefix)}:${hashFn(suffix)}`;
  }
  return KNOWN_BUILTIN_TOOL_NAMES.has(toolName) ? toolName : hashFn(toolName);
}
function redactServerToolKey(key) {
  const colonIndex = key.indexOf(":");
  if (colonIndex === -1) {
    return saltedHash(key);
  }
  const server = key.slice(0, colonIndex);
  const tool = key.slice(colonIndex + 1);
  return `${saltedHash(server)}:${saltedHash(tool)}`;
}
const SAFE_QUERY_PARAMS = /* @__PURE__ */ new Set([
  // Pagination
  "limit",
  "offset",
  "page",
  "page_size",
  "page_token",
  "after_id",
  "per_page",
  "cursor",
  // Sorting
  "sort_by",
  "sort_order",
  "order_by",
  // Date ranges
  "start_date",
  "end_date",
  "date",
  "target_date",
  "days",
  // Non-PII filters
  "metric",
  "type",
  "granularity",
  "severity",
  // UI state
  "tab",
  "mode",
  "step"
]);
/* @__PURE__ */ new Set([
  ...SAFE_QUERY_PARAMS,
  // utm family — envEnrichment captures every utm_*; allowlisting the
  // standard six means a pipeline change doesn't silently regress.
  "utm_source",
  "utm_medium",
  "utm_campaign",
  "utm_term",
  "utm_content",
  "utm_id",
  // Click IDs currently captured via ion-edge cookies.
  "gclid",
  "fbclid",
  "ttclid",
  "rdt_cid",
  // Click IDs not yet captured elsewhere — allowlisting here means a future
  // CAPI integration can read them from url/search without a second PR.
  "dclid",
  "msclkid",
  "twclid",
  "li_fat_id",
  "irclickid",
  "sccid",
  "epik",
  "wbraid",
  "gbraid",
  "yclid"
]);
function deepScrubStrings(obj, opts) {
  const seen = /* @__PURE__ */ new WeakMap();
  const safeScrubString = (s) => {
    try {
      return opts.scrubString(s);
    } catch {
      return "[scrub-error]";
    }
  };
  const walk = (v) => {
    var _a3;
    if (typeof v === "string") {
      return safeScrubString(v);
    }
    if (typeof v !== "object" || v === null) {
      return v;
    }
    if (seen.has(v)) {
      return seen.get(v);
    }
    seen.set(v, "[Circular]");
    if (Array.isArray(v)) {
      const out2 = v.map(walk);
      seen.set(v, out2);
      return out2;
    }
    const out = /* @__PURE__ */ Object.create(null);
    const nextSuffix = /* @__PURE__ */ new Map();
    for (const [k, val] of Object.entries(v)) {
      let outKey = safeScrubString(k);
      if (Object.hasOwn(out, outKey)) {
        const base = outKey;
        let i = nextSuffix.get(base) ?? 2;
        outKey = `${base}[${i}]`;
        while (Object.hasOwn(out, outKey)) {
          i++;
          outKey = `${base}[${i}]`;
        }
        nextSuffix.set(base, i + 1);
      }
      try {
        if ((_a3 = opts.skipKeys) == null ? void 0 : _a3.has(k)) {
          out[outKey] = val;
        } else if (opts.keyHandlers && Object.hasOwn(opts.keyHandlers, k)) {
          out[outKey] = opts.keyHandlers[k](val, k);
        } else {
          out[outKey] = walk(val);
        }
      } catch {
        out[outKey] = "[scrub-error]";
      }
    }
    seen.set(v, out);
    return out;
  };
  try {
    return walk(obj);
  } catch {
    return "[scrub-error]";
  }
}
const SCRUB_FAILED_LINE_PLACEHOLDER = "[line withheld: scrub failed]";
function scrubBufferForBundle(filename, bytes, opts) {
  var _a3;
  const lower = filename.toLowerCase();
  const safeLineScrub = (line) => {
    var _a4;
    try {
      return opts.lineScrub(line);
    } catch (err2) {
      (_a4 = opts.onError) == null ? void 0 : _a4.call(opts, err2, filename);
      return SCRUB_FAILED_LINE_PLACEHOLDER;
    }
  };
  const lineScrubWholeBuffer = () => Buffer.from(
    bytes.toString("utf8").split("\n").map(safeLineScrub).join("\n"),
    "utf8"
  );
  try {
    if (lower.endsWith(".log") || lower.endsWith(".txt")) {
      return lineScrubWholeBuffer();
    }
    if (lower.endsWith(".json")) {
      const parsed = JSON.parse(bytes.toString("utf8"));
      const scrubbed = deepScrubStrings(parsed, opts.jsonScrubOpts);
      return Buffer.from(JSON.stringify(scrubbed), "utf8");
    }
    if (lower.endsWith(".jsonl")) {
      const scrubbed = bytes.toString("utf8").split("\n").map((line) => {
        if (!line.trim()) {
          return line;
        }
        try {
          const parsed = JSON.parse(line);
          return JSON.stringify(deepScrubStrings(parsed, opts.jsonScrubOpts));
        } catch {
          return safeLineScrub(line);
        }
      }).join("\n");
      return Buffer.from(scrubbed, "utf8");
    }
  } catch (err2) {
    (_a3 = opts.onError) == null ? void 0 : _a3.call(opts, err2, filename);
    return lineScrubWholeBuffer();
  }
  return bytes;
}
const EMAIL_RE = /[\w.+-]{1,64}@[\w-]{1,63}(?:\.[\w-]{1,63}){0,7}\.[A-Za-z][\w-]{0,62}/g;
function redactEmail(text) {
  return text.replace(EMAIL_RE, "<email>");
}
const IPV4_RE = /\b(?:\d{1,3}\.){3}\d{1,3}\b/g;
const IPV6_RE = /\b(?:[A-Fa-f0-9]{1,4}:){2,7}(?::?[A-Fa-f0-9]{1,4}){1,7}\b/g;
const TIMESTAMP_LIKE = /^\d{1,2}:\d{2}:\d{2}$/;
function redactIpAddress(text) {
  return text.replace(IPV4_RE, "<ip>").replace(IPV6_RE, (m) => TIMESTAMP_LIKE.test(m) ? m : "<ip>");
}
function redactEmbeddedUrlsToHost(text) {
  return text.replace(/\b(?:https?|wss?):\/\/\S+/gi, (u) => {
    const tailMatch = /[)\].,;:'"}]+$/.exec(u);
    let tail = tailMatch ? tailMatch[0] : "";
    let url = tail ? u.slice(0, -tail.length) : u;
    if (url.includes("[") && !url.includes("]")) {
      const closeIdx = tail.indexOf("]");
      if (closeIdx !== -1) {
        url += tail.slice(0, closeIdx + 1);
        tail = tail.slice(closeIdx + 1);
      }
    }
    try {
      const p = new URL(url);
      if (!p.hostname) {
        return `<url>${tail}`;
      }
      const port = p.port ? `:${p.port}` : "";
      return `${p.protocol}//${p.hostname}${port}/<path>${tail}`;
    } catch {
      return `<url>${tail}`;
    }
  });
}
const CREDENTIAL_KEY_RE = "(?:password|passwd|pwd|pass[-_]?phrase|secret|token|credential|auth|api[-_]?key|api[-_]?token|access[-_]?key|access[-_]?token|refresh[-_]?token|id[-_]?token|client[-_]?secret|private[-_]?key|session[-_]?(?:key|token|id)|sessid|jsessionid|phpsessid|connect\\.sid|aws[-_]?secret[-_]?access[-_]?key)";
const SEP_CORE = `(?:[:=][:=>~|]*(?![:=>~|]))`;
const KV_SEP = `(?:(?:\\\\\\\\)*\\\\["']|['"])?\\s*${SEP_CORE}\\s*`;
const FLAG_KEY = `-{1,2}(?:[A-Za-z0-9]+[-_])*${CREDENTIAL_KEY_RE}`;
const FLAG_SEP = `(?:\\s+|\\s*=\\s*)`;
const branchOpener = (q, escaped) => escaped ? `(?:\\\\\\\\)*\\\\${q}` : `${q}`;
const UNQUOTED_UNIT = `(?:[^\\s'"\\\\]|\\\\[^\\s\\n\\r"']|\\\\$)`;
const placeholderGuard = (terminator) => `(?!(?:<(?:token|redacted|jwt|blob)>|(?:sk-|bedrock-api-key-)?\\[redacted(?:-[a-z-]+)?\\])(?=${terminator}))`;
const MARKER_TERMINATOR = "…<truncated>(?=[\\r\\n]|$)";
const GUARD_UNQUOTED = placeholderGuard(
  // …plus two complement-principle completions (bughunter round 4): a
  // backslash the content class cannot pair (followed by whitespace) also
  // ends the value, and the scrubLogLine truncation marker at end-of-input
  // must not be folded into <redacted> on a SECOND scrub pass (support
  // bundles re-scrub already-scrubbed lines).
  // EXACTLY one backslash + quote as the escaped-close HERE — and only
  // here. At the dominant depth-≤1 corpus, the enclosing closer this
  // guard faces is level-1 (\"); an odd 3+ run's even
  // prefix is pair-consumable, so firing on longer runs fired on
  // consumable bytes. The quotedBranch escaped terminator DELIBERATELY
  // keeps the odd-run family instead: inside nested stringification a
  // depth-k closer IS an odd backslash run (level-2 close = \\\" —
  // load-bearing for the multi-nesting keep pin). Each site reads the
  // complement principle correctly for its own context; an earlier
  // record comment claimed exactness was applied at BOTH sites — wrong,
  // corrected in the record. The two forms are equivalent only at depth
  // ≤ 1 (the measured corpus: tails ship at main parity either way). At
  // depth ≥ 2 they diverge: facing a depth-2 closer (\\\") the exact arm
  // declines, the kv rule consumes the even backslash prefix, and the
  // output carries the label downgraded to <redacted> with the closer
  // demoted to level-1 — over-redaction plus structural demotion, never
  // a leak — where the odd-run family would keep the label. That
  // safe-direction divergence is accepted rather than fixed: a depth-≥2
  // closer after a placeholder at an unquoted site arises from deep
  // nesting (≥ triple stringify — well-formed, measured; an in-pass
  // manufactured placeholder lands there, see the triple-stringify
  // habitat pin) or from malformed input. Either way the cost is label
  // specificity on an already-manufactured placeholder, while firing on
  // odd 3+ runs would make the inverse
  // trade — keeping a label glued to consumable bytes that may be the
  // prefix of a longer real value (under-redaction). Pinned (depth-2
  // divergence pin alongside the depth-1 keep, plus the well-formed
  // triple-stringify habitat pin).
  `$|['"\\s]|\\\\["']|\\\\(?=\\s)|${MARKER_TERMINATOR}`
);
const quotedBranch = (q, escaped) => {
  const opener = `(${branchOpener(q, escaped)})`;
  const pairAware = escaped;
  const pair = `\\\\[^"'\\n\\r]`;
  const content = pairAware ? `(?:[^${q}\\\\\\n\\r]|${pair}|\\\\$)*` : `[^${q}\\n\\r]*`;
  const oppositeQ = q === '"' ? "'" : '"';
  const terminator = `$|[${q}\\n\\r]|${MARKER_TERMINATOR}` + (escaped ? `|\\\\(?=[\\n\\r])|(?:\\\\\\\\)*\\\\[${q}${oppositeQ}]` : "");
  return opener + placeholderGuard(terminator) + content;
};
const QUOTED_VALUE_BRANCHES = `${quotedBranch('"', false)}|${quotedBranch("'", false)}|${quotedBranch('"', true)}|${quotedBranch("'", true)}`;
const UNQUOTED_VALUE = (
  // The truncation marker alone at value position is NOT a secret: an
  // 8KB cut landing exactly at the separator leaves
  // `password=…<truncated>` after the post-scrub append, and a re-scrub
  // (support bundles) must not fabricate `password=<redacted>` out of
  // it — that erases the truncation signal and invents a secret that
  // never existed (posted-scan finding, over-redaction direction).
  // THIRD TOMBSTONE — the fused-assignment refusal (its tripwire FIRED):
  // two architectures tried to stop this branch from consuming a fused
  // follower assignment (`{\"password\":token="secret"}` stranding the
  // follower's quoted secret). The shape-only refusal (operator-before-
  // quote) over-declined base64 padding and shipped tokens; the
  // derived-handoff refusal (this site's final form — the kv rule's own
  // key+sep anchor interpolated) was adjudicated legal by failure-
  // direction analysis and then FALSIFIED by mechanism: a branch-START
  // negative lookahead with a `UNIT*` prefix does not truncate on
  // over-fire — it ABORTS the whole branch, the kv match dies, and the
  // value's HEAD ships raw (`password=hunter2;token="x"` shipped
  // hunter2 where main redacted). It also missed KV_SEP's `\s*` and
  // FLAG_SEP dimensions (bypass routes) and made the scrubber O(n^2)
  // on key-dense text through the uncapped bundle sink. Per the
  // pre-committed tripwire the refusal is REVERTED, and the fused-
  // follower swallow is a PRICED below-main class. BOUNDARY, THRICE
  // CORRECTED BY MEASUREMENT (quoting axis → vocab axis → SEPARATION
  // axis; the posted clean-round candidate found the third): the class
  // is the ASYMMETRIC MIXED FORM — outer key ESCAPED-quoted (main's
  // separator refuses the backslash and never consumes the region; the
  // quote-crossing separator — the defect fix — anchors and consumes)
  // + inner follower whose key is VOCAB-REACHABLE in any spelling the
  // rules themselves anchor — bare (`token`), compound flag
  // (`--db-token`), or env-style (`DB_TOKEN`) — whose value is
  // SEPARATED from its separator by ANYTHING: a quote OR whitespace.
  // The discriminator was never the value's quoting — it is whether
  // the consumed run can reach the value. A quote stops the unquoted
  // run; whitespace stops it too; in both cases the inner value
  // strands while main re-anchors at the intact inner assignment and
  // redacts it. ONLY the zero-separation unquoted spelling
  // (`token=hunter2`) folds into the consumed run whole — redacted,
  // the safe direction (an earlier form of this comment called ALL
  // unquoted followers safe; the whitespace cells falsified that, and
  // the claim is corrected here). The habitat in practice:
  // stringified-JSON log lines with embedded credential assignments —
  // real, and wider than first priced. BOTH uniform quote subspaces
  // (all-plain, all-escaped) and non-vocab inner keys remain at
  // MEASURED PARITY — pinned so the class cannot drift wider than its
  // mechanism. Probe lesson recorded with the pins: uniform vector
  // constructions sit in the symmetric subspace where the builds
  // agree; a class boundary defined by a mechanism ASYMMETRY is only
  // visible to vectors that exercise the asymmetry.
  // COMPOUND-SEPARATOR EXTENSION of this class (priced with the
  // possessive SEP_CORE): a compound-separator assignment with a
  // vocab-reachable follower whose value is SEPARATED from its own
  // separator by anything — a quote (`password ==> token="secret"`)
  // OR whitespace (`password ==> token: secret`,
  // `password ==> --token secret`) — now strands the follower's
  // secret exactly as the 7 enumerated separators always have (this
  // class's own boundary above: "a quote OR whitespace"). Full-run
  // consumption gives compounds correct-separator semantics, so the
  // accepted class extends to them BY CONSTRUCTION. The old
  // enumeration "redacted" these shapes only as an accident of its
  // broken parse (the stranded prefix char killed the first kv value
  // early, letting the follower re-anchor) — the same broken parse
  // that shipped the plain-value secret raw and, under the flag rule,
  // erased the evidence. Measured scope: 305 of the 1,163 compound
  // runs compose with a quoted follower (the design fuzz's
  // enumeration); the whitespace-separated and flag-follower
  // spellings are the same mechanism and are pinned alongside. The
  // ≥40-char blob rules backstop long follower secrets.
  // Distinguishing a value from a follower assignment is
  // follower-awareness, the twice-tombstoned dimension; no third
  // attempt past a fired tripwire. Pinned in the test suite with the
  // trade named.
  // There is STRONG EVIDENCE, not proof, that IMPROVING on main for
  // the vocab subset is unreachable in the minimal regex form — two
  // architectures, one consistent failure mode, and the structural
  // boundary argument (distinguishing a value from a follower
  // assignment requires follower-awareness, the twice-tombstoned
  // dimension). A third architecture may exist; none is attempted
  // past a fired tripwire.
  // DOCTRINE, REPAIRED (three parts, binding): (1) CRITERION — a
  // mechanism may share another rule's shape fragments iff BOTH failure
  // directions are secret-safe; it may never make a decision whose
  // SOUNDNESS requires another rule to match. (2) MECHANISM TAXONOMY —
  // an END-refusal's over-fire truncates (ships terminal anchor bytes,
  // benign); a BRANCH-START lookahead's over-fire ABORTS (ships the
  // head, catastrophic). The original adjudication modeled the former
  // and blessed the latter. (3) PROCEDURE, the root-cause correction —
  // failure directions are MEASURED, never argued: before ruling a
  // shared-fragment mechanism legal, CONSTRUCT the over-fire
  // counter-shape (head-secret-then-later-anchor) and the under-fire
  // counter-shape (the fragment gap) and RUN BOTH against main. The
  // original blessing passed two reviewers on a plausible mechanism
  // story ("ships only anchor vocabulary") that minutes of measurement
  // would have falsified; only the empirical scanner caught it. A
  // direction blessing without measured counter-shapes is VOID — the
  // same measure-don't-argue rule every other claim in this file lives
  // under, which the adjudication itself had been exempt from. The
  // next mechanism will be mis-modeled a different way; measurement is
  // the only review that doesn't depend on modeling it right. And the
  // companion rule for conditions themselves (from the A-vs-B Basic
  // ruling): conditions are read by PURPOSE when the deviation is
  // MEASURED; stretched by argument, never.
  // The two start-refusals are ANY-run (`\\+`) by MEASURED VERDICT,
  // not oversight (scheduled battery, ratified): they inspect only
  // position zero — no consumed head exists, so the abort surface that
  // killed the derived-handoff refusal cannot exist here — and the
  // full run-parity x shape matrix shows zero behavioral delta vs
  // main (odd-run cells are the defect fix's intended handoff;
  // even-run cells are parity-ship on every shape — pinned).
  // Odd-run-restricting them would change output shapes without
  // changing coverage: model consistency is a means, not an end.
  `${GUARD_UNQUOTED}(?!${MARKER_TERMINATOR})(?!\\\\+["'])(?![{\\[]\\\\+["'])${UNQUOTED_UNIT}+`
);
const CREDENTIAL_VALUE_RE = `(?:${QUOTED_VALUE_BRANCHES}|${UNQUOTED_VALUE})`;
const redactValueReplacer = (...args) => {
  return args.slice(1, -2).filter((g) => typeof g === "string").join("") + "<redacted>";
};
const SECRET_PATTERNS = [
  [/\bBearer\s+[A-Za-z0-9._~+/=-]{8,}/gi, "Bearer <token>"],
  // Basic: main's colon-only form, BYTE-IDENTICAL (the regex below
  // diff-verifies against 771f5f6c) — a transcription, not a rewrite.
  // FIFTH TOMBSTONE — the quote allowance (attempted and WITHDRAWN):
  // a post-colon quote allowance briefly let this rule fire inside
  // quoted spans, recovering above-main coverage for quoted/escaped
  // Basic headers. Its blessing rested on 'no under-fire dimension' —
  // an ARGUED claim whose measurement came later and falsified it on
  // TWO independent axes across two scoping iterations: (1) the
  // BACKTICK arm's folded remnant has no downstream catcher (nothing
  // consumes backtick-quoted values) — dropped, keeping dq/sq; (2) the
  // kept arms' 'remnant re-matchable' coverage was GATED on the outer
  // key being vocab (the outer kv eats the whole value) and on the
  // inner separator folding whole (`=` is in the token class; `:` is
  // not) — on a NON-vocab outer with a colon-separated inner
  // assignment (`note: "Basic password: hunter2"`) the fold DESTROYS
  // the inner key main re-anchors on and the value strands below
  // main, in every quote flavor. Two scoping architectures, two fold
  // surfaces, each found on a dimension the prior measurement did not
  // vary: the fold surface is per-flavor x per-outer-key x
  // per-inner-separator — open-ended for scoping, ZERO by deletion.
  // Withdrawn entirely; the quoted-Basic shapes it covered are SHARED
  // limitations at main parity EXCEPT one carve-out that is DERIVED,
  // not sampled: the kv rule's quote-crossing redacts the escaped
  // value iff the outer key is EXACTLY a vocabulary alternative — the
  // matched token must be immediately followed by the separator, so
  // `auth\":` redacts (ABOVE main) while `authorization\":` parity-
  // ships (`auth` matches but the next char is `o`, not the
  // separator; `authorization` is not itself an alternative). The
  // derivation was verified across the vocab axis: sixteen predicted
  // cells (nine exact-vocab ABOVE-main, five vocab-plus-suffix and two
  // non-vocab at parity), zero violations — the boundary holds by
  // construction, not by the two cells that first exposed it. Two
  // earlier drafts of this comment each overclaimed one way
  // ('kv-covered', then 'byte-identical parity, ALL shapes'); both
  // fell to measurement per the enumeration-license rule. And the
  // quoted-prose over-redaction delta died with the widening (its pin
  // retired to a parity assertion, byte-identical confirmed).
  // Meta-rule, now doctrine: measure a widening's FULL failure
  // surface — including every dimension the mechanism is sensitive
  // to — not just the leaks it closes.
  // FOURTH TOMBSTONE — the `=`/`=>` anchor widening (deleted, not
  // repaired): this PR briefly widened Basic's anchor beyond main's
  // colon-only form as NEW coverage. Two token-tail discriminator
  // architectures then tried to stop the widened rule from folding
  // follower KEYS into the token (the token class matches ordinary
  // words like `password`), and between them produced five measured
  // below-main leaks: the flat refusal declined padding-before-colon;
  // the domain-disjointness split missed quoted followers (a `"` is
  // neither `>` nor `:`/`=`), declined UNPADDED base64 abutting `:`
  // (multiple-of-3 encodings — roughly a third of real Basic
  // credentials), declined padded base64 before `>`, and inspected one
  // character where KV_SEP tolerates bilateral whitespace. The anchors
  // were never defect-fix-essential, so the family dies by DELETION at
  // exact main parity: `=basic` simply never anchors, and every
  // follower shape the discriminators fought over is redacted by the
  // kv rule exactly as main does it. ([013]'s key-fold class is
  // permanently moot — the anchor that enabled it no longer exists.)
  [/(:\s*)Basic\s+[A-Za-z0-9+/=]{8,}/gi, "$1Basic <token>"],
  // `.` included so sk-ant-rh-<jwt> (dotted payload/sig) is consumed whole —
  // otherwise the JWT tail survives when no key=value rule can mop it up.
  [/\bsk-ant-[A-Za-z0-9._-]{8,}/g, "<token>"],
  // Both dash and underscore prefix separators: OpenAI-style `sk-…` and
  // Stripe-style `sk_live_…`/`sk_test_…`/`rk_live_…`. Stripe classic keys
  // are 32 chars — below the 40-char blob floor — so prefix-match is the
  // only rule that can catch a bare one. This (and AIza below) shares
  // main's `sk-` rule's priced coincidental-prefix trade-off: a ≥40-char
  // base64 run that happens to contain `[sr]k[-_]` after a non-word char
  // partial-matches here before the blob rule can see it whole. The
  // clean fix is ordering the blob rules before the prefix rules (so
  // ≥40-char runs are caught first and the prefix rules only see the
  // sub-40-char keys they exist for); that relabels every ≥40-char
  // prefix key `<token>`→`<blob>` and is out of scope here.
  [/\b[sr]k[-_][A-Za-z0-9_-]{20,}/g, "<token>"],
  // Case-insensitive so the key still matches after `redactEmbeddedUrlsToHost`
  // rebuilds a URL — `URL.hostname` ASCII-lowercases per WHATWG, which would
  // otherwise defeat these when a key appears as a hostname label (the
  // exfiltration-callback-URL case). Real AWS keys are uppercase-only, so the
  // false-positive surface is negligible.
  [/\bAKIA[0-9A-Z]{16}\b/gi, "<token>"],
  [/\bASIA[0-9A-Z]{16}\b/gi, "<token>"],
  // Google API key: `AIza` + 35 base64url chars, exactly 39 — one below
  // the 40-char blob floor, and the dominant carrier `?key=…` doesn't
  // anchor the kv rule (bare `key` isn't in CREDENTIAL_KEY_RE), so
  // without a dedicated prefix rule it ships raw. Right anchor is a
  // base64url lookahead (not `\b`: `-` is non-word, so a key ending in
  // `-` before `&`/`"`/EOL has no word boundary; and not the union
  // alphabet: declining on `/` would leak a real key since no blob
  // class covers `_`/`-` together with `/`). Same coincidental-prefix
  // trade-off as the `[sr]k` rule above. `/i` for the
  // hostname-lowercasing reason described for AKIA/ASIA.
  [/\bAIza[0-9A-Za-z_-]{35}(?![0-9A-Za-z_-])/gi, "<token>"],
  [/\bgh[opusr]_[A-Za-z0-9]{36,}/g, "<token>"],
  [/\bxox[baprs]-[A-Za-z0-9-]{10,}/g, "<token>"],
  [/\bey[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}/g, "<jwt>"],
  // key=value / key: value / key => value — keep the key, redact the value.
  // Runs after the prefix-specific rules above so `token: Bearer xyz` has
  // `Bearer xyz` collapsed to `<token>` first rather than this rule eating
  // `Bearer` and exposing `xyz`. Optional (possibly JSON-escaped — `\\+["']`)
  // quote before the separator so both JSON `"key":"v"` and nested-stringified
  // `\"key\":\"v\"` match. Left anchor is `(?<![A-Za-z0-9])`, not `\b`, so the
  // key still matches after an underscore — `DB_PASSWORD=x` (common env-var
  // shape) fires, but `myPasswordField` still doesn't (`y` blocks). Separator
  // accepts `=>` so Ruby/Perl hash-rocket form doesn't consume `>` as the
  // value and leak the real one.
  [
    new RegExp(
      `(?<![A-Za-z0-9])(${CREDENTIAL_KEY_RE})(${KV_SEP})${CREDENTIAL_VALUE_RE}`,
      "gi"
    ),
    redactValueReplacer
  ],
  // `-Password foo` / `--token=bar` / `--db-password x` CLI flag form.
  // Left anchor `(?<![\w-])` so a hyphen inside a compound word (`x-api-key`,
  // `re-auth`) isn't mistaken for a flag dash; optional `(?:[A-Za-z0-9]+[-_])*`
  // after the dashes so prefixed flag names (`--db-password`,
  // `--db_password`, `--auth-token`) still match.
  [
    new RegExp(
      `(?<![\\w-])(${FLAG_KEY})(${FLAG_SEP})${CREDENTIAL_VALUE_RE}`,
      "gi"
    ),
    redactValueReplacer
  ],
  // Two opaque-blob rules, split by alphabet so 40-char filesystem paths
  // (which contain at least one of `.`, `_`, `-`) don't match the
  // standard-base64 rule and slash-separated path segments don't match the
  // base64url rule. Both use lookarounds instead of `\b`: `/`, `+`, and `-`
  // are non-word, so `\b` can't anchor a run that starts or ends with one
  // when the delimiter (`=`, `"`, space, EOL) is also non-word — leaking
  // ~6% of AWS secret keys. `=` is deliberately absent from both lookarounds
  // so `key=<secret>` still matches; the `={0,2}` body consumes padding.
  //
  // Standard-base64 (with `/`, no `_`/`-`): AWS secret access keys — exactly
  // 40 chars of [A-Za-z0-9/+], ~47% of which contain a `/` — plus longer
  // standard-base64 secrets (storage-account keys, etc.). The lookaround
  // covers the *union* alphabet (including `_`/`-`) so this rule can't
  // partial-match the 40-char prefix of a base64url token and expose its
  // `-`-separated tail — the base64url rule below sees the whole run.
  [
    new RegExp("(?<![A-Za-z0-9+/_-])[A-Za-z0-9+/]{40,}={0,2}(?![A-Za-z0-9+/_-])", "g"),
    "<blob>"
  ],
  // Base64url (`_`/`-`, no `/`): URL-safe tokens, cursors, etags, 40+ hex.
  // Lookaround covers only *this* rule's alphabet — `/` is deliberately
  // absent so a base64url token delimited by a `/` (URL path segment, e.g.
  // `/v1/<cursor>/next`) still anchors. Partial-matching a standard-base64
  // token is already prevented: the rule above catches those whole first.
  [new RegExp("(?<![A-Za-z0-9+_-])[A-Za-z0-9+_-]{40,}={0,2}(?![A-Za-z0-9+_-])", "g"), "<blob>"]
  // NOTE: an orphan-quoted-tail repair rule lived here across two
  // revisions and is DELETED, with its root cause, rather than guarded
  // again: pair-aware plain-double-quote matching over-consumed past
  // escaped quotes (the follower-swallow), stranding follower fragments
  // the orphan rule existed to mop, and the rule + its guards drew
  // thirteen findings across three scans (ordering, ReDoS, vocabulary, a
  // structure-corruption regression erasing field names in dominant
  // compact JSON, and a guard that re-opened the swallow leak). The
  // plain-dq revert above kills the swallow at the source — "plain
  // quoting styles don't self-escape; escaped styles definitionally do"
  // — and with it the stranded-follower class. Remaining escaped-branch
  // boundary remnants route to the blob rules or ship as DOCUMENTED,
  // PINNED limitations (each verified better-than-or-equal-to pre-PR).
];
function redactSecretLike(text) {
  let out = text;
  for (const [re, sub] of SECRET_PATTERNS) {
    out = typeof sub === "string" ? out.replace(re, sub) : out.replace(re, sub);
  }
  return out;
}
const SCRUB_LINE_MAX = 8 * 1024;
const URL_USERINFO_RE = /:\/\/(?!\[)[^\s/:]*(?::[^\s/]{0,8192})?@(?=[^@\s?#]*(?:[/:?#\s]|$))/g;
const MAX_USERINFO_SCHEMES_PER_SEGMENT = 32;
function stripUrlUserinfo(text) {
  if (!text.includes("@")) {
    return text;
  }
  return text.replace(/\S+/g, (seg) => {
    if (!seg.includes("@")) {
      return seg;
    }
    let schemes = 0;
    for (let i = seg.indexOf("://"); i !== -1; i = seg.indexOf("://", i + 3)) {
      if (++schemes > MAX_USERINFO_SCHEMES_PER_SEGMENT) {
        return `<redacted:dense-urls:${seg.length}b>`;
      }
    }
    if (schemes === 0) {
      return seg;
    }
    return seg.replace(URL_USERINFO_RE, "://<userinfo>@");
  });
}
function scrubFreeText(text, opts) {
  return redactSecretLike(
    redactIpAddress(
      redactEmail(scrubFilesystemPaths(stripUrlUserinfo(text), opts))
    )
  );
}
function scrubLogLine(text, opts) {
  if (text.length > SCRUB_LINE_MAX) {
    return scrubFreeText(text.slice(0, SCRUB_LINE_MAX), opts) + "…<truncated>";
  }
  return scrubFreeText(text, opts);
}
function scrubFilesystemPaths(text, opts) {
  let httpCacheFor;
  let httpSchemeEnds = [];
  let httpTokenEnds = [];
  const inHttpUrl = (str, offset) => {
    if (str !== httpCacheFor) {
      httpSchemeEnds = [];
      httpTokenEnds = [];
      const re = /(https?:\/\/)[^\s'",;|()]*/gi;
      for (let m; (m = re.exec(str)) !== null; ) {
        httpSchemeEnds.push(m.index + m[1].length);
        httpTokenEnds.push(m.index + m[0].length);
      }
    }
    httpCacheFor = str;
    if (httpSchemeEnds.length === 0) {
      return false;
    }
    let lo = 0;
    let hi = httpSchemeEnds.length;
    while (lo < hi) {
      const mid = lo + hi >> 1;
      if (httpSchemeEnds[mid] <= offset) {
        lo = mid + 1;
      } else {
        hi = mid;
      }
    }
    return lo > 0 && offset <= httpTokenEnds[lo - 1];
  };
  let out = text;
  if (opts.appPath) {
    out = out.replaceAll(opts.appPath, "app://");
  }
  if (opts.homedir) {
    out = out.replaceAll(opts.homedir, "<home>");
  }
  out = out.replace(
    /([/\\]+(?:Users|home)[/\\]+)[^/\\\n]+/gi,
    (m, p1, offset, str) => inHttpUrl(str, offset) ? m : `${p1}<user>`
  ).replace(
    /(\/(?:Volumes|mnt|media)\/)[^/\n]+/g,
    (m, p1, offset, str) => inHttpUrl(str, offset) ? m : `${p1}<vol>`
  ).replace(
    /((?:\/etc\/profiles|\/nix\/var\/nix\/profiles)\/per-user\/)[^/\n]+/g,
    (m, p1, offset, str) => inHttpUrl(str, offset) ? m : `${p1}<user>`
  );
  return out.replace(/\b([A-Za-z]):([\\/])/g, "<drv>:$2").replace(/\\\\[^\\]+\\[^\\\s'",:()]+/g, "<unc>");
}
var require$1 = module$1.createRequire("/");
var Worker;
try {
  Worker = require$1("worker_threads").Worker;
} catch (e) {
}
var u8 = Uint8Array, u16 = Uint16Array, i32 = Int32Array;
var fleb = new u8([
  0,
  0,
  0,
  0,
  0,
  0,
  0,
  0,
  1,
  1,
  1,
  1,
  2,
  2,
  2,
  2,
  3,
  3,
  3,
  3,
  4,
  4,
  4,
  4,
  5,
  5,
  5,
  5,
  0,
  /* unused */
  0,
  0,
  /* impossible */
  0
]);
var fdeb = new u8([
  0,
  0,
  0,
  0,
  1,
  1,
  2,
  2,
  3,
  3,
  4,
  4,
  5,
  5,
  6,
  6,
  7,
  7,
  8,
  8,
  9,
  9,
  10,
  10,
  11,
  11,
  12,
  12,
  13,
  13,
  /* unused */
  0,
  0
]);
var clim = new u8([16, 17, 18, 0, 8, 7, 9, 6, 10, 5, 11, 4, 12, 3, 13, 2, 14, 1, 15]);
var freb = function(eb, start) {
  var b = new u16(31);
  for (var i = 0; i < 31; ++i) {
    b[i] = start += 1 << eb[i - 1];
  }
  var r = new i32(b[30]);
  for (var i = 1; i < 30; ++i) {
    for (var j = b[i]; j < b[i + 1]; ++j) {
      r[j] = j - b[i] << 5 | i;
    }
  }
  return { b, r };
};
var _a = freb(fleb, 2), fl = _a.b, revfl = _a.r;
fl[28] = 258, revfl[258] = 28;
var _b = freb(fdeb, 0), revfd = _b.r;
var rev = new u16(32768);
for (var i = 0; i < 32768; ++i) {
  var x = (i & 43690) >> 1 | (i & 21845) << 1;
  x = (x & 52428) >> 2 | (x & 13107) << 2;
  x = (x & 61680) >> 4 | (x & 3855) << 4;
  rev[i] = ((x & 65280) >> 8 | (x & 255) << 8) >> 1;
}
var hMap = function(cd, mb, r) {
  var s = cd.length;
  var i = 0;
  var l = new u16(mb);
  for (; i < s; ++i) {
    if (cd[i])
      ++l[cd[i] - 1];
  }
  var le = new u16(mb);
  for (i = 1; i < mb; ++i) {
    le[i] = le[i - 1] + l[i - 1] << 1;
  }
  var co;
  if (r) {
    co = new u16(1 << mb);
    var rvb = 15 - mb;
    for (i = 0; i < s; ++i) {
      if (cd[i]) {
        var sv = i << 4 | cd[i];
        var r_1 = mb - cd[i];
        var v = le[cd[i] - 1]++ << r_1;
        for (var m = v | (1 << r_1) - 1; v <= m; ++v) {
          co[rev[v] >> rvb] = sv;
        }
      }
    }
  } else {
    co = new u16(s);
    for (i = 0; i < s; ++i) {
      if (cd[i]) {
        co[i] = rev[le[cd[i] - 1]++] >> 15 - cd[i];
      }
    }
  }
  return co;
};
var flt = new u8(288);
for (var i = 0; i < 144; ++i)
  flt[i] = 8;
for (var i = 144; i < 256; ++i)
  flt[i] = 9;
for (var i = 256; i < 280; ++i)
  flt[i] = 7;
for (var i = 280; i < 288; ++i)
  flt[i] = 8;
var fdt = new u8(32);
for (var i = 0; i < 32; ++i)
  fdt[i] = 5;
var flm = /* @__PURE__ */ hMap(flt, 9, 0);
var fdm = /* @__PURE__ */ hMap(fdt, 5, 0);
var shft = function(p) {
  return (p + 7) / 8 | 0;
};
var slc = function(v, s, e) {
  if (e == null || e > v.length)
    e = v.length;
  return new u8(v.subarray(s, e));
};
var ec = [
  "unexpected EOF",
  "invalid block type",
  "invalid length/literal",
  "invalid distance",
  "stream finished",
  "no stream handler",
  ,
  "no callback",
  "invalid UTF-8 data",
  "extra field too long",
  "date not in range 1980-2099",
  "filename too long",
  "stream finishing",
  "invalid zip data"
  // determined by unknown compression method
];
var err = function(ind, msg, nt) {
  var e = new Error(msg || ec[ind]);
  e.code = ind;
  if (Error.captureStackTrace)
    Error.captureStackTrace(e, err);
  if (!nt)
    throw e;
  return e;
};
var wbits = function(d, p, v) {
  v <<= p & 7;
  var o = p / 8 | 0;
  d[o] |= v;
  d[o + 1] |= v >> 8;
};
var wbits16 = function(d, p, v) {
  v <<= p & 7;
  var o = p / 8 | 0;
  d[o] |= v;
  d[o + 1] |= v >> 8;
  d[o + 2] |= v >> 16;
};
var hTree = function(d, mb) {
  var t = [];
  for (var i = 0; i < d.length; ++i) {
    if (d[i])
      t.push({ s: i, f: d[i] });
  }
  var s = t.length;
  var t2 = t.slice();
  if (!s)
    return { t: et, l: 0 };
  if (s == 1) {
    var v = new u8(t[0].s + 1);
    v[t[0].s] = 1;
    return { t: v, l: 1 };
  }
  t.sort(function(a, b) {
    return a.f - b.f;
  });
  t.push({ s: -1, f: 25001 });
  var l = t[0], r = t[1], i0 = 0, i1 = 1, i2 = 2;
  t[0] = { s: -1, f: l.f + r.f, l, r };
  while (i1 != s - 1) {
    l = t[t[i0].f < t[i2].f ? i0++ : i2++];
    r = t[i0 != i1 && t[i0].f < t[i2].f ? i0++ : i2++];
    t[i1++] = { s: -1, f: l.f + r.f, l, r };
  }
  var maxSym = t2[0].s;
  for (var i = 1; i < s; ++i) {
    if (t2[i].s > maxSym)
      maxSym = t2[i].s;
  }
  var tr = new u16(maxSym + 1);
  var mbt = ln(t[i1 - 1], tr, 0);
  if (mbt > mb) {
    var i = 0, dt = 0;
    var lft = mbt - mb, cst = 1 << lft;
    t2.sort(function(a, b) {
      return tr[b.s] - tr[a.s] || a.f - b.f;
    });
    for (; i < s; ++i) {
      var i2_1 = t2[i].s;
      if (tr[i2_1] > mb) {
        dt += cst - (1 << mbt - tr[i2_1]);
        tr[i2_1] = mb;
      } else
        break;
    }
    dt >>= lft;
    while (dt > 0) {
      var i2_2 = t2[i].s;
      if (tr[i2_2] < mb)
        dt -= 1 << mb - tr[i2_2]++ - 1;
      else
        ++i;
    }
    for (; i >= 0 && dt; --i) {
      var i2_3 = t2[i].s;
      if (tr[i2_3] == mb) {
        --tr[i2_3];
        ++dt;
      }
    }
    mbt = mb;
  }
  return { t: new u8(tr), l: mbt };
};
var ln = function(n, l, d) {
  return n.s == -1 ? Math.max(ln(n.l, l, d + 1), ln(n.r, l, d + 1)) : l[n.s] = d;
};
var lc = function(c) {
  var s = c.length;
  while (s && !c[--s])
    ;
  var cl = new u16(++s);
  var cli = 0, cln = c[0], cls = 1;
  var w = function(v) {
    cl[cli++] = v;
  };
  for (var i = 1; i <= s; ++i) {
    if (c[i] == cln && i != s)
      ++cls;
    else {
      if (!cln && cls > 2) {
        for (; cls > 138; cls -= 138)
          w(32754);
        if (cls > 2) {
          w(cls > 10 ? cls - 11 << 5 | 28690 : cls - 3 << 5 | 12305);
          cls = 0;
        }
      } else if (cls > 3) {
        w(cln), --cls;
        for (; cls > 6; cls -= 6)
          w(8304);
        if (cls > 2)
          w(cls - 3 << 5 | 8208), cls = 0;
      }
      while (cls--)
        w(cln);
      cls = 1;
      cln = c[i];
    }
  }
  return { c: cl.subarray(0, cli), n: s };
};
var clen = function(cf, cl) {
  var l = 0;
  for (var i = 0; i < cl.length; ++i)
    l += cf[i] * cl[i];
  return l;
};
var wfblk = function(out, pos, dat) {
  var s = dat.length;
  var o = shft(pos + 2);
  out[o] = s & 255;
  out[o + 1] = s >> 8;
  out[o + 2] = out[o] ^ 255;
  out[o + 3] = out[o + 1] ^ 255;
  for (var i = 0; i < s; ++i)
    out[o + i + 4] = dat[i];
  return (o + 4 + s) * 8;
};
var wblk = function(dat, out, final, syms, lf, df, eb, li, bs, bl, p) {
  wbits(out, p++, final);
  ++lf[256];
  var _a3 = hTree(lf, 15), dlt = _a3.t, mlb = _a3.l;
  var _b2 = hTree(df, 15), ddt = _b2.t, mdb = _b2.l;
  var _c = lc(dlt), lclt = _c.c, nlc = _c.n;
  var _d = lc(ddt), lcdt = _d.c, ndc = _d.n;
  var lcfreq = new u16(19);
  for (var i = 0; i < lclt.length; ++i)
    ++lcfreq[lclt[i] & 31];
  for (var i = 0; i < lcdt.length; ++i)
    ++lcfreq[lcdt[i] & 31];
  var _e = hTree(lcfreq, 7), lct = _e.t, mlcb = _e.l;
  var nlcc = 19;
  for (; nlcc > 4 && !lct[clim[nlcc - 1]]; --nlcc)
    ;
  var flen = bl + 5 << 3;
  var ftlen = clen(lf, flt) + clen(df, fdt) + eb;
  var dtlen = clen(lf, dlt) + clen(df, ddt) + eb + 14 + 3 * nlcc + clen(lcfreq, lct) + 2 * lcfreq[16] + 3 * lcfreq[17] + 7 * lcfreq[18];
  if (bs >= 0 && flen <= ftlen && flen <= dtlen)
    return wfblk(out, p, dat.subarray(bs, bs + bl));
  var lm, ll, dm, dl;
  wbits(out, p, 1 + (dtlen < ftlen)), p += 2;
  if (dtlen < ftlen) {
    lm = hMap(dlt, mlb, 0), ll = dlt, dm = hMap(ddt, mdb, 0), dl = ddt;
    var llm = hMap(lct, mlcb, 0);
    wbits(out, p, nlc - 257);
    wbits(out, p + 5, ndc - 1);
    wbits(out, p + 10, nlcc - 4);
    p += 14;
    for (var i = 0; i < nlcc; ++i)
      wbits(out, p + 3 * i, lct[clim[i]]);
    p += 3 * nlcc;
    var lcts = [lclt, lcdt];
    for (var it = 0; it < 2; ++it) {
      var clct = lcts[it];
      for (var i = 0; i < clct.length; ++i) {
        var len = clct[i] & 31;
        wbits(out, p, llm[len]), p += lct[len];
        if (len > 15)
          wbits(out, p, clct[i] >> 5 & 127), p += clct[i] >> 12;
      }
    }
  } else {
    lm = flm, ll = flt, dm = fdm, dl = fdt;
  }
  for (var i = 0; i < li; ++i) {
    var sym = syms[i];
    if (sym > 255) {
      var len = sym >> 18 & 31;
      wbits16(out, p, lm[len + 257]), p += ll[len + 257];
      if (len > 7)
        wbits(out, p, sym >> 23 & 31), p += fleb[len];
      var dst = sym & 31;
      wbits16(out, p, dm[dst]), p += dl[dst];
      if (dst > 3)
        wbits16(out, p, sym >> 5 & 8191), p += fdeb[dst];
    } else {
      wbits16(out, p, lm[sym]), p += ll[sym];
    }
  }
  wbits16(out, p, lm[256]);
  return p + ll[256];
};
var deo = /* @__PURE__ */ new i32([65540, 131080, 131088, 131104, 262176, 1048704, 1048832, 2114560, 2117632]);
var et = /* @__PURE__ */ new u8(0);
var dflt = function(dat, lvl, plvl, pre, post, st) {
  var s = st.z || dat.length;
  var o = new u8(pre + s + 5 * (1 + Math.ceil(s / 7e3)) + post);
  var w = o.subarray(pre, o.length - post);
  var lst = st.l;
  var pos = (st.r || 0) & 7;
  if (lvl) {
    if (pos)
      w[0] = st.r >> 3;
    var opt = deo[lvl - 1];
    var n = opt >> 13, c = opt & 8191;
    var msk_1 = (1 << plvl) - 1;
    var prev = st.p || new u16(32768), head = st.h || new u16(msk_1 + 1);
    var bs1_1 = Math.ceil(plvl / 3), bs2_1 = 2 * bs1_1;
    var hsh = function(i2) {
      return (dat[i2] ^ dat[i2 + 1] << bs1_1 ^ dat[i2 + 2] << bs2_1) & msk_1;
    };
    var syms = new i32(25e3);
    var lf = new u16(288), df = new u16(32);
    var lc_1 = 0, eb = 0, i = st.i || 0, li = 0, wi = st.w || 0, bs = 0;
    for (; i + 2 < s; ++i) {
      var hv = hsh(i);
      var imod = i & 32767, pimod = head[hv];
      prev[imod] = pimod;
      head[hv] = imod;
      if (wi <= i) {
        var rem = s - i;
        if ((lc_1 > 7e3 || li > 24576) && (rem > 423 || !lst)) {
          pos = wblk(dat, w, 0, syms, lf, df, eb, li, bs, i - bs, pos);
          li = lc_1 = eb = 0, bs = i;
          for (var j = 0; j < 286; ++j)
            lf[j] = 0;
          for (var j = 0; j < 30; ++j)
            df[j] = 0;
        }
        var l = 2, d = 0, ch_1 = c, dif = imod - pimod & 32767;
        if (rem > 2 && hv == hsh(i - dif)) {
          var maxn = Math.min(n, rem) - 1;
          var maxd = Math.min(32767, i);
          var ml = Math.min(258, rem);
          while (dif <= maxd && --ch_1 && imod != pimod) {
            if (dat[i + l] == dat[i + l - dif]) {
              var nl = 0;
              for (; nl < ml && dat[i + nl] == dat[i + nl - dif]; ++nl)
                ;
              if (nl > l) {
                l = nl, d = dif;
                if (nl > maxn)
                  break;
                var mmd = Math.min(dif, nl - 2);
                var md = 0;
                for (var j = 0; j < mmd; ++j) {
                  var ti = i - dif + j & 32767;
                  var pti = prev[ti];
                  var cd = ti - pti & 32767;
                  if (cd > md)
                    md = cd, pimod = ti;
                }
              }
            }
            imod = pimod, pimod = prev[imod];
            dif += imod - pimod & 32767;
          }
        }
        if (d) {
          syms[li++] = 268435456 | revfl[l] << 18 | revfd[d];
          var lin = revfl[l] & 31, din = revfd[d] & 31;
          eb += fleb[lin] + fdeb[din];
          ++lf[257 + lin];
          ++df[din];
          wi = i + l;
          ++lc_1;
        } else {
          syms[li++] = dat[i];
          ++lf[dat[i]];
        }
      }
    }
    for (i = Math.max(i, wi); i < s; ++i) {
      syms[li++] = dat[i];
      ++lf[dat[i]];
    }
    pos = wblk(dat, w, lst, syms, lf, df, eb, li, bs, i - bs, pos);
    if (!lst) {
      st.r = pos & 7 | w[pos / 8 | 0] << 3;
      pos -= 7;
      st.h = head, st.p = prev, st.i = i, st.w = wi;
    }
  } else {
    for (var i = st.w || 0; i < s + lst; i += 65535) {
      var e = i + 65535;
      if (e >= s) {
        w[pos / 8 | 0] = lst;
        e = s;
      }
      pos = wfblk(w, pos + 1, dat.subarray(i, e));
    }
    st.i = s;
  }
  return slc(o, 0, pre + shft(pos) + post);
};
var crct = /* @__PURE__ */ function() {
  var t = new Int32Array(256);
  for (var i = 0; i < 256; ++i) {
    var c = i, k = 9;
    while (--k)
      c = (c & 1 && -306674912) ^ c >>> 1;
    t[i] = c;
  }
  return t;
}();
var crc = function() {
  var c = -1;
  return {
    p: function(d) {
      var cr = c;
      for (var i = 0; i < d.length; ++i)
        cr = crct[cr & 255 ^ d[i]] ^ cr >>> 8;
      c = cr;
    },
    d: function() {
      return ~c;
    }
  };
};
var dopt = function(dat, opt, pre, post, st) {
  if (!st) {
    st = { l: 1 };
    if (opt.dictionary) {
      var dict = opt.dictionary.subarray(-32768);
      var newDat = new u8(dict.length + dat.length);
      newDat.set(dict);
      newDat.set(dat, dict.length);
      dat = newDat;
      st.w = dict.length;
    }
  }
  return dflt(dat, opt.level == null ? 6 : opt.level, opt.mem == null ? st.l ? Math.ceil(Math.max(8, Math.min(13, Math.log(dat.length))) * 1.5) : 20 : 12 + opt.mem, pre, post, st);
};
var mrg = function(a, b) {
  var o = {};
  for (var k in a)
    o[k] = a[k];
  for (var k in b)
    o[k] = b[k];
  return o;
};
var wbytes = function(d, b, v) {
  for (; v; ++b)
    d[b] = v, v >>>= 8;
};
function deflateSync(data, opts) {
  return dopt(data, opts || {}, 0, 0);
}
var fltn = function(d, p, t, o) {
  for (var k in d) {
    var val = d[k], n = p + k, op = o;
    if (Array.isArray(val))
      op = mrg(o, val[1]), val = val[0];
    if (val instanceof u8)
      t[n] = [val, op];
    else {
      t[n += "/"] = [new u8(0), op];
      fltn(val, n, t, o);
    }
  }
};
var te = typeof TextEncoder != "undefined" && /* @__PURE__ */ new TextEncoder();
var td = typeof TextDecoder != "undefined" && /* @__PURE__ */ new TextDecoder();
var tds = 0;
try {
  td.decode(et, { stream: true });
  tds = 1;
} catch (e) {
}
function strToU8(str, latin1) {
  var i;
  if (te)
    return te.encode(str);
  var l = str.length;
  var ar = new u8(str.length + (str.length >> 1));
  var ai = 0;
  var w = function(v) {
    ar[ai++] = v;
  };
  for (var i = 0; i < l; ++i) {
    if (ai + 5 > ar.length) {
      var n = new u8(ai + 8 + (l - i << 1));
      n.set(ar);
      ar = n;
    }
    var c = str.charCodeAt(i);
    if (c < 128 || latin1)
      w(c);
    else if (c < 2048)
      w(192 | c >> 6), w(128 | c & 63);
    else if (c > 55295 && c < 57344)
      c = 65536 + (c & 1023 << 10) | str.charCodeAt(++i) & 1023, w(240 | c >> 18), w(128 | c >> 12 & 63), w(128 | c >> 6 & 63), w(128 | c & 63);
    else
      w(224 | c >> 12), w(128 | c >> 6 & 63), w(128 | c & 63);
  }
  return slc(ar, 0, ai);
}
var exfl = function(ex) {
  var le = 0;
  if (ex) {
    for (var k in ex) {
      var l = ex[k].length;
      if (l > 65535)
        err(9);
      le += l + 4;
    }
  }
  return le;
};
var wzh = function(d, b, f, fn, u, c, ce, co) {
  var fl2 = fn.length, ex = f.extra, col = co && co.length;
  var exl = exfl(ex);
  wbytes(d, b, ce != null ? 33639248 : 67324752), b += 4;
  if (ce != null)
    d[b++] = 20, d[b++] = f.os;
  d[b] = 20, b += 2;
  d[b++] = f.flag << 1 | (c < 0 && 8), d[b++] = u && 8;
  d[b++] = f.compression & 255, d[b++] = f.compression >> 8;
  var dt = new Date(f.mtime == null ? Date.now() : f.mtime), y = dt.getFullYear() - 1980;
  if (y < 0 || y > 119)
    err(10);
  wbytes(d, b, y << 25 | dt.getMonth() + 1 << 21 | dt.getDate() << 16 | dt.getHours() << 11 | dt.getMinutes() << 5 | dt.getSeconds() >> 1), b += 4;
  if (c != -1) {
    wbytes(d, b, f.crc);
    wbytes(d, b + 4, c < 0 ? -c - 2 : c);
    wbytes(d, b + 8, f.size);
  }
  wbytes(d, b + 12, fl2);
  wbytes(d, b + 14, exl), b += 16;
  if (ce != null) {
    wbytes(d, b, col);
    wbytes(d, b + 6, f.attrs);
    wbytes(d, b + 10, ce), b += 14;
  }
  d.set(fn, b);
  b += fl2;
  if (exl) {
    for (var k in ex) {
      var exf = ex[k], l = exf.length;
      wbytes(d, b, +k);
      wbytes(d, b + 2, l);
      d.set(exf, b + 4), b += 4 + l;
    }
  }
  if (col)
    d.set(co, b), b += col;
  return b;
};
var wzf = function(o, b, c, d, e) {
  wbytes(o, b, 101010256);
  wbytes(o, b + 8, c);
  wbytes(o, b + 10, c);
  wbytes(o, b + 12, d);
  wbytes(o, b + 16, e);
};
function zipSync(data, opts) {
  if (!opts)
    opts = {};
  var r = {};
  var files = [];
  fltn(data, "", r, opts);
  var o = 0;
  var tot = 0;
  for (var fn in r) {
    var _a3 = r[fn], file = _a3[0], p = _a3[1];
    var compression = p.level == 0 ? 0 : 8;
    var f = strToU8(fn), s = f.length;
    var com = p.comment, m = com && strToU8(com), ms = m && m.length;
    var exl = exfl(p.extra);
    if (s > 65535)
      err(11);
    var d = compression ? deflateSync(file, p) : file, l = d.length;
    var c = crc();
    c.p(file);
    files.push(mrg(p, {
      size: file.length,
      crc: c.d(),
      c: d,
      f,
      m,
      u: s != fn.length || m && com.length != ms,
      o,
      compression
    }));
    o += 30 + s + exl + l;
    tot += 76 + 2 * (s + exl) + (ms || 0) + l;
  }
  var out = new u8(tot + 22), oe = o, cdl = tot - o;
  for (var i = 0; i < files.length; ++i) {
    var f = files[i];
    wzh(out, f.o, f, f.f, f.u, f.c.length);
    var badd = 30 + f.f.length + exfl(f.extra);
    out.set(f.c, f.o + badd);
    wzh(out, o, f, f.f, f.u, f.c.length, f.o, f.m), o += 16 + badd + (f.m ? f.m.length : 0);
  }
  wzf(out, o, files.length, cdl, oe);
  return out;
}
function getDefaultExportFromCjs(x) {
  return x && x.__esModule && Object.prototype.hasOwnProperty.call(x, "default") ? x["default"] : x;
}
var eventemitter3 = { exports: {} };
var hasRequiredEventemitter3;
function requireEventemitter3() {
  if (hasRequiredEventemitter3) return eventemitter3.exports;
  hasRequiredEventemitter3 = 1;
  (function(module2) {
    var has = Object.prototype.hasOwnProperty, prefix = "~";
    function Events() {
    }
    if (Object.create) {
      Events.prototype = /* @__PURE__ */ Object.create(null);
      if (!new Events().__proto__) prefix = false;
    }
    function EE(fn, context, once) {
      this.fn = fn;
      this.context = context;
      this.once = once || false;
    }
    function addListener(emitter, event, fn, context, once) {
      if (typeof fn !== "function") {
        throw new TypeError("The listener must be a function");
      }
      var listener = new EE(fn, context || emitter, once), evt = prefix ? prefix + event : event;
      if (!emitter._events[evt]) emitter._events[evt] = listener, emitter._eventsCount++;
      else if (!emitter._events[evt].fn) emitter._events[evt].push(listener);
      else emitter._events[evt] = [emitter._events[evt], listener];
      return emitter;
    }
    function clearEvent(emitter, evt) {
      if (--emitter._eventsCount === 0) emitter._events = new Events();
      else delete emitter._events[evt];
    }
    function EventEmitter2() {
      this._events = new Events();
      this._eventsCount = 0;
    }
    EventEmitter2.prototype.eventNames = function eventNames() {
      var names = [], events, name;
      if (this._eventsCount === 0) return names;
      for (name in events = this._events) {
        if (has.call(events, name)) names.push(prefix ? name.slice(1) : name);
      }
      if (Object.getOwnPropertySymbols) {
        return names.concat(Object.getOwnPropertySymbols(events));
      }
      return names;
    };
    EventEmitter2.prototype.listeners = function listeners(event) {
      var evt = prefix ? prefix + event : event, handlers2 = this._events[evt];
      if (!handlers2) return [];
      if (handlers2.fn) return [handlers2.fn];
      for (var i = 0, l = handlers2.length, ee = new Array(l); i < l; i++) {
        ee[i] = handlers2[i].fn;
      }
      return ee;
    };
    EventEmitter2.prototype.listenerCount = function listenerCount(event) {
      var evt = prefix ? prefix + event : event, listeners = this._events[evt];
      if (!listeners) return 0;
      if (listeners.fn) return 1;
      return listeners.length;
    };
    EventEmitter2.prototype.emit = function emit(event, a1, a2, a3, a4, a5) {
      var evt = prefix ? prefix + event : event;
      if (!this._events[evt]) return false;
      var listeners = this._events[evt], len = arguments.length, args, i;
      if (listeners.fn) {
        if (listeners.once) this.removeListener(event, listeners.fn, void 0, true);
        switch (len) {
          case 1:
            return listeners.fn.call(listeners.context), true;
          case 2:
            return listeners.fn.call(listeners.context, a1), true;
          case 3:
            return listeners.fn.call(listeners.context, a1, a2), true;
          case 4:
            return listeners.fn.call(listeners.context, a1, a2, a3), true;
          case 5:
            return listeners.fn.call(listeners.context, a1, a2, a3, a4), true;
          case 6:
            return listeners.fn.call(listeners.context, a1, a2, a3, a4, a5), true;
        }
        for (i = 1, args = new Array(len - 1); i < len; i++) {
          args[i - 1] = arguments[i];
        }
        listeners.fn.apply(listeners.context, args);
      } else {
        var length = listeners.length, j;
        for (i = 0; i < length; i++) {
          if (listeners[i].once) this.removeListener(event, listeners[i].fn, void 0, true);
          switch (len) {
            case 1:
              listeners[i].fn.call(listeners[i].context);
              break;
            case 2:
              listeners[i].fn.call(listeners[i].context, a1);
              break;
            case 3:
              listeners[i].fn.call(listeners[i].context, a1, a2);
              break;
            case 4:
              listeners[i].fn.call(listeners[i].context, a1, a2, a3);
              break;
            default:
              if (!args) for (j = 1, args = new Array(len - 1); j < len; j++) {
                args[j - 1] = arguments[j];
              }
              listeners[i].fn.apply(listeners[i].context, args);
          }
        }
      }
      return true;
    };
    EventEmitter2.prototype.on = function on(event, fn, context) {
      return addListener(this, event, fn, context, false);
    };
    EventEmitter2.prototype.once = function once(event, fn, context) {
      return addListener(this, event, fn, context, true);
    };
    EventEmitter2.prototype.removeListener = function removeListener(event, fn, context, once) {
      var evt = prefix ? prefix + event : event;
      if (!this._events[evt]) return this;
      if (!fn) {
        clearEvent(this, evt);
        return this;
      }
      var listeners = this._events[evt];
      if (listeners.fn) {
        if (listeners.fn === fn && (!once || listeners.once) && (!context || listeners.context === context)) {
          clearEvent(this, evt);
        }
      } else {
        for (var i = 0, events = [], length = listeners.length; i < length; i++) {
          if (listeners[i].fn !== fn || once && !listeners[i].once || context && listeners[i].context !== context) {
            events.push(listeners[i]);
          }
        }
        if (events.length) this._events[evt] = events.length === 1 ? events[0] : events;
        else clearEvent(this, evt);
      }
      return this;
    };
    EventEmitter2.prototype.removeAllListeners = function removeAllListeners(event) {
      var evt;
      if (event) {
        evt = prefix ? prefix + event : event;
        if (this._events[evt]) clearEvent(this, evt);
      } else {
        this._events = new Events();
        this._eventsCount = 0;
      }
      return this;
    };
    EventEmitter2.prototype.off = EventEmitter2.prototype.removeListener;
    EventEmitter2.prototype.addListener = EventEmitter2.prototype.on;
    EventEmitter2.prefixed = prefix;
    EventEmitter2.EventEmitter = EventEmitter2;
    {
      module2.exports = EventEmitter2;
    }
  })(eventemitter3);
  return eventemitter3.exports;
}
var eventemitter3Exports = requireEventemitter3();
const EventEmitter = /* @__PURE__ */ getDefaultExportFromCjs(eventemitter3Exports);
class TimeoutError extends Error {
  constructor(message) {
    super(message);
    this.name = "TimeoutError";
  }
}
class AbortError extends Error {
  constructor(message) {
    super();
    this.name = "AbortError";
    this.message = message;
  }
}
const getDOMException = (errorMessage) => globalThis.DOMException === void 0 ? new AbortError(errorMessage) : new DOMException(errorMessage);
const getAbortedReason = (signal) => {
  const reason = signal.reason === void 0 ? getDOMException("This operation was aborted.") : signal.reason;
  return reason instanceof Error ? reason : getDOMException(reason);
};
function pTimeout(promise, options) {
  const {
    milliseconds,
    fallback,
    message,
    customTimers = { setTimeout, clearTimeout }
  } = options;
  let timer;
  let abortHandler;
  const wrappedPromise = new Promise((resolve, reject) => {
    if (typeof milliseconds !== "number" || Math.sign(milliseconds) !== 1) {
      throw new TypeError(`Expected \`milliseconds\` to be a positive number, got \`${milliseconds}\``);
    }
    if (options.signal) {
      const { signal } = options;
      if (signal.aborted) {
        reject(getAbortedReason(signal));
      }
      abortHandler = () => {
        reject(getAbortedReason(signal));
      };
      signal.addEventListener("abort", abortHandler, { once: true });
    }
    if (milliseconds === Number.POSITIVE_INFINITY) {
      promise.then(resolve, reject);
      return;
    }
    const timeoutError = new TimeoutError();
    timer = customTimers.setTimeout.call(void 0, () => {
      if (fallback) {
        try {
          resolve(fallback());
        } catch (error) {
          reject(error);
        }
        return;
      }
      if (typeof promise.cancel === "function") {
        promise.cancel();
      }
      if (message === false) {
        resolve();
      } else if (message instanceof Error) {
        reject(message);
      } else {
        timeoutError.message = message ?? `Promise timed out after ${milliseconds} milliseconds`;
        reject(timeoutError);
      }
    }, milliseconds);
    (async () => {
      try {
        resolve(await promise);
      } catch (error) {
        reject(error);
      }
    })();
  });
  const cancelablePromise = wrappedPromise.finally(() => {
    cancelablePromise.clear();
    if (abortHandler && options.signal) {
      options.signal.removeEventListener("abort", abortHandler);
    }
  });
  cancelablePromise.clear = () => {
    customTimers.clearTimeout.call(void 0, timer);
    timer = void 0;
  };
  return cancelablePromise;
}
function lowerBound(array, value, comparator) {
  let first = 0;
  let count = array.length;
  while (count > 0) {
    const step = Math.trunc(count / 2);
    let it = first + step;
    if (comparator(array[it], value) <= 0) {
      first = ++it;
      count -= step + 1;
    } else {
      count = step;
    }
  }
  return first;
}
class PriorityQueue {
  constructor() {
    __privateAdd(this, _queue, []);
  }
  enqueue(run, options) {
    options = {
      priority: 0,
      ...options
    };
    const element = {
      priority: options.priority,
      run
    };
    if (this.size && __privateGet(this, _queue)[this.size - 1].priority >= options.priority) {
      __privateGet(this, _queue).push(element);
      return;
    }
    const index = lowerBound(__privateGet(this, _queue), element, (a, b) => b.priority - a.priority);
    __privateGet(this, _queue).splice(index, 0, element);
  }
  dequeue() {
    const item = __privateGet(this, _queue).shift();
    return item == null ? void 0 : item.run;
  }
  filter(options) {
    return __privateGet(this, _queue).filter((element) => element.priority === options.priority).map((element) => element.run);
  }
  get size() {
    return __privateGet(this, _queue).length;
  }
}
_queue = new WeakMap();
class PQueue extends EventEmitter {
  // TODO: The `throwOnTimeout` option should affect the return types of `add()` and `addAll()`
  constructor(options) {
    var _a3, _b2;
    super();
    __privateAdd(this, _PQueue_instances);
    __privateAdd(this, _carryoverConcurrencyCount);
    __privateAdd(this, _isIntervalIgnored);
    __privateAdd(this, _intervalCount, 0);
    __privateAdd(this, _intervalCap);
    __privateAdd(this, _interval);
    __privateAdd(this, _intervalEnd, 0);
    __privateAdd(this, _intervalId);
    __privateAdd(this, _timeoutId);
    __privateAdd(this, _queue2);
    __privateAdd(this, _queueClass);
    __privateAdd(this, _pending, 0);
    // The `!` is needed because of https://github.com/microsoft/TypeScript/issues/32194
    __privateAdd(this, _concurrency);
    __privateAdd(this, _isPaused);
    __privateAdd(this, _throwOnTimeout);
    /**
        Per-operation timeout in milliseconds. Operations fulfill once `timeout` elapses if they haven't already.
    
        Applies to each future operation.
        */
    __publicField(this, "timeout");
    options = {
      carryoverConcurrencyCount: false,
      intervalCap: Number.POSITIVE_INFINITY,
      interval: 0,
      concurrency: Number.POSITIVE_INFINITY,
      autoStart: true,
      queueClass: PriorityQueue,
      ...options
    };
    if (!(typeof options.intervalCap === "number" && options.intervalCap >= 1)) {
      throw new TypeError(`Expected \`intervalCap\` to be a number from 1 and up, got \`${((_a3 = options.intervalCap) == null ? void 0 : _a3.toString()) ?? ""}\` (${typeof options.intervalCap})`);
    }
    if (options.interval === void 0 || !(Number.isFinite(options.interval) && options.interval >= 0)) {
      throw new TypeError(`Expected \`interval\` to be a finite number >= 0, got \`${((_b2 = options.interval) == null ? void 0 : _b2.toString()) ?? ""}\` (${typeof options.interval})`);
    }
    __privateSet(this, _carryoverConcurrencyCount, options.carryoverConcurrencyCount);
    __privateSet(this, _isIntervalIgnored, options.intervalCap === Number.POSITIVE_INFINITY || options.interval === 0);
    __privateSet(this, _intervalCap, options.intervalCap);
    __privateSet(this, _interval, options.interval);
    __privateSet(this, _queue2, new options.queueClass());
    __privateSet(this, _queueClass, options.queueClass);
    this.concurrency = options.concurrency;
    this.timeout = options.timeout;
    __privateSet(this, _throwOnTimeout, options.throwOnTimeout === true);
    __privateSet(this, _isPaused, options.autoStart === false);
  }
  get concurrency() {
    return __privateGet(this, _concurrency);
  }
  set concurrency(newConcurrency) {
    if (!(typeof newConcurrency === "number" && newConcurrency >= 1)) {
      throw new TypeError(`Expected \`concurrency\` to be a number from 1 and up, got \`${newConcurrency}\` (${typeof newConcurrency})`);
    }
    __privateSet(this, _concurrency, newConcurrency);
    __privateMethod(this, _PQueue_instances, processQueue_fn).call(this);
  }
  async add(function_, options = {}) {
    options = {
      timeout: this.timeout,
      throwOnTimeout: __privateGet(this, _throwOnTimeout),
      ...options
    };
    return new Promise((resolve, reject) => {
      __privateGet(this, _queue2).enqueue(async () => {
        var _a3;
        __privateWrapper(this, _pending)._++;
        __privateWrapper(this, _intervalCount)._++;
        try {
          (_a3 = options.signal) == null ? void 0 : _a3.throwIfAborted();
          let operation = function_({ signal: options.signal });
          if (options.timeout) {
            operation = pTimeout(Promise.resolve(operation), { milliseconds: options.timeout });
          }
          if (options.signal) {
            operation = Promise.race([operation, __privateMethod(this, _PQueue_instances, throwOnAbort_fn).call(this, options.signal)]);
          }
          const result = await operation;
          resolve(result);
          this.emit("completed", result);
        } catch (error) {
          if (error instanceof TimeoutError && !options.throwOnTimeout) {
            resolve();
            return;
          }
          reject(error);
          this.emit("error", error);
        } finally {
          __privateMethod(this, _PQueue_instances, next_fn).call(this);
        }
      }, options);
      this.emit("add");
      __privateMethod(this, _PQueue_instances, tryToStartAnother_fn).call(this);
    });
  }
  async addAll(functions, options) {
    return Promise.all(functions.map(async (function_) => this.add(function_, options)));
  }
  /**
  Start (or resume) executing enqueued tasks within concurrency limit. No need to call this if queue is not paused (via `options.autoStart = false` or by `.pause()` method.)
  */
  start() {
    if (!__privateGet(this, _isPaused)) {
      return this;
    }
    __privateSet(this, _isPaused, false);
    __privateMethod(this, _PQueue_instances, processQueue_fn).call(this);
    return this;
  }
  /**
  Put queue execution on hold.
  */
  pause() {
    __privateSet(this, _isPaused, true);
  }
  /**
  Clear the queue.
  */
  clear() {
    __privateSet(this, _queue2, new (__privateGet(this, _queueClass))());
  }
  /**
      Can be called multiple times. Useful if you for example add additional items at a later time.
  
      @returns A promise that settles when the queue becomes empty.
      */
  async onEmpty() {
    if (__privateGet(this, _queue2).size === 0) {
      return;
    }
    await __privateMethod(this, _PQueue_instances, onEvent_fn).call(this, "empty");
  }
  /**
      @returns A promise that settles when the queue size is less than the given limit: `queue.size < limit`.
  
      If you want to avoid having the queue grow beyond a certain size you can `await queue.onSizeLessThan()` before adding a new item.
  
      Note that this only limits the number of items waiting to start. There could still be up to `concurrency` jobs already running that this call does not include in its calculation.
      */
  async onSizeLessThan(limit) {
    if (__privateGet(this, _queue2).size < limit) {
      return;
    }
    await __privateMethod(this, _PQueue_instances, onEvent_fn).call(this, "next", () => __privateGet(this, _queue2).size < limit);
  }
  /**
      The difference with `.onEmpty` is that `.onIdle` guarantees that all work from the queue has finished. `.onEmpty` merely signals that the queue is empty, but it could mean that some promises haven't completed yet.
  
      @returns A promise that settles when the queue becomes empty, and all promises have completed; `queue.size === 0 && queue.pending === 0`.
      */
  async onIdle() {
    if (__privateGet(this, _pending) === 0 && __privateGet(this, _queue2).size === 0) {
      return;
    }
    await __privateMethod(this, _PQueue_instances, onEvent_fn).call(this, "idle");
  }
  /**
  Size of the queue, the number of queued items waiting to run.
  */
  get size() {
    return __privateGet(this, _queue2).size;
  }
  /**
      Size of the queue, filtered by the given options.
  
      For example, this can be used to find the number of items remaining in the queue with a specific priority level.
      */
  sizeBy(options) {
    return __privateGet(this, _queue2).filter(options).length;
  }
  /**
  Number of running items (no longer in the queue).
  */
  get pending() {
    return __privateGet(this, _pending);
  }
  /**
  Whether the queue is currently paused.
  */
  get isPaused() {
    return __privateGet(this, _isPaused);
  }
}
_carryoverConcurrencyCount = new WeakMap();
_isIntervalIgnored = new WeakMap();
_intervalCount = new WeakMap();
_intervalCap = new WeakMap();
_interval = new WeakMap();
_intervalEnd = new WeakMap();
_intervalId = new WeakMap();
_timeoutId = new WeakMap();
_queue2 = new WeakMap();
_queueClass = new WeakMap();
_pending = new WeakMap();
_concurrency = new WeakMap();
_isPaused = new WeakMap();
_throwOnTimeout = new WeakMap();
_PQueue_instances = new WeakSet();
doesIntervalAllowAnother_get = function() {
  return __privateGet(this, _isIntervalIgnored) || __privateGet(this, _intervalCount) < __privateGet(this, _intervalCap);
};
doesConcurrentAllowAnother_get = function() {
  return __privateGet(this, _pending) < __privateGet(this, _concurrency);
};
next_fn = function() {
  __privateWrapper(this, _pending)._--;
  __privateMethod(this, _PQueue_instances, tryToStartAnother_fn).call(this);
  this.emit("next");
};
onResumeInterval_fn = function() {
  __privateMethod(this, _PQueue_instances, onInterval_fn).call(this);
  __privateMethod(this, _PQueue_instances, initializeIntervalIfNeeded_fn).call(this);
  __privateSet(this, _timeoutId, void 0);
};
isIntervalPaused_get = function() {
  const now = Date.now();
  if (__privateGet(this, _intervalId) === void 0) {
    const delay = __privateGet(this, _intervalEnd) - now;
    if (delay < 0) {
      __privateSet(this, _intervalCount, __privateGet(this, _carryoverConcurrencyCount) ? __privateGet(this, _pending) : 0);
    } else {
      if (__privateGet(this, _timeoutId) === void 0) {
        __privateSet(this, _timeoutId, setTimeout(() => {
          __privateMethod(this, _PQueue_instances, onResumeInterval_fn).call(this);
        }, delay));
      }
      return true;
    }
  }
  return false;
};
tryToStartAnother_fn = function() {
  if (__privateGet(this, _queue2).size === 0) {
    if (__privateGet(this, _intervalId)) {
      clearInterval(__privateGet(this, _intervalId));
    }
    __privateSet(this, _intervalId, void 0);
    this.emit("empty");
    if (__privateGet(this, _pending) === 0) {
      this.emit("idle");
    }
    return false;
  }
  if (!__privateGet(this, _isPaused)) {
    const canInitializeInterval = !__privateGet(this, _PQueue_instances, isIntervalPaused_get);
    if (__privateGet(this, _PQueue_instances, doesIntervalAllowAnother_get) && __privateGet(this, _PQueue_instances, doesConcurrentAllowAnother_get)) {
      const job = __privateGet(this, _queue2).dequeue();
      if (!job) {
        return false;
      }
      this.emit("active");
      job();
      if (canInitializeInterval) {
        __privateMethod(this, _PQueue_instances, initializeIntervalIfNeeded_fn).call(this);
      }
      return true;
    }
  }
  return false;
};
initializeIntervalIfNeeded_fn = function() {
  if (__privateGet(this, _isIntervalIgnored) || __privateGet(this, _intervalId) !== void 0) {
    return;
  }
  __privateSet(this, _intervalId, setInterval(() => {
    __privateMethod(this, _PQueue_instances, onInterval_fn).call(this);
  }, __privateGet(this, _interval)));
  __privateSet(this, _intervalEnd, Date.now() + __privateGet(this, _interval));
};
onInterval_fn = function() {
  if (__privateGet(this, _intervalCount) === 0 && __privateGet(this, _pending) === 0 && __privateGet(this, _intervalId)) {
    clearInterval(__privateGet(this, _intervalId));
    __privateSet(this, _intervalId, void 0);
  }
  __privateSet(this, _intervalCount, __privateGet(this, _carryoverConcurrencyCount) ? __privateGet(this, _pending) : 0);
  __privateMethod(this, _PQueue_instances, processQueue_fn).call(this);
};
/**
Executes all queued functions until it reaches the limit.
*/
processQueue_fn = function() {
  while (__privateMethod(this, _PQueue_instances, tryToStartAnother_fn).call(this)) {
  }
};
throwOnAbort_fn = async function(signal) {
  return new Promise((_resolve, reject) => {
    signal.addEventListener("abort", () => {
      reject(signal.reason);
    }, { once: true });
  });
};
onEvent_fn = async function(event, filter) {
  return new Promise((resolve) => {
    const listener = () => {
      if (filter && !filter()) {
        return;
      }
      this.off(event, listener);
      resolve();
    };
    this.on(event, listener);
  });
};
class Mutex {
  constructor() {
    this.tail = Promise.resolve();
    this.pendingCount = 0;
  }
  /**
   * Number of callers currently holding or queued for the lock. Lets
   * keyed-mutex-map owners evict entries only when nothing is in flight —
   * evicting a held mutex would let the next acquirer mint a fresh one and
   * run concurrently with the still-detached holder.
   */
  get pending() {
    return this.pendingCount;
  }
  /**
   * Runs `fn` while holding the lock. The lock is released when `fn`
   * resolves or rejects.
   */
  runExclusive(fn) {
    const prev = this.tail;
    let release;
    this.tail = new Promise((resolve) => {
      release = resolve;
    });
    this.pendingCount++;
    return (async () => {
      await prev;
      try {
        return await fn();
      } finally {
        this.pendingCount--;
        release();
      }
    })();
  }
}
const PRIVATE_FILE_MODE = 384;
const PRIVATE_DIR_MODE = 448;
const isWindows$2 = process.platform === "win32";
const LOCK_RETRY_ATTEMPTS = 3;
const LOCK_RETRY_BACKOFF_MS = 50;
const TRANSIENT_LOCK_ERRNOS = /* @__PURE__ */ new Set([
  "EPERM",
  "EBADF",
  "EACCES",
  "EBUSY"
]);
async function retryTransientLock(op) {
  let lastErr;
  for (let attempt = 0; attempt < LOCK_RETRY_ATTEMPTS; attempt++) {
    try {
      return await op();
    } catch (err2) {
      const code = err2.code;
      if (code == null || !TRANSIENT_LOCK_ERRNOS.has(code)) {
        throw err2;
      }
      lastErr = err2;
      if (attempt < LOCK_RETRY_ATTEMPTS - 1) {
        await promises$1.setTimeout(LOCK_RETRY_BACKOFF_MS * (attempt + 1));
      }
    }
  }
  throw lastErr;
}
const writeMutexes = /* @__PURE__ */ new Map();
function acquireMutex(key) {
  let entry = writeMutexes.get(key);
  if (!entry) {
    entry = { mutex: new Mutex(), refs: 0 };
    writeMutexes.set(key, entry);
  }
  entry.refs++;
  return entry.mutex;
}
function releaseMutex(key) {
  const entry = writeMutexes.get(key);
  if (entry && --entry.refs === 0) {
    writeMutexes.delete(key);
  }
}
function writeFileAtomic(filePath, content, mode = PRIVATE_FILE_MODE) {
  const key = path.resolve(filePath);
  return acquireMutex(key).runExclusive(async () => {
    await fs$1.mkdir(path.dirname(filePath), { recursive: true });
    const tmpFile = `${filePath}.tmp`;
    await retryTransientLock(async () => {
      await fs$1.rm(tmpFile, { force: true });
      await fs$1.writeFile(tmpFile, content, { mode, flag: "wx" });
    });
    let lastErr;
    for (let attempt = 0; attempt < LOCK_RETRY_ATTEMPTS; attempt++) {
      try {
        await fs$1.rename(tmpFile, filePath);
        return;
      } catch (err2) {
        const errnoErr = err2;
        const code = errnoErr.code;
        if (code === "EXDEV") {
          lastErr = errnoErr;
          break;
        }
        if (code != null && TRANSIENT_LOCK_ERRNOS.has(code)) {
          lastErr = errnoErr;
          if (attempt < LOCK_RETRY_ATTEMPTS - 1) {
            await promises$1.setTimeout(LOCK_RETRY_BACKOFF_MS * (attempt + 1));
          }
          continue;
        }
        throw err2;
      }
    }
    console.warn(
      `[privateFile] rename(${tmpFile} → ${filePath}) failed (${lastErr == null ? void 0 : lastErr.code}), falling back to direct write`,
      lastErr
    );
    if (!isWindows$2) {
      await fs$1.chmod(filePath, mode).catch((e) => {
        if (e.code !== "ENOENT") {
          throw e;
        }
      });
    }
    await fs$1.writeFile(filePath, content, { mode });
    try {
      await fs$1.rm(tmpFile, { force: true });
    } catch (rmErr) {
      console.warn(`[privateFile] failed to clean up ${tmpFile}:`, rmErr);
    }
  }).finally(() => releaseMutex(key));
}
function modelEntryName(model) {
  if (typeof model === "string") {
    return model;
  }
  if (model && typeof model === "object") {
    const m = model;
    if (typeof m.id === "string") {
      return m.id;
    }
    if (typeof m.name === "string") {
      return m.name;
    }
  }
  return void 0;
}
const INTERNAL_SERVER_UUIDS = {
  "claude-in-chrome": "a8f3c7e2-4b9d-4f1a-8c3e-9d2a5b7f8e1c",
  office: "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  echo: "e8c0f3a1-5b2d-4e7f-9a6c-1d8b4f3e2a5c",
  "computer-use": "b0a3b6e5-7ca0-462a-8e6f-bac087408b17",
  workspace: "a05f2752-b0d0-4e5e-97f4-0c85957a5eb7",
  "mcp-registry": "8e22a1f5-ee4a-4ab4-b99b-c82e971ebd28",
  plugins: "7f50c7a2-4369-4ac9-9666-83ab8d7f6bea",
  skills: "5f89cf73-627e-46ed-893a-750e52d0a50b",
  "cowork-onboarding": "9105c415-238f-4baa-8790-396b4db1be09",
  "dev-debug": "7e5c02ee-f301-4a0f-918e-d324e58d554f",
  "Claude Preview": "bda6af03-834c-4496-98d1-c0e6d52b99ce",
  // Renamed form of the same server: one surface, two name eras, so both
  // share a uuid and dashboards keyed on server_uuid stay continuous
  // across the rename.
  "Claude Browser": "bda6af03-834c-4496-98d1-c0e6d52b99ce",
  Framebuffer: "10013aa5-ba71-498e-9a4e-10c1504a45c1",
  visualize: "34c3fca1-1148-457c-893f-b629d47bc9d7",
  "Window Halo": "636ab6f5-a669-4adb-b932-26595ced3e89",
  ccd_session: "3a47babc-65de-4869-b865-47a0d3f0c1ed",
  ccd_directory: "1a92b889-f135-4008-9061-80f87e958751",
  ccd_session_mgmt: "8e0701d5-8683-4b58-9860-a2cc1cfc9422",
  terminal: "b94dfe7c-203b-402b-9c46-4dcd448f0c3b",
  ios_simulator: "57ee2155-2a58-490d-a966-7ccf8491571c",
  android_emulator: "07f65f9d-33a1-4654-ba37-5f9e10aa5689",
  "remote-devices": "63c20b00-cc9f-44b6-b75f-b541980465b7"
};
const logger = {
  debug: (...args) => console.debug(...args),
  info: (...args) => console.info(...args),
  warn: (...args) => console.warn(...args),
  error: (...args) => console.error(...args)
};
function scrubPaths(text) {
  return scrubFilesystemPaths(text, getScrubEnv());
}
function scrubText(text) {
  return scrubFreeText(text, getScrubEnv());
}
function stripUrlSecrets(s) {
  const noQueryOrHash = s.split("?")[0].split("#")[0];
  const at = noQueryOrHash.lastIndexOf("@");
  return at >= 0 ? noQueryOrHash.slice(at + 1) : noQueryOrHash;
}
function redactEmbeddedUrls(s) {
  return s.replace(
    /\bhttps?:\/\/\S+/gi,
    (u) => redactMcpServerUrl(u) ?? "<url>"
  );
}
const REDACTED_OUTPUT_MAX_CHARS = 300;
const TRANSCRIPT_TYPE_RE = /"type"\s*:\s*"(user|assistant|system|result|stream_event|text|tool_use|tool_result|thinking|image|control_request|control_response|bash_command|auth_status|prompt_suggestion|rate_limit_event)"/;
const ENUM_VALUE_RE = /^[a-z_]{1,32}$/;
function redactCliOutput(raw) {
  var _a3, _b2;
  const typeMatch = raw.match(TRANSCRIPT_TYPE_RE);
  if (raw.trimStart().startsWith("{") || typeMatch) {
    const fallbackType = (_a3 = raw.match(/"type"\s*:\s*"([^"]+)"/)) == null ? void 0 : _a3[1];
    const type = (typeMatch == null ? void 0 : typeMatch[1]) ?? (fallbackType !== void 0 && ENUM_VALUE_RE.test(fallbackType) ? fallbackType : "json");
    const rawSubtype = (_b2 = raw.match(/"subtype"\s*:\s*"([^"]+)"/)) == null ? void 0 : _b2[1];
    const subtype = rawSubtype !== void 0 && ENUM_VALUE_RE.test(rawSubtype) ? rawSubtype : void 0;
    const label = subtype ? `${type}/${subtype}` : type;
    return `[${label} envelope, ${raw.length} chars]`;
  }
  return redactSecretLike(redactCredentialPatterns(scrubPaths(raw))).slice(
    0,
    REDACTED_OUTPUT_MAX_CHARS
  );
}
function redactCredentialPatterns(s) {
  return s.replace(
    /bedrock-api-key-[A-Za-z0-9+/=]{20,}/g,
    "bedrock-api-key-[redacted]"
  ).replace(/\bA[SK]IA[A-Z0-9]{16}\b/g, "[redacted-aws-key-id]").replace(/\bsk-(?:ant-)?[A-Za-z0-9_-]{20,}\b/g, "sk-[redacted]").replace(
    new RegExp("(?<![A-Za-z0-9_~.-])[A-Za-z0-9_~.-]{3}[78]Q~[A-Za-z0-9_~.-]{31,34}(?![A-Za-z0-9_~.-])", "g"),
    "[redacted-entra-secret]"
  );
}
const ifString = (fn) => (v) => typeof v === "string" ? fn(v) : v;
const eachString = (fn) => (v) => Array.isArray(v) ? v.map((x) => typeof x === "string" ? fn(x) : x) : typeof v === "string" ? fn(v) : v;
const normalizeModelField = (v) => {
  const name = modelEntryName(v);
  return name === void 0 ? v : redactBedrockArnAccountId(name);
};
const FALLBACK_HASH_SALT = "desktop-telemetry-scrub-v1:";
const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
function buildHashKeyHandlers(salt) {
  const hash = (s) => analyticsNameHash(salt + s);
  const hashIfString = ifString(hash);
  const hashEachString = eachString(hash);
  const internalServerNames = new Set(
    Object.keys(INTERNAL_SERVER_UUIDS)
  );
  const normalizeMcpServerName = (name) => name.replace(/[^a-zA-Z0-9_-]/g, "_");
  const INTERNAL_TOOL_SHAPE = /^[a-zA-Z0-9_]{1,64}$/;
  const hashMcpToolName = ifString((s) => {
    if (s.startsWith("internal__")) {
      const rest = s.slice("internal__".length);
      const sep = rest.indexOf("__");
      const server2 = sep >= 0 ? rest.slice(0, sep) : rest;
      if (!internalServerNames.has(server2)) {
        return hash(s);
      }
      const tool2 = sep >= 0 ? rest.slice(sep + 2) : "";
      if (INTERNAL_TOOL_SHAPE.test(tool2)) {
        return s;
      }
      return `internal__${server2}__${hash(tool2)}`;
    }
    if (s.startsWith("official-plugin__")) {
      const rest = s.slice("official-plugin__".length);
      const sep = rest.indexOf("__");
      const pluginId = sep >= 0 ? rest.slice(0, sep) : rest;
      const at = pluginId.lastIndexOf("@");
      const pluginName = at > 0 ? pluginId.slice(0, at) : "";
      if (!isOfficialMarketplacePlugin(pluginId) || !OFFICIAL_PLUGIN_TOOL_SHAPE.test(pluginName)) {
        return hash(s);
      }
      const tail = sep >= 0 ? rest.slice(sep + 2) : "";
      const parts2 = tail.split("__");
      if (parts2.every((p) => OFFICIAL_PLUGIN_TOOL_SHAPE.test(p))) {
        return s;
      }
      return `official-plugin__${pluginId}__${hash(tail)}`;
    }
    if (!s.startsWith("mcp__")) {
      return redactToolName(s, hash);
    }
    const parts = normalizeMcpServerName(s.slice("mcp__".length)).split("__");
    const server = parts[0] ?? "";
    const tool = parts.slice(1).join("__");
    const serverOut = isRegistryServerUuid(server) ? server : hash(server);
    return `mcp__${serverOut}__${hash(tool)}`;
  });
  return {
    // Model-chosen identifiers derived from the user's prompt.
    scheduled_task_id: hashIfString,
    artifact_id: hashIfString,
    // MCP tool names — per-org salted (not the fixed-salt redactToolName).
    tool_name: hashMcpToolName,
    last_tool_name: hashMcpToolName,
    tool: hashMcpToolName,
    // User-chosen MCP server / DXT extension identifiers. Registry-assigned
    // connector UUIDs (ProxyMcpServerManager remote path) pass through
    // unhashed so dbt's mcp_usage allowlist can join cross-org. Gated on
    // isRegistryServerUuid — UUID format AND membership in the runtime set
    // populated from the backend connector-sync response (see
    // registryServerUuids.ts) — not on UUID format alone (a user can name a
    // local server with a UUID-shaped string) and not on the sibling
    // server_type field (deepScrubStrings keyHandlers see only the value;
    // server_type is also derived from user-editable transport config in
    // directMcpManager). Fail-closed: empty/unsynced set → everything
    // hashes as before.
    server_name: ifString((s) => isRegistryServerUuid(s) ? s : hash(s)),
    extension_name: hashIfString,
    extension_author: hashIfString,
    // Remote-connector keys are UUIDs (safe); local-DXT keys are user-chosen
    // names. Hash non-UUID entries so the array is safe regardless of source.
    mcp_server_keys: (v) => Array.isArray(v) ? v.map(
      (k) => typeof k === "string" && !UUID_RE.test(k) ? hash(k) : k
    ) : v,
    // User-defined macOS VPN configuration display names (scutil --nc list)
    // and network interface names.
    connected_vpns: hashEachString,
    vpn_interfaces: hashEachString,
    bridge_interfaces: hashEachString,
    // Most events' `source` is a short enum-like token; hash anything that
    // doesn't look enum-ish in case a free-text value slips through.
    source: ifString((s) => /^[a-z0-9_-]{1,24}$/.test(s) ? s : hash(s)),
    // uuid is sufficient for per-entity aggregation; hash the user-chosen
    // display name (shape preserved for BQ schema compatibility).
    available_remote_mcp_servers: (v) => Array.isArray(v) ? v.map((s) => {
      if (s && typeof s === "object") {
        const o = s;
        return {
          uuid: o.uuid,
          name: typeof o.name === "string" ? hash(o.name) : o.name
        };
      }
      return s;
    }) : v
  };
}
function scrubFreeTextForSink(s) {
  return scrubText(redactEmbeddedUrls(redactCredentialPatterns(s)));
}
const scrubStderrTail = ifString(scrubFreeTextForSink);
const scrubOverrideLabel = ifString(
  (s) => s.length <= 64 && !/[@/\\:=]/.test(s) ? s : "[redacted]"
);
const redactBareHost = ifString((s) => {
  const h = s.toLowerCase();
  if (h.endsWith(".anthropic.com") || h.endsWith(".claude.ai") || h === "localhost" || h.startsWith("127.") || h.startsWith("10.") || h.startsWith("192.168.") || /^172\.(?:1[6-9]|2\d|3[01])\./.test(h)) {
    return s;
  }
  if (/^\d{1,3}(?:\.\d{1,3}){3}$/.test(h)) {
    return "<ip>";
  }
  const tld = h.split(".").pop();
  return tld ? `<host>.${tld}` : "<host>";
});
const LOGEVENT_SCRUB_OPTS = {
  scrubString: scrubPaths,
  skipKeys: /* @__PURE__ */ new Set([
    "product_surface",
    "desktop_variant",
    "deployment_mode",
    "config_source",
    "config_source_remote",
    "inference_provider",
    "inference_host",
    "inference_host_kind",
    "app_version",
    "commit_hash",
    "platform",
    "arch",
    "os_version",
    "os_release",
    "os_build",
    "linux_distro_id",
    "linux_distro_version_id",
    "linux_session_type",
    "linux_desktop_environment",
    "cpu_model",
    "app_session_id",
    "organization_id",
    "vm_network_mode",
    "error_code",
    // Closed set of app-defined error classification literals from
    // validateMemoryFilename / resolveMemoryDir — never user content.
    "error_kind",
    // error_code from the plugin-detail lookup's 404 body (plugin_not_found /
    // marketplace_not_found). Same class as error_code: although it's
    // externally sourced, handlePluginDetailResponse fails it closed to a
    // snake_case enum (ENUM_ERROR_CODE_RE) at the capture site, so it's safe
    // by construction by the time it reaches here.
    "backend_error_code",
    "nest_local_user"
  ]),
  keyHandlers: {
    // User-typed URL: source already strips userinfo/query/fragment; this catches path-embedded keys.
    inference_base_url: ifString(redactSecretLike),
    // Admin-typed URL (enterprise_config.banner.linkUrl); can carry credentials.
    linkUrl: ifString(
      (s) => scrubPaths(redactMcpServerUrl(s) ?? stripUrlSecrets(s))
    ),
    // Bedrock ARNs embed the customer's AWS account ID; some emitters pass the
    // raw InferenceModel object — unwrap+redact at the sink so neither leaks.
    model: normalizeModelField,
    last_message_model: normalizeModelField,
    override_label: scrubOverrideLabel,
    plugin_id: ifString(redactPluginId),
    target_id: ifString(redactPluginId),
    // Server-assigned UUIDs from the account-sync path (see
    // marketplace_plugin_op_result.plugin_uuid). Shape-gated so a
    // compound `name@marketplace` key — which can embed an org-authored
    // marketplace name — can never pass raw; plugin_id above handles that
    // format via redactPluginId.
    plugin_uuid: ifString((s) => UUID_RE.test(s) ? s : "<non-uuid>"),
    marketplace_uuid: ifString((s) => UUID_RE.test(s) ? s : "<non-uuid>"),
    // tool_name / last_tool_name / tool — see buildHashKeyHandlers.
    // Record keyed by `${serverName}:${toolName}` with boolean values —
    // PersistedSession.enabledMcpTools, written into feedback-bundle
    // metadata.json. The PII is in the KEYS. Not redactToolName — the
    // first segment is always a user-chosen server name, never a builtin
    // namespace, so redactToolName's `computer:` passthrough (for the
    // fixed computer-use enum on the tool_name field) would leak a server
    // the user happened to name "computer". redactServerToolKey hashes
    // both segments unconditionally. Fixed-salt is OK here: these keys
    // only ever appear in the support bundle (no org context —
    // FALLBACK_HASH_SALT), not BQ events.
    enabledMcpTools: (v) => {
      if (typeof v !== "object" || v === null) {
        return v;
      }
      const out = /* @__PURE__ */ Object.create(null);
      for (const [k, val] of Object.entries(v)) {
        out[redactServerToolKey(k)] = val;
      }
      return out;
    },
    // PersistedSession.approvedToolNames — tool names with "always allow",
    // same PII class as enabledMcpTools. Entries may be mcp__server__tool,
    // `${serverName}:${toolName}`, or bare builtin names. redactToolName
    // handles mcp__ and bare forms; colon-form goes to redactServerToolKey
    // for the same reason as enabledMcpTools above (the `computer:`
    // passthrough is unsafe when the first segment is a user-chosen server
    // name). Genuine builtin `computer:*` entries get hashed too — an
    // acceptable legibility cost for not leaking the user-named-server case.
    approvedToolNames: eachString(
      (name) => name.startsWith("mcp__") || !name.includes(":") ? redactToolName(name) : redactServerToolKey(name)
    ),
    raw_output: ifString(redactCliOutput),
    raw_output_prefix: ifString(redactCliOutput),
    // stderr is already a bounded tail; redactCliOutput's 300-char slice would drop the stack.
    cli_stderr_tail: scrubStderrTail,
    // Chrome-bridge tool errors embed user browsing URLs verbatim; the
    // default scrubPaths doesn't touch URLs. Path is as sensitive as query
    // for a browsing URL, so drop to scheme://host only.
    error_message: ifString(
      (s) => redactSecretLike(redactEmbeddedUrlsToHost(scrubPaths(s)))
    ),
    // CLI free-text explanation; embeds absolute file paths (see
    // readme/analytics-pii.md rule 1: prefer structured error_code).
    decision_reason: ifString(
      (s) => redactSecretLike(scrubPaths(s)).slice(0, 200)
    ),
    // DXT extension metadata — user-authored extensions carry user-chosen
    // names; directory extensions are safe. redactPluginId handles both.
    extension_id: ifString(redactPluginId),
    // MCP local-server launch command — contains user filesystem paths and
    // potentially env-var values.
    mcp_cmd: ifString((s) => redactSecretLike(scrubPaths(s))),
    // goproxy upstream-error log line — embeds the VM's egress Host header
    // (user's WebFetch/Bash target), same browsing-URL class as error_message
    // above. Keep the error tail; drop the URL to scheme://host only.
    coworkd_upstream_error: ifString(
      (s) => redactSecretLike(redactEmbeddedUrlsToHost(scrubPaths(s))).slice(0, 300)
    ),
    // VM kernel/console tails — free-text dmesg/serial output. scrubFreeText
    // covers URL/IP/email/secret patterns in addition to paths.
    console_tail: ifString(scrubText),
    kernel_console_tail: ifString(scrubText),
    kernel_context: ifString(scrubText),
    // macOS diagnostic command stdout.
    vm_stat_output: ifString(scrubText),
    vz_footprint_output: ifString(scrubText),
    // cic_proxy_stale_deny: user's browsing hostnames from the Chrome
    // extension tab-allowlist. Keep Anthropic/local hosts, collapse the rest.
    session_allowed: eachString((s) => redactBareHost(s)),
    ext_saw: redactBareHost,
    once_approved: redactBareHost,
    // Nested under cowork_3p_diagnostic_bundle.reachability[] — hostnames
    // probed during the diagnostic. deepScrubStrings recurses, so this
    // keyHandler fires on the nested key even though Check C doesn't
    // descend into array element types.
    host: redactBareHost,
    // Bedrock ARN → strip account ID; otherwise pass through (model alias).
    rejected_model: normalizeModelField,
    // URLs — redact to origin+path, drop query/userinfo.
    feedback_url: ifString((s) => redactMcpServerUrl(s) ?? "<url>"),
    bridge_url: ifString((s) => redactMcpServerUrl(s) ?? "<url>"),
    // Free-form error strings from library/OS — path + secret + URL pass.
    error: ifString((s) => redactSecretLike(redactEmbeddedUrls(scrubPaths(s)))),
    errorMessage: ifString(
      (s) => redactSecretLike(redactEmbeddedUrls(scrubPaths(s)))
    ),
    error_description: ifString(
      (s) => redactSecretLike(redactEmbeddedUrls(scrubPaths(s)))
    ),
    error_detail: ifString(
      (s) => redactSecretLike(redactEmbeddedUrls(scrubPaths(s)))
    ),
    error_line: ifString(
      (s) => redactSecretLike(redactEmbeddedUrls(scrubPaths(s)))
    ),
    diagnostic_error: ifString(
      (s) => redactSecretLike(redactEmbeddedUrls(scrubPaths(s)))
    ),
    // User-/model-chosen identifiers — see buildHashKeyHandlers. The
    // fallback salt here is for static consumers (SUPPORT_BUNDLE_SCRUB_OPTS,
    // event-types.consistency.test.ts) that don't have org context;
    // scrubLogEventMetadata overrides these per-call with organization_id.
    ...buildHashKeyHandlers(FALLBACK_HASH_SALT)
  }
};
const SUPPORT_BUNDLE_SCRUB_OPTS = {
  lineScrub: (s) => scrubLogLine(s, getScrubEnv()),
  jsonScrubOpts: {
    ...LOGEVENT_SCRUB_OPTS,
    scrubString: (s) => scrubFreeText(s, getScrubEnv())
  },
  onError: (e, f) => (
    // scrubBufferForBundle never ships raw bytes: it falls back to line-level
    // scrubbing, and withholds the content entirely if even that throws.
    logger.warn("bundle scrub failed for %s; falling back: %o", f, e)
  )
};
class SafeFsError extends Error {
  constructor(code, message) {
    super(message);
    this.name = "SafeFsError";
    this.code = code;
  }
}
class PathEscapeError extends SafeFsError {
  constructor(rel) {
    super("ERR_SAFE_FS_ESCAPE", `Path escapes root: ${JSON.stringify(rel)}`);
    this.name = "PathEscapeError";
  }
}
class SymlinkEncounteredError extends SafeFsError {
  constructor(at) {
    super(
      "ERR_SAFE_FS_SYMLINK",
      `Refusing to follow symlink under root at: ${at}`
    );
    this.name = "SymlinkEncounteredError";
  }
}
class NotRegularFileError extends SafeFsError {
  constructor(at) {
    super("ERR_SAFE_FS_NOT_REGULAR", `Not a regular file: ${at}`);
    this.name = "NotRegularFileError";
  }
}
class SizeLimitError extends SafeFsError {
  constructor(message) {
    super("ERR_SAFE_FS_SIZE", message);
    this.name = "SizeLimitError";
  }
}
class UnsafeRootError extends SafeFsError {
  constructor(message, opts) {
    super("ERR_SAFE_FS_ROOT", message);
    this.name = "UnsafeRootError";
    if ((opts == null ? void 0 : opts.cause) !== void 0) {
      this.cause = opts.cause;
    }
  }
}
let cachedClaudeNative = void 0;
let cachedClaudeNativeLoadError;
function maybeGetClaudeNative() {
  if (cachedClaudeNative !== void 0) {
    return cachedClaudeNative;
  }
  try {
    cachedClaudeNative = require("@ant/claude-native");
  } catch (err2) {
    cachedClaudeNative = null;
    cachedClaudeNativeLoadError = err2;
    {
      logger.error("Failed to load Claude Native %o", err2);
    }
  }
  return cachedClaudeNative;
}
function getClaudeNativeOrThrow() {
  const native = maybeGetClaudeNative();
  if (native === null) {
    throw new Error(
      "@ant/claude-native is required for safe-fs containment but failed to load; refusing to fall back to a path-based open (CC-2885)",
      { cause: cachedClaudeNativeLoadError }
    );
  }
  return native;
}
fs.constants.O_NOFOLLOW ?? 0;
fs.constants.O_DIRECTORY ?? 0;
fs.constants.O_NONBLOCK ?? 0;
const isWindows$1 = process.platform === "win32";
const WIN_DRIVE_RE = /^[A-Za-z]:/;
const WIN_DEVICE_RE = /^[\\/]{2}[?.][\\/]/;
const UNC_RE = /^[\\/]{2}/;
const WIN_RESERVED_RE = /^(con|prn|aux|nul|com[0-9\u00b9\u00b2\u00b3]|lpt[0-9\u00b9\u00b2\u00b3])(\.|$)/i;
function isBadSegment(seg) {
  if (seg.length === 0 || seg === "." || seg === "..") {
    return seg === "..";
  }
  if (isWindows$1) {
    if (WIN_RESERVED_RE.test(seg)) {
      return true;
    }
    if (/[. ]$/.test(seg)) {
      return true;
    }
    if (seg.includes(":")) {
      return true;
    }
  }
  return false;
}
function lexicalResolve(rootCanonical, rel) {
  if (typeof rel !== "string") {
    throw new PathEscapeError(String(rel));
  }
  if (rel.includes("\0")) {
    throw new PathEscapeError(rel);
  }
  const unified = isWindows$1 ? rel.replace(/\\/g, "/") : rel;
  if (UNC_RE.test(rel) || WIN_DEVICE_RE.test(rel) || isWindows$1 && WIN_DRIVE_RE.test(unified)) {
    throw new PathEscapeError(rel);
  }
  if (path.posix.isAbsolute(unified)) {
    throw new PathEscapeError(rel);
  }
  let normalized = path.posix.normalize(unified);
  if (normalized.length > 1 && normalized.endsWith("/")) {
    normalized = normalized.slice(0, -1);
  }
  if (normalized === ".." || normalized.startsWith("../")) {
    throw new PathEscapeError(rel);
  }
  const segments = normalized === "." ? [] : normalized.split("/").filter(Boolean);
  for (const seg of segments) {
    if (isBadSegment(seg)) {
      throw new PathEscapeError(rel);
    }
  }
  const full = segments.length === 0 ? rootCanonical : path.join(rootCanonical, ...segments);
  const leaf = segments.length > 0 ? segments[segments.length - 1] : void 0;
  return {
    full,
    rel: segments.join("/"),
    dirSegments: segments.slice(0, -1),
    leaf
  };
}
async function walkIntermediates(rootCanonical, r) {
  let walked = rootCanonical;
  for (const seg of r.dirSegments) {
    walked = path.join(walked, seg);
    const st = await fs$1.lstat(walked);
    if (st.isSymbolicLink() || !st.isDirectory()) {
      throw new SymlinkEncounteredError(walked);
    }
  }
}
async function resolveUnder(rootCanonical, rel) {
  const r = lexicalResolve(rootCanonical, rel);
  await walkIntermediates(rootCanonical, r);
  return r;
}
function toNativeErrno(e) {
  if (e instanceof Error) {
    const m = /^([A-Z]{3,12}): /.exec(e.message);
    if (m) {
      e.code = m[1];
    }
    return e;
  }
  return Object.assign(new Error(String(e)), { code: "EUNKNOWN" });
}
async function openLeaf(rootFd, r, flags, mode) {
  if (r.leaf === void 0) {
    throw new PathEscapeError(r.rel);
  }
  const native = getClaudeNativeOrThrow();
  try {
    return await native.openBeneath(
      rootFd,
      [...r.dirSegments, r.leaf],
      flags,
      mode ?? 384
    );
  } catch (e) {
    const err2 = toNativeErrno(e);
    if (err2.code === "ELOOP" || err2.code === "ENOTDIR" || err2.code === "EXDEV") {
      throw new SymlinkEncounteredError(r.full);
    }
    throw err2;
  }
}
async function openRootHandle(canonical) {
  const native = getClaudeNativeOrThrow();
  try {
    return await native.openRootDir(canonical);
  } catch (e) {
    throw toNativeErrno(e);
  }
}
async function renameAt(rootFd, src, dst) {
  const native = getClaudeNativeOrThrow();
  try {
    await native.renameBeneath(rootFd, [...src], [...dst]);
  } catch (e) {
    const err2 = toNativeErrno(e);
    if (err2.code === "ELOOP" || err2.code === "ENOTDIR") {
      throw new SymlinkEncounteredError(dst.join("/"));
    }
    throw err2;
  }
}
async function unlinkAt(rootFd, segments) {
  const native = getClaudeNativeOrThrow();
  try {
    await native.unlinkBeneath(rootFd, [...segments]);
  } catch (e) {
    const err2 = toNativeErrno(e);
    if (err2.code === "ELOOP" || err2.code === "ENOTDIR") {
      throw new SymlinkEncounteredError(segments.join("/"));
    }
    throw err2;
  }
}
async function mkdirAt(rootFd, segments, mode) {
  const native = getClaudeNativeOrThrow();
  try {
    await native.mkdirBeneath(rootFd, [...segments], mode);
  } catch (e) {
    const err2 = toNativeErrno(e);
    if (err2.code === "ELOOP" || err2.code === "ENOTDIR") {
      throw new SymlinkEncounteredError(segments.join("/"));
    }
    throw err2;
  }
}
const pClose = (fd) => new Promise((res, rej) => fs.close(fd, (e) => e ? rej(e) : res()));
const pFstat = (fd) => new Promise((res, rej) => fs.fstat(fd, (e, s) => e ? rej(e) : res(s)));
const pFtruncate = (fd, len) => new Promise((res, rej) => fs.ftruncate(fd, len, (e) => e ? rej(e) : res()));
const pFchmod = (fd, mode) => new Promise((res, rej) => fs.fchmod(fd, mode, (e) => e ? rej(e) : res()));
const pFsync = (fd) => new Promise((res, rej) => fs.fsync(fd, (e) => e ? rej(e) : res()));
const pRead = (fd, buf, off, len, pos) => new Promise(
  (res, rej) => fs.read(fd, buf, off, len, pos, (e, n) => e ? rej(e) : res(n))
);
const pWriteAt = (fd, data, off) => new Promise(
  (res, rej) => fs.write(
    fd,
    data,
    off,
    data.byteLength - off,
    null,
    (e, n) => e ? rej(e) : res(n)
  )
);
const pWrite = async (fd, data) => {
  let off = 0;
  while (off < data.byteLength) {
    const n = await pWriteAt(fd, data, off);
    if (n === 0) {
      throw Object.assign(new Error("short write: 0 bytes written"), {
        code: "EIO"
      });
    }
    off += n;
  }
  return off;
};
class SafeFile {
  /** @internal */
  constructor(fd, tier) {
    __privateAdd(this, _SafeFile_instances);
    __privateAdd(this, _fd);
    __privateAdd(this, _tier);
    __privateAdd(this, _closed, false);
    __privateSet(this, _fd, fd);
    __privateSet(this, _tier, tier);
  }
  /** fstat the open handle — pinned to the inode opened race-free under
   *  the root, so `nlink` / `mode` / `mtime` here describe the same
   *  object the subsequent `truncate`/`write` will affect. */
  stat() {
    return pFstat(__privateGet(this, _fd));
  }
  /** Read the entire file. When `maxBytes` applies (always, on
   *  workspace/vm tiers), reads into a buffer initially sized to the
   *  file's stat'd size and grown only if the file grows during the
   *  read; {@link SizeLimitError} is thrown if it grows past `maxBytes`.
   *  Without `maxBytes` (appdata tier only), reads to EOF. */
  async readFile(opts) {
    const max = __privateMethod(this, _SafeFile_instances, requireMaxBytes_fn).call(this, opts);
    const { size } = await pFstat(__privateGet(this, _fd));
    if (max === void 0) {
      return boundedReadFd(
        __privateGet(this, _fd),
        size,
        Math.max(size, 1 << 20),
        false,
        opts == null ? void 0 : opts.signal
      );
    }
    if (size > max) {
      throw new SizeLimitError(`File is ${size} bytes; maxBytes is ${max}`);
    }
    return boundedReadFd(__privateGet(this, _fd), size, max, true, opts == null ? void 0 : opts.signal);
  }
  async readText(opts) {
    return (await this.readFile(opts)).toString("utf-8");
  }
  /** Read up to `length` bytes at `position`. No maxBytes gate — the
   *  caller has already bounded the read by choosing `length`. */
  async read(buffer, offset, length, position) {
    const bytesRead = await pRead(__privateGet(this, _fd), buffer, offset, length, position);
    return { bytesRead, buffer };
  }
  async write(data) {
    const buf = typeof data === "string" ? Buffer.from(data, "utf-8") : data;
    const bytesWritten = await pWrite(__privateGet(this, _fd), buf);
    return { bytesWritten };
  }
  truncate(len = 0) {
    return pFtruncate(__privateGet(this, _fd), len);
  }
  /** fsync the pinned fd — used by `SafeRoot.writeFileAtomic` so the tmp
   *  inode's data is durable before the rename makes it visible at the
   *  target name. */
  sync() {
    return pFsync(__privateGet(this, _fd));
  }
  /** @internal — fchmod on the pinned fd; SafeRoot.chmod is the public
   *  entrypoint. */
  chmod(mode) {
    return pFchmod(__privateGet(this, _fd), mode);
  }
  /** `fs.createReadStream` bound to this fd (not a path). `end` is
   *  derived from `maxBytes` so the stream self-terminates instead of
   *  reading an adversary-controlled file to EOF. On workspace/vm
   *  tiers `maxBytes` is required. The returned stream does NOT close
   *  the fd (`autoClose: false`); the SafeFile's own disposal does. */
  createReadStream(opts) {
    const max = __privateMethod(this, _SafeFile_instances, requireMaxBytes_fn).call(this, opts);
    const start = (opts == null ? void 0 : opts.start) ?? 0;
    const end = max !== void 0 ? start + max - 1 : void 0;
    return fs.createReadStream("", {
      fd: __privateGet(this, _fd),
      autoClose: false,
      start,
      end
    });
  }
  /** `fs.createWriteStream` bound to this fd — a `pipeline` sink for
   *  downloads / archive extraction where {@link write} would buffer
   *  the whole payload.
   *
   *  The returned stream **consumes the handle**: when it finishes (or
   *  errors) the fd is closed, and further operations on this `SafeFile`
   *  fail with EBADF. With `autoClose: false` an fd-backed write stream
   *  never releases its internal ref and the enclosing `withFile` /
   *  `await using` would hang on `close()`; `autoClose: true` is the
   *  only shape that works, and `fs.close` is idempotent so this
   *  SafeFile's own disposal is a no-op afterward. */
  createWriteStream(opts) {
    __privateSet(this, _closed, true);
    return fs.createWriteStream("", {
      fd: __privateGet(this, _fd),
      autoClose: true,
      ...(opts == null ? void 0 : opts.start) !== void 0 && { start: opts.start }
    });
  }
  async close() {
    if (__privateGet(this, _closed)) {
      return;
    }
    __privateSet(this, _closed, true);
    await pClose(__privateGet(this, _fd));
  }
  [Symbol.asyncDispose]() {
    return this.close();
  }
}
_fd = new WeakMap();
_tier = new WeakMap();
_closed = new WeakMap();
_SafeFile_instances = new WeakSet();
requireMaxBytes_fn = function(opts) {
  if (__privateGet(this, _tier) !== "appdata" && (opts == null ? void 0 : opts.maxBytes) === void 0) {
    throw new SizeLimitError(
      `maxBytes is required for reads on a "${__privateGet(this, _tier)}"-tier file`
    );
  }
  return opts == null ? void 0 : opts.maxBytes;
};
async function boundedReadFd(fd, knownSize, max, enforce, signal) {
  let buf = Buffer.allocUnsafe(Math.min(knownSize, max) + 1);
  let off = 0;
  for (; ; ) {
    signal == null ? void 0 : signal.throwIfAborted();
    if (off === buf.length) {
      const ceiling = enforce ? max + 1 : buf.length * 2;
      const next = Buffer.allocUnsafe(Math.min(buf.length * 2, ceiling));
      buf.copy(next, 0, 0, off);
      buf = next;
    }
    const n = await pRead(fd, buf, off, buf.length - off, off);
    if (n === 0) {
      break;
    }
    off += n;
    if (enforce && off > max) {
      throw new SizeLimitError(`File grew past maxBytes (${max}) during read`);
    }
  }
  return Buffer.from(buf.subarray(0, off));
}
const closeFd = pClose;
const fstatFd = pFstat;
function isUncPath(p) {
  const n = path.normalize(p);
  return n.startsWith("\\\\") || n.startsWith("//");
}
const WSL_UNC_RE = /^[\\/]{2}(wsl\$|wsl\.localhost)(?=[\\/]|$)/i;
const WSL_ALIAS_UNC_RE = /^[\\/]{2}wsl\$(?=[\\/]|$)/i;
function isWslUncPath(p) {
  return WSL_UNC_RE.test(p);
}
function canonicalizeWslPath(p) {
  if (!isWslUncPath(p)) {
    return p;
  }
  const s = p.replace(/\//g, "\\");
  return s.replace(
    /^\\\\(wsl\$|wsl\.localhost)(\\[^\\]+)?/i,
    (_m, _host, distro = "") => `\\\\wsl.localhost${distro.toLowerCase()}`
  );
}
function isUnsafeUnc(p) {
  return isUncPath(p) && !isWslUncPath(p);
}
function uncHost(p) {
  const n = path.normalize(p).replace(/\//g, "\\");
  const long = n.match(/^\\\\[?.]\\UNC\\([^\\]+)/i);
  if (long) {
    return long[1].toLowerCase();
  }
  if (/^\\\\[?.]\\/.test(n)) {
    return null;
  }
  const m = n.match(/^\\\\([^\\]+)/);
  return m ? m[1].toLowerCase() : null;
}
class UncHopError extends Error {
}
class HopLimitError extends Error {
}
class UncVerifyError extends UncHopError {
  constructor(message, code) {
    super(message);
    this.code = code;
  }
}
const MAX_SYMLINK_HOPS = 40;
const SEG_SPLIT = process.platform === "win32" ? /[\\/]+/ : /\/+/;
async function assertNoUncSymlinkHop(p, opts) {
  p = canonicalizeWslPath(p);
  if (!(opts == null ? void 0 : opts.allowRootUnc) && isUnsafeUnc(p)) {
    throw new UncHopError(`UNC path not allowed: ${p}`);
  }
  const allowedHost = (opts == null ? void 0 : opts.allowRootUnc) ? uncHost(p) : null;
  let cur = path.resolve(p);
  let hops = 0;
  for (; ; ) {
    if ((isUnsafeUnc(cur) || (opts == null ? void 0 : opts.rejectWslHops) && isWslUncPath(cur)) && !(allowedHost !== null && uncHost(cur) === allowedHost)) {
      throw new UncHopError(`UNC path not allowed: ${cur}`);
    }
    const { root } = path.parse(cur);
    const segs = cur.slice(root.length).split(SEG_SPLIT).filter(Boolean);
    let walked = root;
    let i = 0;
    for (; i < segs.length; i++) {
      walked = path.join(walked, segs[i]);
      let st;
      try {
        st = await fs$1.lstat(walked);
      } catch (err2) {
        const code = err2.code;
        if (code === "ENOENT" || code === "ENOTDIR") {
          return;
        }
        throw new UncVerifyError(
          `Cannot verify segment: ${walked} (${code})`,
          code
        );
      }
      if (st.isSymbolicLink()) {
        break;
      }
    }
    if (i === segs.length) {
      return;
    }
    if (++hops > MAX_SYMLINK_HOPS) {
      throw new HopLimitError(`Symlink hop limit exceeded: ${p}`);
    }
    let rawTarget;
    try {
      rawTarget = await fs$1.readlink(walked);
    } catch (err2) {
      const code = err2.code;
      throw new UncVerifyError(`Cannot read link: ${walked} (${code})`, code);
    }
    if ((opts == null ? void 0 : opts.forbidWslAliasTargetHops) && WSL_ALIAS_UNC_RE.test(rawTarget)) {
      throw new UncHopError(
        `Symlink to \\\\wsl$ target: ${walked} -> ${rawTarget}`
      );
    }
    const target = canonicalizeWslPath(rawTarget);
    if (isUnsafeUnc(target) || (opts == null ? void 0 : opts.rejectWslHops) && isWslUncPath(target)) {
      throw new UncHopError(`Symlink to UNC target: ${walked} -> ${target}`);
    }
    cur = path.resolve(path.dirname(walked), target, ...segs.slice(i + 1));
    if (opts == null ? void 0 : opts.refuseSubstitutedPath) {
      let acc = path.isAbsolute(target) ? path.parse(path.resolve(path.dirname(walked), target)).root : path.dirname(walked);
      for (const seg of [target, ...segs.slice(i + 1)].join("/").split(SEG_SPLIT).filter(Boolean)) {
        acc = path.resolve(acc, seg);
        if (opts.refuseSubstitutedPath(acc)) {
          throw new UncHopError(
            `Symlink through refused namespace: ${walked} -> ${target}`
          );
        }
      }
    }
  }
}
const isWindows = process.platform === "win32";
const WIN_DEVICE_PREFIX_RE = /^[\\/]{2}[?.][\\/]/;
const _SafeRoot = class _SafeRoot {
  constructor(canonical, tier, allowUnc, rootFd, removeOnDispose = false) {
    __privateAdd(this, _SafeRoot_instances);
    __privateAdd(this, _canonical);
    __privateAdd(this, _tier2);
    __privateAdd(this, _allowUnc);
    /** Kernel fd for the canonical root directory, obtained via
     *  `@ant/claude-native.openRootDir`. Every fd-relative operation
     *  (`openLeaf` / `mkdirAt`) walks from this. */
    __privateAdd(this, _rootFd);
    /** Set by {@link SafeRoot.scratch}: `rm -rf` the root directory on
     *  dispose. Only ever true for a `mkdtemp`-created root. */
    __privateAdd(this, _removeOnDispose);
    __privateAdd(this, _disposed, false);
    /** Count of fd-relative ops currently between `#assertLive` and the
     *  native call returning — see {@link #withRootFd}. */
    __privateAdd(this, _inflight, 0);
    /** Resolver `[Symbol.asyncDispose]` parks on while `#inflight > 0`. */
    __privateAdd(this, _drained);
    __privateSet(this, _canonical, canonical);
    __privateSet(this, _tier2, tier);
    __privateSet(this, _allowUnc, allowUnc);
    __privateSet(this, _rootFd, rootFd);
    __privateSet(this, _removeOnDispose, removeOnDispose);
  }
  /** The canonical (realpath'd) absolute root. Exposed for logging and
   *  for interop with code that still needs a path string (e.g.
   *  `shell.showItemInFolder`). Do NOT `path.join` this with untrusted
   *  input — use the instance methods. */
  get path() {
    return __privateGet(this, _canonical);
  }
  get tier() {
    return __privateGet(this, _tier2);
  }
  /**
   * Open a root capability at `abs`.
   *
   * `abs` must be an absolute path. It is passed through the UNC /
   * symlink-hop guard from `./unc` (so a `\\host\share`
   * root, or one reached via a junction to UNC, is rejected *before*
   * any SMB connect could leak NTLM), then `realpath`'d once. The
   * resulting canonical path is what every later operation is resolved
   * under.
   *
   * Throws {@link UnsafeRootError} when `abs` is relative, UNC (unless
   * `opts.allowUnc`), `\\?\`-prefixed, nonexistent, or not a directory.
   */
  static async open(abs, tier, opts) {
    if (typeof abs !== "string" || abs.length === 0 || abs.includes("\0")) {
      throw new UnsafeRootError(`Invalid root path: ${JSON.stringify(abs)}`);
    }
    if (WIN_DEVICE_PREFIX_RE.test(abs)) {
      throw new UnsafeRootError(
        `Windows device-namespace root not allowed: ${abs}`
      );
    }
    const isUnc = isUncPath(abs) && !isWslUncPath(abs);
    if (isUnc && !(opts == null ? void 0 : opts.allowUnc)) {
      throw new UnsafeRootError(`UNC root not allowed: ${abs}`);
    }
    if (!isUnc && !path.isAbsolute(abs)) {
      throw new UnsafeRootError(`Root must be absolute: ${abs}`);
    }
    try {
      await assertNoUncSymlinkHop(abs, { allowRootUnc: opts == null ? void 0 : opts.allowUnc });
    } catch (e) {
      throw new UnsafeRootError(
        `Root failed symlink/UNC guard: ${e instanceof Error ? e.message : String(e)}`,
        { cause: e }
      );
    }
    let canonical;
    try {
      canonical = await fs$1.realpath(abs);
    } catch (e) {
      throw new UnsafeRootError(
        `Root does not exist or is unreadable: ${abs} (${e.code ?? e})`,
        { cause: e }
      );
    }
    if (!(opts == null ? void 0 : opts.allowUnc) && isUncPath(canonical) && !isWslUncPath(canonical)) {
      throw new UnsafeRootError(`Root resolves to UNC: ${canonical}`);
    }
    let rootFd;
    try {
      rootFd = await openRootHandle(canonical);
    } catch (e) {
      throw new UnsafeRootError(
        `Root is not an accessible directory: ${canonical} (${e.code ?? e})`,
        { cause: e }
      );
    }
    return new _SafeRoot(canonical, tier, (opts == null ? void 0 : opts.allowUnc) ?? false, rootFd);
  }
  /**
   * `mkdir -p` then {@link SafeRoot.open}. For the bootstrap case where
   * an appdata directory doesn't exist on first run. `abs` is trusted
   * (same contract as `open`) — the recursive mkdir is a plain
   * `fs.mkdir`, not the per-segment guarded walk that {@link mkdir}
   * applies to untrusted relative paths. Mode defaults to 0o700.
   */
  static async openEnsured(abs, tier, opts) {
    await fs$1.mkdir(abs, {
      recursive: true,
      mode: (opts == null ? void 0 : opts.mode) ?? PRIVATE_DIR_MODE
    });
    return _SafeRoot.open(abs, tier, opts);
  }
  /**
   * Create a fresh `mkdtemp` directory under `os.tmpdir()` and open it
   * as a root. The directory is 0o700 with an unpredictable suffix, so
   * it is process-private by construction; the default `"appdata"` tier
   * reflects that. Disposing the returned root (`await using` /
   * `Symbol.asyncDispose`) removes the directory and everything under
   * it — pair with `await using` or a `try`/`finally` so the scratch
   * tree is cleaned up on every exit path.
   */
  static async scratch(prefix = "claude-scratch-", tier = "appdata") {
    const dir = await fs$1.mkdtemp(path.join(os.tmpdir(), prefix));
    let canonical;
    let rootFd;
    try {
      canonical = await fs$1.realpath(dir);
      rootFd = await openRootHandle(canonical);
    } catch (e) {
      await fs$1.rm(dir, { recursive: true, force: true }).catch(() => void 0);
      throw new UnsafeRootError(
        `Scratch root not openable: ${dir} (${e.code ?? e})`
      );
    }
    return new _SafeRoot(canonical, tier, false, rootFd, true);
  }
  /**
   * Open a root at `abs`, run `fn` with it, and dispose it on return or
   * throw. In an `async` scope, `await using root = await SafeRoot.open(…)`
   * is the equivalent idiom; this static exists for callers that can't
   * `await` — a sync event handler or a `(): void` helper — where the
   * only alternative is the verbose `open().then(async r => { try { … }
   * finally { await r[Symbol.asyncDispose](); } })` chain. Those callers
   * write `void SafeRoot.with(abs, tier, fn).catch(…)` and still get
   * guaranteed disposal on both the fulfilled and rejected path.
   */
  static async with(abs, tier, fn, opts) {
    const root = await _SafeRoot.open(abs, tier, opts);
    try {
      return await fn(root);
    } finally {
      await root[Symbol.asyncDispose]();
    }
  }
  // ─── Reads ────────────────────────────────────────────────────────────────
  /** Read a file under the root. See {@link ReadFileOptions.maxBytes}. */
  async readFile(rel, opts) {
    const max = __privateMethod(this, _SafeRoot_instances, requireMaxBytes_fn2).call(this, opts);
    const r = __privateMethod(this, _SafeRoot_instances, lexicalLeaf_fn).call(this, rel);
    const fd = await __privateMethod(this, _SafeRoot_instances, withRootFd_fn).call(this, (rootFd) => openLeaf(rootFd, r, fs.constants.O_RDONLY));
    try {
      const st = await fstatFd(fd);
      if (!st.isFile()) {
        throw new NotRegularFileError(r.full);
      }
      if (max !== void 0 && st.size > max) {
        throw new SizeLimitError(
          `${r.rel} is ${st.size} bytes; maxBytes is ${max}`
        );
      }
      return await boundedReadFd(
        fd,
        st.size,
        max ?? Math.max(st.size, 1 << 20),
        max !== void 0
      );
    } finally {
      await closeFd(fd).catch(() => void 0);
    }
  }
  async readText(rel, opts) {
    return (await this.readFile(rel, opts)).toString("utf-8");
  }
  /** Read and `JSON.parse` a file. When `schema` is given, the result is
   *  validated and narrowed to `T`; without it the return type is `unknown`
   *  so callers must narrow explicitly. */
  async readJson(rel, opts) {
    const parsed = JSON.parse(await this.readText(rel, opts));
    return (opts == null ? void 0 : opts.schema) ? opts.schema.parse(parsed) : parsed;
  }
  /** `lstat` the leaf — does NOT follow a symlink at the leaf, so callers
   *  can distinguish symlink / file / directory. Intermediate symlinks are
   *  rejected as usual. */
  async stat(rel) {
    __privateMethod(this, _SafeRoot_instances, assertLive_fn).call(this);
    const r = await resolveUnder(__privateGet(this, _canonical), rel);
    return fs$1.lstat(r.full);
  }
  /** `true` when `rel` names an existing entry under the root. Lexical
   *  escapes and intermediate symlinks still throw — only ENOENT maps
   *  to `false`. Prefer this over `access()` for plain existence. */
  async exists(rel) {
    __privateMethod(this, _SafeRoot_instances, assertLive_fn).call(this);
    const r = await resolveUnder(__privateGet(this, _canonical), rel).catch((e) => {
      if (e.code === "ENOENT") {
        return null;
      }
      throw e;
    });
    if (r === null) {
      return false;
    }
    try {
      await fs$1.lstat(r.full);
      return true;
    } catch (e) {
      if (e.code === "ENOENT") {
        return false;
      }
      throw e;
    }
  }
  /** `fs.access` under the root — checks the calling process's
   *  permission bits (e.g. `fs.constants.X_OK` for executability).
   *  Throws on failure with the underlying errno. A symlink at the
   *  leaf is rejected rather than followed; use {@link exists} for a
   *  boolean existence check. */
  async access(rel, mode) {
    const r = await __privateMethod(this, _SafeRoot_instances, resolveLeaf_fn).call(this, rel);
    await __privateMethod(this, _SafeRoot_instances, assertNotSymlinkLeaf_fn).call(this, r);
    await fs$1.access(r.full, mode);
  }
  /** Read a symbolic link's target string. Intermediate symlinks are
   *  rejected as usual; the leaf is the link being read and is not
   *  followed (that's what `readlink` does). Throws EINVAL when the
   *  leaf is not a symlink, matching `fs.readlink`. */
  async readlink(rel) {
    const r = await __privateMethod(this, _SafeRoot_instances, resolveLeaf_fn).call(this, rel);
    return fs$1.readlink(r.full);
  }
  /** Filesystem stats (`statfs`) for the volume the root lives on —
   *  free-block / free-inode preflight before a large download. `rel`
   *  defaults to the root itself since every path under one root is on
   *  the same filesystem. */
  async statfs(rel = ".") {
    __privateMethod(this, _SafeRoot_instances, assertLive_fn).call(this);
    const r = await resolveUnder(__privateGet(this, _canonical), rel);
    if (r.leaf !== void 0) {
      await __privateMethod(this, _SafeRoot_instances, assertNotSymlinkLeaf_fn).call(this, r);
    }
    return fs$1.statfs(r.full);
  }
  /** List a directory under the root. Entries are reported with `lstat`
   *  semantics (a symlink entry has `isSymbolicLink: true` and is NOT
   *  followed). `path` on each entry is root-relative so it feeds straight
   *  back into another SafeRoot call.
   *
   *  With `{recursive: true}` the subtree under `rel` is walked
   *  breadth-first. Symlink entries are still reported but never
   *  descended into, so the walk cannot escape the root — this is the
   *  difference from `fs.readdir({recursive})`, which follows symlinked
   *  directories. */
  async readdir(rel = ".", opts) {
    __privateMethod(this, _SafeRoot_instances, assertLive_fn).call(this);
    const r = await resolveUnder(__privateGet(this, _canonical), rel);
    if (r.leaf !== void 0) {
      const st = await fs$1.lstat(r.full);
      if (st.isSymbolicLink() || !st.isDirectory()) {
        throw new SymlinkEncounteredError(r.full);
      }
    }
    const listOne = async (full, base) => {
      const entries = await fs$1.readdir(full, { withFileTypes: true });
      return entries.map((e) => ({
        name: e.name,
        path: base.length > 0 ? `${base}/${e.name}` : e.name,
        isFile: e.isFile(),
        isDirectory: e.isDirectory(),
        isSymbolicLink: e.isSymbolicLink()
      }));
    };
    if (!(opts == null ? void 0 : opts.recursive)) {
      return listOne(r.full, r.rel);
    }
    const out = [];
    const queue = [[r.full, r.rel]];
    while (queue.length > 0) {
      const [full, base] = queue.shift();
      for (const e of await listOne(full, base)) {
        out.push(e);
        if (e.isDirectory && !e.isSymbolicLink) {
          queue.push([path.join(full, e.name), e.path]);
        }
      }
    }
    return out;
  }
  // ─── Writes ───────────────────────────────────────────────────────────────
  /**
   * Atomic write: write to `{leaf}.{rand}.tmp`, fsync, rename over the
   * target, fsync the parent directory. The tmp file is a fresh inode
   * created at `mode` (default 0o600), so a previously world-readable
   * target is fixed on next write with no window where new bytes sit in
   * a permissive file — same guarantee as `helpers/privateFile.writeFileAtomic`,
   * which this supersedes for callers under a SafeRoot.
   *
   * Both the tmp open and the rename are fd-relative (`openBeneath` /
   * `renameBeneath`), so a concurrent symlink/junction swap on any
   * intermediate component cannot redirect either step (CC-2885). On
   * Windows, transient AV/backup-sync locks on the target
   * (EBUSY/EACCES/EPERM) are retried with backoff; EXDEV (folder
   * redirection / Offline Files) falls back to a direct fd-pinned
   * truncate+write of the target — that fallback is NOT atomic (a crash
   * mid-write leaves an empty file), matching `privateFile`'s behaviour.
   *
   * Parent directories are NOT created implicitly — call {@link mkdir}
   * first. Implicit mkdir would let a `rel` with a typo silently create
   * a new tree.
   */
  async writeFileAtomic(rel, data, opts) {
    const r = __privateMethod(this, _SafeRoot_instances, lexicalLeaf_fn).call(this, rel);
    const mode = (opts == null ? void 0 : opts.mode) ?? PRIVATE_FILE_MODE;
    const tmpLeaf = `.${r.leaf}.${process.pid}.${Math.random().toString(36).slice(2, 8)}.tmp`;
    const tmpSegs = [...r.dirSegments, tmpLeaf];
    const dstSegs = [...r.dirSegments, r.leaf];
    let tmp;
    try {
      const fd = await __privateMethod(this, _SafeRoot_instances, withRootFd_fn).call(this, (rootFd) => openLeaf(
        rootFd,
        { ...r, leaf: tmpLeaf, rel: tmpSegs.join("/") },
        fs.constants.O_WRONLY | fs.constants.O_CREAT | fs.constants.O_EXCL,
        mode
      ));
      tmp = new SafeFile(fd, __privateGet(this, _tier2));
      await tmp.write(data);
      await tmp.sync();
      await tmp.close();
    } catch (e) {
      await (tmp == null ? void 0 : tmp.close().catch(() => void 0));
      await __privateMethod(this, _SafeRoot_instances, withRootFd_fn).call(this, (rootFd) => unlinkAt(rootFd, tmpSegs)).catch(
        () => void 0
      );
      throw e;
    }
    try {
      await __privateMethod(this, _SafeRoot_instances, renameTmp_fn).call(this, tmpSegs, dstSegs, data, mode);
    } catch (e) {
      await __privateMethod(this, _SafeRoot_instances, withRootFd_fn).call(this, (rootFd) => unlinkAt(rootFd, tmpSegs)).catch(
        () => void 0
      );
      throw e;
    }
  }
  /** Atomic JSON write, 2-space indent. */
  writeJsonAtomic(rel, data, opts) {
    return this.writeFileAtomic(rel, JSON.stringify(data, null, 2), opts);
  }
  /** Append to a file under the root, creating it at `mode` (default
   *  0o600) if it does not exist. The append goes through an
   *  `O_NOFOLLOW` open, so a symlink at the leaf is rejected rather
   *  than followed. Not atomic — callers that need atomicity should
   *  read-modify-{@link writeFileAtomic}. */
  async appendFile(rel, data, opts) {
    const r = __privateMethod(this, _SafeRoot_instances, lexicalLeaf_fn).call(this, rel);
    const fd = await __privateMethod(this, _SafeRoot_instances, withRootFd_fn).call(this, (rootFd) => openLeaf(
      rootFd,
      r,
      fs.constants.O_WRONLY | fs.constants.O_CREAT | fs.constants.O_APPEND,
      (opts == null ? void 0 : opts.mode) ?? PRIVATE_FILE_MODE
    ));
    const f = new SafeFile(fd, __privateGet(this, _tier2));
    try {
      await f.write(data);
    } finally {
      await f.close();
    }
  }
  /** Rename `srcRel` to `dstRel`, both under the root, via the
   *  fd-relative `renameAt` (POSIX `renameat` / Windows
   *  `NtSetInformationFile` with `RootDirectory`). A symlink/junction at
   *  any component of either side is refused; a symlink at `srcRel`
   *  itself is moved, not followed (rename operates on the link). The
   *  parent of `dstRel` must already exist. Refuses to rename the root
   *  itself. */
  async rename(srcRel, dstRel) {
    const src = __privateMethod(this, _SafeRoot_instances, lexicalLeaf_fn).call(this, srcRel);
    const dst = __privateMethod(this, _SafeRoot_instances, lexicalLeaf_fn).call(this, dstRel);
    await __privateMethod(this, _SafeRoot_instances, withRootFd_fn).call(this, (rootFd) => renameAt(
      rootFd,
      [...src.dirSegments, src.leaf],
      [...dst.dirSegments, dst.leaf]
    ));
  }
  /** Copy a single file from `srcRel` to `dstRel`. `mode` is passed
   *  through to `fs.copyFile` — so `fs.constants.COPYFILE_FICLONE`
   *  (reflink where supported) and `COPYFILE_EXCL` work. A symlink at
   *  either leaf is rejected rather than followed; for a directory
   *  tree use {@link cp}. */
  async copyFile(srcRel, dstRel, mode) {
    const src = await __privateMethod(this, _SafeRoot_instances, resolveLeaf_fn).call(this, srcRel);
    const dst = await __privateMethod(this, _SafeRoot_instances, resolveLeaf_fn).call(this, dstRel);
    const srcSt = await __privateMethod(this, _SafeRoot_instances, assertNotSymlinkLeaf_fn).call(this, src);
    if (srcSt !== null && !srcSt.isFile()) {
      throw new NotRegularFileError(src.full);
    }
    await __privateMethod(this, _SafeRoot_instances, assertNotSymlinkLeaf_fn).call(this, dst);
    await fs$1.copyFile(src.full, dst.full, mode);
  }
  /** Hard-link `srcRel` to `dstRel`. Both must be under the root and on
   *  the same filesystem (EXDEV otherwise). A symlink at `srcRel` is
   *  rejected — POSIX leaves `link(2)` on a symlink implementation-
   *  defined, and the callers that need this (link-or-copy staging)
   *  want the file, not the link. */
  async link(srcRel, dstRel) {
    const src = await __privateMethod(this, _SafeRoot_instances, resolveLeaf_fn).call(this, srcRel);
    const dst = await __privateMethod(this, _SafeRoot_instances, resolveLeaf_fn).call(this, dstRel);
    await __privateMethod(this, _SafeRoot_instances, assertNotSymlinkLeaf_fn).call(this, src);
    await fs$1.link(src.full, dst.full);
  }
  /** Change the mode bits of a file under the root. Goes through an
   *  `O_NOFOLLOW` open + `fchmod` on the resulting fd, so the inode
   *  whose mode changes is pinned — a symlink at the leaf is rejected,
   *  not followed. No-op on Windows (POSIX mode bits don't map to
   *  ACLs; see {@link writeFileAtomic}'s fallback). */
  async chmod(rel, mode) {
    if (isWindows) {
      return;
    }
    const r = __privateMethod(this, _SafeRoot_instances, lexicalLeaf_fn).call(this, rel);
    const fd = await __privateMethod(this, _SafeRoot_instances, withRootFd_fn).call(this, (rootFd) => openLeaf(rootFd, r, fs.constants.O_RDONLY));
    const f = new SafeFile(fd, __privateGet(this, _tier2));
    try {
      await f.chmod(mode);
    } finally {
      await f.close();
    }
  }
  /** mkdir under the root. Each component is created via the native
   *  fd-relative `mkdirat` walk, so an existing symlink/junction at any
   *  component fails the call rather than being followed. Mode defaults
   *  to 0o700 (PRIVATE_DIR_MODE). */
  async mkdir(rel, opts) {
    __privateMethod(this, _SafeRoot_instances, assertLive_fn).call(this);
    const r = lexicalResolve(__privateGet(this, _canonical), rel);
    if (r.leaf === void 0) {
      return;
    }
    const mode = (opts == null ? void 0 : opts.mode) ?? PRIVATE_DIR_MODE;
    const all = [...r.dirSegments, r.leaf];
    if (!(opts == null ? void 0 : opts.recursive)) {
      await __privateMethod(this, _SafeRoot_instances, withRootFd_fn).call(this, (rootFd) => mkdirAt(rootFd, all, mode));
      return;
    }
    for (let i = 1; i <= all.length; i++) {
      try {
        await __privateMethod(this, _SafeRoot_instances, withRootFd_fn).call(this, (rootFd) => mkdirAt(rootFd, all.slice(0, i), mode));
      } catch (e) {
        if (e.code !== "EEXIST") {
          throw e;
        }
        if (i === all.length) {
          const st = await fs$1.lstat(r.full);
          if (st.isSymbolicLink() || !st.isDirectory()) {
            throw new SymlinkEncounteredError(r.full);
          }
        }
      }
    }
  }
  /** Remove a path under the root. `recursive` removes a directory tree.
   *  `maxRetries` / `retryDelay` are passed through to `fs.rm` for the
   *  Windows AV-lock case. Refuses to remove the root itself (`rel`
   *  resolving to `"."`). */
  async rm(rel, opts) {
    __privateMethod(this, _SafeRoot_instances, assertLive_fn).call(this);
    const r = await resolveUnder(__privateGet(this, _canonical), rel);
    if (r.leaf === void 0) {
      throw new PathEscapeError(rel);
    }
    const st = await fs$1.lstat(r.full).catch((e) => {
      if (e.code === "ENOENT") {
        return null;
      }
      throw e;
    });
    if (st === null) {
      return;
    }
    if (st.isSymbolicLink()) {
      await fs$1.unlink(r.full);
      return;
    }
    await fs$1.rm(r.full, {
      recursive: (opts == null ? void 0 : opts.recursive) ?? false,
      force: true,
      ...(opts == null ? void 0 : opts.maxRetries) !== void 0 && { maxRetries: opts.maxRetries },
      ...(opts == null ? void 0 : opts.retryDelay) !== void 0 && { retryDelay: opts.retryDelay }
    });
  }
  /** Remove a single empty directory. Fails with ENOTEMPTY when the
   *  directory has entries — use this instead of {@link rm} when
   *  "delete only if nothing is left" is the intended semantics (e.g.
   *  pruning an index directory after its last item is removed). */
  async rmdir(rel) {
    const r = await __privateMethod(this, _SafeRoot_instances, resolveLeaf_fn).call(this, rel);
    await __privateMethod(this, _SafeRoot_instances, assertNotSymlinkLeaf_fn).call(this, r);
    await fs$1.rmdir(r.full);
  }
  /** Copy a file or (with `{recursive: true}`) a directory tree from
   *  `srcRel` to `dstRel`. The tree walk uses this root's own
   *  `lstat`-guarded `readdir`, so a symlink anywhere under `srcRel`
   *  throws {@link SymlinkEncounteredError} rather than being followed
   *  or silently copied — callers that need to preserve symlinks should
   *  keep their raw `fs.cp` escape hatch. Directory mode defaults to
   *  0o700; file mode is preserved from the source. */
  async cp(srcRel, dstRel, opts) {
    const src = await __privateMethod(this, _SafeRoot_instances, resolveLeaf_fn).call(this, srcRel);
    const dst = await __privateMethod(this, _SafeRoot_instances, resolveLeaf_fn).call(this, dstRel);
    const srcSt = await __privateMethod(this, _SafeRoot_instances, assertNotSymlinkLeaf_fn).call(this, src);
    if (srcSt === null) {
      await fs$1.copyFile(src.full, dst.full);
      return;
    }
    if (srcSt.isFile()) {
      await __privateMethod(this, _SafeRoot_instances, assertNotSymlinkLeaf_fn).call(this, dst);
      await fs$1.copyFile(src.full, dst.full);
      return;
    }
    if (!srcSt.isDirectory()) {
      throw new NotRegularFileError(src.full);
    }
    if (!(opts == null ? void 0 : opts.recursive)) {
      const err2 = new Error(
        `cp: ${src.rel} is a directory (pass {recursive: true})`
      );
      err2.code = "EISDIR";
      throw err2;
    }
    await this.mkdir(dst.rel, { recursive: true });
    for (const e of await this.readdir(src.rel, { recursive: true })) {
      if (e.isSymbolicLink) {
        throw new SymlinkEncounteredError(path.join(__privateGet(this, _canonical), e.path));
      }
      const sub = e.path.slice(src.rel.length + 1);
      const dstEntry = `${dst.rel}/${sub}`;
      if (e.isDirectory) {
        await this.mkdir(dstEntry, { recursive: true });
      } else if (e.isFile) {
        await this.copyFile(e.path, dstEntry);
      }
    }
  }
  // ─── Handles ──────────────────────────────────────────────────────────────
  /** Open a {@link SafeFile} at `rel`. Prefer {@link withFile} for scoped
   *  access — this variant is for callers that need to hold the handle
   *  across an await point the `withFile` callback shape doesn't fit. */
  async openFile(rel, flags, mode = PRIVATE_FILE_MODE) {
    const r = __privateMethod(this, _SafeRoot_instances, lexicalLeaf_fn).call(this, rel);
    const numFlags = typeof flags === "string" ? stringFlagsToInt(flags) : flags;
    const fd = await __privateMethod(this, _SafeRoot_instances, withRootFd_fn).call(this, (rootFd) => openLeaf(rootFd, r, numFlags, mode));
    try {
      const st = await fstatFd(fd);
      if (!st.isFile()) {
        throw new NotRegularFileError(r.full);
      }
    } catch (e) {
      await closeFd(fd).catch(() => void 0);
      throw e;
    }
    return new SafeFile(fd, __privateGet(this, _tier2));
  }
  /**
   * Open `rel` and return a detached `ReadStream` that owns its fd.
   *
   * This exists for callers that must hand a stream to code outside
   * the `SafeRoot`'s lifetime — `form-data` multipart upload,
   * `readline.createInterface`, `tar.create`, an `electron.net`
   * response body — where {@link SafeFile.createReadStream} would
   * require holding the `SafeFile` open until the consumer finishes.
   * The returned stream has `.path` set to the resolved absolute path
   * so `form-data` can infer filename / Content-Type, and (by default)
   * closes the fd itself when the stream ends or errors.
   *
   * The fd is obtained via `O_NOFOLLOW` and `fstat`-checked for
   * `isFile()` before the stream is created, so a symlink or FIFO at
   * the leaf is rejected with the same errors as {@link readFile}.
   * `maxBytes` is translated to the stream's `end` offset (required on
   * workspace/vm tiers).
   */
  async createReadStream(rel, opts) {
    const max = __privateMethod(this, _SafeRoot_instances, requireMaxBytes_fn2).call(this, opts);
    const r = __privateMethod(this, _SafeRoot_instances, lexicalLeaf_fn).call(this, rel);
    const fd = await __privateMethod(this, _SafeRoot_instances, withRootFd_fn).call(this, (rootFd) => openLeaf(rootFd, r, fs.constants.O_RDONLY));
    try {
      const st = await fstatFd(fd);
      if (!st.isFile()) {
        throw new NotRegularFileError(r.full);
      }
    } catch (e) {
      await closeFd(fd).catch(() => void 0);
      throw e;
    }
    const start = (opts == null ? void 0 : opts.start) ?? 0;
    const end = max !== void 0 ? start + max - 1 : void 0;
    const stream = fs.createReadStream("", {
      fd,
      autoClose: (opts == null ? void 0 : opts.autoClose) ?? true,
      start,
      end
    });
    stream.path = r.full;
    return stream;
  }
  /** Run `fn` with a {@link SafeFile} open at `rel`; the handle is closed
   *  on return or throw. */
  async withFile(rel, flags, fn) {
    const f = await this.openFile(rel, flags);
    try {
      return await fn(f);
    } finally {
      await f.close();
    }
  }
  /** Derive a sub-capability rooted at `rel`. The child's canonical path
   *  is under this root's, and its tier is inherited, so handing a child
   *  to less-trusted code narrows what that code can reach. */
  async child(rel) {
    __privateMethod(this, _SafeRoot_instances, assertLive_fn).call(this);
    const r = await resolveUnder(__privateGet(this, _canonical), rel);
    const opts = { allowUnc: __privateGet(this, _allowUnc) };
    if (r.leaf === void 0) {
      return _SafeRoot.open(__privateGet(this, _canonical), __privateGet(this, _tier2), opts);
    }
    const st = await fs$1.lstat(r.full);
    if (st.isSymbolicLink() || !st.isDirectory()) {
      throw new SymlinkEncounteredError(r.full);
    }
    const child = await _SafeRoot.open(r.full, __privateGet(this, _tier2), opts);
    const parentWithSep = __privateGet(this, _canonical).endsWith(path.sep) ? __privateGet(this, _canonical) : __privateGet(this, _canonical) + path.sep;
    if (!(__privateGet(child, _canonical) + path.sep).startsWith(parentWithSep)) {
      await child[Symbol.asyncDispose]();
      throw new SymlinkEncounteredError(r.full);
    }
    return child;
  }
  // ─── Lifetime ─────────────────────────────────────────────────────────────
  async [Symbol.asyncDispose]() {
    if (__privateGet(this, _disposed)) {
      return;
    }
    __privateSet(this, _disposed, true);
    if (__privateGet(this, _inflight) > 0) {
      await new Promise((resolve) => {
        __privateSet(this, _drained, resolve);
      });
    }
    await closeFd(__privateGet(this, _rootFd)).catch(() => void 0);
    if (__privateGet(this, _removeOnDispose)) {
      await fs$1.rm(__privateGet(this, _canonical), {
        recursive: true,
        force: true,
        maxRetries: 3
      }).catch(() => void 0);
    }
  }
};
_canonical = new WeakMap();
_tier2 = new WeakMap();
_allowUnc = new WeakMap();
_rootFd = new WeakMap();
_removeOnDispose = new WeakMap();
_disposed = new WeakMap();
_inflight = new WeakMap();
_drained = new WeakMap();
_SafeRoot_instances = new WeakSet();
assertLive_fn = function() {
  if (__privateGet(this, _disposed)) {
    throw new SafeFsDisposedError();
  }
};
requireMaxBytes_fn2 = function(opts) {
  if (__privateGet(this, _tier2) !== "appdata" && (opts == null ? void 0 : opts.maxBytes) === void 0) {
    throw new SizeLimitError(
      `maxBytes is required for reads on a "${__privateGet(this, _tier2)}"-tier root`
    );
  }
  return opts == null ? void 0 : opts.maxBytes;
};
resolveLeaf_fn = async function(rel) {
  __privateMethod(this, _SafeRoot_instances, assertLive_fn).call(this);
  const r = await resolveUnder(__privateGet(this, _canonical), rel);
  if (r.leaf === void 0) {
    throw new PathEscapeError(rel);
  }
  return r;
};
/** Lexical-only resolve for fd-relative ops. The native `openBeneath`
 *  walk does the per-segment no-follow check itself, so the lstat
 *  pre-walk in {@link resolveUnder} is redundant (and a wasted N
 *  syscalls per call). */
lexicalLeaf_fn = function(rel) {
  __privateMethod(this, _SafeRoot_instances, assertLive_fn).call(this);
  const r = lexicalResolve(__privateGet(this, _canonical), rel);
  if (r.leaf === void 0) {
    throw new PathEscapeError(rel);
  }
  return r;
};
withRootFd_fn = async function(fn) {
  __privateMethod(this, _SafeRoot_instances, assertLive_fn).call(this);
  __privateWrapper(this, _inflight)._++;
  try {
    return await fn(__privateGet(this, _rootFd));
  } finally {
    __privateWrapper(this, _inflight)._--;
    if (__privateGet(this, _inflight) === 0 && __privateGet(this, _drained) !== void 0) {
      const resolve = __privateGet(this, _drained);
      __privateSet(this, _drained, void 0);
      resolve();
    }
  }
};
assertNotSymlinkLeaf_fn = async function(r) {
  const st = await fs$1.lstat(r.full).catch((e) => {
    if (e.code === "ENOENT") {
      return null;
    }
    throw e;
  });
  if (st == null ? void 0 : st.isSymbolicLink()) {
    throw new SymlinkEncounteredError(r.full);
  }
  return st;
};
renameTmp_fn = async function(tmpSegs, dstSegs, data, mode) {
  for (let attempt = 0; attempt < 3; attempt++) {
    try {
      await __privateMethod(this, _SafeRoot_instances, withRootFd_fn).call(this, (rootFd) => renameAt(rootFd, tmpSegs, dstSegs));
      return;
    } catch (e) {
      const code = e.code;
      if (code === "EXDEV") {
        break;
      }
      if (code !== void 0 && RETRYABLE_RENAME_ERRNOS.has(code)) {
        if (attempt < 2) {
          await promises$1.setTimeout(50 * (attempt + 1));
        }
        continue;
      }
      throw e;
    }
  }
  await this.withFile(
    dstSegs.join("/"),
    fs.constants.O_WRONLY | fs.constants.O_CREAT,
    async (f) => {
      if (!isWindows) {
        await f.chmod(mode);
      }
      await f.truncate(0);
      await f.write(data);
      await f.sync();
    }
  );
  await __privateMethod(this, _SafeRoot_instances, withRootFd_fn).call(this, (rootFd) => unlinkAt(rootFd, tmpSegs)).catch(
    () => void 0
  );
};
let SafeRoot = _SafeRoot;
class SafeFsDisposedError extends SafeFsError {
  constructor() {
    super("ERR_SAFE_FS_DISPOSED", "SafeRoot used after dispose");
    this.name = "SafeFsDisposedError";
  }
}
const STRING_FLAGS = {
  r: fs.constants.O_RDONLY,
  "r+": fs.constants.O_RDWR,
  w: fs.constants.O_WRONLY | fs.constants.O_CREAT | fs.constants.O_TRUNC,
  wx: fs.constants.O_WRONLY | fs.constants.O_CREAT | fs.constants.O_TRUNC | fs.constants.O_EXCL,
  a: fs.constants.O_WRONLY | fs.constants.O_CREAT | fs.constants.O_APPEND
};
const RETRYABLE_RENAME_ERRNOS = /* @__PURE__ */ new Set([
  "EPERM",
  "EBADF",
  "EACCES",
  "EBUSY"
]);
function stringFlagsToInt(flags) {
  const n = STRING_FLAGS[flags];
  if (n === void 0) {
    throw new TypeError(
      `SafeRoot: unsupported flag string ${JSON.stringify(flags)}; pass numeric fs.constants`
    );
  }
  return n;
}
const MAX_BUNDLE_FILE_BYTES = 50 * 1024 * 1024;
async function readRegularFileNoFollow(filePath) {
  try {
    var _stack = [];
    try {
      const root = __using(_stack, await SafeRoot.open(path.dirname(filePath), "vm", {
        allowUnc: true
      }), true);
      return await root.readFile(path.basename(filePath), {
        maxBytes: MAX_BUNDLE_FILE_BYTES
      });
    } catch (_) {
      var _error = _, _hasError = true;
    } finally {
      var _promise = __callDispose(_stack, _error, _hasError);
      _promise && await _promise;
    }
  } catch {
    return null;
  }
}
const EXCLUDED_LOG_ENTRIES = /* @__PURE__ */ new Set(["echo.log", "echo1.log", "traces"]);
const SESSION_EXPORT_PREFIX = "session-export-";
const STALE_EXPORT_TMP_AGE_MS = 10 * 60 * 1e3;
async function exportSessionTranscript({
  cliSessionId,
  projectsDir,
  metadataFilePath,
  extraFiles,
  logsDir,
  downloadsDir
}) {
  const zipData = {};
  let transcriptFound = false;
  let transcriptUnreadable = false;
  let transcriptTooLarge = false;
  try {
    const projectDirs = await fs.promises.readdir(projectsDir);
    const queue = new PQueue({ concurrency: 20 });
    const hits = await queue.addAll(
      projectDirs.map((projectHash) => async () => {
        const projectPath = path.join(projectsDir, projectHash);
        const stats = await fs.promises.lstat(projectPath).catch(() => null);
        if (!stats || stats.isSymbolicLink() || !stats.isDirectory()) {
          return null;
        }
        const transcriptPath = path.join(projectPath, `${cliSessionId}.jsonl`);
        const transcriptStat = await fs.promises.lstat(transcriptPath).catch(() => null);
        if (!(transcriptStat == null ? void 0 : transcriptStat.isFile())) {
          return null;
        }
        return { projectPath, transcriptPath, size: transcriptStat.size };
      })
    );
    for (const hit of hits) {
      if (!hit) {
        continue;
      }
      const content = await readRegularFileNoFollow(hit.transcriptPath);
      if (content === null) {
        logger.warn(
          "[transcriptExport] Transcript present but unreadable — skipping",
          { transcriptPath: hit.transcriptPath, size: hit.size }
        );
        transcriptUnreadable = true;
        if (hit.size > MAX_BUNDLE_FILE_BYTES) {
          transcriptTooLarge = true;
        }
        continue;
      }
      const transcriptBytes = new Uint8Array(content);
      zipData["transcript.jsonl"] = transcriptBytes;
      zipData[`${cliSessionId}.jsonl`] = transcriptBytes;
      transcriptFound = true;
      const sessionDir = path.join(hit.projectPath, cliSessionId);
      try {
        const sessionDirStat = await fs.promises.lstat(sessionDir);
        if (sessionDirStat.isDirectory()) {
          await addDirectoryToZip(sessionDir, cliSessionId, zipData);
        }
      } catch {
      }
      break;
    }
  } catch {
    logger.warn("[transcriptExport] projects directory not found", {
      projectsDir
    });
  }
  if (!transcriptFound) {
    logger.warn("[transcriptExport] No transcript found — failing export", {
      cliSessionId,
      projectsDir,
      transcriptUnreadable,
      transcriptTooLarge
    });
    return {
      success: false,
      error: transcriptTooLarge ? "Transcript is too large to export." : transcriptUnreadable ? "Transcript couldn't be read. You can try again." : "Transcript not found for this session. You can try again."
    };
  }
  if (metadataFilePath) {
    try {
      const metadataContent = await fs.promises.readFile(
        metadataFilePath,
        "utf-8"
      );
      zipData["metadata.json"] = new TextEncoder().encode(metadataContent);
    } catch {
      logger.warn(
        "[transcriptExport] Failed to read session metadata — omitting",
        { metadataFilePath }
      );
    }
  }
  const reservedNames = /* @__PURE__ */ new Set([
    "transcript.jsonl",
    `${cliSessionId}.jsonl`,
    "metadata.json"
  ]);
  for (const [name, bytes] of Object.entries(extraFiles ?? {})) {
    if (reservedNames.has(name)) {
      logger.warn(
        "[transcriptExport] Ignoring extraFiles entry with reserved name",
        { name }
      );
      continue;
    }
    zipData[name] = new Uint8Array(
      scrubBufferForBundle(name, Buffer.from(bytes), SUPPORT_BUNDLE_SCRUB_OPTS)
    );
  }
  try {
    await addDirectoryToZip(
      logsDir,
      "logs",
      zipData,
      EXCLUDED_LOG_ENTRIES,
      (name, buf) => scrubBufferForBundle(name, buf, SUPPORT_BUNDLE_SCRUB_OPTS)
    );
  } catch (error) {
    logger.warn("[transcriptExport] Failed to include app logs — omitting", {
      error
    });
  }
  const compressed = zipSync(zipData, { level: 6 });
  for (const entry of await fs.promises.readdir(downloadsDir).catch(() => [])) {
    if (!entry.startsWith(SESSION_EXPORT_PREFIX) || !entry.endsWith(".zip.tmp")) {
      continue;
    }
    const tmpPath = path.join(downloadsDir, entry);
    const tmpStat = await fs.promises.stat(tmpPath).catch(() => null);
    if (tmpStat && Date.now() - tmpStat.mtimeMs > STALE_EXPORT_TMP_AGE_MS) {
      await fs.promises.rm(tmpPath).catch(() => void 0);
    }
  }
  const filename = `${SESSION_EXPORT_PREFIX}${Date.now()}.zip`;
  const outputPath = path.join(downloadsDir, filename);
  await writeFileAtomic(outputPath, compressed, 438);
  logger.info(
    `[transcriptExport] Session ${cliSessionId} exported to ${outputPath} (${compressed.length} bytes, ${Object.keys(zipData).length} files)`
  );
  return { success: true, filePath: outputPath };
}
async function addDirectoryToZip(dirPath, zipPrefix, zipData, exclude, transform) {
  const entries = await fs.promises.readdir(dirPath);
  for (const entry of entries) {
    if (exclude == null ? void 0 : exclude.has(entry)) {
      continue;
    }
    const fullPath = path.join(dirPath, entry);
    const zipPath = `${zipPrefix}/${entry}`;
    try {
      const stats = await fs.promises.lstat(fullPath);
      if (stats.isSymbolicLink()) {
        continue;
      }
      if (stats.isDirectory()) {
        await addDirectoryToZip(fullPath, zipPath, zipData, exclude, transform);
      } else if (stats.isFile()) {
        const content = await readRegularFileNoFollow(fullPath);
        if (content !== null) {
          zipData[zipPath] = new Uint8Array(
            transform ? transform(entry, content) : content
          );
        }
      }
    } catch (error) {
      logger.warn("[transcriptExport] Skipping unreadable entry", {
        fullPath,
        error
      });
    }
  }
}
const handlers = {
  codeStats: ({ claudeConfigDir }) => computeCodeStats(claudeConfigDir),
  // Bind main's redaction env before the first scrub (contract in
  // telemetryScrubEnv.ts); destructured so the thunk doesn't hold extraFiles.
  transcriptExport: ({ scrubEnv, registryServerUuids, ...params }) => {
    setScrubEnvSource(() => scrubEnv);
    noteRegistryServerUuids(registryServerUuids);
    return exportSessionTranscript(params);
  },
  copyWorktreeFiles: ({ srcDir, destDir, files, skipExisting }, signal) => copyFiles(srcDir, destDir, files, { skipExisting, signal })
};
const inflightAborts = /* @__PURE__ */ new Map();
function postToParent(port, message) {
  try {
    port.postMessage(message);
  } catch {
  }
}
function isHeavyWorkRequest(data) {
  if (typeof data !== "object" || data === null) {
    return false;
  }
  const c = data;
  return typeof c.requestId === "number" && typeof c.task === "string" && c.task in handlers && typeof c.params === "object" && c.params !== null;
}
function isUtilityWorkerCancel(data) {
  if (typeof data !== "object" || data === null) {
    return false;
  }
  const c = data;
  return c.type === "cancel" && typeof c.requestId === "number";
}
async function handle(port, req, signal) {
  try {
    const result = await handlers[req.task](req.params, signal);
    postToParent(port, {
      type: "result",
      requestId: req.requestId,
      task: req.task,
      result
    });
  } catch (err2) {
    postToParent(port, {
      type: "error",
      requestId: req.requestId,
      message: err2 instanceof Error ? err2.message : String(err2),
      stack: err2 instanceof Error ? err2.stack : void 0
    });
  }
}
function attachPort(port) {
  port.on("message", (event) => {
    var _a3;
    const data = event.data;
    if (isUtilityWorkerCancel(data)) {
      (_a3 = inflightAborts.get(data.requestId)) == null ? void 0 : _a3.abort();
      return;
    }
    if (!isHeavyWorkRequest(data)) {
      return;
    }
    if (!data.cancellable) {
      void handle(port, data, void 0);
      return;
    }
    const abort = new AbortController();
    inflightAborts.set(data.requestId, abort);
    void handle(port, data, abort.signal).finally(
      () => inflightAborts.delete(data.requestId)
    );
  });
  port.start();
}
(_a2 = process.parentPort) == null ? void 0 : _a2.once("message", (e) => {
  const [port] = e.ports;
  attachPort(port);
});
process.on("SIGTERM", () => {
  const exit = () => process.exit(0);
  setTimeout(exit, 2e3);
  void sweepInFlightWrites().then(exit, exit);
});
process.on("SIGINT", () => process.exit(0));
const _test = {
  handlers,
  isHeavyWorkRequest,
  attachPort,
  inflightAborts
};
exports._test = _test;
