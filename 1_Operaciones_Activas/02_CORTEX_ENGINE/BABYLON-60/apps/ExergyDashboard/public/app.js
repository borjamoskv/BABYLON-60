// C5-REAL EXERGY CERTIFIED
document.addEventListener('DOMContentLoaded', () => {
    const statusText = document.getElementById('status-text');
    const currentScoreEl = document.getElementById('current-score');
    const scoreTrendEl = document.getElementById('score-trend');
    const latestCommitEl = document.getElementById('latest-commit');
    const entropyStatusEl = document.getElementById('entropy-status');
    const tableBody = document.querySelector('#events-table tbody');
    const sparklineContainer = document.getElementById('sparkline-container');

    const fetchMetrics = async () => {
        try {
            const response = await fetch('/api/metrics');
            if (!response.ok) throw new Error('Network response was not ok');
            const data = await response.json();

            if (data.error) {
                console.error("Server error:", data.error);
                statusText.textContent = "Database Error";
                statusText.style.color = "var(--danger-color)";
                return;
            }

            statusText.textContent = "Synchronized";
            statusText.style.color = "var(--success-color)";

            if (data.length > 0) {
                updateKPIs(data[0], data);
                updateTable(data);
                drawSparkline(data);
            }
        } catch (error) {
            console.error('Error fetching metrics:', error);
            statusText.textContent = "Connection Lost";
            statusText.style.color = "var(--danger-color)";
        }
    };

    const updateKPIs = (latest, allData) => {
        const score = parseFloat(latest.exergy_score).toFixed(1);
        currentScoreEl.textContent = score;

        if (score >= 950) {
            currentScoreEl.style.color = "var(--success-color)";
        } else if (score >= 700) {
            currentScoreEl.style.color = "var(--warning-color)";
        } else {
            currentScoreEl.style.color = "var(--danger-color)";
        }

        latestCommitEl.textContent = latest.commit_hash.substring(0, 7);
        entropyStatusEl.textContent = latest.entropy === "No anomalies detected." ? "Optimal" : "Anomalies Detected";

        if (allData.length > 1) {
            const prevScore = parseFloat(allData[1].exergy_score);
            const diff = (score - prevScore).toFixed(1);
            if (diff > 0) {
                scoreTrendEl.textContent = `▲ +${diff} from last commit`;
                scoreTrendEl.style.color = "var(--success-color)";
            } else if (diff < 0) {
                scoreTrendEl.textContent = `▼ ${diff} from last commit`;
                scoreTrendEl.style.color = "var(--danger-color)";
            } else {
                scoreTrendEl.textContent = `▶ Stable at ${score}`;
                scoreTrendEl.style.color = "var(--text-secondary)";
            }
        }
    };

    const updateTable = (data) => {
        tableBody.innerHTML = '';
        data.slice(0, 10).forEach(row => {
            const tr = document.createElement('tr');

            const date = new Date(row.timestamp * 1000);
            const scoreClass = row.exergy_score >= 950 ? 'optimal' : (row.exergy_score >= 700 ? 'warning' : 'danger');

            tr.innerHTML = `
                <td>${date.toLocaleTimeString()}</td>
                <td class="td-hash">${row.commit_hash.substring(0, 7)}</td>
                <td class="td-score ${scoreClass}">${parseFloat(row.exergy_score).toFixed(1)}</td>
                <td>${row.entropy}<br><span style="font-size:0.8rem;color:var(--text-secondary)">${row.gradient}</span></td>
            `;
            tableBody.appendChild(tr);
        });
    };

    const drawSparkline = (data) => {
        // Reverse data to show oldest to newest (left to right)
        const chartData = [...data].slice(0, 20).reverse().map(d => parseFloat(d.exergy_score));
        if (chartData.length < 2) return;

        const w = sparklineContainer.clientWidth;
        const h = sparklineContainer.clientHeight;
        const padding = 10;

        const min = Math.min(...chartData, 500); // Floor at 500 for scale
        const max = 1000; // Ceiling at 1000

        const scaleX = (w - padding * 2) / (chartData.length - 1);
        const scaleY = (h - padding * 2) / (max - min);

        const points = chartData.map((val, i) => {
            const x = padding + i * scaleX;
            const y = h - padding - (val - min) * scaleY;
            return `${x},${y}`;
        });

        const pathD = `M ${points.join(' L ')}`;
        const areaD = `${pathD} L ${padding + (chartData.length - 1) * scaleX},${h} L ${padding},${h} Z`;

        sparklineContainer.innerHTML = `
            <svg viewBox="0 0 ${w} ${h}">
                <defs>
                    <linearGradient id="gradient" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" stop-color="var(--accent-color)" stop-opacity="0.8" />
                        <stop offset="100%" stop-color="var(--accent-color)" stop-opacity="0" />
                    </linearGradient>
                </defs>
                <path class="sparkline-area" d="${areaD}" />
                <path class="sparkline-path" d="${pathD}" />
            </svg>
        `;
    };

    // Initial fetch
    fetchMetrics();

    // Poll every 5 seconds
    setInterval(fetchMetrics, 5000);

    // Redraw chart on resize
    window.addEventListener('resize', () => {
        fetchMetrics();
    });
});
