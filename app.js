const CATEGORY_COLORS = {
  Food: "#ff6b6b",
  Transportation: "#4ecdc4",
  Entertainment: "#45b7d1",
  Utilities: "#96ceb4",
  Unknown: "#feca57",
};

const state = {
  expenses: [],
  filtered: [],
  budgets: {},
  charts: {},
};

const monthFilter = document.getElementById("monthFilter");
const searchInput = document.getElementById("searchInput");
const summaryText = document.getElementById("summaryText");
const totalExpenses = document.getElementById("totalExpenses");
const budgetStatus = document.getElementById("budgetStatus");
const budgetInputs = document.getElementById("budgetInputs");
const budgetProgress = document.getElementById("budgetProgress");
const dataTableHead = document.querySelector("#dataTable thead");
const dataTableBody = document.querySelector("#dataTable tbody");
const csvUpload = document.getElementById("csvUpload");

function init() {
  initMonthFilter();
  initBudgetInputs();
  bindEvents();
  applyFilterAndRender();
}

function initMonthFilter() {
  monthFilter.innerHTML = "";
  const all = document.createElement("option");
  all.value = "All";
  all.textContent = "All";
  monthFilter.appendChild(all);
  for (let i = 1; i <= 12; i += 1) {
    const opt = document.createElement("option");
    opt.value = String(i).padStart(2, "0");
    opt.textContent = String(i).padStart(2, "0");
    monthFilter.appendChild(opt);
  }
}

function initBudgetInputs() {
  const categories = Object.keys(CATEGORY_COLORS);
  budgetInputs.innerHTML = "";
  categories.forEach((category) => {
    const row = document.createElement("div");
    row.className = "budget-row";
    row.innerHTML = `
      <span>${category}</span>
      <input type="number" step="0.01" min="0.01" placeholder="Budget">
      <button class="btn tiny">Set</button>
    `;
    const input = row.querySelector("input");
    row.querySelector("button").addEventListener("click", () => {
      const budget = Number(input.value);
      if (!Number.isFinite(budget) || budget <= 0) {
        alert("Budget must be greater than zero.");
        return;
      }
      state.budgets[category] = budget;
      applyFilterAndRender();
      input.value = "";
    });
    budgetInputs.appendChild(row);
  });
}

function bindEvents() {
  document.getElementById("loadSampleBtn").addEventListener("click", loadSampleData);
  document.getElementById("exportCsvBtn").addEventListener("click", exportCsv);
  document.getElementById("exportPdfBtn").addEventListener("click", exportPdf);
  searchInput.addEventListener("input", applyFilterAndRender);
  monthFilter.addEventListener("change", applyFilterAndRender);
  csvUpload.addEventListener("change", handleCsvUpload);
  document.getElementById("addExpenseForm").addEventListener("submit", addExpense);
}

function parseRowsToExpenses(rows) {
  const out = [];
  rows.forEach((row) => {
    const date = new Date(row.Date);
    const amount = Number(row.Amount);
    if (Number.isNaN(date.getTime()) || !Number.isFinite(amount)) {
      return;
    }
    out.push({
      Date: date,
      Category: row.Category ? String(row.Category).trim() : "Unknown",
      Amount: amount,
      Description: row.Description ? String(row.Description).trim() : "",
    });
  });
  return out;
}

function handleCsvUpload(event) {
  const file = event.target.files[0];
  if (!file) return;
  Papa.parse(file, {
    header: true,
    skipEmptyLines: true,
    complete: (result) => {
      state.expenses = parseRowsToExpenses(result.data);
      applyFilterAndRender();
    },
    error: (err) => alert(`Failed to parse CSV: ${err.message}`),
  });
}

async function loadSampleData() {
  try {
    const response = await fetch("sample_expenses.csv");
    if (!response.ok) throw new Error("Could not load sample_expenses.csv");
    const text = await response.text();
    const result = Papa.parse(text, { header: true, skipEmptyLines: true });
    state.expenses = parseRowsToExpenses(result.data);
    applyFilterAndRender();
  } catch (err) {
    alert(`Failed to load sample data: ${err.message}`);
  }
}

