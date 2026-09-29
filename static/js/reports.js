/**
 * AnnSeva - Live Reports & Visualizations (reports.js)
 * Real-time dynamic dashboard:
 * - Polls /api/reports-data every 4 seconds.
 * - Smoothly updates Chart.js figures and KPI counters without page reload.
 * - Supports Live Counter Reset to 0 (for viva demonstration from zero).
 * - Supports Restoring Demo Data on demand.
 */

let statusChartInstance = null;
let categoryChartInstance = null;
let livePollingInterval = null;
let isLivePolling = true;

// Store previous values for animated number transitions
const previousValues = {
    foodSaved: 0,
    mealsServed: 0,
    totalDonations: 0,
    completedCount: 0
};

document.addEventListener('DOMContentLoaded', function () {
    const statusCtx = document.getElementById('statusChart');
    const categoryCtx = document.getElementById('categoryChart');

    if (!statusCtx || !categoryCtx) return;

    // 1. Initialize Chart Instances with Initial Skeleton
    initCharts(statusCtx, categoryCtx);

    // 2. Fetch live data immediately
    fetchLiveReportsData();

    // 3. Start Live Auto-Refresh (every 4 seconds)
    livePollingInterval = setInterval(fetchLiveReportsData, 4000);

    // 4. Setup Live Controls
    setupControlButtons();
});

function setupControlButtons() {
    const btnToggleLive = document.getElementById('btnToggleLive');
    const btnManualRefresh = document.getElementById('btnManualRefresh');
    const btnResetCounters = document.getElementById('btnResetCounters');
    const btnRestoreDemo = document.getElementById('btnRestoreDemo');

    // A. Pause / Resume Toggle
    if (btnToggleLive) {
        btnToggleLive.addEventListener('click', function () {
            isLivePolling = !isLivePolling;
            if (isLivePolling) {
                btnToggleLive.innerHTML = '⏸️ Pause Live';
                btnToggleLive.classList.remove('btn-secondary');
                btnToggleLive.classList.add('btn-primary');
                document.getElementById('liveStatusDot').style.display = 'inline-block';
                document.getElementById('liveStatusText').textContent = 'LIVE ACTIVE';
                fetchLiveReportsData();
                livePollingInterval = setInterval(fetchLiveReportsData, 4000);
            } else {
                btnToggleLive.innerHTML = '▶️ Resume Live';
                btnToggleLive.classList.remove('btn-primary');
                btnToggleLive.classList.add('btn-secondary');
                document.getElementById('liveStatusDot').style.display = 'none';
                document.getElementById('liveStatusText').textContent = 'PAUSED';
                clearInterval(livePollingInterval);
            }
        });
    }

    // B. Manual Refresh Now
    if (btnManualRefresh) {
        btnManualRefresh.addEventListener('click', function () {
            btnManualRefresh.disabled = true;
            btnManualRefresh.innerHTML = '⏳ Syncing...';
            fetchLiveReportsData().then(() => {
                setTimeout(() => {
                    btnManualRefresh.disabled = false;
                    btnManualRefresh.innerHTML = '🔄 Refresh';
                }, 400);
            });
        });
    }

    // C. Live Reset Report Counters to 0
    if (btnResetCounters) {
        btnResetCounters.addEventListener('click', function () {
            if (!confirm("Reset all report counters to 0 for a fresh live demonstration?")) {
                return;
            }

            btnResetCounters.disabled = true;
            btnResetCounters.innerHTML = '⏳ Resetting...';

            fetch('/api/reports/reset', { method: 'POST' })
                .then(res => res.json())
                .then(data => {
                    btnResetCounters.disabled = false;
                    btnResetCounters.innerHTML = '🔴 Reset Counters to 0';
                    if (data.success) {
                        showLiveBanner("✨ All report counters have been reset to 0! You can now post a fresh donation to demonstrate live counting.", "success");
                        updateDashboardDOM(data.stats);
                        updateCharts(data.stats);
                        updateLiveActivityStream(data.stats.activity_stream);
                    } else {
                        showLiveBanner("Error resetting counters: " + data.error, "danger");
                    }
                })
                .catch(err => {
                    btnResetCounters.disabled = false;
                    btnResetCounters.innerHTML = '🔴 Reset Counters to 0';
                    showLiveBanner("Failed to communicate with reset endpoint.", "danger");
                });
        });
    }

    // D. Restore Sample Demo Records
    if (btnRestoreDemo) {
        btnRestoreDemo.addEventListener('click', function () {
            btnRestoreDemo.disabled = true;
            btnRestoreDemo.innerHTML = '⏳ Loading...';

            fetch('/api/reports/restore-demo', { method: 'POST' })
                .then(res => res.json())
                .then(data => {
                    btnRestoreDemo.disabled = false;
                    btnRestoreDemo.innerHTML = '📦 Load Sample Data';
                    if (data.success) {
                        showLiveBanner("📦 Sample demo records restored successfully!", "info");
                        updateDashboardDOM(data.stats);
                        updateCharts(data.stats);
                        updateLiveActivityStream(data.stats.activity_stream);
                    } else {
                        showLiveBanner("Error restoring demo data: " + data.error, "danger");
                    }
                })
                .catch(err => {
                    btnRestoreDemo.disabled = false;
                    btnRestoreDemo.innerHTML = '📦 Load Sample Data';
                    showLiveBanner("Failed to communicate with restore endpoint.", "danger");
                });
        });
    }
}

