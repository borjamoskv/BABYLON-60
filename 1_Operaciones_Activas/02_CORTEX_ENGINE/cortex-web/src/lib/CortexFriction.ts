import * as fs from 'fs';
import * as path from 'path';

export class CortexFriction {
    static ping(componentId: string, type: 'RENDER' | 'API_HIT' | 'INTERACTION' = 'RENDER'): void {
        if (typeof window !== 'undefined') {
            console.log(`[CORTEX-TELEMETRY-CLIENT] ping: ${componentId} (${type})`);
            return;
        }
        try {
            const LEDGER_PATH = path.join(process.cwd(), '.cortex_ledger.json');
            let ledger: Record<string, any> = {};
            if (fs.existsSync(LEDGER_PATH)) {
                const data = fs.readFileSync(LEDGER_PATH, 'utf-8');
                ledger = JSON.parse(data);
            }
            ledger[componentId] = {
                componentId,
                timestamp: Date.now(),
                type
            };
            fs.writeFileSync(LEDGER_PATH, JSON.stringify(ledger, null, 2), 'utf-8');
        } catch (error) {
            console.error(`[CORTEX-TELEMETRY-ERROR] Could not register friction for ${componentId}.`, error);
        }
    }
}
