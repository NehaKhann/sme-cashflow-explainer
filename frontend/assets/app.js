// Ledger frontend -- vanilla JS, no build step, deploys as a static site.

const el = (id) => document.getElementById(id);

const dropzone = el("dropzone");
const fileInput = el("file-input");
const analyzeBtn = el("analyze-btn");
const useSampleBtn = el("use-sample-btn");
const fileChosen = el("file-chosen");
const errorBanner = el("error-banner");
const apiBaseInput = el("api-base");
const apiStatus = el("api-status");
const resetBtn = el("reset-btn");

const intakeSection = el("intake");
const loadingSection = el("loading");
const resultsSection = el("results");

let selectedFile = null;
let selectedSampleMode = false;

const SAMPLE_CSV = `date,amount,counterparty,category
2025-01-02,4511.54,Acme Retail Co,revenue
2025-01-03,-4086.66,vendor,payroll
2025-01-04,1077.33,Cedar & Co,revenue
2025-01-08,-1500.0,vendor,rent
2025-01-10,912.10,Northwind Traders,revenue
2025-01-12,-620.40,vendor,supplies
2025-02-02,4700.00,Acme Retail Co,revenue
2025-02-05,-4100.00,vendor,payroll
2025-02-08,-1500.0,vendor,rent
2025-02-12,1050.00,BlueSky Logistics,revenue
2025-06-02,1800.00,Acme Retail Co,revenue
2025-06-05,-3900.00,vendor,payroll
2025-06-08,-1500.0,vendor,rent
2025-07-02,1750.00,Acme Retail Co,revenue
2025-07-05,-3950.00,vendor,payroll
2025-07-08,-1500.0,vendor,rent
`;

function apiBase() {
  return apiBaseInput.value.replace(/\/$/, "");
}

async function checkHealth() {
  try {
    const res = await fetch(`${apiBase()}/health`, { method: "GET" });
    if (res.ok) {
      apiStatus.textContent = "API connected";
      apiStatus.className = "status-pill status-ok";
    } else {
      throw new Error("bad status");
    }
  } catch {
    apiStatus.textContent = "API unreachable";
    apiStatus.className = "status-pill status-down";
  }
}

function showError(msg) {
  errorBanner.textContent = msg;
  errorBanner.hidden = false;
}
function clearError() {
  errorBanner.hidden = true;
  errorBanner.textContent = "";
}

function setSelectedFile(file) {
  selectedFile = file;
  selectedSampleMode = false;
  fileChosen.textContent = file ? `Selected: ${file.name}` : "";
  analyzeBtn.disabled = !file;
  clearError();
}

dropzone.addEventListener("click", () => fileInput.click());
dropzone.addEventListener("dragover", (e) => { e.preventDefault(); dropzone.classList.add("drag-over"); });
dropzone.addEventListener("dragleave", () => dropzone.classList.remove("drag-over"));
dropzone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropzone.classList.remove("drag-over");
  const file = e.dataTransfer.files[0];
  if (file) setSelectedFile(file);
});
fileInput.addEventListener("change", (e) => {
  if (e.target.files[0]) setSelectedFile(e.target.files[0]);
});

useSampleBtn.addEventListener("click", () => {
  selectedSampleMode = true;
  selectedFile = null;
  fileChosen.textContent = "Using built-in sample dataset";
  analyzeBtn.disabled = false;
  clearError();
});

resetBtn.addEventListener("click", () => {
  resultsSection.hidden = true;
  intakeSection.hidden = false;
  setSelectedFile(null);
  selectedSampleMode = false;
  fileChosen.textContent = "";
});

analyzeBtn.addEventListener("click", async () => {
  clearError();
  intakeSection.hidden = true;
  loadingSection.hidden = false;

  const formData = new FormData();
  if (selectedSampleMode) {
    const blob = new Blob([SAMPLE_CSV], { type: "text/csv" });
    formData.append("file", blob, "sample_transactions.csv");
  } else if (selectedFile) {
    formData.append("file", selectedFile);
  } else {
    return;
  }

  try {
    const res = await fetch(`${apiBase()}/api/analyze`, { method: "POST", body: formData });
    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.detail || "Analysis failed.");
    }

    renderResults(data);
    loadingSection.hidden = true;
    resultsSection.hidden = false;
  } catch (err) {
    loadingSection.hidden = true;
    intakeSection.hidden = false;
    showError(err.message || "Could not reach the API. Check the endpoint configuration below.");
  }
});

function money(n) {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(n);
}

