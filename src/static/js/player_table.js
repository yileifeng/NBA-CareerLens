// query selectors
const seasonFilter = document.getElementById("season-filter");
const playerSearch = document.getElementById("player-search");
const searchButton = document.getElementById("search-button");

const tableContainer = document.getElementById("table-container");
const tableBody = document.getElementById("player-table-body");

const loadingMessage = document.getElementById("loading-message");
const errorMessage = document.getElementById("error-message");
const emptyMessage = document.getElementById("empty-message");

const prevButton = document.getElementById("previous-page");
const nextButton = document.getElementById("next-page");

const pageInfo = document.getElementById("page-information");
const resultCount = document.getElementById("result-count");

let currentPage = 1;
const perPage = 25;

// format statistic value
function formatNumber(value, decimalPlaces = 1) {
    if (value === null || value === undefined) {
        return "—";
    }

    return Number(value).toFixed(decimalPlaces);
}

// format percentage values
function formatPercentage(value) {
    if (value === null || value === undefined) {
        return "—";
    }

    return `${(Number(value) * 100).toFixed(1)}%`;
}

// call API endpoint to load season stats data
async function loadSeasons() {
    try {
        const response = await fetch("/api/seasons");

        if (!response.ok) {
            throw new Error("Unable to load available seasons.");
        }

        const data = await response.json();

        // add each season as an option in select dropdown
        for (const season of data.seasons) {
            const option = document.createElement("option");

            option.value = season;
            option.textContent = season;

            seasonFilter.appendChild(option);
        }

        if (data.seasons.length > 0) {
            seasonFilter.value = data.seasons[0];
        }
    } catch (error) {
        showError(error.message);
    }
}

// build each player's stats as a row in database summary table
function buildPlayerRow(player) {
    const row = document.createElement("tr");
    row.classList.add("player-row");
    row.dataset.playerId = player.player_id;

    // add all player metadata + stats
    row.innerHTML = `
        <td>
            <span class="fw-semibold">
                ${player.player_name}
            </span>
        </td>
        <td>${player.season ?? "—"}</td>
        <td>${player.team_abbreviation ?? "—"}</td>
        <td>${player.age ?? "—"}</td>
        <td>${player.games_played ?? "—"}</td>
        <td>${formatNumber(player.minutes_per_game)}</td>
        <td>${formatNumber(player.points_per_game)}</td>
        <td>${formatNumber(player.rebounds_per_game)}</td>
        <td>${formatNumber(player.assists_per_game)}</td>
        <td>${formatPercentage(player.field_goal_pct)}</td>
        <td>${formatPercentage(player.three_point_pct)}</td>
        <td>${formatPercentage(player.free_throw_pct)}</td>
    `;

    // clicking a player navigates to that player's profile page
    row.addEventListener("click", () => {
        window.location.href = `/players/${player.player_id}`;
    });

    return row;
}

// load players on a given page
async function loadPlayers(page = 1) {
    currentPage = page;
    showLoading();

    const params = new URLSearchParams({
        page: String(currentPage),
        per_page: String(perPage),
    });

    const selectedSeason = seasonFilter.value;
    const searchValue = playerSearch.value.trim();

    if (selectedSeason) {
        params.set("season", selectedSeason);
    }
    if (searchValue) {
        params.set("search", searchValue);
    }

    try {
        const response = await fetch(
            `/api/player-seasons?${params.toString()}`
        );

        if (!response.ok) {
            throw new Error("Unable to load player statistics.");
        }

        const data = await response.json();

        // render players and pagination after loading stats
        renderPlayers(data.items);
        renderPagination(data.pagination);
    } catch (error) {
        showError(error.message);
    }
}

// render players in table
function renderPlayers(players) {
    tableBody.innerHTML = "";

    loadingMessage.classList.add("d-none");
    errorMessage.classList.add("d-none");

    if (players.length === 0) {
        tableContainer.classList.add("d-none");
        emptyMessage.classList.remove("d-none");
        return;
    }

    emptyMessage.classList.add("d-none");
    tableContainer.classList.remove("d-none");

    for (const player of players) {
        tableBody.appendChild(buildPlayerRow(player));
    }
}

// add pagination to tables
function renderPagination(pagination) {
    prevButton.disabled = !pagination.has_previous;
    nextButton.disabled = !pagination.has_next;

    pageInfo.textContent =
        `Page ${pagination.page} of ${pagination.total_pages || 1}`;

    resultCount.textContent =
        `${pagination.total_items} result${pagination.total_items === 1 ? "" : "s"}`;
}

// toggle display on for loading indicator
function showLoading() {
    loadingMessage.classList.remove("d-none");
    errorMessage.classList.add("d-none");
    emptyMessage.classList.add("d-none");
    tableContainer.classList.add("d-none");
}

// toggle display on for error messages
function showError(message) {
    loadingMessage.classList.add("d-none");
    tableContainer.classList.add("d-none");
    emptyMessage.classList.add("d-none");

    errorMessage.textContent = message;
    errorMessage.classList.remove("d-none");
}

searchButton.addEventListener("click", () => {
    loadPlayers(1);
});
playerSearch.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
        loadPlayers(1);
    }
});
seasonFilter.addEventListener("change", () => {
    loadPlayers(1);
});
prevButton.addEventListener("click", () => {
    if (currentPage > 1) {
        loadPlayers(currentPage - 1);
    }
});
nextButton.addEventListener("click", () => {
    loadPlayers(currentPage + 1);
});

async function initializePage() {
    await loadSeasons();
    await loadPlayers(1);
}

initializePage();