const TYPE_COLORS = {
  normal: "#a8a77a", fire: "#ee8130", water: "#6390f0", electric: "#f7d02c",
  grass: "#7ac74c", ice: "#96d9d6", fighting: "#c22e28", poison: "#a33ea1",
  ground: "#e2bf65", flying: "#a98ff3", psychic: "#f95587", bug: "#a6b91a",
  rock: "#b6a136", ghost: "#735797", dragon: "#6f35fc", dark: "#705746",
  steel: "#b7b7ce", fairy: "#d685ad",
};
const STAT_LABELS = [
  ["hp", "HP"], ["attack", "Attack"], ["defense", "Defense"],
  ["special_attack", "Sp. attack"], ["special_defense", "Sp. defense"], ["speed", "Speed"],
];
const state = { page: 1, query: "", type: "", generation: "", sort: "number", pages: 1, requestId: 0 };
const elements = {
  grid: document.querySelector("#pokemon-grid"),
  resultCount: document.querySelector("#result-count"),
  pageLabel: document.querySelector("#page-label"),
  pageNumber: document.querySelector("#page-number"),
  previous: document.querySelector("#previous-page"),
  next: document.querySelector("#next-page"),
  emptyState: document.querySelector("#empty-state"),
  search: document.querySelector("#search-input"),
  type: document.querySelector("#type-filter"),
  generation: document.querySelector("#generation-filter"),
  sort: document.querySelector("#sort-select"),
  dialog: document.querySelector("#pokemon-dialog"),
  dialogContent: document.querySelector("#dialog-content"),
};

function escapeHtml(value = "") {
  return String(value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[character]);
}

function typeColor(type) {
  return TYPE_COLORS[type] || "#8b988d";
}

function formatNumber(number) {
  return Number(number || 0).toLocaleString();
}

async function fetchJson(url) {
  const response = await fetch(url);
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || `Request failed (${response.status})`);
  return payload;
}

function renderFailure(message) {
  elements.grid.innerHTML = `<div class="empty-state"><span>!</span><h3>Could not load Pokémon</h3><p>${escapeHtml(message)}</p></div>`;
  elements.grid.style.display = "block";
  elements.emptyState.hidden = true;
}

async function loadOverview() {
  const overview = await fetchJson("/api/overview");
  document.querySelector("#pokemon-count").textContent = formatNumber(overview.summary.pokemon_count);
  document.querySelector("#generation-count").textContent = formatNumber(overview.summary.generation_count);
  document.querySelector("#legendary-count").textContent = formatNumber(overview.summary.legendary_count);
  document.querySelector("#average-stats").textContent = formatNumber(overview.summary.average_stats);

  for (const type of overview.types) {
    elements.type.add(new Option(`${type.name[0].toUpperCase()}${type.name.slice(1)}`, type.name));
  }
  for (const generation of overview.generations) {
    elements.generation.add(new Option(`Generation ${generation}`, generation));
  }
  renderTypeChart(overview.types);
  renderTopPokemon(overview.top_pokemon);
}

function renderTypeChart(types) {
  const total = types.reduce((sum, type) => sum + type.count, 0) || 1;
  const topTypes = types.slice(0, 6);
  document.querySelector("#type-chart").innerHTML = topTypes.map((type) =>
    `<span class="type-chart-segment" title="${escapeHtml(type.name)}: ${type.count}" style="width:${(type.count / total) * 100}%;background:${typeColor(type.name)}"></span>`,
  ).join("");
  document.querySelector("#type-legend").innerHTML = topTypes.map((type) =>
    `<span class="legend-item"><i class="legend-swatch" style="background:${typeColor(type.name)}"></i>${escapeHtml(type.name)}<span class="legend-count">${type.count}</span></span>`,
  ).join("");
}

function renderTopPokemon(pokemon) {
  document.querySelector("#top-pokemon").innerHTML = pokemon.map((item) =>
    `<button class="top-pick" type="button" data-pokemon-id="${item.id}" aria-label="View ${escapeHtml(item.name)}">
      <span class="top-pick-image">${item.sprite_url ? `<img src="${escapeHtml(item.sprite_url)}" alt="" loading="lazy">` : "◉"}</span>
      <span class="top-pick-name">${escapeHtml(item.name)}</span><span class="top-pick-stat">${item.total_stats} BST</span>
    </button>`,
  ).join("");
  document.querySelector("#top-pokemon").addEventListener("click", handlePokemonClick);
}

function renderPokemon(pokemon) {
  elements.grid.style.display = "grid";
  elements.grid.innerHTML = pokemon.map((item) => {
    const types = (item.types || "").split(",").map((type) => type.trim()).filter(Boolean);
    const marks = item.is_legendary ? "✦" : item.is_mythical ? "✧" : "";
    return `<button class="pokemon-card" type="button" data-pokemon-id="${item.id}" aria-label="View ${escapeHtml(item.name)} details">
      <span class="card-top"><span>#${String(item.id).padStart(4, "0")}</span><span class="card-special">${marks}</span></span>
      <span class="pokemon-art">${item.sprite_url ? `<img src="${escapeHtml(item.sprite_url)}" alt="${escapeHtml(item.name)}" loading="lazy">` : "<span>◉</span>"}</span>
      <span class="pokemon-name">${escapeHtml(item.name)}</span>
      <span class="type-pills">${types.map((type) => `<span class="type-pill" style="background:${typeColor(type)}">${escapeHtml(type)}</span>`).join("")}</span>
      <span class="card-stats"><span>BST <strong>${item.total_stats ?? "—"}</strong></span><span>·</span><span>SPD <strong>${item.speed ?? "—"}</strong></span></span>
    </button>`;
  }).join("");
  elements.emptyState.hidden = pokemon.length !== 0;
  elements.grid.style.display = pokemon.length ? "grid" : "none";
}

