/**
 * CORTEX Ecosystem Master Exergy Inventory
 * Zero-Dependency Node.js Static Server
 * Author: Borja Moskv (SYS_ID: borjamoskv)
 * Reality Level: C5-REAL
 */

const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = process.argv[2] || 8000;

const MIME_TYPES = {
    '.html': 'text/html',
    '.css': 'text/css',
    '.js': 'text/javascript',
    '.json': 'application/json',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.svg': 'image/svg+xml',
    '.md': 'text/markdown'
};

const server = http.createServer((req, res) => {
    console.log(`[CORTEX-SERVER] GET ${req.url}`);
    
    // Normalize url
    let filePath = '.' + req.url;
    if (filePath === './') {
        filePath = './index.html';
    }

    // Resolve extension
    const extname = String(path.extname(filePath)).toLowerCase();
    const contentType = MIME_TYPES[extname] || 'application/octet-stream';

    fs.readFile(filePath, (error, content) => {
        if (error) {
            if (error.code === 'ENOENT') {
                res.writeHead(404, { 'Content-Type': 'text/html' });
                res.end('<h1>404 Not Found (CORTEX-SERVER)</h1>', 'utf-8');
            } else {
                res.writeHead(500);
                res.end(`Server Error: ${error.code} ..\n`);
            }
        } else {
            res.writeHead(200, { 'Content-Type': contentType });
            res.end(content, 'utf-8');
        }
    });
});

server.listen(PORT, () => {
    console.log(`\n◈ CORTEX ZERO-DEPENDENCY NODE SERVER ACTIVE`);
    console.log(`◈ Listening on: http://localhost:${PORT}`);
    console.log(`◈ Vercel dependencies: 0\n`);
});
