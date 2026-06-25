// Decorative embedding-space scatter. Pure SVG, no data needed, no random().
// Positions are computed deterministically from the node index.

const PALETTE = [
  "#3b82f6", // blue
  "#8b5cf6", // violet
  "#06b6d4", // cyan
  "#60a5fa", // blue-400
  "#a78bfa", // violet-400
];

// Deterministic pseudo-random from a seed integer.
function seededVal(seed: number, offset: number): number {
  const x = Math.sin(seed * 127.1 + offset * 311.7) * 43758.5453;
  return x - Math.floor(x);
}

const NODES = Array.from({ length: 42 }, (_, i) => ({
  cx: 12 + seededVal(i, 0) * 576,
  cy: 12 + seededVal(i, 1) * 276,
  r: 3 + seededVal(i, 2) * 7,
  fill: PALETTE[Math.floor(seededVal(i, 3) * PALETTE.length)],
  opacity: 0.18 + seededVal(i, 4) * 0.45,
}));

// A handful of faint connecting lines between nearby nodes.
const EDGES = [
  [0, 3], [1, 7], [2, 9], [4, 12], [5, 15], [6, 20],
  [8, 22], [10, 24], [11, 26], [13, 30], [14, 33], [16, 38],
  [17, 35], [18, 40], [19, 41],
];

export function EmbeddingCloud({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 600 300"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-hidden="true"
    >
      {EDGES.map(([a, b], i) => (
        <line
          key={i}
          x1={NODES[a].cx}
          y1={NODES[a].cy}
          x2={NODES[b].cx}
          y2={NODES[b].cy}
          stroke="#3b82f6"
          strokeOpacity={0.1}
          strokeWidth={0.8}
        />
      ))}
      {NODES.map((n, i) => (
        <circle
          key={i}
          cx={n.cx}
          cy={n.cy}
          r={n.r}
          fill={n.fill}
          opacity={n.opacity}
        />
      ))}
    </svg>
  );
}
