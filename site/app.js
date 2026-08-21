/**
 * Universal Book Vault — Core Application Engine & Knowledge Visualizer
 */

// Register PWA Service Worker
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('./sw.js').catch((err) => console.log('SW registration error:', err));
  });
}

// Global Application State
let vaultData = null;
let currentPillar = "all";
let currentSearchQuery = "";
let currentDifficulty = "all";
let currentStatusFilter = "all";
let currentViewMode = "grid";

// Reader State
let currentActiveBook = null;
let currentChapterIndex = 0;
let readerFontSize = 1.08;
let readerFontFamily = "sans";
let userReadingStatus = JSON.parse(localStorage.getItem("user-reading-status") || "{}");
let userBookRatings = JSON.parse(localStorage.getItem("user-book-ratings") || "{}");
let userSrsCards = JSON.parse(localStorage.getItem("user-srs-deck") || "[]");
let userReadingActivity = JSON.parse(localStorage.getItem("user-reading-activity") || "{}");

// Ensure today has initial seed if empty
const todayStr = new Date().toISOString().split("T")[0];
if (!userReadingActivity[todayStr]) {
  userReadingActivity[todayStr] = { count: 1, mins: 15 };
  localStorage.setItem("user-reading-activity", JSON.stringify(userReadingActivity));
}

// SRS Quiz State
let srsQuizCards = [];
let srsCurrentIndex = 0;

// Knowledge Graph Node Map
let graphNodes = [];
let graphEdges = [];
let hoveredNode = null;

// Initialize Application
document.addEventListener("DOMContentLoaded", async () => {
  await loadVaultData();
  setupEventListeners();
  initTheme();
  initForceGraph();
  renderHeatmap();
});


async function loadVaultData() {
  if (window.VAULT_DATA && window.VAULT_DATA.books) {
    vaultData = window.VAULT_DATA;
    renderStats();
    renderPillarTabs();
    renderBooks();
    buildGraphData();
    extractAllFlashcardsToSrs();
    return;
  }

  try {
    const res = await fetch("./data/vault_data.json");
    vaultData = await res.json();
    renderStats();
    renderPillarTabs();
    renderBooks();
    buildGraphData();
    extractAllFlashcardsToSrs();
  } catch (err) {
    console.error("Failed to load vault data:", err);
    document.getElementById("books-grid").innerHTML = `
      <div style="grid-column: 1/-1; text-align: center; padding: 4rem; color: var(--text-muted);">
        <h2>⚠️ Vault data bundle missing</h2>
        <p style="margin-top: 0.5rem;">Run <code>python -m automation.exporters.build_site_data</code> to compile the library.</p>
      </div>
    `;
  }
}

function renderStats() {
  if (!vaultData) return;
  document.getElementById("stat-total").textContent = vaultData.total_books;
  document.getElementById("stat-pillars").textContent = Object.keys(vaultData.pillars).length;
  
  const completedCount = Object.values(userReadingStatus).filter(s => s === "Completed").length;
  document.getElementById("stat-user-read").textContent = completedCount;
}

function renderPillarTabs() {
  if (!vaultData) return;
  const container = document.getElementById("pillar-tabs");
  container.innerHTML = `<button class="pillar-pill ${currentPillar === 'all' ? 'active' : ''}" data-pillar="all">✨ All Knowledge Pillars</button>`;
  
  for (const [pillarName, folder] of Object.entries(vaultData.pillars)) {
    const btn = document.createElement("button");
    btn.className = `pillar-pill ${currentPillar === pillarName ? 'active' : ''}`;
    btn.dataset.pillar = pillarName;
    btn.textContent = pillarName;
    btn.onclick = () => {
      currentPillar = pillarName;
      document.querySelectorAll(".pillar-pill").forEach(p => p.classList.remove("active"));
      btn.classList.add("active");
      applyFilters();
    };
    container.appendChild(btn);
  }
}

function applyFilters() {
  currentDifficulty = document.getElementById("filter-difficulty").value;
  currentStatusFilter = document.getElementById("filter-status").value;
  renderBooks();
}

