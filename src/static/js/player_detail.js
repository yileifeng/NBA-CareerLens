const playerId = window.PLAYER_ID;

// query selectors
const playerName = document.getElementById('player-name');
const playerSeason = document.getElementById('player-season');

const projLoading = document.getElementById('projection-loading');
const projError = document.getElementById('projection-error');
const projContent = document.getElementById('projection-content');
const projSeason = document.getElementById('projection-season');

const similarLoading = document.getElementById('similar-loading');
const similarError = document.getElementById('similar-error');
const similarContent = document.getElementById('similar-content');
const similarTableBody = document.getElementById('similar-table-body');

const projectedPpg = document.getElementById('projected-ppg');
const projectedRpg = document.getElementById('projected-rpg');
const projectedApg = document.getElementById('projected-apg');

const trajectoryLoading = document.getElementById('trajectory-loading');
const trajectoryError = document.getElementById('trajectory-error');
const trajectoryContent = document.getElementById('trajectory-content');
const trajectoryList = document.getElementById('trajectory-list');

const historyLoading = document.getElementById('history-loading');
const historyError = document.getElementById('history-error');
const historyContent = document.getElementById('history-content');
const historyTableBody = document.getElementById('history-table-body');
const historyCount = document.getElementById('history-count');

const historyCollapse = document.getElementById('history-collapse');
const historyToggle = document.getElementById('history-toggle');
const historyToggleText = document.getElementById('history-toggle-text');
const historyToggleIcon = document.getElementById('history-toggle-icon');

historyCollapse.addEventListener('show.bs.collapse', () => {
    historyToggleText.textContent = 'Hide table';
    historyToggleIcon.textContent = '▲';
});

historyCollapse.addEventListener('hide.bs.collapse', () => {
    historyToggleText.textContent = 'Show table';
    historyToggleIcon.textContent = '▼';
});

const careerChartLoading = document.getElementById('career-chart-loading');
const careerChartError = document.getElementById('career-chart-error');
const careerChartContent = document.getElementById('career-chart-content');
const careerChartCanvas = document.getElementById('career-chart');

let careerChart = null;

// format statistic value
function formatStat(value) {
    if (value === null || value === undefined) {
        return '—';
    }

    return Number(value).toFixed(1);
}

// format similariy values
function formatPercentage(value) {
    if (value === null || value === undefined) {
        return '—';
    }

    const numericValue = Number(value);
    return `${(numericValue * 100).toFixed(1)}%`;
}

// call API endpoint for loading player projection
async function loadProjection() {
    try {
        const response = await fetch(`/api/players/${playerId}/projection?history=3`);

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Unable to load player projection.');
        }

        // populate DOM
        playerName.textContent = data.player_name;
        playerSeason.textContent = `Latest season: ${data.latest_season}`;
        projSeason.textContent = data.projection_season;

        // projections
        projectedPpg.textContent = formatStat(data.projected_stats.points_per_game);
        projectedRpg.textContent = formatStat(data.projected_stats.rebounds_per_game);
        projectedApg.textContent = formatStat(data.projected_stats.assists_per_game);

        projLoading.classList.add('d-none');
        projError.classList.add('d-none');
        projContent.classList.remove('d-none');

        await loadSimilarPlayers(data.latest_season);
    } catch (error) {
        // hide all DOM elements on error
        projLoading.classList.add('d-none');
        projError.textContent = error.message;
        projError.classList.remove('d-none');

        similarLoading.classList.add('d-none');
        similarError.textContent = 'Similar players could not be loaded.';
        similarError.classList.remove('d-none');
    }
}

// call API endpoint for loading similar player comps
async function loadSimilarPlayers(season) {
    // unhide player comp DOM elements
    similarLoading.classList.remove('d-none');
    similarError.classList.add('d-none');
    similarContent.classList.add('d-none');

    try {
        const params = new URLSearchParams({
            season,
            limit: '5'
        });

        const response = await fetch(`/api/players/${playerId}/similar?${params.toString()}`);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Unable to load similar players.');
        }

        renderSimilarPlayers(data.similar_players);
        similarLoading.classList.add('d-none');
    } catch (error) {
        // hide all player comp DOM elements
        similarLoading.classList.add('d-none');
        similarError.textContent = error.message;
        similarError.classList.remove('d-none');
    }
}

