// @C5-REAL
import * as fs from "fs";
import * as path from "path";

// CORTEX-Persist: Telemetry Ledger
// Purpose: Record C5-REAL friction to prevent the Ouroboros Daemon from purging stable components.

const LEDGER_PATH = path.join(process.cwd(), ".cortex_ledger.json");

interface FrictionEvent {
  componentId: string;
  timestamp: number;
  type: "RENDER" | "API_HIT" | "INTERACTION";
}

export class CortexFriction {
  private static writeQueue: {
    componentId: string;
    type: FrictionEvent["type"];
  }[] = [];
  private static isProcessing = false;
  private static pingTimestamps: number[] = [];

  /**
   * Records a friction event for a component.
   * @param componentId Unique component identifier (e.g. "Layout.astro", "Engine.ts").
   * @param type Friction type (default: RENDER).
   */
  static ping(
    componentId: string,
    type: FrictionEvent["type"] = "RENDER",
  ): void {
    this.writeQueue.push({ componentId, type });
    this.processQueue();
  }

  /**
   * Processes the queue sequentially to prevent file I/O collisions.
   */
  private static async processQueue(): Promise<void> {
    if (this.isProcessing) return;
    this.isProcessing = true;

    while (this.writeQueue.length > 0) {
      const task = this.writeQueue.shift();
      if (!task) continue;

      const now = Date.now();
      this.pingTimestamps.push(now);
      // Keep only pings from the last 10 seconds to compute velocity
      this.pingTimestamps = this.pingTimestamps.filter((t) => now - t < 10000);

      try {
        let ledger: Record<string, FrictionEvent> = {};
        let ledgerSize = 0;

        if (fs.existsSync(LEDGER_PATH)) {
          const data = fs.readFileSync(LEDGER_PATH, "utf-8");
          ledger = JSON.parse(data);
          ledgerSize = data.length;
        }

        // Compute Reynolds Number: Re_c = (v * L) / (complexity * scale)
        const v = this.pingTimestamps.length / 10; // writes/second
        const L = ledgerSize; // ledger size in bytes
        const complexity = Math.max(1, Object.keys(ledger).length);
        const scale = 100;

        const Re_c = (v * L) / (complexity * scale);

        // If Reynolds number indicates turbulent flow (>= 12.5), trigger reactive throttle
        if (Re_c >= 12.5) {
          const delay = Math.min(150, Math.floor(Re_c * 2));
          await new Promise((resolve) => setTimeout(resolve, delay));
        }

        ledger[task.componentId] = {
          componentId: task.componentId,
          timestamp: Date.now(),
          type: task.type,
        };

        fs.writeFileSync(LEDGER_PATH, JSON.stringify(ledger, null, 2), "utf-8");
      } catch (error) {
        console.error(
          `[CORTEX-TELEMETRY-ERROR] Could not register friction for ${task.componentId}.`,
          error,
        );
      }
    }

    this.isProcessing = false;
  }

  /**
   * Returns the complete ledger for the Ouroboros Daemon to read.
   */
  static getLedger(): Record<string, FrictionEvent> {
    if (!fs.existsSync(LEDGER_PATH)) return {};
    try {
      return JSON.parse(fs.readFileSync(LEDGER_PATH, "utf-8"));
    } catch {
      return {};
    }
  }
}