function addExpense(event) {
  event.preventDefault();
  const dateValue = document.getElementById("addDate").value;
  const category = document.getElementById("addCategory").value.trim() || "Unknown";
  const amount = Number(document.getElementById("addAmount").value);
  const description = document.getElementById("addDescription").value.trim();
  const date = new Date(dateValue);

  if (Number.isNaN(date.getTime()) || !Number.isFinite(amount) || amount <= 0) {
    alert("Please enter valid expense values.");
    return;
  }

  state.expenses.push({
    Date: date,
    Category: category,
    Amount: amount,
    Description: description,
  });
  event.target.reset();
  applyFilterAndRender();
}

function applyFilterAndRender() {
  const month = monthFilter.value || "All";
  const q = (searchInput.value || "").toLowerCase();
  state.filtered = state.expenses.filter((row) => {
    const monthOk = month === "All" || String(row.Date.getMonth() + 1).padStart(2, "0") === month;
    const searchOk = !q || row.Description.toLowerCase().includes(q) || row.Category.toLowerCase().includes(q);
    return monthOk && searchOk;
  });

  renderSummary();
  renderDashboard();
  renderTable();
  renderCharts();
}

function aggregateByCategory(rows) {
  const totals = {};
  rows.forEach((r) => {
    const c = r.Category || "Unknown";
    totals[c] = (totals[c] || 0) + r.Amount;
  });
  return totals;
}

function aggregateByDay(rows) {
  const totals = {};
  rows.forEach((r) => {
    const key = r.Date.toISOString().slice(0, 10);
    totals[key] = (totals[key] || 0) + r.Amount;
  });
  return totals;
}

function aggregateByMonth(rows) {
  const totals = {};
  rows.forEach((r) => {
    const key = `${r.Date.getFullYear()}-${String(r.Date.getMonth() + 1).padStart(2, "0")}`;
    totals[key] = (totals[key] || 0) + r.Amount;
  });
  return totals;
}

function renderSummary() {
  if (!state.filtered.length) {
    summaryText.textContent = "No data to display.";
    return;
  }
  const total = state.filtered.reduce((sum, r) => sum + r.Amount, 0);
  const categoryTotals = aggregateByCategory(state.filtered);
  const monthTotals = aggregateByMonth(state.filtered);

  let text = `Total Expenses: $${total.toFixed(2)}\n\nExpenses by Category:\n`;
  Object.entries(categoryTotals)
    .sort((a, b) => b[1] - a[1])
    .forEach(([cat, amount]) => {
      text += `${cat}: $${amount.toFixed(2)}\n`;
    });
  text += "\nMonthly Breakdown:\n";
  Object.entries(monthTotals)
    .sort(([a], [b]) => a.localeCompare(b))
    .forEach(([period, amount]) => {
      text += `${period}: $${amount.toFixed(2)}\n`;
    });
  summaryText.textContent = text;
}

function renderDashboard() {
  if (!state.filtered.length) {
    totalExpenses.textContent = "$0.00";
    budgetStatus.textContent = "Budget Status: No Data";
    budgetProgress.innerHTML = "";
    return;
  }

  const total = state.filtered.reduce((sum, r) => sum + r.Amount, 0);
  totalExpenses.textContent = `$${total.toFixed(2)}`;

  const categoryTotals = aggregateByCategory(state.filtered);
  const overspent = Object.entries(state.budgets)
    .filter(([cat, budget]) => (categoryTotals[cat] || 0) > budget)
    .map(([cat]) => cat);

  budgetStatus.textContent = overspent.length
    ? `Overspent in: ${overspent.join(", ")}`
    : "Budget Status: On Track";
  budgetStatus.className = overspent.length ? "danger" : "ok";

  budgetProgress.innerHTML = "";
  Object.entries(state.budgets).forEach(([cat, budget]) => {
    const spent = categoryTotals[cat] || 0;
    const percent = Math.min((spent / budget) * 100, 100);
    const row = document.createElement("div");
    row.className = "progress-row";
    row.innerHTML = `
      <div class="progress-label">${cat}: $${spent.toFixed(2)} / $${budget.toFixed(2)}</div>
      <div class="progress-track">
        <div class="progress-fill" style="width:${percent}%; background:${CATEGORY_COLORS[cat] || "#888"}"></div>
      </div>
    `;
    budgetProgress.appendChild(row);
  });
}