function renderResults(data) {
  el("memo-period").textContent = `${data.start_date} — ${data.end_date} (${data.num_months} mo)`;

  const stamp = el("risk-stamp");
  const stampText = el("risk-stamp-text");
  stamp.className = `risk-stamp ${data.risk_band}`;
  stampText.textContent = `${data.risk_band} risk`;

  el("fig-inflow").textContent = money(data.total_inflow);
  el("fig-outflow").textContent = money(Math.abs(data.total_outflow));
  el("fig-net").textContent = money(data.net_cash_flow);
  el("fig-volatility").textContent = `${data.revenue_volatility_pct}%`;
  el("fig-concentration").textContent = `${data.top_customer_share_pct}%`;
  el("fig-score").textContent = `${data.risk_score} / 100`;

  renderChart(data.monthly_revenue, data.monthly_expenses);

  const flagsList = el("flags-list");
  flagsList.innerHTML = "";
  data.risk_flags.forEach((f) => {
    const li = document.createElement("li");
    li.className = `flag-item ${f.severity}`;
    li.innerHTML = `<span class="flag-severity ${f.severity}">${f.severity}</span><span>${f.message}</span>`;
    flagsList.appendChild(li);
  });

  el("narrative-text").textContent = data.narrative;
}

function renderChart(monthlyRevenue, monthlyExpenses) {
  const svg = el("chart-svg");
  svg.innerHTML = "";

  const months = Object.keys(monthlyRevenue).sort();
  if (months.length === 0) return;

  const revValues = months.map((m) => monthlyRevenue[m] || 0);
  const expValues = months.map((m) => monthlyExpenses[m] || 0);
  const maxVal = Math.max(...revValues, ...expValues, 1);

  const W = 720, H = 260;
  const padL = 50, padR = 16, padT = 16, padB = 34;
  const chartW = W - padL - padR;
  const chartH = H - padT - padB;
  const barGroupW = chartW / months.length;
  const barW = Math.min(18, barGroupW * 0.32);

  const ns = "http://www.w3.org/2000/svg";
  const makeEl = (tag, attrs) => {
    const node = document.createElementNS(ns, tag);
    Object.entries(attrs).forEach(([k, v]) => node.setAttribute(k, v));
    return node;
  };

  // gridlines
  for (let i = 0; i <= 4; i++) {
    const y = padT + (chartH / 4) * i;
    svg.appendChild(makeEl("line", {
      x1: padL, x2: W - padR, y1: y, y2: y,
      stroke: "#C7C2AC", "stroke-width": 1, "stroke-dasharray": "2,3",
    }));
    const val = Math.round(maxVal * (1 - i / 4));
    const label = makeEl("text", {
      x: padL - 8, y: y + 4, "text-anchor": "end",
      "font-family": "IBM Plex Mono, monospace", "font-size": 9, fill: "#565044",
    });
    label.textContent = val >= 1000 ? `${Math.round(val / 1000)}k` : val;
    svg.appendChild(label);
  }

  months.forEach((m, i) => {
    const groupX = padL + i * barGroupW + barGroupW / 2;
    const revH = (revValues[i] / maxVal) * chartH;
    const expH = (expValues[i] / maxVal) * chartH;

    svg.appendChild(makeEl("rect", {
      x: groupX - barW - 2, y: padT + chartH - revH, width: barW, height: Math.max(revH, 1),
      fill: "#1F3D2E",
    }));
    svg.appendChild(makeEl("rect", {
      x: groupX + 2, y: padT + chartH - expH, width: barW, height: Math.max(expH, 1),
      fill: "#7A2C2C", opacity: 0.75,
    }));

    const label = makeEl("text", {
      x: groupX, y: H - 10, "text-anchor": "middle",
      "font-family": "IBM Plex Mono, monospace", "font-size": 9, fill: "#565044",
    });
    label.textContent = m.slice(5); // "MM"
    svg.appendChild(label);
  });

  // legend
  const legend = makeEl("g", {});
  const legendItems = [
    { label: "Revenue", color: "#1F3D2E", x: padL },
    { label: "Expenses", color: "#7A2C2C", x: padL + 110 },
  ];
  legendItems.forEach((item) => {
    legend.appendChild(makeEl("rect", { x: item.x, y: 0, width: 10, height: 10, fill: item.color }));
    const t = makeEl("text", {
      x: item.x + 16, y: 9, "font-family": "IBM Plex Mono, monospace", "font-size": 10, fill: "#565044",
    });
    t.textContent = item.label;
    legend.appendChild(t);
  });
  svg.appendChild(legend);
}

// initial health check
checkHealth();
apiBaseInput.addEventListener("change", checkHealth);
