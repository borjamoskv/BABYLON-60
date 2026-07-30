import { forwardRef } from "react";

interface KennyProps {
  x?: number;
  y?: number;
  scale?: number;
  running?: boolean;
}

const Kenny = forwardRef<SVGSVGElement, KennyProps>(
  ({ x = 0, y = 0, scale = 1, running = false }, ref) => {
    const legOffset = running ? 8 : 0;
    
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
        <g className="kenny-character">
          {/* Legs */}
          <rect x="30" y="95" width="16" height="30" rx="3" fill="#ff6600" stroke="#000" strokeWidth="3" 
            transform={`rotate(${running ? -15 : 0}, 38, 95)`} />
          <rect x="54" y="95" width="16" height="30" rx="3" fill="#ff6600" stroke="#000" strokeWidth="3" 
            transform={`rotate(${running ? 15 : 0}, 62, 95)`} />
          {/* Shoes */}
          <ellipse cx={38 - legOffset} cy="128" rx="9" ry="5" fill="#000" />
          <ellipse cx={62 + legOffset} cy="128" rx="9" ry="5" fill="#000" />
          {/* Body */}
          <rect x="22" y="65" width="56" height="38" rx="6" fill="#ff6600" stroke="#000" strokeWidth="3" />
          <line x1="50" y1="65" x2="50" y2="103" stroke="#000" strokeWidth="2" />
          {/* Hands */}
          <circle cx="16" cy="82" r="7" fill="#8B4513" stroke="#000" strokeWidth="2" />
          <circle cx="84" cy="82" r="7" fill="#8B4513" stroke="#000" strokeWidth="2" />
          {/* Hood (closed) */}
          <ellipse cx="50" cy="42" rx="30" ry="28" fill="#ff6600" stroke="#000" strokeWidth="3" />
          {/* Face opening */}
          <ellipse cx="50" cy="42" rx="16" ry="14" fill="#5c3317" stroke="#000" strokeWidth="2" />
          {/* Eyes visible through hood */}
          <ellipse cx="44" cy="42" rx="5" ry="6" fill="#fff" stroke="#000" strokeWidth="1.5" />
          <ellipse cx="56" cy="42" rx="5" ry="6" fill="#fff" stroke="#000" strokeWidth="1.5" />
          <circle cx="45" cy="42" r="1.5" fill="#000" />
          <circle cx="55" cy="42" r="1.5" fill="#000" />
          {/* Hood tightening cord */}
          <path d="M 35,65 Q 50,72 65,65" fill="none" stroke="#000" strokeWidth="2" />
        </g>
      </svg>
    );
  }
);

Kenny.displayName = "Kenny";
export default Kenny;
