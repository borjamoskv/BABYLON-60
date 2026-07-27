import { forwardRef } from "react";

interface CartmanProps {
  x?: number;
  y?: number;
  scale?: number;
  expression?: "angry" | "shocked" | "neutral" | "yelling";
}

const Cartman = forwardRef<SVGSVGElement, CartmanProps>(
  ({ x = 0, y = 0, scale = 1, expression = "neutral" }, ref) => {
    const eyeY = expression === "shocked" ? -4 : expression === "yelling" ? -2 : 0;
    const mouthPath =
      expression === "angry" || expression === "yelling"
        ? "M 38,52 Q 50,65 62,52 Q 50,70 38,52"
        : expression === "shocked"
        ? "M 44,50 Q 50,62 56,50 Q 50,42 44,50"
        : "M 42,54 Q 50,58 58,54";

    return (
      <svg
        ref={ref}
        viewBox="0 0 120 150"
        style={{
          position: "absolute",
          left: x,
          top: y,
          width: 120 * scale,
          height: 150 * scale,
          overflow: "visible",
        }}
      >
        <g className="cartman-character">
          {/* Pants */}
          <rect x="30" y="100" width="60" height="35" rx="5" fill="#654321" stroke="#000" strokeWidth="3" />
          <line x1="60" y1="100" x2="60" y2="135" stroke="#000" strokeWidth="2" />
          {/* Shoes */}
          <ellipse cx="42" cy="137" rx="12" ry="6" fill="#000" />
          <ellipse cx="78" cy="137" rx="12" ry="6" fill="#000" />
          {/* Body (fat) */}
          <ellipse cx="60" cy="80" rx="48" ry="38" fill="#c41e3a" stroke="#000" strokeWidth="3" />
          <line x1="60" y1="50" x2="60" y2="110" stroke="#000" strokeWidth="2" />
          <circle cx="56" cy="68" r="3" fill="#000" />
          <circle cx="64" cy="68" r="3" fill="#000" />
          <circle cx="56" cy="85" r="3" fill="#000" />
          <circle cx="64" cy="85" r="3" fill="#000" />
          {/* Hands */}
          <circle cx="15" cy="85" r="10" fill="#ffd700" stroke="#000" strokeWidth="2" />
          <circle cx="105" cy="85" r="10" fill="#ffd700" stroke="#000" strokeWidth="2" />
          {/* Head (double chin) */}
          <ellipse cx="60" cy="38" rx="38" ry="32" fill="#f5cba7" stroke="#000" strokeWidth="3" />
          <path d="M 32,52 Q 60,60 88,52" fill="none" stroke="#000" strokeWidth="2" />
          {/* Hat */}
          <path d="M 22,28 Q 60,-5 98,28" fill="#4a90c4" stroke="#000" strokeWidth="3" />
          <ellipse cx="60" cy="28" rx="38" ry="8" fill="#ffd700" stroke="#000" strokeWidth="3" />
          <circle cx="60" cy="8" r="6" fill="#ffd700" stroke="#000" strokeWidth="2" />
          {/* Eyes */}
          <g transform={`translate(0, ${eyeY})`}>
            <ellipse cx="48" cy="35" rx="8" ry="10" fill="#fff" stroke="#000" strokeWidth="2" />
            <ellipse cx="72" cy="35" rx="8" ry="10" fill="#fff" stroke="#000" strokeWidth="2" />
            <circle cx="50" cy="35" r="2.5" fill="#000" />
            <circle cx="70" cy="35" r="2.5" fill="#000" />
          </g>
          {/* Mouth */}
          <path d={mouthPath} fill={expression === "angry" || expression === "yelling" ? "#000" : "none"} stroke="#000" strokeWidth="2" strokeLinecap="round" />
        </g>
      </svg>
    );
  }
);

Cartman.displayName = "Cartman";
export default Cartman;
