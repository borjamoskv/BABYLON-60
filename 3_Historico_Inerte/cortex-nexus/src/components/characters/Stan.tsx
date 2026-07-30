import { forwardRef } from "react";

interface StanProps {
  x?: number;
  y?: number;
  scale?: number;
  expression?: "worried" | "shocked" | "neutral" | "angry";
}

const Stan = forwardRef<SVGSVGElement, StanProps>(
  ({ x = 0, y = 0, scale = 1, expression = "neutral" }, ref) => {
    const eyeY = expression === "worried" ? -2 : expression === "shocked" ? -4 : 0;
    const mouthPath =
      expression === "worried"
        ? "M 42,58 Q 50,52 58,58"
        : expression === "shocked"
        ? "M 44,55 Q 50,65 56,55 Q 50,48 44,55"
        : expression === "angry"
        ? "M 44,58 Q 50,54 56,58"
        : "M 44,56 Q 50,60 56,56";

    return (
      <svg
        ref={ref}
        viewBox="0 0 100 140"
        style={{
          position: "absolute",
          left: x,
          top: y,
          width: 100 * scale,
          height: 140 * scale,
          overflow: "visible",
        }}
      >
        <g className="stan-character">
          {/* Pants */}
          <rect x="28" y="95" width="44" height="35" fill="#2d4f7c" stroke="#000" strokeWidth="3" />
          <line x1="50" y1="95" x2="50" y2="130" stroke="#000" strokeWidth="2" />
          {/* Shoes */}
          <ellipse cx="35" cy="132" rx="10" ry="5" fill="#000" />
          <ellipse cx="65" cy="132" rx="10" ry="5" fill="#000" />
          {/* Jacket */}
          <rect x="22" y="65" width="56" height="38" rx="4" fill="#8B6914" stroke="#000" strokeWidth="3" />
          <line x1="50" y1="65" x2="50" y2="103" stroke="#000" strokeWidth="2" />
          <circle cx="48" cy="75" r="2" fill="#d4af37" />
          <circle cx="52" cy="75" r="2" fill="#d4af37" />
          <circle cx="48" cy="88" r="2" fill="#d4af37" />
          <circle cx="52" cy="88" r="2" fill="#d4af37" />
          {/* Collar */}
          <rect x="38" y="62" width="24" height="8" rx="2" fill="#c41e3a" stroke="#000" strokeWidth="2" />
          {/* Hands */}
          <circle cx="18" cy="82" r="7" fill="#c41e3a" stroke="#000" strokeWidth="2" />
          <circle cx="82" cy="82" r="7" fill="#c41e3a" stroke="#000" strokeWidth="2" />
          {/* Head */}
          <circle cx="50" cy="42" r="28" fill="#f5cba7" stroke="#000" strokeWidth="3" />
          {/* Hat */}
          <path d="M 20,38 Q 20,10 50,10 Q 80,10 80,38" fill="#2d5f8a" stroke="#000" strokeWidth="3" />
          <rect x="18" y="35" width="64" height="10" rx="3" fill="#c41e3a" stroke="#000" strokeWidth="3" />
          {/* Pom pom */}
          <circle cx="50" cy="10" r="8" fill="#c41e3a" stroke="#000" strokeWidth="2" />
          {/* Eyes */}
          <g transform={`translate(0, ${eyeY})`}>
            <ellipse cx="42" cy="42" rx="7" ry="9" fill="#fff" stroke="#000" strokeWidth="2" />
            <ellipse cx="58" cy="42" rx="7" ry="9" fill="#fff" stroke="#000" strokeWidth="2" />
            <circle cx="44" cy="42" r="2" fill="#000" />
            <circle cx="56" cy="42" r="2" fill="#000" />
          </g>
          {/* Mouth */}
          <path d={mouthPath} fill="none" stroke="#000" strokeWidth="2" strokeLinecap="round" />
        </g>
      </svg>
    );
  }
);

Stan.displayName = "Stan";
export default Stan;
