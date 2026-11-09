const SIZE = 76;
const STROKE = 7;
const RADIUS = (SIZE - STROKE) / 2;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

export function ProgressRing({ percent }: { percent: number }) {
  const clamped = Math.min(100, Math.max(0, percent));
  return (
    <svg
      className="ring"
      width={SIZE}
      height={SIZE}
      viewBox={`0 0 ${SIZE} ${SIZE}`}
      role="img"
      aria-label={`${Math.round(clamped)}% concluído`}
    >
      <circle className="ring-track" cx={SIZE / 2} cy={SIZE / 2} r={RADIUS} strokeWidth={STROKE} fill="none" />
      <circle
        className="ring-value"
        cx={SIZE / 2}
        cy={SIZE / 2}
        r={RADIUS}
        strokeWidth={STROKE}
        fill="none"
        strokeLinecap="round"
        strokeDasharray={CIRCUMFERENCE}
        strokeDashoffset={CIRCUMFERENCE * (1 - clamped / 100)}
        transform={`rotate(-90 ${SIZE / 2} ${SIZE / 2})`}
      />
      <text x="50%" y="50%" dominantBaseline="central" textAnchor="middle" className="ring-label">
        {Math.round(clamped)}%
      </text>
    </svg>
  );
}
