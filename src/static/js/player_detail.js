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

// format statistic value
function formatStat(value) {
    if (value === null || value === undefined) {
        return '—';
    }

    return Number(value).toFixed(1);
}

// format similariy values
function formatSimilarity(value) {
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
                ${formatSimilarity(player.similarity)}
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

loadProjection();
await loadSimilarPlayers(data.latest_season);
