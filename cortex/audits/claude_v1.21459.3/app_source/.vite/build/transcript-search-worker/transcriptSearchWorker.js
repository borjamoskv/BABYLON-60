"use strict";
var _a;
Object.defineProperty(exports, Symbol.toStringTag, { value: "Module" });
const node_fs = require("node:fs");
const node_readline = require("node:readline");
const promises = require("node:fs/promises");
const SDK_MESSAGE_TYPES = /* @__PURE__ */ new Set([
  "user",
  "assistant",
  "system",
  "result",
  "stream_event",
  "tool_use_summary",
  "tool_progress",
  "auth_status",
  "prompt_suggestion",
  "rate_limit_event"
]);
async function openTranscriptNoFollow(filePath) {
  const st = await promises.lstat(filePath);
  if (!st.isFile()) {
    const err = new Error(
      `Refusing to open non-regular transcript path: ${filePath}`
    );
    err.code = "ELOOP";
    throw err;
  }
  let flags = node_fs.constants.O_RDONLY;
  if (node_fs.constants.O_NOFOLLOW !== void 0) {
    flags |= node_fs.constants.O_NOFOLLOW;
  }
  if (node_fs.constants.O_NONBLOCK !== void 0) {
    flags |= node_fs.constants.O_NONBLOCK;
  }
  return promises.open(filePath, flags);
}
const LARGE_TRANSCRIPT_THRESHOLD = 50 * 1024 * 1024;
const EMPTY_BOUNDARY = Buffer.alloc(0);
const TRUNCATED_READ_SIZE = 50 * 1024 * 1024;
function parseBoundaryLine(line) {
  var _a2;
  try {
    const parsed = JSON.parse(line);
    if (parsed.type !== "system" || parsed.subtype !== "compact_boundary") {
      return null;
    }
    return {
      hasPreservedSegment: Boolean((_a2 = parsed.compactMetadata) == null ? void 0 : _a2.preservedSegment)
    };
  } catch {
    return null;
  }
}
async function findLastCompactBoundaryOffset(filePath, fileSize) {
  const searchChunkSize = 30 * 1024 * 1024;
  const searchStart = Math.max(0, fileSize - searchChunkSize);
  const fileHandle = await promises.open(filePath, "r");
  try {
    const readSize = fileSize - searchStart;
    const buffer = Buffer.alloc(readSize);
    await fileHandle.read(buffer, 0, readSize, searchStart);
    const chunk = buffer.toString("utf-8");
    const lines = chunk.split("\n");
    let lastBoundaryEndOffset = -1;
    let hasPreservedSegment = false;
    let byteOffset = searchStart;
    for (const line of lines) {
      const lineByteLength = Buffer.byteLength(line, "utf-8") + 1;
      if (line.includes('"compact_boundary"')) {
        const hit = parseBoundaryLine(line);
        if (hit) {
          lastBoundaryEndOffset = byteOffset + lineByteLength;
          hasPreservedSegment = hit.hasPreservedSegment;
        }
      }
      byteOffset += lineByteLength;
    }
    return { offset: lastBoundaryEndOffset, hasPreservedSegment };
  } finally {
    await fileHandle.close();
  }
}
async function verifyAndReadJsonlDelta(filePath, resumeOffset, lastLineBytes, maxSize) {
  const fd = await openTranscriptNoFollow(filePath);
  try {
    const st = await fd.stat();
    if (!st.isFile()) {
      return null;
    }
    const len = lastLineBytes.length;
    let boundaryOk = false;
    if (len === 0 && resumeOffset === 0) {
      boundaryOk = true;
    } else if (len > 0 && resumeOffset >= len && st.size >= resumeOffset) {
      const bbuf = Buffer.allocUnsafe(len);
      const { bytesRead } = await fd.read(bbuf, 0, len, resumeOffset - len);
      boundaryOk = bytesRead === len && bbuf.equals(lastLineBytes);
    }
    let deltaLines = [];
    let bytesConsumed = 0;
    if (boundaryOk && st.size > resumeOffset && st.size <= maxSize) {
      const want = st.size - resumeOffset;
      const dbuf = Buffer.allocUnsafe(want);
      let totalRead = 0;
      while (totalRead < want) {
        const { bytesRead } = await fd.read(
          dbuf,
          totalRead,
          want - totalRead,
          resumeOffset + totalRead
        );
        if (bytesRead === 0) {
          break;
        }
        totalRead += bytesRead;
      }
      const lastNl = totalRead > 0 ? dbuf.lastIndexOf(10, totalRead - 1) : -1;
      if (lastNl !== -1) {
        bytesConsumed = lastNl + 1;
        deltaLines = dbuf.toString("utf-8", 0, bytesConsumed).split("\n").filter((l) => l.length > 0);
      }
    }
    return {
      ino: st.ino,
      mtimeMs: st.mtimeMs,
      size: st.size,
      boundaryOk,
      deltaLines,
      bytesConsumed
    };
  } finally {
    await fd.close();
  }
}
async function readLinesFromOffset(filePath, startOffset) {
  const rl = node_readline.createInterface({
    input: node_fs.createReadStream(filePath, {
      encoding: "utf-8",
      start: startOffset
    }),
    crlfDelay: Infinity
  });
  const lines = [];
  for await (const line of rl) {
    if (line.trim()) {
      lines.push(line);
    }
  }
  return lines;
}
async function readLinesFromTail(filePath, fileSize, byteCount) {
  const startOffset = Math.max(0, fileSize - byteCount);
  const lines = await readLinesFromOffset(filePath, startOffset);
  if (startOffset > 0 && lines.length > 0) {
    lines.shift();
  }
  return lines;
}
async function extractInferenceLogIds(transcriptPath) {
  var _a2;
  const fileStat = await promises.lstat(transcriptPath).catch((err) => {
    const code = err == null ? void 0 : err.code;
    if (code === "ENOENT" || code === "ENOTDIR") {
      return null;
    }
    throw err;
  });
  if (fileStat === null) {
    return [];
  }
  if (!fileStat.isFile()) {
    throw new Error(
      `Refusing to read non-regular transcript path: ${transcriptPath}`
    );
  }
  const MAX_INFERENCE_LOG_IDS = 1e5;
  const ids = /* @__PURE__ */ new Set();
  const rl = node_readline.createInterface({
    input: node_fs.createReadStream(transcriptPath, { encoding: "utf-8" }),
    crlfDelay: Infinity
  });
  for await (const line of rl) {
    if (!line.includes("msg_")) {
      continue;
    }
    try {
      const parsed = JSON.parse(line);
      const id = (_a2 = parsed.message) == null ? void 0 : _a2.id;
      if (parsed.type === "assistant" && (id == null ? void 0 : id.startsWith("msg_"))) {
        ids.add(id);
      }
    } catch {
    }
    if (ids.size >= MAX_INFERENCE_LOG_IDS) {
      rl.close();
      break;
    }
  }
  return Array.from(ids);
}
async function readTranscriptLines(transcriptPath) {
  const fileStat = await promises.lstat(transcriptPath);
  if (!fileStat.isFile()) {
    throw new Error(
      `Refusing to read non-regular transcript path: ${transcriptPath}`
    );
  }
  let fileSize = fileStat.size;
  const statFields = { fileSize, ino: fileStat.ino, mtimeMs: fileStat.mtimeMs };
  if (fileSize <= LARGE_TRANSCRIPT_THRESHOLD) {
    const r = await verifyAndReadJsonlDelta(
      transcriptPath,
      0,
      EMPTY_BOUNDARY,
      LARGE_TRANSCRIPT_THRESHOLD
    );
    if (r === null) {
      throw new Error(
        `Refusing to read non-regular transcript path: ${transcriptPath}`
      );
    }
    if (r.size <= LARGE_TRANSCRIPT_THRESHOLD) {
      return {
        lines: r.deltaLines,
        strategy: "none",
        bytesConsumed: r.bytesConsumed,
        fileSize: r.size,
        ino: r.ino,
        mtimeMs: r.mtimeMs
      };
    }
    fileSize = r.size;
  }
  const { offset: boundaryOffset, hasPreservedSegment } = await findLastCompactBoundaryOffset(transcriptPath, fileSize);
  if (boundaryOffset > 0 && hasPreservedSegment) {
    const lines2 = await readLinesFromOffset(transcriptPath, 0);
    return {
      lines: lines2,
      strategy: "preserved",
      bytesConsumed: fileSize,
      ...statFields
    };
  }
  if (boundaryOffset > 0) {
    const remainingBytes = fileSize - boundaryOffset;
    if (remainingBytes < LARGE_TRANSCRIPT_THRESHOLD) {
      const lines3 = await readLinesFromOffset(transcriptPath, boundaryOffset);
      return {
        lines: lines3,
        strategy: "compaction",
        bytesConsumed: fileSize,
        ...statFields
      };
    }
    const lines2 = await readLinesFromTail(
      transcriptPath,
      fileSize,
      TRUNCATED_READ_SIZE
    );
    return { lines: lines2, strategy: "tail", bytesConsumed: fileSize, ...statFields };
  }
  const lines = await readLinesFromTail(
    transcriptPath,
    fileSize,
    TRUNCATED_READ_SIZE
  );
  return { lines, strategy: "tail", bytesConsumed: fileSize, ...statFields };
}
function filterTranscriptAfterCompact(lines, onParseError, opts) {
  const dropPreBoundary = (opts == null ? void 0 : opts.dropPreBoundary) ?? true;
  const parsed = lines.flatMap((line) => {
    if (line.length === 0) {
      return [];
    }
    try {
      return [JSON.parse(line)];
    } catch {
      onParseError == null ? void 0 : onParseError(line);
      return [];
    }
  });
  const { absoluteLastBoundaryIdx, lastSeg, lastSegBoundaryIdx } = parsed.reduce(
    (acc, r, i) => {
      var _a2;
      if (r.type !== "system" || r.subtype !== "compact_boundary") {
        return acc;
      }
      const seg = (_a2 = r.compactMetadata) == null ? void 0 : _a2.preservedSegment;
      return seg ? { absoluteLastBoundaryIdx: i, lastSeg: seg, lastSegBoundaryIdx: i } : { ...acc, absoluteLastBoundaryIdx: i };
    },
    {
      absoluteLastBoundaryIdx: -1,
      lastSeg: void 0,
      lastSegBoundaryIdx: -1
    }
  );
  const segIsLive = lastSeg && lastSegBoundaryIdx === absoluteLastBoundaryIdx;
  const walkPreservedChain = (seg) => {
    const byUuid = new Map(
      parsed.map((r, i) => [r.uuid, { parentUuid: r.parentUuid, idx: i }])
    );
    const collected = /* @__PURE__ */ new Set();
    const seen = /* @__PURE__ */ new Set();
    let cur = seg.tailUuid;
    while (cur && !seen.has(cur)) {
      seen.add(cur);
      const entry = byUuid.get(cur);
      if (!entry || entry.idx >= absoluteLastBoundaryIdx) {
        break;
      }
      collected.add(cur);
      if (cur === seg.headUuid) {
        return collected;
      }
      cur = entry.parentUuid ?? void 0;
    }
    return /* @__PURE__ */ new Set();
  };
  const preservedUuids = segIsLive && lastSeg ? walkPreservedChain(lastSeg) : /* @__PURE__ */ new Set();
  const startIdx = dropPreBoundary && absoluteLastBoundaryIdx >= 0 ? absoluteLastBoundaryIdx + 1 : 0;
  return parsed.filter((r, i) => {
    const include = i >= startIdx || r.uuid && preservedUuids.has(r.uuid);
    if (!include) {
      return false;
    }
    if (r.isCompactSummary || r.isVisibleInTranscriptOnly) {
      return false;
    }
    return r.type !== void 0 && SDK_MESSAGE_TYPES.has(r.type);
  });
}
const LAST_LINE_BYTES_CAP = 64 * 1024;
function lastLineBytesOf(lines) {
  if (lines.length === 0) {
    return Buffer.alloc(0);
  }
  const buf = Buffer.from(lines[lines.length - 1] + "\n", "utf-8");
  return buf.length > LAST_LINE_BYTES_CAP ? Buffer.from(buf.subarray(buf.length - LAST_LINE_BYTES_CAP)) : buf;
}
async function readAndParseTranscript(transcriptPath, onParseError) {
  const { lines, strategy, ino, mtimeMs, bytesConsumed } = await readTranscriptLines(transcriptPath);
  const parsed = filterTranscriptAfterCompact(lines, onParseError, {
    dropPreBoundary: strategy !== "none"
  });
  return {
    parsed,
    strategy,
    ino,
    mtimeMs,
    bytesConsumed,
    lastLineBytes: lastLineBytesOf(lines)
  };
}
function postToParent(port, message) {
  try {
    port.postMessage(message);
  } catch {
  }
}
const SNIPPET_RADIUS = 80;
const SCAN_CONCURRENCY = 4;
function buildPrefilter(needle) {
  const tokens = needle.split(/\s+/).filter(Boolean);
  if (tokens.length === 0) {
    return null;
  }
  for (const t of tokens) {
    if (/["\\]|[^\x20-\x7e]/.test(t)) {
      return null;
    }
  }
  const regexes = tokens.map(
    (t) => new RegExp(t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "iu")
  );
  return (line) => {
    if (regexes.every((re) => re.test(line))) {
      return true;
    }
    if (!line.includes("İ")) {
      return false;
    }
    const lower = line.toLowerCase();
    return tokens.every((tok) => lower.includes(tok));
  };
}
function extractText(content) {
  if (typeof content === "string") {
    return content;
  }
  if (Array.isArray(content)) {
    let out = "";
    for (const block of content) {
      if (block && typeof block === "object" && block.type === "text" && typeof block.text === "string") {
        out += block.text + " ";
      }
    }
    return out;
  }
  return "";
}
function makeSnippet(text, idx, qLen) {
  const start = Math.max(0, idx - SNIPPET_RADIUS);
  const end = Math.min(text.length, idx + qLen + SNIPPET_RADIUS);
  const slice = text.slice(start, end).trim();
  return (start > 0 ? "…" : "") + slice + (end < text.length ? "…" : "");
}
async function scanFile(session, needle, messageTypes, prefilter) {
  var _a2;
  let snippet = null;
  const stream = node_fs.createReadStream(session.transcriptPath, { encoding: "utf8" });
  const rl = node_readline.createInterface({ input: stream, crlfDelay: Infinity });
  try {
    for await (const line of rl) {
      if (!line) {
        continue;
      }
      if (prefilter && !prefilter(line)) {
        continue;
      }
      let parsed;
      try {
        parsed = JSON.parse(line);
      } catch {
        continue;
      }
      if (!parsed.type || !messageTypes.has(parsed.type)) {
        continue;
      }
      const text = extractText((_a2 = parsed.message) == null ? void 0 : _a2.content);
      if (!text) {
        continue;
      }
      const normalized = text.replace(/\s+/g, " ");
      const idx = normalized.toLowerCase().indexOf(needle);
      if (idx === -1) {
        continue;
      }
      snippet = makeSnippet(normalized, idx, needle.length);
      break;
    }
  } finally {
    rl.close();
    stream.destroy();
  }
  if (snippet === null) {
    return null;
  }
  return {
    sessionId: session.sessionId,
    snippet,
    lastActivityAt: session.lastActivityAt
  };
}
async function handleSearch(port, req) {
  const needle = req.query.replace(/\s+/g, " ").trim().toLowerCase();
  const messageTypes = new Set(req.messageTypes);
  const prefilter = buildPrefilter(needle);
  const hits = [];
  const inputOrder = new Map(req.sessions.map((s, i) => [s.sessionId, i]));
  let nextIndex = 0;
  const inFlight = /* @__PURE__ */ new Set();
  const launchNext = () => {
    if (hits.length >= req.limit || nextIndex >= req.sessions.length) {
      return;
    }
    const session = req.sessions[nextIndex++];
    const p = scanFile(session, needle, messageTypes, prefilter).then((hit) => {
      if (hit) {
        hits.push(hit);
      }
    }).catch(() => {
    }).finally(() => {
      inFlight.delete(p);
      launchNext();
    });
    inFlight.add(p);
  };
  for (let i = 0; i < SCAN_CONCURRENCY; i++) {
    launchNext();
  }
  while (inFlight.size > 0) {
    await Promise.race(inFlight);
  }
  hits.sort(
    (a, b) => b.lastActivityAt - a.lastActivityAt || (inputOrder.get(a.sessionId) ?? 0) - (inputOrder.get(b.sessionId) ?? 0)
  );
  postToParent(port, {
    type: "result",
    requestId: req.requestId,
    hits: hits.slice(0, req.limit)
  });
}
async function handleReadTranscript(port, req) {
  const result = await readAndParseTranscript(
    req.transcriptPath,
    (line) => console.warn(`Failed to parse transcript line: ${line.slice(0, 200)}`)
  );
  postToParent(port, { type: "transcript", requestId: req.requestId, result });
}
async function handleExtractInferenceLogIds(port, req) {
  const ids = await extractInferenceLogIds(req.transcriptPath);
  postToParent(port, {
    type: "inferenceLogIds",
    requestId: req.requestId,
    ids
  });
}
function dispatch(port, data) {
  switch (data.type) {
    case "search":
      return handleSearch(port, data);
    case "readTranscript":
      return handleReadTranscript(port, data);
    case "extractInferenceLogIds":
      return handleExtractInferenceLogIds(port, data);
    default:
      return Promise.resolve();
  }
}
(_a = process.parentPort) == null ? void 0 : _a.once("message", (e) => {
  var _a2;
  if (e.data.type !== "init" || !((_a2 = e.ports) == null ? void 0 : _a2[0])) {
    process.exit(1);
  }
  const port = e.ports[0];
  port.on("message", (event) => {
    const data = event.data;
    dispatch(port, data).catch((error) => {
      const message = error instanceof Error ? error.message : "Unknown error";
      postToParent(port, {
        type: "error",
        requestId: data.requestId,
        message
      });
    });
  });
  port.start();
});
process.on("SIGTERM", () => process.exit(0));
process.on("SIGINT", () => process.exit(0));
const _test = {
  buildPrefilter,
  scanFile,
  handleSearch,
  handleReadTranscript,
  handleExtractInferenceLogIds,
  SCAN_CONCURRENCY
};
exports._test = _test;
