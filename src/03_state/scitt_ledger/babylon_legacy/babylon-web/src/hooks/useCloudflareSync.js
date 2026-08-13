// C5-REAL EXERGY CERTIFIED
import { useState, useEffect, useRef } from 'react';

export function useCloudflareSync() {
  const syncQueueRef = useRef([]);
  const [cloudSyncStatus, setCloudSyncStatus] = useState('IDLE');

  useEffect(() => {
    const intervalId = setInterval(async () => {
      if (syncQueueRef.current.length === 0) {
        setCloudSyncStatus('IDLE');
        return;
      }

      setCloudSyncStatus('SYNCING...');
      const batch = [...syncQueueRef.current];
      syncQueueRef.current = []; // clear queue immediately

      try {
        const res = await fetch('http://127.0.0.1:8787/seal', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ logs: batch })
        });
        if (res.ok) {
          setCloudSyncStatus(`SEALED (${batch.length})`);
          setTimeout(() => setCloudSyncStatus('IDLE'), 2000);
        } else {
          setCloudSyncStatus('ERROR: CLOUD');
          syncQueueRef.current = [...batch, ...syncQueueRef.current]; // restore failed items
        }
      } catch (err) {
        console.error("Cloudflare Notary Sync Error:", err);
        setCloudSyncStatus('OFFLINE');
        syncQueueRef.current = [...batch, ...syncQueueRef.current]; // restore on network error
      }
    }, 5000);

    return () => clearInterval(intervalId);
  }, []);

  const pushToSyncQueue = (item) => {
    syncQueueRef.current.push(item);
  };

  return { cloudSyncStatus, pushToSyncQueue };
}
