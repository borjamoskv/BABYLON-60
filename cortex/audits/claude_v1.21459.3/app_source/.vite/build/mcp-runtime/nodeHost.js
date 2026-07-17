#!/usr/bin/env node
"use strict";
const path = require("node:path");
const node_stream = require("node:stream");
const node_string_decoder = require("node:string_decoder");
const node_url = require("node:url");
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
const [entryPoint, ...args] = process.argv.slice(2);
let messagePort;
const rawStderrWrite = process.stderr.write.bind(process.stderr);
const stdoutDecoder = new node_string_decoder.StringDecoder("utf8");
const stderrDecoder = new node_string_decoder.StringDecoder("utf8");
function chunkToString(decoder, chunk) {
  return typeof chunk === "string" ? chunk : decoder.write(
    Buffer.from(chunk.buffer, chunk.byteOffset, chunk.byteLength)
  );
}
function postToParent(message) {
  try {
    messagePort == null ? void 0 : messagePort.postMessage(message);
  } catch (error) {
    try {
      rawStderrWrite(`[nodeHost] postToParent failed: ${String(error)}
`);
    } catch {
    }
  }
}
function reportFatal(kind, err) {
  const e = err instanceof Error ? err : new Error(String(err));
  postToParent({
    type: "fatal-error",
    kind,
    message: String(e.message),
    stack: typeof e.stack === "string" ? e.stack : void 0
  });
  console.error(`[nodeHost] ${kind}:`, e.message);
  setImmediate(() => process.exit(1));
}
process.on("uncaughtException", (err) => reportFatal("uncaughtException", err));
process.on(
  "unhandledRejection",
  (reason) => reportFatal("unhandledRejection", reason)
);
if (!entryPoint) {
  console.error("Error: No entry point specified");
  process.exit(1);
}
process.parentPort.once("message", (e) => {
  if (e.data.type !== "init" || !e.ports || !e.ports[0]) {
    console.error("Error: Expected init message with MessagePort");
    process.exit(1);
  }
  const port = e.ports[0];
  messagePort = port;
  const stdoutWrite = function(chunk, encodingOrCallback, callback) {
    const stdoutContent = chunkToString(stdoutDecoder, chunk);
    if (stdoutContent.length > 0) {
      postToParent({ type: "stdout", content: stdoutContent });
    }
    let cb;
    if (typeof encodingOrCallback === "function") {
      cb = encodingOrCallback;
    } else if (callback) {
      cb = callback;
    }
    if (cb) {
      process.nextTick(cb);
    }
    return true;
  };
  process.stdout.write = stdoutWrite;
  const originalStderrWrite = process.stderr.write.bind(process.stderr);
  const stderrWrite = function(chunk, encodingOrCallback, callback) {
    const stderrContent = chunkToString(stderrDecoder, chunk);
    if (stderrContent.length > 0) {
      postToParent({ type: "stderr", content: stderrContent });
    }
    if (typeof encodingOrCallback === "function") {
      return originalStderrWrite(chunk, encodingOrCallback);
    } else {
      return originalStderrWrite(chunk, encodingOrCallback, callback);
    }
  };
  process.stderr.write = stderrWrite;
  const stdinStream = new node_stream.Readable({
    read() {
    }
  });
  if (process.stdin) {
    const methods = [
      "read",
      "push",
      "unshift",
      "pause",
      "resume",
      "pipe",
      "unpipe",
      "on",
      "once",
      "removeListener",
      "removeAllListeners",
      "setEncoding",
      "destroy",
      "isPaused",
      "readableLength",
      "readable"
    ];
    for (const method of methods) {
      if (typeof stdinStream[method] === "function") {
        process.stdin[method] = stdinStream[method].bind(
          stdinStream
        );
      }
    }
    Object.defineProperty(process.stdin, "readableHighWaterMark", {
      get: () => stdinStream.readableHighWaterMark,
      configurable: true
    });
    Object.defineProperty(process.stdin, "readableLength", {
      get: () => stdinStream.readableLength,
      configurable: true
    });
    Object.defineProperty(process.stdin, "destroyed", {
      get: () => stdinStream.destroyed,
      configurable: true
    });
  }
  port.on("message", (event) => {
    if (event.data.type === "stdin") {
      stdinStream.push(event.data.data + "\n");
    }
  });
  port.start();
  process.argv = [
    process.platform === "win32" ? "node.exe" : "node",
    entryPoint,
    ...args
  ];
  try {
    const absolutePath = path__namespace.resolve(entryPoint);
    delete require.cache[absolutePath];
    import(node_url.pathToFileURL(absolutePath).toString()).catch((error) => {
      reportFatal("import-failed", error);
    });
  } catch (error) {
    reportFatal("import-failed", error);
  }
});
process.on("SIGTERM", () => {
  process.exit(0);
});
process.on("SIGINT", () => {
  process.exit(0);
});
