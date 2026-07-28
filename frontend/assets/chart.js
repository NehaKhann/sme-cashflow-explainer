const CHART_W = 720, CHART_H = 260;
const PAD_L = 50, PAD_R = 16, PAD_T = 16, PAD_B = 34;
const PLOT_W = CHART_W - PAD_L - PAD_R;
const PLOT_H = CHART_H - PAD_T - PAD_B;
const GRID_LINES = 4;
const SVG_NS = "http://www.w3.org/2000/svg";

function makeEl(tag, attrs) {
  const node = document.createElementNS(SVG_NS, tag);
  for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
  return node;
}

function renderGridlines(svg, maxVal) {
  for (let i = 0; i <= GRID_LINES; i++) {
    const y = PAD_T + (PLOT_H / GRID_LINES) * i;
    svg.appendChild(makeEl("line", {
      x1: PAD_L, x2: CHART_W - PAD_R, y1: y, y2: y,
      stroke: "#C7C2AC", "stroke-width": 1, "stroke-dasharray": "2,3",
    }));
    const val = Math.round(maxVal * (1 - i / GRID_LINES));
    const label = makeEl("text", {
      x: PAD_L - 8, y: y + 4, "text-anchor": "end",
      "font-family": "IBM Plex Mono, monospace", "font-size": 9, fill: "#565044",
    });
    label.textContent = val >= 1000 ? `${Math.round(val / 1000)}k` : val;
    svg.appendChild(label);
  }
}

function renderBars(svg, months, revValues, expValues, maxVal) {
  const barGroupW = PLOT_W / months.length;
  const barW = Math.min(18, barGroupW * 0.32);

  months.forEach((m, i) => {
    const groupX = PAD_L + i * barGroupW + barGroupW / 2;
    const revH = (revValues[i] / maxVal) * PLOT_H;
    const expH = (expValues[i] / maxVal) * PLOT_H;

    svg.appendChild(makeEl("rect", {
      x: groupX - barW - 2, y: PAD_T + PLOT_H - revH,
      width: barW, height: Math.max(revH, 1),
      fill: "#1F3D2E",
    }));
    svg.appendChild(makeEl("rect", {
      x: groupX + 2, y: PAD_T + PLOT_H - expH,
      width: barW, height: Math.max(expH, 1),
      fill: "#7A2C2C", opacity: 0.75,
    }));

    const label = makeEl("text", {
      x: groupX, y: CHART_H - 10, "text-anchor": "middle",
      "font-family": "IBM Plex Mono, monospace", "font-size": 9, fill: "#565044",
    });
    label.textContent = m.slice(5);
    svg.appendChild(label);
  });
}

function renderLegend(svg) {
  const legend = makeEl("g", {});
  const items = [
    { label: "Revenue", color: "#1F3D2E", x: PAD_L },
    { label: "Expenses", color: "#7A2C2C", x: PAD_L + 110 },
  ];
  for (const item of items) {
    legend.appendChild(makeEl("rect", { x: item.x, y: 0, width: 10, height: 10, fill: item.color }));
    const t = makeEl("text", {
      x: item.x + 16, y: 9,
      "font-family": "IBM Plex Mono, monospace", "font-size": 10, fill: "#565044",
    });
    t.textContent = item.label;
    legend.appendChild(t);
  }
  svg.appendChild(legend);
}

export function renderChart(monthlyRevenue, monthlyExpenses) {
  const svg = document.getElementById("chart-svg");
  svg.innerHTML = "";

  const months = Object.keys(monthlyRevenue).sort();
  if (months.length === 0) return;

  const revValues = months.map((m) => monthlyRevenue[m] || 0);
  const expValues = months.map((m) => monthlyExpenses[m] || 0);
  const maxVal = Math.max(...revValues, ...expValues, 1);

  renderGridlines(svg, maxVal);
  renderBars(svg, months, revValues, expValues, maxVal);
  renderLegend(svg);
}