function showLiveBanner(message, type) {
    const banner = document.getElementById('liveAlertBanner');
    if (!banner) return;

    banner.textContent = message;
    banner.style.display = 'block';

    if (type === 'success') {
        banner.style.backgroundColor = '#ecfdf5';
        banner.style.color = '#065f46';
        banner.style.border = '1px solid #a7f3d0';
    } else if (type === 'danger') {
        banner.style.backgroundColor = '#fef2f2';
        banner.style.color = '#991b1b';
        banner.style.border = '1px solid #fecaca';
    } else {
        banner.style.backgroundColor = '#eff6ff';
        banner.style.color = '#1e40af';
        banner.style.border = '1px solid #bfdbfe';
    }

    setTimeout(() => {
        banner.style.opacity = '0';
        setTimeout(() => {
            banner.style.display = 'none';
            banner.style.opacity = '1';
        }, 400);
    }, 6000);
}

function initCharts(statusCtx, categoryCtx) {
    // A. Status Doughnut Chart
    statusChartInstance = new Chart(statusCtx, {
        type: 'doughnut',
        data: {
            labels: ['Pending', 'Accepted', 'Picked Up', 'Completed', 'Rejected'],
            datasets: [{
                data: [0, 0, 0, 0, 0],
                backgroundColor: ['#f59e0b', '#3b82f6', '#8b5cf6', '#10b981', '#ef4444'],
                borderWidth: 2,
                borderColor: '#ffffff',
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 500 },
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { padding: 15, font: { size: 12, weight: '600' } }
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            const val = context.raw || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const pct = total > 0 ? ((val / total) * 100).toFixed(1) : 0;
                            return ` ${context.label}: ${val} (${pct}%)`;
                        }
                    }
                }
            },
            cutout: '65%'
        }
    });

    // B. Category Bar Chart
    categoryChartInstance = new Chart(categoryCtx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Total Quantity (kg)',
                    data: [],
                    backgroundColor: '#10b981',
                    borderRadius: 6
                },
                {
                    label: 'Donation Requests',
                    data: [],
                    backgroundColor: '#3b82f6',
                    borderRadius: 6
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 500 },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: '#f1f5f9' },
                    ticks: { font: { size: 11 } }
                },
                x: {
                    grid: { display: false },
                    ticks: { font: { size: 11 }, maxRotation: 25, minRotation: 0 }
                }
            },
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { font: { size: 12, weight: '600' } }
                }
            }
        }
    });
}

function fetchLiveReportsData() {
    return fetch('/api/reports-data')
        .then(res => res.json())
        .then(data => {
            updateDashboardDOM(data);
            updateCharts(data);
            updateLiveActivityStream(data.activity_stream);
        })
        .catch(err => {
            console.warn('[AnnSeva Live] Could not poll reports data:', err);
        });
}