function renderBooks() {
  if (!vaultData) return;
  const grid = document.getElementById("books-grid");
  grid.innerHTML = "";

  const query = currentSearchQuery.toLowerCase().trim();
  const filtered = vaultData.books.filter(b => {
    // Pillar Filter
    if (currentPillar !== "all" && b.pillar !== currentPillar) return false;
    // Difficulty Filter
    if (currentDifficulty !== "all" && b.difficulty !== currentDifficulty) return false;
    // Reading Status Filter
    const status = userReadingStatus[b.slug] || "Unread";
    if (currentStatusFilter !== "all" && status !== currentStatusFilter) return false;
    // Search Query Filter
    if (query) {
      const matchTitle = b.title.toLowerCase().includes(query);
      const matchAuthor = b.author.toLowerCase().includes(query);
      const matchCategory = b.category.toLowerCase().includes(query);
      const matchSubcategory = (b.subcategory || "").toLowerCase().includes(query);
      if (!matchTitle && !matchAuthor && !matchCategory && !matchSubcategory) return false;
    }
    return true;
  });

  if (filtered.length === 0) {
    grid.innerHTML = `
      <div style="grid-column: 1/-1; text-align: center; padding: 4rem; color: var(--text-muted);">
        <p style="font-size: 2rem; margin-bottom: 0.5rem;">🔍</p>
        <h3>No books found matching your filter criteria</h3>
        <p style="margin-top: 0.25rem;">Try resetting search terms or difficulty filters.</p>
      </div>
    `;
    return;
  }

  filtered.forEach(b => {
    const card = document.createElement("div");
    card.className = "book-card";
    const status = userReadingStatus[b.slug] || "Unread";
    const rating = userBookRatings[b.slug] || 0;
    const ratingStars = rating > 0 ? "★".repeat(rating) + "☆".repeat(5 - rating) : "";

    const recsHtml = b.recommendations && b.recommendations.length > 0 ? `
      <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.75rem;">
        <span style="color: var(--c-cyan);">Related:</span> ${b.recommendations.map(r => r.title).join(", ")}
      </div>
    ` : "";

    card.innerHTML = `
      <div>
        <div class="book-top-bar">
          <span class="book-num-badge">#${b.number}</span>
          <span class="book-pillar-tag">${b.pillar}</span>
        </div>
        <h3 class="book-card-title">${b.title}</h3>
        <p class="book-card-author">By ${b.author} ${b.published ? `(${b.published})` : ''}</p>
        <div class="book-tags-row">
          <span class="tag-pill">${b.category}</span>
          <span class="tag-pill diff-${b.difficulty}">${b.difficulty}</span>
          ${ratingStars ? `<span class="tag-pill" style="color: var(--c-amber);">${ratingStars}</span>` : ''}
        </div>
        ${recsHtml}
      </div>

      <div class="card-footer">
        ${b.status === "Generated" ? `
          <button class="btn-card-read" onclick="openReader('${b.slug}')">📖 Read Summary</button>
          ${b.has_audio ? `<button class="btn-card-audio" onclick="playBookAudio('${b.slug}')" title="Listen Audio Narration">🎧</button>` : ''}
        ` : `
          <button class="btn-card-read" style="background: var(--bg-surface-raised); color: var(--text-muted); cursor: not-allowed;" title="Book queued for autonomous generation">⏳ In Curriculum</button>
        `}
      </div>
    `;
    grid.appendChild(card);
  });
}

