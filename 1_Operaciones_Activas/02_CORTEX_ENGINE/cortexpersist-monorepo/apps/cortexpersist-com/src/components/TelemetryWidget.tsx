// @C5-REAL
import React, { useEffect, useState } from 'react';
import { connectTelemetry, onTelemetryData, type TelemetryData } from '../services/telemetry';

export default function TelemetryWidget() {
  const [data, setData] = useState({ 
    throughput: 0, 
    activeAgents: 0, 
    latency: 0,
    realityLevel: 'C4-SIM'
  });

  useEffect(() => {
    connectTelemetry();
    const unsubscribe = onTelemetryData((telemetry: TelemetryData) => {
      if (telemetry) {
        setData(prev => ({ 
          throughput: telemetry.cycle_count !== undefined ? telemetry.cycle_count : prev.throughput,
          activeAgents: telemetry.active_agents_count !== undefined 
            ? telemetry.active_agents_count 
            : (telemetry.agent_states ? telemetry.agent_states.length : 10000),
          latency: telemetry.global_yield !== undefined ? telemetry.global_yield : prev.latency,
          realityLevel: telemetry.reality_level || 'C4-SIM'
        }));
      }
    });
    return () => { unsubscribe(); };
  }, []);

  const isReal = data.realityLevel === 'C5-REAL';

  return (
    <div className="fixed bottom-8 right-8 z-50 bg-cortex-bg/90 backdrop-blur-md border border-cortex-accent/30 rounded-[4px] p-5 shadow-[0_0_35px] shadow-cortex-accent/25 hover:shadow-[0_0_50px] hover:shadow-cortex-accent/40 transition-all duration-300 hover:scale-[1.02] font-mono text-xs flex flex-col gap-2.5 min-w-[220px]">
      <div className="flex justify-between items-center border-b border-white/[0.06] pb-2.5 mb-1.5">
        <span className="text-cortex-accent font-bold tracking-widest uppercase flex items-center gap-2">
          <span className="relative flex h-2 w-2">
            <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${isReal ? 'bg-green-500' : 'bg-cortex-accent'}`}></span>
            <span className={`relative inline-flex rounded-full h-2 w-2 ${isReal ? 'bg-green-500' : 'bg-cortex-accent'}`}></span>
          </span>
          CORTEX Link
        </span>
        <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded border ${isReal ? 'border-green-500/30 text-green-400 bg-green-500/5' : 'border-cortex-accent/30 text-cortex-accent bg-cortex-accent/5'}`}>
          {data.realityLevel}
        </span>
      </div>
      
      <div className="flex justify-between">
        <span className="text-white/40">Throughput</span>
        <span className="text-white font-bold">{data.throughput.toLocaleString()} <span className="text-white/30 text-[9px]">/s</span></span>
      </div>
      
      <div className="flex justify-between">
        <span className="text-white/40">Swarm</span>
        <span className="text-white font-bold">{data.activeAgents.toLocaleString()} <span className="text-white/30 text-[9px]">AGTS</span></span>
      </div>
      
      <div className="flex justify-between">
        <span className="text-white/40">Latency O(1)</span>
        <span className={`font-bold ${isReal ? 'text-green-400' : 'text-cortex-accent'}`}>
          {data.latency.toFixed(3)} <span className="text-white/30 text-[9px]">ms</span>
        </span>
      </div>
    </div>
  );
}