async function loadPokemon() {
  const requestId = ++state.requestId;
  const parameters = new URLSearchParams({
    page: state.page, q: state.query, type: state.type,
    generation: state.generation, sort: state.sort,
  });
  elements.grid.innerHTML = Array.from({ length: 12 }, () => '<div class="loading-card"></div>').join("");
  elements.grid.style.display = "grid";
  elements.emptyState.hidden = true;
  try {
    const result = await fetchJson(`/api/pokemon?${parameters}`);
    if (requestId !== state.requestId) return;
    renderPokemon(result.items);
    state.pages = result.pages;
    elements.resultCount.textContent = `(${formatNumber(result.count)})`;
    const start = result.count ? (result.page - 1) * result.page_size + 1 : 0;
    const end = Math.min(result.page * result.page_size, result.count);
    elements.pageLabel.textContent = result.count ? `Showing ${start}–${end} of ${formatNumber(result.count)} Pokémon` : "No Pokémon to show";
    elements.pageNumber.textContent = `Page ${result.page} of ${Math.max(result.pages, 1)}`;
    elements.previous.disabled = result.page <= 1;
    elements.next.disabled = result.page >= result.pages;
  } catch (error) {
    if (requestId === state.requestId) renderFailure(error.message);
  }
}

async function openPokemon(id) {
  try {
    const pokemon = await fetchJson(`/api/pokemon/${id}`);
    const types = (pokemon.types || "").split(",").map((type) => type.trim()).filter(Boolean);
    const facts = [
      ["Height", `${(pokemon.height / 100).toFixed(1)} m`],
      ["Weight", `${Number(pokemon.weight).toFixed(1)} kg`],
      ["Generation", pokemon.generation ? `Generation ${pokemon.generation}` : "Unknown"],
      ["Base experience", pokemon.base_experience ?? "Unknown"],
      ["Abilities", pokemon.abilities || "Unknown"],
      ["Hidden ability", pokemon.hidden_abilities || "None"],
      ["Capture rate", pokemon.capture_rate ?? "Unknown"],
      ["Base happiness", pokemon.base_happiness ?? "Unknown"],
    ];
    elements.dialogContent.innerHTML = `
      <div class="dialog-hero">
        <div class="dialog-number">#${String(pokemon.id).padStart(4, "0")}</div>
        ${pokemon.sprite_url ? `<img src="${escapeHtml(pokemon.sprite_url)}" alt="${escapeHtml(pokemon.name)}">` : ""}
        <h2>${escapeHtml(pokemon.name)}</h2>
        <div class="type-pills">${types.map((type) => `<span class="type-pill" style="background:${typeColor(type)}">${escapeHtml(type)}</span>`).join("")}</div>
      </div>
      <div class="dialog-detail">
        <div class="detail-section-title">BASE STATS <span style="float:right">TOTAL ${pokemon.total_stats ?? "—"}</span></div>
        ${STAT_LABELS.map(([key, label]) => `<div class="stat-row"><span>${label}</span><span class="stat-number">${pokemon[key] ?? "—"}</span><span class="stat-track"><span class="stat-fill" style="display:block;width:${Math.min(100, (pokemon[key] / 180) * 100)}%;background:${typeColor(pokemon.primary_type)}"></span></span></div>`).join("")}
        <div class="detail-section-title">SPECIES DETAILS</div>
        <div class="detail-facts">${facts.map(([label, value]) => `<div class="fact"><div class="fact-label">${escapeHtml(label)}</div><div class="fact-value">${escapeHtml(value)}</div></div>`).join("")}</div>
      </div>`;
    elements.dialog.showModal();
  } catch (error) {
    renderFailure(error.message);
  }
}

function handlePokemonClick(event) {
  const button = event.target.closest("[data-pokemon-id]");
  if (button) openPokemon(button.dataset.pokemonId);
}

elements.search.addEventListener("input", () => {
  window.clearTimeout(elements.search.debounceTimer);
  elements.search.debounceTimer = window.setTimeout(() => {
    state.query = elements.search.value;
    state.page = 1;
    loadPokemon();
  }, 180);
});
elements.type.addEventListener("change", () => { state.type = elements.type.value; state.page = 1; loadPokemon(); });
elements.generation.addEventListener("change", () => { state.generation = elements.generation.value; state.page = 1; loadPokemon(); });
elements.sort.addEventListener("change", () => { state.sort = elements.sort.value; state.page = 1; loadPokemon(); });
elements.previous.addEventListener("click", () => { if (state.page > 1) { state.page -= 1; loadPokemon(); } });
elements.next.addEventListener("click", () => { if (state.page < state.pages) { state.page += 1; loadPokemon(); } });
elements.grid.addEventListener("click", handlePokemonClick);
document.querySelector(".dialog-close").addEventListener("click", () => elements.dialog.close());
elements.dialog.addEventListener("click", (event) => {
  if (event.target === elements.dialog) elements.dialog.close();
});
document.addEventListener("keydown", (event) => {
  if (event.key === "/" && !["INPUT", "SELECT", "TEXTAREA"].includes(document.activeElement.tagName)) {
    event.preventDefault();
    elements.search.focus();
  }
});

Promise.all([loadOverview(), loadPokemon()]).catch((error) => {
  renderFailure(error.message);
  document.querySelector("#pokemon-count").textContent = "—";
});
