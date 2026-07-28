interface ChartCardProps {
  monthlyRevenue: Record<string, number>;
  monthlyExpenses: Record<string, number>;
}

const W = 720, H = 280;
const PAD_L = 56, PAD_R = 16, PAD_T = 20, PAD_B = 36;
const PLOT_W = W - PAD_L - PAD_R;
const PLOT_H = H - PAD_T - PAD_B;
const GRID = 4;

const C_REVENUE = "#3b82f6";
const C_EXPENSES = "#ef4444";
const C_GRID = "#e2e5ea";
const C_LABEL = "#6b7280";

function formatVal(v: number) {
  return v >= 1000 ? `${Math.round(v / 1000)}k` : String(v);
}

function Chart({ rev, exp, months }: { rev: number[]; exp: number[]; months: string[] }) {
  const maxVal = Math.max(...rev, ...exp, 1);
  const barGroupW = PLOT_W / months.length;
  const barW = Math.min(20, barGroupW * 0.34);

  const gridlines = [];
  for (let i = 0; i <= GRID; i++) {
    const y = PAD_T + (PLOT_H / GRID) * i;
    const val = Math.round(maxVal * (1 - i / GRID));
    gridlines.push(
      <g key={`grid-${i}`}>
        <line x1={PAD_L} y1={y} x2={W - PAD_R} y2={y} stroke={C_GRID} strokeWidth={1} />
        <text x={PAD_L - 10} y={y + 4} textAnchor="end" fontFamily="JetBrains Mono, monospace" fontSize={10} fill={C_LABEL}>
          {formatVal(val)}
        </text>
      </g>
    );
  }

  const bars = months.map((m, i) => {
    const cx = PAD_L + i * barGroupW + barGroupW / 2;
    const revH = (rev[i] / maxVal) * PLOT_H;
    const expH = (exp[i] / maxVal) * PLOT_H;
    return (
      <g key={m}>
        <rect x={cx - barW - 3} y={PAD_T + PLOT_H - revH} width={barW} height={Math.max(revH, 1)} fill={C_REVENUE} rx={3} />
        <rect x={cx + 3} y={PAD_T + PLOT_H - expH} width={barW} height={Math.max(expH, 1)} fill={C_EXPENSES} rx={3} opacity={0.8} />
        <text x={cx} y={H - 8} textAnchor="middle" fontFamily="JetBrains Mono, monospace" fontSize={10} fill={C_LABEL}>
          {m.slice(5)}
        </text>
      </g>
    );
  });

  return (
    <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="xMidYMid meet">
      {gridlines}
      {bars}
      <g>
        <rect x={PAD_L} y={0} width={10} height={10} fill={C_REVENUE} rx={2} />
        <text x={PAD_L + 16} y={9} fontFamily="JetBrains Mono, monospace" fontSize={10} fill={C_LABEL}>Revenue</text>
        <rect x={PAD_L + 110} y={0} width={10} height={10} fill={C_EXPENSES} rx={2} />
        <text x={PAD_L + 126} y={9} fontFamily="JetBrains Mono, monospace" fontSize={10} fill={C_LABEL}>Expenses</text>
      </g>
    </svg>
  );
}

export function ChartCard({ monthlyRevenue, monthlyExpenses }: ChartCardProps) {
  const months = Object.keys(monthlyRevenue).sort();
  const rev = months.map((m) => monthlyRevenue[m] || 0);
  const exp = months.map((m) => monthlyExpenses[m] || 0);

  return (
    <div className="card chart-card">
      <div className="card-header">
        <h3>Monthly revenue vs. expenses</h3>
        <div className="chart-legend">
          <span className="legend-item"><span className="legend-swatch swatch-revenue" /> Revenue</span>
          <span className="legend-item"><span className="legend-swatch swatch-expenses" /> Expenses</span>
        </div>
      </div>
      <div className="card-body chart-body">
        {months.length > 0 ? (
          <Chart rev={rev} exp={exp} months={months} />
        ) : (
          <p style={{ textAlign: "center", color: C_LABEL, fontSize: 13 }}>No data to display</p>
        )}
      </div>
    </div>
  );
}