function renderTable() {
  dataTableHead.innerHTML = "";
  dataTableBody.innerHTML = "";
  const cols = ["Date", "Category", "Amount", "Description"];
  const tr = document.createElement("tr");
  cols.forEach((col) => {
    const th = document.createElement("th");
    th.textContent = col;
    tr.appendChild(th);
  });
  dataTableHead.appendChild(tr);

  state.filtered.forEach((row) => {
    const r = document.createElement("tr");
    r.innerHTML = `
      <td>${row.Date.toISOString().slice(0, 10)}</td>
      <td>${escapeHtml(row.Category)}</td>
      <td>$${row.Amount.toFixed(2)}</td>
      <td>${escapeHtml(row.Description)}</td>
    `;
    dataTableBody.appendChild(r);
  });
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function destroyCharts() {
  Object.values(state.charts).forEach((chart) => chart.destroy());
  state.charts = {};
}

function renderCharts() {
  destroyCharts();
  if (!state.filtered.length) return;

  const categoryTotals = aggregateByCategory(state.filtered);
  const dayTotals = aggregateByDay(state.filtered);
  const monthTotals = aggregateByMonth(state.filtered);

  const catLabels = Object.keys(categoryTotals);
  const catValues = Object.values(categoryTotals);
  const catColors = catLabels.map((c) => CATEGORY_COLORS[c] || "#888888");

  state.charts.categoryBar = new Chart(document.getElementById("categoryBar"), {
    type: "bar",
    data: { labels: catLabels, datasets: [{ label: "Amount", data: catValues, backgroundColor: catColors }] },
    options: { plugins: { legend: { display: false } } },
  });

  state.charts.categoryPie = new Chart(document.getElementById("categoryPie"), {
    type: "pie",
    data: { labels: catLabels, datasets: [{ data: catValues, backgroundColor: catColors }] },
  });

  state.charts.dailyLine = new Chart(document.getElementById("dailyLine"), {
    type: "line",
    data: {
      labels: Object.keys(dayTotals).sort(),
      datasets: [{ label: "Daily Expenses", data: Object.keys(dayTotals).sort().map((k) => dayTotals[k]), borderColor: "#2b7fff" }],
    },
  });

  state.charts.monthlyBar = new Chart(document.getElementById("monthlyBar"), {
    type: "bar",
    data: {
      labels: Object.keys(monthTotals).sort(),
      datasets: [{ label: "Monthly Expenses", data: Object.keys(monthTotals).sort().map((k) => monthTotals[k]), backgroundColor: "#ff8c42" }],
    },
    options: { plugins: { legend: { display: false } } },
  });
}

function exportCsv() {
  if (!state.filtered.length) {
    alert("No data to export.");
    return;
  }
  const lines = ["Date,Category,Amount,Description"];
  state.filtered.forEach((r) => {
    const date = r.Date.toISOString().slice(0, 10);
    const category = csvSafe(r.Category);
    const amount = r.Amount.toFixed(2);
    const description = csvSafe(r.Description);
    lines.push(`${date},${category},${amount},${description}`);
  });
  downloadBlob(lines.join("\n"), "text/csv;charset=utf-8;", "expenses_summary.csv");
}

function csvSafe(text) {
  const value = String(text ?? "");
  if (value.includes(",") || value.includes('"') || value.includes("\n")) {
    return `"${value.replaceAll('"', '""')}"`;
  }
  return value;
}

function exportPdf() {
  if (!state.filtered.length) {
    alert("No data to export.");
    return;
  }
  const { jsPDF } = window.jspdf;
  const pdf = new jsPDF();
  let y = 15;
  const total = state.filtered.reduce((sum, r) => sum + r.Amount, 0);
  const categoryTotals = aggregateByCategory(state.filtered);

  pdf.setFontSize(14);
  pdf.text("Expense Tracker Report", 14, y);
  y += 10;
  pdf.setFontSize(11);
  pdf.text(`Total Expenses: $${total.toFixed(2)}`, 14, y);
  y += 10;
  pdf.text("Expenses by Category:", 14, y);
  y += 8;
  Object.entries(categoryTotals).forEach(([cat, amt]) => {
    pdf.text(`${cat}: $${amt.toFixed(2)}`, 14, y);
    y += 7;
    if (y > 280) {
      pdf.addPage();
      y = 15;
    }
  });
  pdf.save("expense_report.pdf");
}

function downloadBlob(content, type, filename) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

init();
