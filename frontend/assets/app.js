import { SAMPLE_CSV } from "./sample-data.js";
import { checkHealth, analyzeTransactions } from "./api.js";
import {
  elements, showError, clearError, updateApiStatus,
  renderResults, showLoading, showIntake, showResults, money,
} from "./ui.js";

let selectedFile = null;
let selectedSampleMode = false;

function apiBase() {
  return elements.apiBaseInput.value.replace(/\/$/, "");
}

function updateFileSelection() {
  elements.fileChosen.textContent = selectedFile ? `Selected: ${selectedFile.name}` : "";
  elements.analyzeBtn.disabled = !selectedFile && !selectedSampleMode;
}

elements.dropzone.addEventListener("click", () => elements.fileInput.click());
elements.dropzone.addEventListener("dragover", (e) => {
  e.preventDefault();
  elements.dropzone.classList.add("drag-over");
});
elements.dropzone.addEventListener("dragleave", () => {
  elements.dropzone.classList.remove("drag-over");
});
elements.dropzone.addEventListener("drop", (e) => {
  e.preventDefault();
  elements.dropzone.classList.remove("drag-over");
  const file = e.dataTransfer.files[0];
  if (file) {
    selectedFile = file;
    selectedSampleMode = false;
    updateFileSelection();
    clearError();
  }
});
elements.fileInput.addEventListener("change", (e) => {
  if (e.target.files[0]) {
    selectedFile = e.target.files[0];
    selectedSampleMode = false;
    updateFileSelection();
    clearError();
  }
});

elements.useSampleBtn.addEventListener("click", () => {
  selectedSampleMode = true;
  selectedFile = null;
  elements.fileChosen.textContent = "Using built-in sample dataset";
  elements.analyzeBtn.disabled = false;
  clearError();
});

elements.resetBtn.addEventListener("click", () => {
  selectedFile = null;
  selectedSampleMode = false;
  elements.fileChosen.textContent = "";
  showIntake();
});

elements.analyzeBtn.addEventListener("click", async () => {
  clearError();
  showLoading();

  const formData = new FormData();
  if (selectedSampleMode) {
    const blob = new Blob([SAMPLE_CSV], { type: "text/csv" });
    formData.append("file", blob, "sample_transactions.csv");
  } else if (selectedFile) {
    formData.append("file", selectedFile);
  } else {
    showIntake();
    return;
  }

  try {
    const data = await analyzeTransactions(apiBase(), formData);
    renderResults(data);
    showResults();
  } catch (err) {
    showIntake();
    showError(err.message || "Could not reach the API. Check the endpoint configuration below.");
  }
});

async function initHealthCheck() {
  const status = await checkHealth(apiBase());
  updateApiStatus(status);
}

initHealthCheck();
elements.apiBaseInput.addEventListener("change", initHealthCheck);
