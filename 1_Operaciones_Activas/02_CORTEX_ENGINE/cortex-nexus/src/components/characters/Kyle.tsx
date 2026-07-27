import { forwardRef } from "react";

interface KyleProps {
  x?: number;
  y?: number;
  scale?: number;
  expression?: "screaming" | "worried" | "neutral" | "angry";
}

const Kyle = forwardRef<SVGSVGElement, KyleProps>(
  ({ x = 0, y = 0, scale = 1, expression = "neutral" }, ref) => {
    const eyeY = expression === "screaming" ? -3 : 0;
    const mouthPath =
      expression === "screaming"
        ? "M 42,55 Q 50,70 58,55 Q 50,48 42,55"
        : expression === "worried"
        ? "M 44,58 Q 50,52 56,58"
        : expression === "angry"
        ? "M 42,55 L 46,60 L 50,55 L 54,60 L 58,55"
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
        <g className="kyle-character">
          {/* Pants */}
          <rect x="28" y="95" width="44" height="35" fill="#2d5a27" stroke="#000" strokeWidth="3" />
          <line x1="50" y1="95" x2="50" y2="130" stroke="#000" strokeWidth="2" />
          {/* Shoes */}
          <ellipse cx="35" cy="132" rx="10" ry="5" fill="#000" />
          <ellipse cx="65" cy="132" rx="10" ry="5" fill="#000" />
          {/* Jacket */}
          <rect x="22" y="65" width="56" height="38" rx="4" fill="#ff6600" stroke="#000" strokeWidth="3" />
          <line x1="50" y1="65" x2="50" y2="103" stroke="#000" strokeWidth="2" />
          <rect x="30" y="75" width="16" height="12" rx="2" fill="#cc5200" stroke="#000" strokeWidth="1.5" />
          <rect x="54" y="75" width="16" height="12" rx="2" fill="#cc5200" stroke="#000" strokeWidth="1.5" />
          {/* Collar */}
          <rect x="38" y="62" width="24" height="8" rx="2" fill="#1a1a2e" stroke="#000" strokeWidth="2" />
          {/* Hands */}
          <circle cx="18" cy="82" r="7" fill="#ff6600" stroke="#000" strokeWidth="2" />
          <circle cx="82" cy="82" r="7" fill="#ff6600" stroke="#000" strokeWidth="2" />
          {/* Head */}
          <circle cx="50" cy="42" r="26" fill="#f5cba7" stroke="#000" strokeWidth="3" />
          {/* Hat - ear flaps */}
          <path d="M 24,20 Q 50,5 76,20 L 76,45 Q 76,55 66,50 L 66,25 Q 50,20 34,25 L 34,50 Q 24,55 24,45 Z" fill="#2d5a27" stroke="#000" strokeWidth="3" />
          {/* Hat brim */}
          <rect x="22" y="35" width="56" height="10" rx="3" fill="#1a3a1a" stroke="#000" strokeWidth="3" />
          {/* Eyes */}
          <g transform={`translate(0, ${eyeY})`}>
            <ellipse cx="42" cy="42" rx="7" ry="9" fill="#fff" stroke="#000" strokeWidth="2" />
            <ellipse cx="58" cy="42" rx="7" ry="9" fill="#fff" stroke="#000" strokeWidth="2" />
            <circle cx="44" cy="42" r="2" fill="#000" />
            <circle cx="56" cy="42" r="2" fill="#000" />
          </g>
          {/* Mouth */}
          <path d={mouthPath} fill={expression === "screaming" ? "#000" : "none"} stroke="#000" strokeWidth="2" strokeLinecap="round" />
        </g>
      </svg>
    );
  }
);

Kyle.displayName = "Kyle";
export default Kyle;