// display all similar player comparisons on page
function renderSimilarPlayers(players) {
    similarTableBody.innerHTML = '';

    // for each player comp create a new row in table
    for (const player of players) {
        const row = document.createElement('tr');

        row.classList.add('player-row');
        row.innerHTML = `
            <td>
                <span class="fw-semibold">
                    ${player.player_name}
                </span>
            </td>
            <td class="similarity-score">
                ${formatPercentage(player.similarity)}
            </td>
            <td>
                ${formatStat(player.points_per_game ?? player.stats?.points_per_game)}
            </td>
            <td>
                ${formatStat(player.rebounds_per_game ?? player.stats?.rebounds_per_game)}
            </td>
            <td>
                ${formatStat(player.assists_per_game ?? player.stats?.assists_per_game)}
            </td>
        `;

        // link to player comp id
        row.addEventListener('click', () => {
            window.location.href = `/players/${player.player_id}`;
        });

        similarTableBody.appendChild(row);
    }

    similarError.classList.add('d-none');
    similarContent.classList.remove('d-none');
}

// call API endpoint to load trajectory player comps
async function loadTrajectoryComparisons() {
    // hide error messages and unhide loading indicator
    trajectoryLoading.classList.remove('d-none');
    trajectoryError.classList.add('d-none');
    trajectoryContent.classList.add('d-none');

    try {
        const params = new URLSearchParams({
            seasons: '3',
            limit: '5'
        });

        const response = await fetch(`/api/players/${playerId}/trajectory-comp?${params.toString()}`);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Unable to load trajectory comparisons.');
        }

        renderTrajectoryComparisons(data.trajectory_comparisons);
        trajectoryLoading.classList.add('d-none');
    } catch (error) {
        // hide loading indicator and unhide error
        trajectoryLoading.classList.add('d-none');
        trajectoryError.textContent = error.message;
        trajectoryError.classList.remove('d-none');
    }
}

// normalize object and flattened list trajectory input
function normalizeTrajectory(trajectory) {
    if (!Array.isArray(trajectory)) {
        return [];
    }

    // base off of API return object structure
    if (trajectory.length > 0 && typeof trajectory[0] === 'object') {
        return trajectory.map((entry, index) => ({
            year: entry.years_of_experience ?? index + 1,
            points_per_game: entry.stats?.points_per_game ?? entry.points_per_game,
            rebounds_per_game: entry.stats?.rebounds_per_game ?? entry.rebounds_per_game,
            assists_per_game: entry.stats?.assists_per_game ?? entry.assists_per_game
        }));
    }

    // otherwise flattened API structure: [year1 PPG, year1 RPG, year1 APG, year2 PPG, year2 RPG, year2 APG, ...]
    const res = [];
    for (let index = 0; index < trajectory.length; index += 3) {
        res.push({
            year: index / 3 + 1,
            points_per_game: trajectory[index],
            rebounds_per_game: trajectory[index + 1],
            assists_per_game: trajectory[index + 2]
        });
    }
    return res;
}

// display all similar player trajectory comparisons on page
function renderTrajectoryComparisons(comparisons) {
    trajectoryList.innerHTML = '';

    for (const comp of comparisons) {
        const column = document.createElement('div');
        column.className = 'col-md-6 col-xl-4';

        const yearlyStats = normalizeTrajectory(comp.trajectory);
        const historyRows = yearlyStats
            .map(
                (year) => `
                <tr>
                    <td>Year ${year.year}</td>
                    <td>${formatStat(year.points_per_game)}</td>
                    <td>${formatStat(year.rebounds_per_game)}</td>
                    <td>${formatStat(year.assists_per_game)}</td>
                </tr>
            `
            )
            .join('');

        // construct player comp UI
        column.innerHTML = `
            <div class="comp-card h-100">
                <div
                    class="d-flex justify-content-between
                           align-items-start mb-3"
                >
                    <div>
                        <h3 class="h6 mb-1">
                            ${comp.player_name}
                        </h3>
                    </div>
                    <span class="badge text-bg-primary">
                        ${formatPercentage(comp.similarity)}
                    </span>
                </div>

                <div class="table-responsive">
                    <table class="table table-sm mb-0">
                        <thead>
                            <tr>
                                <th>Season</th>
                                <th>PPG</th>
                                <th>RPG</th>
                                <th>APG</th>
                            </tr>
                        </thead>

                        <tbody>
                            ${historyRows}
                        </tbody>
                    </table>
                </div>

                <button
                    type="button"
                    class="btn btn-outline-primary btn-sm mt-3
                           view-comp-player"
                >
                    View player
                </button>
            </div>
        `;
        const button = column.querySelector('.view-comp-player');

        // add event handler to navigate to comp player's profile
        button.addEventListener('click', () => {
            window.location.href = `/players/${comp.player_id}`;
        });

        trajectoryList.appendChild(column);
    }

    trajectoryError.classList.add('d-none');
    trajectoryContent.classList.remove('d-none');
}