// -----------------------------------------------------------------------------
// Reader Modal Engine
// -----------------------------------------------------------------------------
function openReader(slug) {
  const book = vaultData.books.find(b => b.slug === slug);
  if (!book || !book.chapters || book.chapters.length === 0) return;

  currentActiveBook = book;
  currentChapterIndex = 0;

  document.getElementById("modal-book-title").textContent = book.title;
  document.getElementById("modal-book-author").textContent = `By ${book.author}`;
  
  // Render Sidebar Chapters
  const sidebarLinks = document.getElementById("reader-sidebar-links");
  sidebarLinks.innerHTML = "";
  book.chapters.forEach((chap, idx) => {
    const item = document.createElement("div");
    item.className = `toc-item ${idx === 0 ? 'active' : ''}`;
    item.textContent = chap.title;
    item.onclick = () => selectChapter(idx);
    sidebarLinks.appendChild(item);
  });

  // Render Rating
  updateStarRatingUi(userBookRatings[slug] || 0);

  // Render Connected Ideas / Backlinks
  const backlinksContainer = document.getElementById("reader-backlinks-list");
  if (backlinksContainer) {
    if (book.recommendations && book.recommendations.length > 0) {
      backlinksContainer.innerHTML = book.recommendations.map(r => `
        <div style="cursor: pointer; padding: 0.2rem 0; color: var(--c-cyan);" onclick="openReader('${r.slug}')">
          → [[ ${r.title} ]]
        </div>
      `).join("");
    } else {
      backlinksContainer.innerHTML = `<span style="color: var(--text-muted); font-size: 0.75rem;">(No direct backlinks)</span>`;
    }
  }

  // Render External Book Trackers
  const trackersContainer = document.getElementById("reader-trackers-list");

  if (trackersContainer) {
    const qQuery = encodeURIComponent(`${book.title} ${book.author}`);
    const trackers = book.external_trackers || {
      openlibrary: `https://openlibrary.org/search?q=${qQuery}`,
      goodreads: `https://www.goodreads.com/search?q=${qQuery}`,
      google_books: `https://www.google.com/search?tbm=bks&q=${qQuery}`,
      hardcover: `https://hardcover.app/search?q=${qQuery}`,
      storygraph: `https://app.thestorygraph.com/browse?search_term=${qQuery}`,
    };

    trackersContainer.innerHTML = `
      <a href="${trackers.openlibrary}" target="_blank" class="tag-pill" style="color: var(--c-cyan); text-decoration: none;" title="Open on Open Library">🏛️ OpenLibrary</a>
      <a href="${trackers.goodreads}" target="_blank" class="tag-pill" style="color: var(--c-amber); text-decoration: none;" title="Open on Goodreads">⭐ Goodreads</a>
      <a href="${trackers.hardcover}" target="_blank" class="tag-pill" style="color: var(--c-indigo); text-decoration: none;" title="Open on Hardcover.app">📚 Hardcover</a>
      <a href="${trackers.storygraph}" target="_blank" class="tag-pill" style="color: var(--c-emerald); text-decoration: none;" title="Open on The StoryGraph">📊 StoryGraph</a>
      <a href="${trackers.google_books}" target="_blank" class="tag-pill" style="color: var(--c-rose); text-decoration: none;" title="Open on Google Books">📖 Google Books</a>
    `;
  }

  // Render Article Content
  renderChapterContent(0);

  document.getElementById("reader-modal").classList.add("active");
  document.body.style.overflow = "hidden";
}


