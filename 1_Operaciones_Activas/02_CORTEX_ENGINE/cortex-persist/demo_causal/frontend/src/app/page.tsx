'use client';
import { useEffect, useState } from 'react';

interface Evidence {
  generated_at: string;
  events_count: parseInt;
  replay_count: parseInt;
  initial_hash: string;
  final_hash: string;
  integrity_result: string;
  git_commit: string;
  hash_match: boolean;
}

interface Event {
  id: number;
  timestamp: string;
  type: string;
  actor: string;
  payload: any;
  parent_event: number;
  hash: string;
}

export default function ForensicDashboard() {
  const [evidence, setEvidence] = useState<Evidence | null>(null);
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const [evRes, evtsRes] = await Promise.all([
          fetch('http://localhost:8001/api/evidence'),
          fetch('http://localhost:8001/api/events?limit=25')
        ]);
        
        if (evRes.ok) setEvidence(await evRes.json());
        if (evtsRes.ok) setEvents(await evtsRes.json());
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  return (
    <div className="min-h-screen bg-[#0A0A0A] text-gray-300 font-sans p-8 selection:bg-[#2B3BE5] selection:text-white">
      <div className="max-w-5xl mx-auto space-y-12">
        {/* Header */}
        <header className="border-b border-gray-800 pb-6 flex items-end justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-white mb-2 uppercase flex items-center gap-3">
              <span className="w-3 h-3 rounded-full bg-[#2B3BE5] animate-pulse"></span>
              CORTEX-PERSIST
            </h1>
            <p className="text-sm text-gray-500 uppercase tracking-widest font-mono">Dependency Lineage Replay Verified</p>
          </div>
          <div className="text-right">
            <p className="text-xs text-gray-600 font-mono">MOSKV-1 APEX SINGULARITY</p>
            <p className="text-xs text-gray-600 font-mono">C5-REAL EXECUTION KERNEL</p>
          </div>
        </header>

        {loading ? (
          <div className="text-center py-20 font-mono text-[#2B3BE5]">AWAITING FORENSIC DATA...</div>
        ) : (
          <main className="space-y-12">
            
            {/* Evidence Block */}
            <section className="border border-gray-800 bg-[#111] p-6 rounded-sm relative overflow-hidden">
              <div className="absolute top-0 left-0 w-1 h-full bg-[#2B3BE5]"></div>
              <h2 className="text-xs uppercase tracking-widest text-gray-500 mb-6 font-mono">Runtime Evidence (Golden Artifact)</h2>
              
              {evidence ? (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                  <div>
                    <p className="text-xs text-gray-500 mb-1 uppercase">Replay Match</p>
                    <p className={`text-xl font-mono ${evidence.hash_match ? 'text-green-500' : 'text-red-500'}`}>
                      {evidence.hash_match ? 'TRUE' : 'FALSE'}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 mb-1 uppercase">Total Events</p>
                    <p className="text-xl font-mono text-white">{evidence.events_count}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 mb-1 uppercase">Git Commit</p>
                    <p className="text-xl font-mono text-white truncate" title={evidence.git_commit}>
                      {evidence.git_commit.substring(0, 8)}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 mb-1 uppercase">Integrity</p>
                    <p className="text-xl font-mono text-[#2B3BE5] uppercase">{evidence.integrity_result}</p>
                  </div>
                  <div className="col-span-2 md:col-span-4 mt-4 pt-4 border-t border-gray-800">
                    <p className="text-xs text-gray-500 mb-1 uppercase">Merkle Root (SHA3-256)</p>
                    <p className="text-xs font-mono text-gray-400 break-all">{evidence.final_hash}</p>
                  </div>
                </div>
              ) : (
                <div className="text-sm text-red-500 font-mono">Artifact not found. Run golden path generation.</div>
              )}
            </section>

            {/* Timeline */}
            <section>
              <h2 className="text-xs uppercase tracking-widest text-gray-500 mb-6 font-mono flex items-center justify-between">
                <span>Dependency Graph (Latest 25)</span>
                <span className="text-[#2B3BE5]">READ-ONLY</span>
              </h2>
              <div className="space-y-4">
                {events.map((evt) => (
                  <div key={evt.id} className="group flex gap-4 font-mono text-xs p-4 bg-[#111] border border-gray-800 hover:border-[#2B3BE5] transition-colors rounded-sm">
                    <div className="flex-shrink-0 text-gray-600 w-12 text-right">
                      {evt.id}
                    </div>
                    <div className="flex-1 space-y-2">
                      <div className="flex gap-4">
                        <span className="text-gray-400">{evt.timestamp}</span>
                        <span className="text-white">{evt.type}</span>
                        <span className="text-[#2B3BE5] uppercase">@{evt.actor}</span>
                        {evt.parent_event && (
                          <span className="text-gray-500 flex items-center gap-1">
                            <span>↳</span>
                            <span>depends on: {evt.parent_event}</span>
                          </span>
                        )}
                      </div>
                      <div className="text-gray-500 break-all">
                        {evt.hash}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </section>

          </main>
        )}
      </div>
    </div>
  );
}