// call API endpoint to load player historical data
async function loadPlayerHistory() {
    // hide error messages and unhide loading indicator
    historyLoading.classList.remove('d-none');
    historyError.classList.add('d-none');
    historyContent.classList.add('d-none');

    try {
        const response = await fetch(`/api/players/${playerId}/seasons`);

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Unable to load career history.');
        }

        // render HTML for player history
        renderPlayerHistory(data.seasons);
        renderCareerChart(data.seasons);
        historyLoading.classList.add('d-none');
    } catch (error) {
        // hide loading indicator and unhide error messages
        historyLoading.classList.add('d-none');
        historyError.textContent = error.message;
        historyError.classList.remove('d-none');
    }
}

// render UI for player historical data
function renderPlayerHistory(seasons) {
    historyTableBody.innerHTML = '';
    historyCount.textContent = `${seasons.length} season${seasons.length === 1 ? '' : 's'}`;

    // for each season render valid table row data
    for (const season of seasons) {
        const row = document.createElement('tr');

        // add all season metadata and player statistics
        row.innerHTML = `
            <td class="fw-semibold">
                ${season.season ?? '—'}
            </td>
            <td>${season.team_abbreviation ?? '—'}</td>
            <td>${season.age ?? '—'}</td>
            <td>${season.games_played ?? '—'}</td>
            <td>
                ${formatStat(season.minutes_per_game)}
            </td>
            <td class="fw-semibold">
                ${formatStat(season.points_per_game)}
            </td>
            <td>
                ${formatStat(season.rebounds_per_game)}
            </td>
            <td>
                ${formatStat(season.assists_per_game)}
            </td>
            <td>
                ${formatPercentage(season.field_goal_pct)}
            </td>
            <td>
                ${formatPercentage(season.three_point_pct)}
            </td>
            <td>
                ${formatPercentage(season.free_throw_pct)}
            </td>
        `;
        historyTableBody.appendChild(row);
    }

    historyError.classList.add('d-none');
    historyContent.classList.remove('d-none');
}

// render player career chart
function renderCareerChart(seasons) {
    const labels = seasons.map((season) => season.season);
    const pointsData = seasons.map((season) => season.points_per_game);
    const reboundsData = seasons.map((season) => season.rebounds_per_game);
    const assistsData = seasons.map((season) => season.assists_per_game);

    // Destroy the previous chart before creating another one.
    if (careerChart) {
        careerChart.destroy();
    }

    // build chart configuration
    careerChart = new Chart(careerChartCanvas, {
        type: 'line',
        data: {
            labels,
            datasets: [
                {
                    label: 'Points per game',
                    data: pointsData,
                    borderColor: '#0d6efd',
                    backgroundColor: '#0d6efd',
                    tension: 0.25,
                    pointRadius: 4,
                    pointHoverRadius: 6
                },
                {
                    label: 'Rebounds per game',
                    data: reboundsData,
                    borderColor: '#198754',
                    backgroundColor: '#198754',
                    tension: 0.25,
                    pointRadius: 4,
                    pointHoverRadius: 6
                },
                {
                    label: 'Assists per game',
                    data: assistsData,
                    borderColor: '#fd7e14',
                    backgroundColor: '#fd7e14',
                    tension: 0.25,
                    pointRadius: 4,
                    pointHoverRadius: 6
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: {
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label(context) {
                            const label = context.dataset.label || '';

                            const value = Number(context.parsed.y).toFixed(1);

                            return `${label}: ${value}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Season'
                    },

                    grid: {
                        display: false
                    }
                },
                y: {
                    beginAtZero: true,

                    title: {
                        display: true,
                        text: 'Per-game average'
                    }
                }
            }
        }
    });

    // hide loading indicators and errors
    careerChartLoading.classList.add('d-none');
    careerChartError.classList.add('d-none');
    careerChartContent.classList.remove('d-none');
}

async function initializePlayerPage() {
    await Promise.all([loadPlayerHistory(), loadProjection(), loadTrajectoryComparisons()]);
}

initializePlayerPage();
