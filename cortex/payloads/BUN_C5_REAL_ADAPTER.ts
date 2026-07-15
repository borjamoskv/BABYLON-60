// [C5-REAL] Bun / Node Universal Adapter (Lock-in Mitigation)
// Aísla las APIs específicas de Bun (bun:sqlite, Bun.file) para permitir
// validación cruzada en CI con Node.js/Deno. (Transición 940 -> 965+).

export interface DatabaseAdapter {
    query(sql: string, params: any[]): any;
    execute(sql: string, params: any[]): void;
}

export interface FsAdapter {
    readText(path: string): Promise<string>;
    writeText(path: string, content: string): Promise<void>;
}

// Factoría Determinista (Carga Condicional C5-REAL)
export async function createRuntimeAdapter(): Promise<{ db: DatabaseAdapter, fs: FsAdapter }> {
    const isBun = typeof process !== 'undefined' && process.versions && process.versions.bun;
    
    if (isBun) {
        // Ejecución Nivel 1: Bun Nativo (JSC + Zig + C SQLite)
        const { Database } = await import('bun:sqlite');
        const dbInstance = new Database('operon-cli.db');
        
        return {
            db: {
                query: (sql, params) => dbInstance.query(sql).all(...params),
                execute: (sql, params) => dbInstance.query(sql).run(...params)
            },
            fs: {
                readText: async (path) => await Bun.file(path).text(),
                writeText: async (path, content) => { await Bun.write(path, content); }
            }
        };
    } else {
        // Ejecución Nivel 2: Node.js Fallback (V8 + better-sqlite3)
        // Requerido para CI Matrix Cross-Validation
        const Database = (await import('better-sqlite3')).default;
        const fs = await import('fs/promises');
        const dbInstance = new Database('operon-cli.db');
        
        return {
            db: {
                query: (sql, params) => dbInstance.prepare(sql).all(...params),
                execute: (sql, params) => dbInstance.prepare(sql).run(...params)
            },
            fs: {
                readText: async (path) => await fs.readFile(path, 'utf8'),
                writeText: async (path, content) => await fs.writeFile(path, content, 'utf8')
            }
        };
    }
}
