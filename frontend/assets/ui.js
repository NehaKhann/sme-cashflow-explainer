import { renderChart } from "./chart.js";

export const $ = (id) => document.getElementById(id);

export const elements = {
  dropzone: $("dropzone"),
  fileInput: $("file-input"),
  analyzeBtn: $("analyze-btn"),
  useSampleBtn: $("use-sample-btn"),
  fileChosen: $("file-chosen"),
  errorBanner: $("error-banner"),
  apiBaseInput: $("api-base"),
  apiStatus: $("api-status"),
  resetBtn: $("reset-btn"),
  intake: $("intake"),
  loading: $("loading"),
  results: $("results"),
  memoPeriod: $("memo-period"),
  riskStamp: $("risk-stamp"),
  riskStampText: $("risk-stamp-text"),
  figInflow: $("fig-inflow"),
  figOutflow: $("fig-outflow"),
  figNet: $("fig-net"),
  figVolatility: $("fig-volatility"),
  figConcentration: $("fig-concentration"),
  figScore: $("fig-score"),
  flagsList: $("flags-list"),
  narrativeText: $("narrative-text"),
};

export function showError(msg) {
  elements.errorBanner.textContent = msg;
  elements.errorBanner.hidden = false;
}

export function clearError() {
  elements.errorBanner.hidden = true;
  elements.errorBanner.textContent = "";
}

export function setSelectedFile(file, onUpdate) {
  if (onUpdate) onUpdate(file);
}

export function updateApiStatus(status) {
  elements.apiStatus.textContent = status.label;
  elements.apiStatus.className = `status-pill ${status.className}`;
}

export function money(n) {
  return new Intl.NumberFormat("en-US", {
    style: "currency", currency: "USD", maximumFractionDigits: 0,
  }).format(n);
}

export function renderResults(data) {
  elements.memoPeriod.textContent = `${data.start_date} — ${data.end_date} (${data.num_months} mo)`;

  elements.riskStamp.className = `risk-stamp ${data.risk_band}`;
  elements.riskStampText.textContent = `${data.risk_band} risk`;

  elements.figInflow.textContent = money(data.total_inflow);
  elements.figOutflow.textContent = money(Math.abs(data.total_outflow));
  elements.figNet.textContent = money(data.net_cash_flow);
  elements.figVolatility.textContent = `${data.revenue_volatility_pct}%`;
  elements.figConcentration.textContent = `${data.top_customer_share_pct}%`;
  elements.figScore.textContent = `${data.risk_score} / 100`;

  renderChart(data.monthly_revenue, data.monthly_expenses);

  elements.flagsList.innerHTML = "";
  for (const f of data.risk_flags) {
    const li = document.createElement("li");
    li.className = `flag-item ${f.severity}`;
    li.innerHTML = `<span class="flag-severity ${f.severity}">${f.severity}</span><span>${f.message}</span>`;
    elements.flagsList.appendChild(li);
  }

  elements.narrativeText.textContent = data.narrative;
}

export function showLoading() {
  elements.intake.hidden = true;
  elements.loading.hidden = false;
  elements.results.hidden = true;
}

export function showIntake() {
  elements.intake.hidden = false;
  elements.loading.hidden = true;
  elements.results.hidden = true;
}

export function showResults() {
  elements.loading.hidden = true;
  elements.results.hidden = false;
}
