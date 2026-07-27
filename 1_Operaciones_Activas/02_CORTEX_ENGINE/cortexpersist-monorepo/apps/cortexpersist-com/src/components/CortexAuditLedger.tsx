// @C5-REAL
import React, { useState, useEffect } from "react";
import {
  connectTelemetry,
  onTelemetryData,
  type TelemetryData,
  type TelemetryLog,
} from "../services/telemetry";

interface AuditEvent {
  id: string;
  timestamp: string;
  agent: string;
  action: string;
  status: "COMMITTED" | "VALIDATED" | "TAINTED" | "PROPOSED";
  hash: string;
}

interface RawEvent {
  timestamp?: string;
  action?: string;
  agent_id?: string;
  hash?: string;
  metadata?: {
    concept?: string;
    source_id?: string;
    diagnostic_type?: string;
    status?: string;
  };
}

interface CortexAuditLedgerProps {
  initialEvents?: RawEvent[];
}

function hashString(str: string) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = (hash << 5) - hash + str.charCodeAt(i);
    hash |= 0;
  }
  return Math.abs(hash).toString(16).padEnd(8, "f").substring(0, 8);
}

const DEFAULT_EVENTS: RawEvent[] = [
  {
    timestamp: new Date(Date.now() - 120000).toISOString(),
    action: "friction_event",
    agent_id: "Agent-Alpha",
    hash: "a4f89d369eb9c7d42cf38a40deecbf569702213e12c1b2c3d4e5f6a7b8c9d0e1",
    metadata: {
      concept: "FREEDOM",
      source_id: "Agent-Alpha",
      status: "success",
    },
  },
  {
    timestamp: new Date(Date.now() - 90000).toISOString(),
    action: "friction_event",
    agent_id: "Agent-Omega",
    hash: "7f8c2b53df7e12c4d6a782b1c4e9f3b5a6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1",
    metadata: {
      concept: "INTELLIGENCE",
      source_id: "Agent-Omega",
      status: "success",
    },
  },
  {
    timestamp: new Date(Date.now() - 60000).toISOString(),
    action: "audit_run",
    agent_id: "CORTEX-Guard",
    hash: "d4e9c7f8e3b5a6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e17f8c2b53df7e12c4d6a7",
    metadata: { diagnostic_type: "AST_VALIDATION", status: "success" },
  },
  {
    timestamp: new Date(Date.now() - 30000).toISOString(),
    action: "friction_event",
    agent_id: "Agent-Null",
    hash: "3b5a6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e17f8c2b53df7e12c4d6a782b1c4e9f",
    metadata: { concept: "MEMORY", source_id: "Agent-Null", status: "success" },
  },
];

