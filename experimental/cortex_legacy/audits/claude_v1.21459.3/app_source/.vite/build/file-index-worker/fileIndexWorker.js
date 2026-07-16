"use strict";
Object.defineProperty(exports, Symbol.toStringTag, { value: "Module" });
const path = require("node:path");
const SCORE_MATCH = 16;
const BONUS_BOUNDARY = 8;
const BONUS_CAMEL = 6;
const BONUS_CONSECUTIVE = 4;
const BONUS_FIRST_CHAR = 8;
const PENALTY_GAP_START = 3;
const PENALTY_GAP_EXTENSION = 1;
const TOP_LEVEL_CACHE_LIMIT = 100;
const MAX_QUERY_LEN = 64;
const CHUNK_MS = 4;
const posBuf = new Int32Array(MAX_QUERY_LEN);
class FileIndex {
  constructor() {
    this.paths = [];
    this.lowerPaths = [];
    this.charBits = new Int32Array(0);
    this.pathLens = new Uint16Array(0);
    this.topLevelCache = null;
    this.readyCount = 0;
  }
  /**
   * True once the async build has indexed every path. Callers can use this
   * to skip fallback paths that only make sense while the index is partial.
   * Returns false for a freshly-constructed (empty) index so cold-start
   * fallbacks still fire before buildAsync() has populated anything.
   */
  get isFullyBuilt() {
    return this.paths.length > 0 && this.readyCount === this.paths.length;
  }
  /**
   * Load paths from an array of strings.
   * Automatically deduplicates and filters empty strings.
   */
  loadFromFileList(fileList) {
    const seen = /* @__PURE__ */ new Set();
    const paths = [];
    for (const line of fileList) {
      if (line.length > 0 && !seen.has(line)) {
        seen.add(line);
        paths.push(line);
      }
    }
    this.buildIndex(paths);
  }
  /**
   * Async variant: yields to the event loop every few ms so large indexes
   * (270k+ files) don't block the main thread. Identical result to
   * loadFromFileList.
   *
   * Returns { queryable, done }:
   *   - queryable: resolves as soon as the first chunk is indexed (search
   *     returns partial results).
   *   - done: resolves when the entire index is built.
   */
  loadFromFileListAsync(fileList) {
    let markQueryable;
    const queryable = new Promise((resolve) => {
      markQueryable = resolve;
    });
    const done = this.buildAsync(fileList, markQueryable);
    return { queryable, done };
  }
  async buildAsync(fileList, markQueryable) {
    const seen = /* @__PURE__ */ new Set();
    const paths = [];
    let chunkStart = performance.now();
    for (let i = 0; i < fileList.length; i++) {
      const line = fileList[i];
      if (line.length > 0 && !seen.has(line)) {
        seen.add(line);
        paths.push(line);
      }
      if ((i & 255) === 255 && performance.now() - chunkStart > CHUNK_MS) {
        await yieldToEventLoop();
        chunkStart = performance.now();
      }
    }
    this.resetArrays(paths);
    chunkStart = performance.now();
    let firstChunk = true;
    for (let i = 0; i < paths.length; i++) {
      this.indexPath(i);
      if ((i & 255) === 255 && performance.now() - chunkStart > CHUNK_MS) {
        this.readyCount = i + 1;
        if (firstChunk) {
          markQueryable();
          firstChunk = false;
        }
        await yieldToEventLoop();
        chunkStart = performance.now();
      }
    }
    this.readyCount = paths.length;
    markQueryable();
  }
  buildIndex(paths) {
    this.resetArrays(paths);
    for (let i = 0; i < paths.length; i++) {
      this.indexPath(i);
    }
    this.readyCount = paths.length;
  }
  resetArrays(paths) {
    const n = paths.length;
    this.paths = paths;
    this.lowerPaths = Array.from({ length: n }, () => "");
    this.charBits = new Int32Array(n);
    this.pathLens = new Uint16Array(n);
    this.readyCount = 0;
    this.topLevelCache = computeTopLevelEntries(paths, TOP_LEVEL_CACHE_LIMIT);
  }
  // Precompute: lowercase, a–z bitmap, length. Bitmap gives O(1) rejection
  // of paths missing any needle letter.
  indexPath(i) {
    const lp = this.paths[i].toLowerCase();
    this.lowerPaths[i] = lp;
    const len = lp.length;
    this.pathLens[i] = len;
    let bits = 0;
    for (let j = 0; j < len; j++) {
      const c = lp.charCodeAt(j);
      if (c >= 97 && c <= 122) {
        bits |= 1 << c - 97;
      }
    }
    this.charBits[i] = bits;
  }
  /**
   * Search for files matching the query using fuzzy matching.
   * Returns top N results sorted by match score.
   */
  search(query, limit) {
    if (limit <= 0) {
      return [];
    }
    if (query.length === 0) {
      if (this.topLevelCache) {
        return this.topLevelCache.slice(0, limit);
      }
      return [];
    }
    const caseSensitive = query !== query.toLowerCase();
    const needle = caseSensitive ? query : query.toLowerCase();
    const nLen = Math.min(needle.length, MAX_QUERY_LEN);
    let needleBitmap = 0;
    const needleChars = Array.from({ length: nLen }, (_, j) => {
      const ch = needle.charAt(j);
      const cc = ch.charCodeAt(0);
      if (cc >= 97 && cc <= 122) {
        needleBitmap |= 1 << cc - 97;
      }
      return ch;
    });
    const scoreCeiling = nLen * (SCORE_MATCH + BONUS_BOUNDARY) + BONUS_FIRST_CHAR + 32;
    const topK = [];
    let threshold = -Infinity;
    const { paths, lowerPaths, charBits, pathLens, readyCount } = this;
    outer: for (let i = 0; i < readyCount; i++) {
      if ((charBits[i] & needleBitmap) !== needleBitmap) {
        continue;
      }
      const haystack = caseSensitive ? paths[i] : lowerPaths[i];
      let pos = haystack.indexOf(needleChars[0]);
      if (pos === -1) {
        continue;
      }
      posBuf[0] = pos;
      let gapPenalty = 0;
      let consecBonus = 0;
      let prev = pos;
      for (let j = 1; j < nLen; j++) {
        pos = haystack.indexOf(needleChars[j], prev + 1);
        if (pos === -1) {
          continue outer;
        }
        posBuf[j] = pos;
        const gap = pos - prev - 1;
        if (gap === 0) {
          consecBonus += BONUS_CONSECUTIVE;
        } else {
          gapPenalty += PENALTY_GAP_START + gap * PENALTY_GAP_EXTENSION;
        }
        prev = pos;
      }
      if (topK.length === limit && scoreCeiling + consecBonus - gapPenalty <= threshold) {
        continue;
      }
      const path2 = paths[i];
      const hLen = pathLens[i];
      let score = nLen * SCORE_MATCH + consecBonus - gapPenalty;
      score += scoreBonusAt(path2, posBuf[0], true);
      for (let j = 1; j < nLen; j++) {
        score += scoreBonusAt(path2, posBuf[j], false);
      }
      score += Math.max(0, 32 - (hLen >> 2));
      if (topK.length < limit) {
        topK.push({
          path: path2,
          fuzzScore: score,
          positions: Array.from(posBuf.subarray(0, nLen))
        });
        if (topK.length === limit) {
          topK.sort((a, b) => a.fuzzScore - b.fuzzScore);
          threshold = topK[0].fuzzScore;
        }
      } else if (score > threshold) {
        let lo = 0;
        let hi = topK.length;
        while (lo < hi) {
          const mid = lo + hi >> 1;
          if (topK[mid].fuzzScore < score) {
            lo = mid + 1;
          } else {
            hi = mid;
          }
        }
        topK.splice(lo, 0, {
          path: path2,
          fuzzScore: score,
          positions: Array.from(posBuf.subarray(0, nLen))
        });
        topK.shift();
        threshold = topK[0].fuzzScore;
      }
    }
    topK.sort((a, b) => b.fuzzScore - a.fuzzScore);
    const denom = Math.max(topK.length, 1);
    return topK.map(({ path: path2, positions }, i) => {
      const positionScore = i / denom;
      const finalScore = path2.includes("test") ? Math.min(positionScore * 1.05, 1) : positionScore;
      return { path: path2, score: finalScore, positions };
    });
  }
}
function scoreBonusAt(path2, pos, first) {
  if (pos === 0) {
    return first ? BONUS_FIRST_CHAR : 0;
  }
  const prevCh = path2.charCodeAt(pos - 1);
  if (isBoundary(prevCh)) {
    return BONUS_BOUNDARY;
  }
  if (isLower(prevCh) && isUpper(path2.charCodeAt(pos))) {
    return BONUS_CAMEL;
  }
  return 0;
}
function isBoundary(code) {
  return code === 47 || // /
  code === 92 || // \
  code === 45 || // -
  code === 95 || // _
  code === 46 || // .
  code === 32;
}
function isLower(code) {
  return code >= 97 && code <= 122;
}
function isUpper(code) {
  return code >= 65 && code <= 90;
}
function yieldToEventLoop() {
  return new Promise((resolve) => setImmediate(resolve));
}
function computeTopLevelEntries(paths, limit) {
  const topLevel = /* @__PURE__ */ new Set();
  for (const p of paths) {
    let end = p.length;
    for (let i = 0; i < p.length; i++) {
      const c = p.charCodeAt(i);
      if (c === 47 || c === 92) {
        end = i;
        break;
      }
    }
    const segment = p.slice(0, end);
    if (segment.length > 0) {
      topLevel.add(segment);
      if (topLevel.size >= limit) {
        break;
      }
    }
  }
  const sorted = Array.from(topLevel);
  sorted.sort((a, b) => {
    const lenDiff = a.length - b.length;
    if (lenDiff !== 0) {
      return lenDiff;
    }
    return a < b ? -1 : a > b ? 1 : 0;
  });
  return sorted.slice(0, limit).map((path2) => ({ path: path2, score: 0, positions: [] }));
}
class FileIndexHost {
  constructor() {
    this.entries = [];
    this.pathToFile = /* @__PURE__ */ new Map();
    this.index = null;
  }
  /** Drop all state (focused cwd changed). */
  clear() {
    this.entries = [];
    this.pathToFile = /* @__PURE__ */ new Map();
    this.index = null;
  }
  /** Replace the file list with pre-parsed entries (SSH / BFS listings). */
  setEntries(files) {
    this.commit(files);
  }
  /** Replace the file list from raw `git ls-files` stdout(s): files + derived
   *  parent-directory entries (parents first, deduped), each repo namespaced
   *  under its prefix. */
  setGitListing(cwd, repos) {
    const seen = /* @__PURE__ */ new Set();
    const files = [];
    const push = (name, relativePath, isDirectory) => {
      seen.add(relativePath);
      files.push({
        name,
        relativePath,
        fullPath: path.join(cwd, relativePath),
        isDirectory
      });
    };
    for (const { prefix, stdout } of repos) {
      if (prefix.length > 0 && !seen.has(prefix)) {
        push(prefix, prefix, true);
      }
      for (const line of stdout.split("\n")) {
        if (line.length === 0) {
          continue;
        }
        const relativePath = prefix.length > 0 ? `${prefix}/${line}` : line;
        const parts = relativePath.split("/");
        for (let i = 1; i < parts.length; i++) {
          const dirPath = parts.slice(0, i).join("/");
          if (!seen.has(dirPath)) {
            push(parts[i - 1], dirPath, true);
          }
        }
        if (!seen.has(relativePath)) {
          push(parts[parts.length - 1], relativePath, false);
        }
      }
    }
    this.commit(files);
  }
  /** Bounded snapshot of the current file list (listProjectFiles IPC). */
  list(limit) {
    return this.entries.slice(0, limit);
  }
  /** Fuzzy-rank over the full file list. */
  search(query, limit) {
    const matches = [];
    if (this.index) {
      for (const { path: relativePath, positions } of this.index.search(
        query,
        limit
      )) {
        const file = this.pathToFile.get(relativePath);
        if (file) {
          matches.push({ ...file, positions: Array.from(positions) });
        }
      }
    }
    return matches;
  }
  commit(files) {
    const pathToFile = /* @__PURE__ */ new Map();
    const relativePaths = files.map((f) => {
      pathToFile.set(f.relativePath, f);
      return f.relativePath;
    });
    try {
      const index = new FileIndex();
      index.loadFromFileList(relativePaths);
      this.entries = files;
      this.pathToFile = pathToFile;
      this.index = index;
    } catch (error) {
      console.error("[file-index] FileIndex build failed:", error);
      this.clear();
    }
  }
}
if (process.parentPort !== void 0) {
  process.parentPort.once("message", (e) => {
    var _a;
    if (e.data.type !== "init" || !((_a = e.ports) == null ? void 0 : _a[0])) {
      process.exit(1);
    }
    const host = new FileIndexHost();
    const port = e.ports[0];
    const post = (message) => {
      try {
        port.postMessage(message);
      } catch {
      }
    };
    const handle = (request) => {
      switch (request.type) {
        case "clear":
          return host.clear();
        case "set-entries":
          host.setEntries(request.files);
          break;
        case "set-git-listing":
          host.setGitListing(request.cwd, request.repos);
          break;
        case "search":
          return post({
            type: "search-result",
            requestId: request.requestId,
            results: host.search(request.query, request.limit)
          });
        case "list":
          return post({
            type: "list-result",
            requestId: request.requestId,
            files: host.list(request.limit)
          });
        default:
          return request;
      }
      post({ type: "set-result", requestId: request.requestId });
    };
    port.on("message", (event) => {
      const request = event.data;
      try {
        handle(request);
      } catch (error) {
        if (request.type !== "clear") {
          post({
            type: "error",
            requestId: request.requestId,
            message: error instanceof Error ? error.message : "Unknown error"
          });
        }
      }
    });
    port.start();
  });
  process.on("SIGTERM", () => process.exit(0));
  process.on("SIGINT", () => process.exit(0));
}
exports.FileIndexHost = FileIndexHost;
