// C5-REAL EXERGY CERTIFIED
import React from "react";

export function renderSyntaxHighlight(code: string, lang: string, accentColor: string) {
  const lines = code.split('\n');
  const keywords = ['def', 'class', 'import', 'from', 'return', 'raise', 'if', 'else', 'self', 'pub', 'fn', 'struct', 'impl', 'use', 'let', 'mut', 'SELECT', 'FROM', 'WHERE', 'ORDER', 'BY', 'LIMIT', 'name', 'on', 'jobs', 'steps', 'runs-on'];

  return lines.map((line, lIdx) => {
    let formatted = line;

    // Highlight comments
    if (line.trim().startsWith('#') || line.trim().startsWith('//') || line.trim().startsWith('%')) {
      return <div key={lIdx} className="text-emerald-500/60 italic">{line}</div>;
    }

    // Basic tokenization
    const tokens = line.split(/(\s+|[(),:=.{}[\]"])/);
    return (
      <div key={lIdx}>
        {tokens.map((token, tIdx) => {
          if (keywords.includes(token)) {
            return <span key={tIdx} style={{ color: accentColor, fontWeight: 500 }}>{token}</span>;
          }
          if (token.startsWith('"') || token.endsWith('"') || token.startsWith("'") || token.endsWith("'")) {
            return <span key={tIdx} className="text-amber-300">{token}</span>;
          }
          if (/^\d+$/.test(token)) {
            return <span key={tIdx} className="text-cyan-400">{token}</span>;
          }
          return <span key={tIdx}>{token}</span>;
        })}
      </div>
    );
  });
}