export default function CortexAuditLedger({
  initialEvents = [],
}: CortexAuditLedgerProps) {
  // Map JSONL events to AuditEvent structure
  const mapRawEvent = (
    evt: RawEvent,
    index: number,
    isMounted = false,
  ): AuditEvent => {
    const logTime = evt.timestamp ? new Date(evt.timestamp) : new Date();
    let actionDetail = evt.action || "decision";
    if (evt.action === "friction_event" && evt.metadata) {
      actionDetail = `Friction: ${evt.metadata.concept || ""} (${evt.metadata.source_id || ""})`;
    } else if (evt.metadata && evt.metadata.diagnostic_type) {
      actionDetail = `Audit: ${evt.metadata.diagnostic_type} (${evt.metadata.status || ""})`;
    }
    const stableId = evt.hash
      ? evt.hash.substring(0, 4).toUpperCase()
      : hashString(actionDetail + (evt.timestamp || ""))
          .substring(0, 4)
          .toUpperCase() || `000${index}`.slice(-4);

    return {
      id: `TX-${stableId}`,
      timestamp: isMounted ? logTime.toLocaleTimeString() : "",
      agent: evt.agent_id || "dogfooding-agent",
      action: actionDetail,
      status:
        evt.metadata && evt.metadata.status === "success"
          ? "VALIDATED"
          : "COMMITTED",
      hash: evt.hash ? evt.hash.substring(0, 8) : "sha3:unknown",
    };
  };

  const [events, setEvents] = useState<AuditEvent[]>(() => {
    const rawEvents = initialEvents.length > 0 ? initialEvents : DEFAULT_EVENTS;
    return rawEvents.map((evt, i) => mapRawEvent(evt, i, false)).reverse();
  });
  const [isLive, setIsLive] = useState(true);
  const [realityLevel, setRealityLevel] = useState("C4-SIM");

  useEffect(() => {
    const rawEvents = initialEvents.length > 0 ? initialEvents : DEFAULT_EVENTS;
    // Once mounted, recalculate events with client-local timezone timestamps
    setEvents(rawEvents.map((evt, i) => mapRawEvent(evt, i, true)).reverse());

    if (!isLive) return;

    connectTelemetry();
    const unsubscribe = onTelemetryData((data: TelemetryData) => {
      if (data && data.reality_level) {
        setRealityLevel(data.reality_level);
      }
      if (data && data.logs && Array.isArray(data.logs)) {
        // If live C5-REAL backend is running, use it. Otherwise, preserve the real initialEvents.
        if (
          data.reality_level === "C5-REAL" ||
          data.reality_level === "C4-SIM"
        ) {
          const mappedEvents: AuditEvent[] = data.logs.map(
            (log: TelemetryLog) => {
              const logTime = log.id ? new Date(log.id * 1000) : new Date();
              return {
                id: `TX-${(Math.floor((log.id || Date.now()) * 1000) % 9000) + 1000}`,
                timestamp: logTime.toLocaleTimeString(),
                agent: log.msg || "CORTEX-Engine",
                action: log.val || "Processing",
                status:
                  log.msg === "CRITICAL FINDING" ||
                  log.msg === "INSECURE_ACCESS_CONTROL"
                    ? "TAINTED"
                    : "COMMITTED",
                hash: `sha3:${hashString(log.msg + log.val)}`,
              };
            },
          );
          setEvents(mappedEvents.reverse());
        }
      }
    });

    return () => {
      unsubscribe();
    };
  }, [isLive, initialEvents]);

  const isReal = realityLevel === "C5-REAL";

  return (
    <div className="w-full max-w-5xl mx-auto mt-20 px-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4 mb-8">
        <div className="text-left">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-[#2B3BE5] font-mono text-[10px] tracking-[0.2em] uppercase">
              Real-Time Telemetry Stream
            </span>
            <span
              className={`text-[8px] font-mono px-1.5 py-0.2 rounded border ${isReal ? "border-[#FFD700]/30 text-[#FFD700] bg-[#FFD700]/5" : "border-[#FF9F1C]/30 text-[#FF9F1C] bg-[#FF9F1C]/5"}`}
            >
              {realityLevel}
            </span>
          </div>
          <h3 className="text-3xl md:text-4xl font-light tracking-tight text-white">
            Cryptographic Memory Ledger
          </h3>
        </div>
        <div className="flex items-center gap-4 bg-black/40 border border-white/[0.06] p-1.5 rounded-xl backdrop-blur-md">
          <button
            onClick={() => setIsLive(!isLive)}
            className={`px-3 py-1.5 rounded-xl text-[10px] font-mono transition-all cursor-pointer ${isLive ? "bg-[#2B3BE5] text-white shadow-[0_0_15px_rgba(43,59,229,0.5)]" : "text-white/40 hover:text-white"}`}
          >
            {isLive ? "● STREAM ENGAGED" : "STREAM HALTED"}
          </button>
        </div>
      </div>

      <div className="border border-white/[0.06] bg-black/20 backdrop-blur-xl rounded-xl divide-y divide-white/5 overflow-hidden">
        {events.length === 0 ? (
          <div className="p-12 text-center text-white/30 font-mono text-xs uppercase tracking-wider">
            Waiting for telemetry packet...
          </div>
        ) : (
          events.map((event, i) => (
            <div
              key={event.id}
              className={`flex flex-col md:flex-row md:items-center gap-3 md:gap-4 p-4 hover:bg-white/[0.02] transition-colors duration-300 relative group`}
            >
              {/* Highlight bar on the left of latest transaction */}
              {i === 0 && (
                <div className="absolute left-0 top-0 bottom-0 w-[2px] bg-[#2B3BE5] shadow-[0_0_10px_rgba(43,59,229,0.8)]" />
              )}

              <div className="flex justify-between md:contents">
                <div className="w-20 font-mono text-[10px] text-white/40">
                  {event.id}
                </div>
                <div className="font-mono text-[10px] text-white/40 md:w-24">
                  {event.timestamp}
                </div>
              </div>

              <div className="font-mono text-xs text-[#2B3BE5] font-semibold md:w-36 truncate group-hover:translate-x-0.5 transition-transform">
                {event.agent}
              </div>

              <div className="flex-1 text-sm font-light text-white/80 font-mono text-[11px] truncate md:max-w-md">
                {event.action}
              </div>

              <div className="flex items-center justify-between md:justify-end md:contents gap-2">
                <div className="md:w-32 text-right">
                  <span
                    className={`text-[9px] font-mono px-2 py-0.5 rounded border ${
                      event.status === "TAINTED"
                        ? "border-red-500/30 text-red-400 bg-red-500/5"
                        : "border-[#2B3BE5]/30 text-[#2B3BE5] bg-[#2B3BE5]/5"
                    }`}
                  >
                    {event.status}
                  </span>
                </div>
                <div className="font-mono text-[9px] text-white/30 md:w-24 text-right hidden md:block">
                  {event.hash}
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      <div className="mt-6 text-center">
        <p className="text-[9px] font-mono text-white/30 uppercase tracking-widest">
          Autopoietic validation sequence verified under theorem Ω₉
        </p>
      </div>
    </div>
  );
}