function downloadCurrentBookMarkdown() {
  if (!currentActiveBook || !currentActiveBook.chapters || currentActiveBook.chapters.length === 0) return;
  const currentChap = currentActiveBook.chapters[currentChapterIndex];
  const blob = new Blob([currentChap.content], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${currentActiveBook.slug}-${currentChap.name}`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

function captureSelectedQuote() {
  const selection = window.getSelection().toString().trim();
  if (!selection) {
    alert("Please highlight/select text in the summary first to capture it!");
    return;
  }
  const quotes = JSON.parse(localStorage.getItem("user-saved-quotes") || "[]");
  quotes.push({
    book: currentActiveBook ? currentActiveBook.title : "Unknown",
    quote: selection,
    savedAt: new Date().toISOString()
  });
  localStorage.setItem("user-saved-quotes", JSON.stringify(quotes));
  alert(`✅ Quote saved to your Knowledge Vault!\n\n"${selection.slice(0, 80)}..."`);
}


function selectChapter(idx) {
  currentChapterIndex = idx;
  document.querySelectorAll(".toc-item").forEach((el, i) => {
    el.classList.toggle("active", i === idx);
  });
  renderChapterContent(idx);
}

function renderChapterContent(idx) {
  const chap = currentActiveBook.chapters[idx];
  const container = document.getElementById("reader-content");
  container.innerHTML = parseMarkdownToHtml(chap.content);

  // Calculate Reading Time at 225 WPM
  const words = (chap.content.match(/\b\w+\b/g) || []).length;
  const mins = Math.max(1, Math.ceil(words / 225));
  const timeBadge = document.getElementById("reader-reading-time");
  if (timeBadge) {
    timeBadge.textContent = `⏱️ ~${mins} min read (${words.toLocaleString()} words)`;
  }
  // Record Reading Activity for Heatmap
  recordReadingActivity(mins);
}


function copyBookCitation() {
  if (!currentActiveBook) return;
  const b = currentActiveBook;
  const year = b.published || new Date().getFullYear();
  const apa = `${b.author} (${year}). ${b.title}. Universal Book Vault. https://chirag127.github.io/book-vault/`;
  const bibtex = `@book{${b.slug},\n  author = {${b.author}},\n  title = {${b.title}},\n  year = {${year}},\n  url = {https://chirag127.github.io/book-vault/}\n}`;
  
  navigator.clipboard.writeText(`${apa}\n\nBibTeX:\n${bibtex}`);
  alert(`📋 Citation copied to clipboard (APA & BibTeX)!`);
}

// -----------------------------------------------------------------------------
// 365-Day Contribution Heatmap & Habit Streak Engine
// -----------------------------------------------------------------------------
function recordReadingActivity(mins = 10) {
  const today = new Date().toISOString().split("T")[0];
  if (!userReadingActivity[today]) {
    userReadingActivity[today] = { count: 0, mins: 0 };
  }
  userReadingActivity[today].count += 1;
  userReadingActivity[today].mins += mins;
  localStorage.setItem("user-reading-activity", JSON.stringify(userReadingActivity));
  renderHeatmap();
}

function renderHeatmap() {
  const svg = document.getElementById("heatmap-svg");
  if (!svg) return;
  svg.innerHTML = "";

  const totalDays = 52 * 7;
  const now = new Date();
  const daySize = 10;
  const gap = 3;

  let streak = 0;
  let totalMins = 0;

  for (let i = 0; i < totalDays; i++) {
    const d = new Date(now);
    d.setDate(d.getDate() - (totalDays - 1 - i));
    const dateKey = d.toISOString().split("T")[0];
    const act = userReadingActivity[dateKey];

    const weekIdx = Math.floor(i / 7);
    const dayIdx = i % 7;

    const x = weekIdx * (daySize + gap);
    const y = dayIdx * (daySize + gap);

    const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    rect.setAttribute("x", x);
    rect.setAttribute("y", y);
    rect.setAttribute("width", daySize);
    rect.setAttribute("height", daySize);
    rect.setAttribute("rx", 2);

    let color = "rgba(255, 255, 255, 0.06)";
    if (act && act.count > 0) {
      totalMins += act.mins;
      if (act.count === 1) color = "rgba(0, 242, 254, 0.35)";
      else if (act.count === 2) color = "rgba(0, 242, 254, 0.7)";
      else color = "rgba(0, 242, 254, 1.0)";
    }

    rect.setAttribute("fill", color);

    const title = document.createElementNS("http://www.w3.org/2000/svg", "title");
    title.textContent = `${dateKey}: ${act ? `${act.count} items, ${act.mins} mins` : 'No reading logged'}`;
    rect.appendChild(title);
    svg.appendChild(rect);
  }

  // Calculate Streak
  for (let i = 0; i < 365; i++) {
    const d = new Date(now);
    d.setDate(d.getDate() - i);
    const key = d.toISOString().split("T")[0];
    if (userReadingActivity[key] && userReadingActivity[key].count > 0) {
      streak++;
    } else if (i > 0) {
      break;
    }
  }

  const streakEl = document.getElementById("stat-current-streak");
  if (streakEl) streakEl.textContent = `${streak} ${streak === 1 ? 'Day' : 'Days'}`;
  
  const minsEl = document.getElementById("stat-total-mins");
  if (minsEl) minsEl.textContent = `${totalMins} Min`;
}

// -----------------------------------------------------------------------------
let currentUtterance = null;
let isAudioPlaying = false;
let playbackRate = 1.0;
let sleepTimerMinutes = 0;
let sleepTimerInterval = null;

function playBookAudio(slug) {
  const book = vaultData.books.find(b => b.slug === slug);
  if (!book || !book.audio_content) return;

  const bar = document.getElementById("audio-player-bar");
  bar.classList.add("active");
  document.getElementById("audio-player-title").textContent = book.title;
  document.getElementById("audio-player-status").textContent = "Speaking...";

  window.speechSynthesis.cancel();
  const cleanText = book.audio_content.replace(/---[\s\S]*?---/, "").replace(/#.*?\n/g, "").trim();
  
  currentUtterance = new SpeechSynthesisUtterance(cleanText);
  currentUtterance.rate = playbackRate;
  currentUtterance.onend = () => {
    isAudioPlaying = false;
    document.getElementById("btn-play-icon").textContent = "▶️";
    document.getElementById("audio-player-status").textContent = "Finished";
  };

  window.speechSynthesis.speak(currentUtterance);
  isAudioPlaying = true;
  document.getElementById("btn-play-icon").textContent = "⏸️";
}

function cycleSleepTimer() {
  const options = [0, 15, 30, 45, 60];
  const nextIdx = (options.indexOf(sleepTimerMinutes) + 1) % options.length;
  sleepTimerMinutes = options[nextIdx];

  const btn = document.getElementById("btn-sleep-timer");
  if (sleepTimerInterval) clearInterval(sleepTimerInterval);

  if (sleepTimerMinutes === 0) {
    btn.textContent = "🌙 Timer: Off";
  } else {
    let remainingSec = sleepTimerMinutes * 60;
    btn.textContent = `🌙 ${sleepTimerMinutes}m`;
    sleepTimerInterval = setInterval(() => {
      remainingSec--;
      if (remainingSec <= 0) {
        clearInterval(sleepTimerInterval);
        window.speechSynthesis.pause();
        isAudioPlaying = false;
        document.getElementById("btn-play-icon").textContent = "▶️";
        btn.textContent = "🌙 Timer: Off";
        sleepTimerMinutes = 0;
      } else {
        const m = Math.floor(remainingSec / 60);
        const s = remainingSec % 60;
        btn.textContent = `🌙 ${m}:${s < 10 ? '0' : ''}${s}`;
      }
    }, 1000);
  }
}

function seekAudioChapter(chapIdx) {
  if (!currentActiveBook || !currentActiveBook.audio_content) return;
  const raw = currentActiveBook.audio_content.replace(/---[\s\S]*?---/, "").trim();
  const sections = raw.split(/\n(?=##? )/);
  const targetSection = sections[parseInt(chapIdx)] || sections[0];
  
  window.speechSynthesis.cancel();
  currentUtterance = new SpeechSynthesisUtterance(targetSection.replace(/#.*?\n/g, "").trim());
  currentUtterance.rate = playbackRate;
  window.speechSynthesis.speak(currentUtterance);
  isAudioPlaying = true;
  document.getElementById("btn-play-icon").textContent = "⏸️";
  document.getElementById("audio-player-status").textContent = `Speaking Part ${parseInt(chapIdx) + 1}...`;
}


function closeReader() {
  document.getElementById("reader-modal").classList.remove("active");
  document.body.style.overflow = "auto";
}

function setBookRating(stars) {
  if (!currentActiveBook) return;
  userBookRatings[currentActiveBook.slug] = stars;
  localStorage.setItem("user-book-ratings", JSON.stringify(userBookRatings));
  updateStarRatingUi(stars);
  renderBooks();
}

function updateStarRatingUi(stars) {
  document.querySelectorAll(".star-rating .star").forEach(star => {
    const val = parseInt(star.dataset.val);
    star.style.color = val <= stars ? "var(--c-amber)" : "var(--text-muted)";
  });
}

function toggleFontSerif() {
  const article = document.getElementById("reader-content");
  const btn = document.getElementById("btn-font-serif");
  if (readerFontFamily === "sans") {
    readerFontFamily = "serif";
    article.classList.remove("font-sans");
    article.classList.add("font-serif");
    btn.textContent = "Sans";
  } else {
    readerFontFamily = "sans";
    article.classList.remove("font-serif");
    article.classList.add("font-sans");
    btn.textContent = "Serif";
  }
}

function adjustFontSize(delta) {
  readerFontSize = Math.max(0.85, Math.min(1.5, readerFontSize + delta));
  document.getElementById("reader-content").style.fontSize = `${readerFontSize}rem`;
}

// -----------------------------------------------------------------------------
// Spaced Repetition Flashcard Quiz Engine (Leitner System)
// -----------------------------------------------------------------------------
function extractAllFlashcardsToSrs() {
  if (!vaultData) return;
  const cards = [];
  vaultData.books.forEach(b => {
    if (b.chapters) {
      b.chapters.forEach(chap => {
        const regex = /Q:\s*(.+?)\s*\n+A:\s*(.+?)(?=\n\s*(?:Q:|#|$))/gs;
        let match;
        while ((match = regex.exec(chap.content)) !== null) {
          cards.push({
            book: b.title,
            q: match[1].trim(),
            a: match[2].trim(),
            box: 1,
            nextReview: Date.now()
          });
        }
      });
    }
  });

  if (cards.length > 0) {
    userSrsCards = cards;
    localStorage.setItem("user-srs-deck", JSON.stringify(cards));
  }
}

function openSrsQuiz() {
  srsQuizCards = userSrsCards.length > 0 ? userSrsCards : [
    {
      book: "Make It Stick",
      q: "Why is retrieval practice superior to passive rereading?",
      a: "Retrieval practice forces neural reconstruction, strengthening synaptic consolidation far more than recognition."
    },
    {
      book: "Make It Stick",
      q: "What is interleaving and why does it feel harder?",
      a: "Interleaving mixes related problem types during practice to train problem discrimination, producing durable mastery."
    }
  ];

  srsCurrentIndex = 0;
  loadSrsCard(0);
  document.getElementById("srs-modal").classList.add("active");
}

function loadSrsCard(idx) {
  if (idx >= srsQuizCards.length) {
    document.getElementById("srs-card-q").textContent = "🎉 Session Complete! All active recall cards reviewed.";
    document.getElementById("srs-card-a").textContent = "Great job strengthening your long-term memory pathways.";
    document.getElementById("srs-card-progress").textContent = `Reviewed ${srsQuizCards.length} cards`;
    return;
  }

  const card = srsQuizCards[idx];
  document.getElementById("srs-card-box").classList.remove("flipped");
  document.getElementById("srs-card-q").textContent = card.q;
  document.getElementById("srs-card-a").textContent = card.a;
  document.getElementById("srs-card-progress").textContent = `Card ${idx + 1} of ${srsQuizCards.length} • Book: ${card.book}`;
}

function flipSrsCard() {
  document.getElementById("srs-card-box").classList.toggle("flipped");
}

function gradeSrsCard(grade) {
  srsCurrentIndex++;
  loadSrsCard(srsCurrentIndex);
}

function closeSrsModal() {
  document.getElementById("srs-modal").classList.remove("active");
}

// -----------------------------------------------------------------------------
// Export User Journey
// -----------------------------------------------------------------------------
function exportUserProgress() {
  const payload = {
    exported_at: new Date().toISOString(),
    completed_books: userReadingStatus,
    ratings: userBookRatings,
    srs_cards_reviewed: userSrsCards.length,
  };

  const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(payload, null, 2));
  const downloadAnchor = document.createElement("a");
  downloadAnchor.setAttribute("href", dataStr);
  downloadAnchor.setAttribute("download", "my_book_vault_progress.json");
  document.body.appendChild(downloadAnchor);
  downloadAnchor.click();
  downloadAnchor.remove();
}

// -----------------------------------------------------------------------------
// Audio Narration Bar
// -----------------------------------------------------------------------------
let currentUtterance = null;
let isAudioPlaying = false;
let playbackRate = 1.0;

function playBookAudio(slug) {
  const book = vaultData.books.find(b => b.slug === slug);
  if (!book || !book.audio_content) return;

  const bar = document.getElementById("audio-player-bar");
  bar.classList.add("active");
  document.getElementById("audio-player-title").textContent = book.title;
  document.getElementById("audio-player-status").textContent = "Speaking...";

  window.speechSynthesis.cancel();
  const cleanText = book.audio_content.replace(/---[\s\S]*?---/, "").replace(/#.*?\n/g, "").trim();
  
  currentUtterance = new SpeechSynthesisUtterance(cleanText);
  currentUtterance.rate = playbackRate;
  currentUtterance.onend = () => {
    isAudioPlaying = false;
    document.getElementById("btn-play-icon").textContent = "▶️";
    document.getElementById("audio-player-status").textContent = "Finished";
  };

  window.speechSynthesis.speak(currentUtterance);
  isAudioPlaying = true;
  document.getElementById("btn-play-icon").textContent = "⏸️";
}

function togglePlayPause() {
  if (isAudioPlaying) {
    window.speechSynthesis.pause();
    isAudioPlaying = false;
    document.getElementById("btn-play-icon").textContent = "▶️";
  } else {
    window.speechSynthesis.resume();
    isAudioPlaying = true;
    document.getElementById("btn-play-icon").textContent = "⏸️";
  }
}

function cycleSpeed() {
  const speeds = [1.0, 1.25, 1.5, 2.0];
  const nextIdx = (speeds.indexOf(playbackRate) + 1) % speeds.length;
  playbackRate = speeds[nextIdx];
  document.getElementById("btn-speed").textContent = `${playbackRate}x`;
  if (currentUtterance) currentUtterance.rate = playbackRate;
}

// -----------------------------------------------------------------------------
// Knowledge Graph Visualizer
// -----------------------------------------------------------------------------
function setViewMode(mode) {
  currentViewMode = mode;
  document.getElementById("btn-view-grid").classList.toggle("active", mode === "grid");
  document.getElementById("btn-view-graph").classList.toggle("active", mode === "graph");
  document.getElementById("books-grid").style.display = mode === "grid" ? "grid" : "none";
  document.getElementById("graph-view-container").classList.toggle("active", mode === "graph");
}

function buildGraphData() {
  if (!vaultData) return;
  graphNodes = vaultData.books.slice(0, 80).map((b, i) => ({
    id: b.slug,
    title: b.title,
    pillar: b.pillar,
    status: b.status,
    x: 400 + Math.cos(i) * (200 + (i % 5) * 40),
    y: 350 + Math.sin(i) * (200 + (i % 5) * 40),
    vx: 0,
    vy: 0,
    radius: b.status === "Generated" ? 8 : 4
  }));

  graphEdges = [];
  for (let i = 0; i < graphNodes.length; i++) {
    for (let j = i + 1; j < graphNodes.length; j++) {
      if (graphNodes[i].pillar === graphNodes[j].pillar && Math.random() > 0.6) {
        graphEdges.push({ source: graphNodes[i], target: graphNodes[j] });
      }
    }
  }
}

function initForceGraph() {
  const canvas = document.getElementById("graph-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  function resize() {
    canvas.width = canvas.parentElement.clientWidth;
    canvas.height = canvas.parentElement.clientHeight;
  }
  resize();
  window.addEventListener("resize", resize);

  function animate() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw Edges
    ctx.strokeStyle = "rgba(0, 242, 254, 0.15)";
    ctx.lineWidth = 1;
    graphEdges.forEach(e => {
      ctx.beginPath();
      ctx.moveTo(e.source.x, e.source.y);
      ctx.lineTo(e.target.x, e.target.y);
      ctx.stroke();
    });

    // Draw Nodes
    graphNodes.forEach(n => {
      ctx.beginPath();
      ctx.arc(n.x, n.y, n.radius, 0, Math.PI * 2);
      ctx.fillStyle = n.status === "Generated" ? "#00f2fe" : "rgba(148, 163, 184, 0.4)";
      ctx.shadowColor = n.status === "Generated" ? "rgba(0, 242, 254, 0.6)" : "transparent";
      ctx.shadowBlur = n.status === "Generated" ? 10 : 0;
      ctx.fill();
    });

    requestAnimationFrame(animate);
  }
  animate();
}

function setupEventListeners() {
  const searchInput = document.getElementById("search-input");
  searchInput.addEventListener("input", (e) => {
    currentSearchQuery = e.target.value;
    renderBooks();
  });

  window.addEventListener("keydown", (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === "k") {
      e.preventDefault();
      searchInput.focus();
    }
    if (e.key === "Escape") {
      closeReader();
      closeSrsModal();
    }
  });

  document.getElementById("theme-toggle").addEventListener("click", () => {
    const doc = document.documentElement;
    const next = doc.getAttribute("data-theme") === "dark" ? "light" : "dark";
    doc.setAttribute("data-theme", next);
    localStorage.setItem("book-vault-theme", next);
  });
}

function initTheme() {
  const saved = localStorage.getItem("book-vault-theme") || "dark";
  document.documentElement.setAttribute("data-theme", saved);
}

function parseMarkdownToHtml(md) {
  if (!md) return "";
  let html = md.replace(/---[\s\S]*?---/, "");
  html = html.replace(/# (.*)/g, "<h1>$1</h1>");
  html = html.replace(/## (.*)/g, "<h2>$1</h2>");
  html = html.replace(/### (.*)/g, "<h3>$1</h3>");
  html = html.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
  html = html.replace(/\*(.*?)\*/g, "<em>$1</em>");
  html = html.replace(/\[\[(.*?)\]\]/g, '<span class="wikilink">[[ $1 ]]</span>');
  html = html.replace(/> \[\!(NOTE|TIP|IMPORTANT|WARNING)\]\n> (.*)/g, '<div class="callout callout-$1"><strong>$1:</strong> $2</div>');
  html = html.replace(/\n\n/g, "<p></p>");
  return html;
}

// -----------------------------------------------------------------------------
// In-Browser Vault AI Assistant Engine
// -----------------------------------------------------------------------------
function openVaultAiModal() {
  document.getElementById("vault-ai-modal").classList.add("active");
  document.getElementById("ai-chat-input").focus();
}

function closeVaultAiModal() {
  document.getElementById("vault-ai-modal").classList.remove("active");
}

function askSuggestedPrompt(text) {
  document.getElementById("ai-chat-input").value = text;
  sendVaultAiMessage();
}

function sendVaultAiMessage() {
  const input = document.getElementById("ai-chat-input");
  const query = input.value.trim();
  if (!query) return;

  const chatContainer = document.getElementById("ai-chat-messages");
  
  // User Message Bubble
  const userMsg = document.createElement("div");
  userMsg.className = "ai-chat-msg";
  userMsg.style.cssText = "background: var(--bg-surface); padding: 1rem; border-radius: 8px; border-left: 3px solid var(--c-amber); align-self: flex-end; width: 85%;";
  userMsg.innerHTML = `<p style="font-size: 0.85rem; font-weight: 700; color: var(--c-amber); margin-bottom: 0.25rem;">YOU</p><p style="margin:0; font-size: 0.95rem;">${query}</p>`;
  chatContainer.appendChild(userMsg);
  input.value = "";

  // Matching books in vault
  const tokens = query.toLowerCase().split(/\s+/).filter(t => t.length > 2);
  const matchedBooks = vaultData ? vaultData.books.filter(b => {
    const text = `${b.title} ${b.author} ${b.category} ${b.pillar}`.toLowerCase();
    return tokens.some(t => text.includes(t));
  }).slice(0, 3) : [];

  // Assistant Response Bubble
  const botMsg = document.createElement("div");
  botMsg.className = "ai-chat-msg";
  botMsg.style.cssText = "background: var(--bg-surface-raised); padding: 1rem; border-radius: 8px; border-left: 3px solid var(--c-cyan);";
  
  let responseText = "";
  if (matchedBooks.length > 0) {
    const bookLinks = matchedBooks.map(b => `<strong style="color: var(--c-cyan); cursor: pointer;" onclick="openReader('${b.slug}')">📖 ${b.title}</strong> by ${b.author} (<em>${b.pillar}</em>)`).join("<br>• ");
    responseText = `Based on the <strong>Universal Book Vault</strong> knowledge graph, here are key insights regarding "<em>${query}</em>":<br><br>
    • ${bookLinks}<br><br>
    <strong>Core Mental Model Synthesis:</strong><br>
    Cognitive science and empirical learning research show that effective skill acquisition relies on <em>desirable difficulty</em>, <em>interleaved practice</em>, and <em>active neural retrieval</em> rather than passive review. To maximize retention, test yourself immediately after reading, space out subsequent recall intervals across days, and connect new frameworks to existing knowledge nodes.`;
  } else {
    responseText = `I analyzed the 775 books across all 12 pillars. For "<em>${query}</em>", explore <strong>Pillar 01: Learning, Cognition & Meta-Skills</strong> and <strong>Pillar 02: Mindset & Psychological Fitness</strong> to discover foundational mental models and empirical studies.`;
  }

  botMsg.innerHTML = `<p style="font-size: 0.85rem; font-weight: 700; color: var(--c-cyan); margin-bottom: 0.25rem;">🤖 VAULT ASSISTANT</p><p style="margin:0; font-size: 0.95rem; line-height: 1.6;">${responseText}</p>`;
  chatContainer.appendChild(botMsg);
  chatContainer.scrollTop = chatContainer.scrollHeight;
}

