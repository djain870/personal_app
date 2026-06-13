function renderCategoryChart() {
    const chartEl = document.getElementById("categoryChart");
    if (!chartEl || !window.financeData) return;

    const categoryTotals = window.financeData.categoryTotals || {};
    const colors = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

    new Chart(chartEl, {
        type: 'doughnut',
        data: {
            labels: Object.keys(categoryTotals),
            datasets: [{
                data: Object.values(categoryTotals),
                backgroundColor: colors,
                borderColor: 'transparent',
                hoverOffset: 10
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: { color: 'white', font: { family: 'Inter' } }
                }
            }
        }
    });
}

function renderWealthCharts() {
    if (!document.getElementById("networthChart") || !window.financeData) return;

    Chart.register(ChartDataLabels);

    const networth = window.financeData.networth || {};
    const types = window.financeData.typeTotals || {};
    const volatility = window.financeData.volatilityTotals || {};
    const labels = Object.keys(networth).sort();
    const values = labels.map(k => networth[k]);

    new Chart(document.getElementById('networthChart'), {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Net Worth',
                data: values,
                borderColor: '#6366f1',
                tension: 0.4
            }]
        },
        options: {
            maintainAspectRatio: false,
            layout: { padding: { top: 20, right: 10, left: 10 } },
            plugins: {
                legend: { labels: { color: 'white' } },
                datalabels: {
                    color: 'white',
                    clamp: false,
                    clip: false,
                    font: { size: 10 },
                    align: 'top',
                    offset: 6,
                    formatter: value => value.toLocaleString()
                }
            }
        }
    });

    new Chart(document.getElementById('typeChart'), {
        type: 'doughnut',
        data: {
            labels: Object.keys(types),
            datasets: [{ data: Object.values(types) }]
        },
        options: {
            maintainAspectRatio: true,
            aspectRatio: 1,
            layout: { padding: 5 },
            plugins: {
                legend: { labels: { color: 'white' } },
                datalabels: {
                    color: 'white',
                    clamp: true,
                    clip: true,
                    font: { size: 10 },
                    formatter: (value, ctx) => {
                        const sum = ctx.chart.data.datasets[0].data.reduce((a, b) => a + b, 0);
                        return ((value / sum) * 100).toFixed(1) + '%';
                    }
                }
            }
        }
    });

    new Chart(document.getElementById('volatilityChart'), {
        type: 'pie',
        data: {
            labels: Object.keys(volatility),
            datasets: [{ data: Object.values(volatility) }]
        },
        options: {
            maintainAspectRatio: true,
            aspectRatio: 1,
            layout: { padding: 5 },
            plugins: {
                legend: { labels: { color: 'white' } },
                datalabels: {
                    color: 'white',
                    clamp: true,
                    clip: true,
                    font: { size: 10 },
                    formatter: (value, ctx) => {
                        const sum = ctx.chart.data.datasets[0].data.reduce((a, b) => a + b, 0);
                        return ((value / sum) * 100).toFixed(1) + '%';
                    }
                }
            }
        }
    });

    const growth = [];
    for (let i = 1; i < values.length; i++) {
        growth.push(values[i] - values[i - 1]);
    }

    new Chart(document.getElementById('growthChart'), {
        type: 'bar',
        data: {
            labels: labels.slice(1),
            datasets: [{
                label: 'Growth',
                data: growth
            }]
        },
        options: {
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: 'white' } },
                datalabels: {
                    color: 'white',
                    clamp: true,
                    clip: true,
                    font: { size: 10 },
                    anchor: 'end',
                    align: 'top',
                    formatter: value => value.toLocaleString()
                }
            }
        }
    });
}

function renderCashflowCharts() {
    if (!document.getElementById("cashflowChart") || !window.financeData) return;

    const income = window.financeData.income || {};
    const expenseCf = window.financeData.expenseCf || {};
    const savings = window.financeData.savings || {};
    const cfLabels = Object.keys(income).sort();

    new Chart(document.getElementById('cashflowChart'), {
        type: 'line',
        data: {
            labels: cfLabels,
            datasets: [
                {
                    label: 'Income',
                    data: cfLabels.map(k => income[k]),
                    borderColor: '#10b981'
                },
                {
                    label: 'Expense',
                    data: cfLabels.map(k => expenseCf[k]),
                    borderColor: '#ef4444'
                }
            ]
        },
        options: {
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: 'white' } }
            }
        }
    });

    new Chart(document.getElementById('savingsChart'), {
        type: 'bar',
        data: {
            labels: cfLabels,
            datasets: [{
                label: 'Savings',
                data: cfLabels.map(k => savings[k]),
                backgroundColor: '#6366f1'
            }]
        },
        options: {
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: 'white' } }
            }
        }
    });
}

document.addEventListener("DOMContentLoaded", function () {
    renderCategoryChart();
    renderWealthCharts();
    renderCashflowCharts();
});
