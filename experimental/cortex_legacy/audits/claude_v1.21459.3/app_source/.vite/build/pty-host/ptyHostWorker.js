"use strict";
Object.defineProperty(exports, Symbol.toStringTag, { value: "Module" });
const node_child_process = require("node:child_process");
const nodePty = require("node-pty");
class PtyHostWorker {
  constructor(post) {
    this.post = post;
    this.ptys = /* @__PURE__ */ new Map();
  }
  handle(request) {
    var _a, _b;
    switch (request.type) {
      case "spawn":
        this.spawn(request);
        return;
      case "write":
        try {
          (_a = this.ptys.get(request.ptyId)) == null ? void 0 : _a.write(request.data);
        } catch {
        }
        return;
      case "resize":
        try {
          (_b = this.ptys.get(request.ptyId)) == null ? void 0 : _b.resize(request.cols, request.rows);
        } catch {
        }
        return;
      case "kill": {
        const pty = this.ptys.get(request.ptyId);
        if (!pty) {
          return;
        }
        this.ptys.delete(request.ptyId);
        try {
          pty.kill();
        } catch {
        }
        this.post({ type: "exit", ptyId: request.ptyId, exitCode: 0 });
        return;
      }
      case "shutdown":
        this.killAllPtys();
        return;
      default:
        return request;
    }
  }
  /**
   * Last-resort cleanup when this process is told to exit: main's quit
   * handler tree-kills PTYs whose pid it knows, but a kill for a pty whose
   * spawn ack is still in flight only exists as a queued port message that
   * dies with us. Windows gets a taskkill tree sweep (SIGHUP-ignoring
   * supervisors survive a bare kill); POSIX shells exit when the PTY master
   * closes, and main's pgrep walk already covered known pids.
   */
  killAllPtys() {
    const pids = [];
    for (const pty of this.ptys.values()) {
      {
        try {
          pty.kill();
        } catch {
        }
      }
    }
    if (pids.length > 0) {
      node_child_process.spawnSync(
        "taskkill",
        [...pids.flatMap((pid) => ["/pid", String(pid)]), "/T", "/F"],
        { windowsHide: true, timeout: 5e3 }
      );
    }
    this.ptys.clear();
  }
  spawn(request) {
    const { ptyId, file, args, opts } = request;
    let pty;
    try {
      pty = nodePty.spawn(file, args, {
        name: opts.name,
        cols: opts.cols,
        rows: opts.rows,
        cwd: opts.cwd,
        env: opts.env
      });
    } catch (error) {
      this.post({
        type: "spawn-error",
        ptyId,
        message: error instanceof Error ? error.message : String(error)
      });
      return;
    }
    this.ptys.set(ptyId, pty);
    let reportedPid = pty.pid;
    this.post({ type: "spawned", ptyId, pid: reportedPid });
    pty.onData((data) => {
      if (reportedPid <= 0 && pty.pid > 0) {
        reportedPid = pty.pid;
        this.post({ type: "spawned", ptyId, pid: reportedPid });
      }
      this.post({ type: "data", ptyId, data });
    });
    pty.onExit(({ exitCode }) => {
      this.ptys.delete(ptyId);
      this.post({ type: "exit", ptyId, exitCode });
    });
  }
}
if (process.parentPort !== void 0) {
  process.parentPort.once("message", (e) => {
    var _a;
    if (e.data.type !== "init" || !((_a = e.ports) == null ? void 0 : _a[0])) {
      process.exit(1);
    }
    const port = e.ports[0];
    const worker = new PtyHostWorker((message) => {
      try {
        port.postMessage(message);
      } catch {
      }
    });
    port.on("message", (event) => {
      const request = event.data;
      worker.handle(request);
      if (request.type === "shutdown") {
        process.exit(0);
      }
    });
    port.start();
    const shutdown = () => {
      worker.killAllPtys();
      process.exit(0);
    };
    process.on("SIGTERM", shutdown);
    process.on("SIGINT", shutdown);
  });
  process.on("unhandledRejection", (reason) => {
    console.warn(`[pty-host] unhandled rejection: ${String(reason)}`);
  });
}
const _test = { PtyHostWorker };
exports._test = _test;