function updateDashboardDOM(data) {
    // 1. KPI Cards with Smooth Value Updates
    const elFoodSaved = document.getElementById('liveFoodSaved');
    if (elFoodSaved) {
        elFoodSaved.innerHTML = `${data.total_food_saved} <small style="font-size: 1rem; font-weight: 600;">kg</small>`;
    }

    const elMeals = document.getElementById('liveMealsServed');
    if (elMeals) {
        elMeals.textContent = `${data.estimated_meals_served}+`;
    }

    const elTotal = document.getElementById('liveTotalDonations');
    if (elTotal) {
        elTotal.textContent = data.total_donations;
    }

    const elCompleted = document.getElementById('liveCompletedCount');
    if (elCompleted) {
        elCompleted.textContent = data.completed_count;
    }

    // 2. Status Breakdowns
    const elPending = document.getElementById('livePendingCount');
    if (elPending) elPending.textContent = data.pending_count;

    const elAccepted = document.getElementById('liveAcceptedCount');
    if (elAccepted) elAccepted.textContent = data.accepted_count;

    const elPickedUp = document.getElementById('livePickedUpCount');
    if (elPickedUp) elPickedUp.textContent = data.picked_up_count !== undefined ? data.picked_up_count : 0;

    const elCompletedBadge = document.getElementById('liveCompletedBadge');
    if (elCompletedBadge) elCompletedBadge.textContent = data.completed_count;

    const elRejected = document.getElementById('liveRejectedCount');
    if (elRejected) elRejected.textContent = data.rejected_count;

    // 3. Community Stats
    const elDonors = document.getElementById('liveTotalDonors');
    if (elDonors) elDonors.textContent = data.total_donors;

    const elNGOs = document.getElementById('liveTotalNGOs');
    if (elNGOs) elNGOs.textContent = data.total_ngos;

    const elInTransit = document.getElementById('liveAcceptedFood');
    if (elInTransit) elInTransit.textContent = `${data.accepted_food} kg`;

    // 4. Timestamp
    const elTimestamp = document.getElementById('liveSyncTimestamp');
    if (elTimestamp) elTimestamp.textContent = data.timestamp;

    // Store for animation comparisons
    previousValues.foodSaved = data.total_food_saved;
    previousValues.mealsServed = data.estimated_meals_served;
    previousValues.totalDonations = data.total_donations;
    previousValues.completedCount = data.completed_count;
}

function updateCharts(data) {
    if (statusChartInstance && data.charts && data.charts.status) {
        const isAllZero = data.charts.status.data.every(v => v === 0);
        if (isAllZero) {
            statusChartInstance.data.labels = ['No Donations Yet'];
            statusChartInstance.data.datasets[0].data = [1];
            statusChartInstance.data.datasets[0].backgroundColor = ['#e2e8f0'];
        } else {
            statusChartInstance.data.labels = data.charts.status.labels;
            statusChartInstance.data.datasets[0].data = data.charts.status.data;
            statusChartInstance.data.datasets[0].backgroundColor = data.charts.status.colors;
        }
        statusChartInstance.update();
    }

    if (categoryChartInstance && data.charts && data.charts.categories) {
        categoryChartInstance.data.labels = data.charts.categories.labels;
        categoryChartInstance.data.datasets[0].data = data.charts.categories.weights;
        categoryChartInstance.data.datasets[1].data = data.charts.categories.counts;
        categoryChartInstance.update();
    }
}

function updateLiveActivityStream(activities) {
    const tableBody = document.getElementById('liveActivityBody');
    if (!tableBody) return;

    if (!activities || activities.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 2rem;">No donation records in database. Counters are currently at 0. Listed donations will appear here live!</td></tr>';
        return;
    }

    let rowsHtml = '';
    activities.forEach(item => {
        const badgeClass = `status-${item.status.toLowerCase()}`;
        rowsHtml += `
            <tr class="live-stream-row">
                <td><strong>#${item.id}</strong></td>
                <td><strong>${item.food_type}</strong></td>
                <td><strong style="color: var(--primary);">${item.quantity} ${item.unit}</strong></td>
                <td>${item.donor}</td>
                <td>${item.location}</td>
                <td><span class="status-badge ${badgeClass}">${item.status}</span></td>
                <td><small style="color: var(--text-muted);">${item.created_at}</small></td>
            </tr>
        `;
    });
    tableBody.innerHTML = rowsHtml;
}
