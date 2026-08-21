/**
 * Universal Book Vault — State-of-the-Art Interactive Client
 */

let vaultData = null;
let currentPillar = "ALL";
let currentDifficulty = "ALL";
let currentStatusFilter = "ALL";
let currentBook = null;
let currentChapterIndex = 0;
let synth = window.speechSynthesis;
let speechUtterance = null;
let isPlaying = false;
let playbackRate = 1.0;
let readerFontSize = 1.08;
let readerFontFamily = "sans";
let userReadingStatus = JSON.parse(localStorage.getItem("user-reading-status") || "{}");

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
});

async function loadVaultData() {
  try {
    const res = await fetch("data/vault_data.json");
    vaultData = await res.json();
    renderStats();
    renderPillarTabs();
    renderBooks();
    buildGraphData();
  } catch (err) {
    console.error("Failed to load vault data:", err);
    document.getElementById("books-grid").innerHTML = `
      <div style="grid-column: 1/-1; text-align: center; padding: 4rem; color: var(--text-muted);">
        <h2>⚠️ Vault data bundle missing</h2>
        <p style="margin-top: 0.5rem;">Run <code>python -m automation.build_site_data</code> to compile the library.</p>
      </div>
    `;
  }
}

function renderStats() {
  if (!vaultData) return;
  document.getElementById("stat-total").textContent = vaultData.total_books;
  document.getElementById("stat-pillars").textContent = Object.keys(vaultData.pillars).length;
  document.getElementById("stat-generated").textContent = vaultData.generated_books;
  
  const completedCount = Object.values(userReadingStatus).filter(s => s === "Completed").length;
  document.getElementById("stat-user-read").textContent = completedCount;
}

function renderPillarTabs() {
  const container = document.getElementById("pillar-tabs");
  container.innerHTML = `<button class="pill-filter active" data-pillar="ALL">🏛️ All 12 Pillars</button>`;

  for (const [name, folder] of Object.entries(vaultData.pillars)) {
    const btn = document.createElement("button");
    btn.className = "pill-filter";
    btn.dataset.pillar = name;
    btn.textContent = name;
    btn.addEventListener("click", () => {
      document.querySelectorAll(".pill-filter").forEach(t => t.classList.remove("active"));
      btn.classList.add("active");
      currentPillar = name;
      renderBooks();
    });
    container.appendChild(btn);
  }

  container.querySelector('[data-pillar="ALL"]').addEventListener("click", (e) => {
    document.querySelectorAll(".pill-filter").forEach(t => t.classList.remove("active"));
    e.target.classList.add("active");
    currentPillar = "ALL";
    renderBooks();
  });
}

function renderBooks() {
  const grid = document.getElementById("books-grid");
  const query = document.getElementById("search-input").value.toLowerCase().trim();

  let filtered = vaultData.books.filter(b => {
    const matchesPillar = currentPillar === "ALL" || b.pillar === currentPillar;
    const matchesDiff = currentDifficulty === "ALL" || b.difficulty === currentDifficulty;
    const userStatus = userReadingStatus[b.slug] || "Unread";
    const matchesStatus = currentStatusFilter === "ALL" || userStatus === currentStatusFilter;
    const matchesQuery = !query || 
      b.title.toLowerCase().includes(query) || 
      b.author.toLowerCase().includes(query) || 
      b.category.toLowerCase().includes(query) ||
      b.slug.toLowerCase().includes(query);
    return matchesPillar && matchesDiff && matchesStatus && matchesQuery;
  });

  if (filtered.length === 0) {
    grid.innerHTML = `
      <div style="grid-column: 1/-1; text-align: center; padding: 4rem; color: var(--text-muted);">
        <h3>No books found matching your current filters.</h3>
        <p style="margin-top: 0.5rem; font-size: 0.9rem;">Try adjusting your search query or pillar selection.</p>
      </div>
    `;
    return;
  }

  grid.innerHTML = filtered.map(b => {
    const status = userReadingStatus[b.slug] || "Unread";
    const wordEst = b.chapters ? b.chapters.reduce((acc, c) => acc + (c.content ? c.content.split(/\s+/).length : 0), 0) : 2500;
    const readingTime = Math.max(8, Math.round(wordEst / 220));

    return `
    <div class="book-card">
      <div>
        <div class="book-top-bar">
          <span class="book-num-badge">#${b.number}</span>
          <span class="book-pillar-tag">${b.pillar.split(",")[0]}</span>
        </div>
        
        <h3 class="book-card-title">${b.title}</h3>
        <div class="book-card-author">By ${b.author} (${b.published})</div>

        <div class="book-tags-row">
          <span class="tag-pill diff-${b.difficulty}">${b.difficulty}</span>
          <span class="tag-pill">${b.category}</span>
          <span class="tag-pill">⏱️ ${readingTime} min read</span>
          <span class="tag-pill" style="color: ${b.status === 'Generated' ? 'var(--c-emerald)' : 'var(--text-muted)'}">${b.status}</span>
        </div>
      </div>

      <div>
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.75rem;">
          <span style="font-size: 0.75rem; color: var(--text-muted); font-weight: 600;">Status:</span>
          <select class="user-status-btn" onchange="updateBookStatus('${b.slug}', this.value)">
            <option value="Unread" ${status === 'Unread' ? 'selected' : ''}>⏳ Unread</option>
            <option value="Want to Read" ${status === 'Want to Read' ? 'selected' : ''}>🎯 Want to Read</option>
            <option value="Reading" ${status === 'Reading' ? 'selected' : ''}>📖 Reading</option>
            <option value="Completed" ${status === 'Completed' ? 'selected' : ''}>✅ Completed</option>
          </select>
        </div>

        <div class="card-footer">
          <button class="btn-card-read" onclick="openReader('${b.slug}')">📖 Read Summary</button>
          <button class="btn-card-audio" onclick="playAudioEdition('${b.slug}')" title="Listen with Audio TTS">🎧 Audio</button>
        </div>
      </div>
    </div>
  `;
  }).join("");
}

window.updateBookStatus = function(slug, status) {
  userReadingStatus[slug] = status;
  localStorage.setItem("user-reading-status", JSON.stringify(userReadingStatus));
  renderStats();
};

window.filterDifficulty = function(val) {
  currentDifficulty = val;
  renderBooks();
};

window.filterStatus = function(val) {
  currentStatusFilter = val;
  renderBooks();
};

// Markdown Parser for reader view
function parseMarkdown(md) {
  if (!md) return "";
  let html = md.replace(/^---[\s\S]*?---\n/, ""); // strip YAML frontmatter
  html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
  html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
  html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');
  html = html.replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>');
  html = html.replace(/\*(.*?)\*/gim, '<em>$1</em>');
  html = html.replace(/\[\[(?:[^\]|]+\|)?([^\]]+)\]\]/gim, '<span class="wikilink" style="color: var(--c-cyan); font-weight: 600; cursor: pointer;">🔗 $1</span>');
  html = html.replace(/^> \[\!(.*?)\]\s*(.*$)/gim, '<div class="callout"><div class="callout-title">$1</div>$2</div>');
  html = html.replace(/^\- (.*$)/gim, '<li>$1</li>');
  html = html.replace(/\n\n+/g, '</p><p>');
  return `<p>${html}</p>`;
}

// Reader Modal Logic
window.openReader = function(slug) {
  const book = vaultData.books.find(b => b.slug === slug);
  if (!book) return;
  currentBook = book;
  currentChapterIndex = 0;

  document.getElementById("modal-book-title").textContent = book.title;
  document.getElementById("modal-book-author").textContent = `By ${book.author} (${book.published}) • ${book.pillar}`;

  const sidebar = document.getElementById("reader-sidebar-links");
  if (book.chapters && book.chapters.length > 0) {
    sidebar.innerHTML = book.chapters.map((ch, idx) => `
      <div class="toc-nav-item ${idx === 0 ? 'active' : ''}" onclick="switchChapter(${idx})">
        📄 ${ch.title}
      </div>
    `).join("") + `
      <div class="toc-nav-item quiz-tab-item" onclick="openFlashcardTab()">
        🧠 Active Recall Quiz
      </div>
    `;
    displayChapter(0);
  } else {
    sidebar.innerHTML = `<div class="toc-nav-item active">Master Overview</div>`;
    document.getElementById("reader-content").innerHTML = `
      <div style="text-align: center; padding: 4rem; color: var(--text-muted);">
        <h3>📚 Curriculum Book Note</h3>
        <p style="margin-top: 0.5rem;">This book is in the generation queue. Run <code>python -m automation.generate --slug ${book.slug}</code> to generate its full summary.</p>
      </div>
    `;
  }

  document.getElementById("reader-modal").classList.add("active");
};

window.switchChapter = function(index) {
  currentChapterIndex = index;
  document.querySelectorAll(".toc-nav-item").forEach((el, idx) => {
    el.classList.toggle("active", idx === index);
  });
  displayChapter(index);
};

function displayChapter(index) {
  if (!currentBook || !currentBook.chapters[index]) return;
  const chapter = currentBook.chapters[index];
  document.getElementById("reader-content").innerHTML = parseMarkdown(chapter.content);
  document.getElementById("reader-content").scrollTop = 0;
}

window.openFlashcardTab = function() {
  document.querySelectorAll(".toc-nav-item").forEach(el => el.classList.remove("active"));
  
  let allText = currentBook.chapters.map(c => c.content).join("\n\n");
  let regex = /Q:\s*(.+?)\s*\n+A:\s*(.+?)(?=\n\s*(?:Q:|#|$))/g;
  let matches = [...allText.matchAll(regex)];

  if (matches.length === 0) {
    document.getElementById("reader-content").innerHTML = `
      <div style="text-align: center; padding: 4rem; color: var(--text-muted);">
        <h3>🧠 Spaced Repetition Flashcards</h3>
        <p style="margin-top: 0.5rem;">No flashcards found for this summary yet. Generate the full note to enable active recall.</p>
      </div>
    `;
    return;
  }

  let cardsHtml = matches.map((m, i) => `
    <div class="flashcard-wrapper" onclick="this.classList.toggle('flipped')">
      <div class="flashcard-badge">Card #${i+1} • Click to Flip</div>
      <div class="flashcard-question">Q: ${m[1].trim()}</div>
      <div class="flashcard-answer-box">
        <strong style="color: var(--c-emerald);">Answer:</strong> ${m[2].trim()}
      </div>
    </div>
  `).join("");

  document.getElementById("reader-content").innerHTML = `
    <div class="quiz-container">
      <h2 style="border: none; margin-bottom: 0.2rem;">🧠 Active Recall Self-Test</h2>
      <p style="color: var(--text-muted); margin-bottom: 2rem;">Test your retention of core concepts before revealing the answers:</p>
      ${cardsHtml}
    </div>
  `;
};

window.closeReader = function() {
  document.getElementById("reader-modal").classList.remove("active");
};

// Typography Customizer
window.adjustFontSize = function(delta) {
  readerFontSize = Math.max(0.85, Math.min(1.45, readerFontSize + delta));
  document.getElementById("reader-content").style.fontSize = `${readerFontSize}rem`;
};

window.toggleFontSerif = function() {
  const content = document.getElementById("reader-content");
  readerFontFamily = readerFontFamily === "sans" ? "serif" : "sans";
  content.classList.toggle("font-serif", readerFontFamily === "serif");
  document.getElementById("btn-font-serif").classList.toggle("active", readerFontFamily === "serif");
};

// Audio TTS Player Logic
window.playAudioEdition = function(slug) {
  const book = vaultData.books.find(b => b.slug === slug);
  if (!book) return;

  if (synth.speaking) {
    synth.cancel();
  }

  let textToRead = book.audio_content || (book.chapters.length > 0 ? book.chapters[0].content : "");
  if (!textToRead) {
    alert("Audio narration for this book is pending generation.");
    return;
  }

  // Clean text for natural speech synthesis
  textToRead = textToRead.replace(/^---[\s\S]*?---\n/, "")
    .replace(/[#*`_>]/g, " ")
    .replace(/\[\[(?:[^\]|]+\|)?([^\]]+)\]\]/g, "$1");

  document.getElementById("audio-player-bar").classList.add("active");
  document.getElementById("audio-player-title").textContent = book.title;
  document.getElementById("audio-player-status").textContent = `Narrating • ${playbackRate}x Speed`;
  document.getElementById("btn-play-icon").textContent = "⏸️";
  isPlaying = true;

  speechUtterance = new SpeechSynthesisUtterance(textToRead);
  speechUtterance.rate = playbackRate;

  speechUtterance.onend = () => {
    isPlaying = false;
    document.getElementById("btn-play-icon").textContent = "▶️";
    document.getElementById("audio-player-status").textContent = "Completed";
  };

  speechUtterance.onerror = (e) => {
    console.error("Speech error:", e);
    isPlaying = false;
    document.getElementById("btn-play-icon").textContent = "▶️";
  };

  synth.speak(speechUtterance);
};

window.togglePlayPause = function() {
  if (!speechUtterance) return;
  if (synth.speaking) {
    if (synth.paused) {
      synth.resume();
      isPlaying = true;
      document.getElementById("btn-play-icon").textContent = "⏸️";
    } else {
      synth.pause();
      isPlaying = false;
      document.getElementById("btn-play-icon").textContent = "▶️";
    }
  }
};

window.cycleSpeed = function() {
  const rates = [0.8, 1.0, 1.25, 1.5, 2.0];
  let nextIdx = (rates.indexOf(playbackRate) + 1) % rates.length;
  playbackRate = rates[nextIdx];
  document.getElementById("btn-speed").textContent = `${playbackRate}x`;
  if (synth.speaking && isPlaying) {
    window.playAudioEdition(currentBook ? currentBook.slug : vaultData.books[0].slug);
  }
};

// 2D Force-Directed Knowledge Graph Visualizer
function buildGraphData() {
  if (!vaultData) return;
  const colors = ["#00f2fe", "#818cf8", "#34d399", "#fbbf24", "#f43f5e", "#c084fc"];
  const pillars = Object.keys(vaultData.pillars);

  graphNodes = vaultData.books.slice(0, 80).map((b, idx) => {
    const pIdx = pillars.indexOf(b.pillar) % colors.length;
    return {
      id: b.slug,
      label: b.title,
      pillar: b.pillar,
      color: colors[pIdx >= 0 ? pIdx : 0],
      x: (Math.random() - 0.5) * 800,
      y: (Math.random() - 0.5) * 600,
      vx: 0,
      vy: 0,
      radius: b.difficulty === "Advanced" ? 7 : (b.difficulty === "Intermediate" ? 5 : 4),
    };
  });

  graphEdges = [];
  for (let i = 0; i < graphNodes.length; i++) {
    for (let j = i + 1; j < graphNodes.length; j++) {
      if (graphNodes[i].pillar === graphNodes[j].pillar && Math.random() > 0.65) {
        graphEdges.push({ source: graphNodes[i], target: graphNodes[j] });
      }
    }
  }
}

function initForceGraph() {
  const canvas = document.getElementById("graphCanvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  function resize() {
    canvas.width = canvas.parentElement.clientWidth;
    canvas.height = canvas.parentElement.clientHeight;
  }
  resize();
  window.addEventListener("resize", resize);

  let cameraX = canvas.width / 2;
  let cameraY = canvas.height / 2;

  function simulate() {
    // Spring physics between nodes
    graphEdges.forEach(e => {
      const dx = e.target.x - e.source.x;
      const dy = e.target.y - e.source.y;
      const dist = Math.sqrt(dx * dx + dy * dy) || 1;
      const force = (dist - 90) * 0.002;
      const fx = (dx / dist) * force;
      const fy = (dy / dist) * force;
      e.source.vx += fx;
      e.source.vy += fy;
      e.target.vx -= fx;
      e.target.vy -= fy;
    });

    graphNodes.forEach(n => {
      n.x += n.vx;
      n.y += n.vy;
      n.vx *= 0.88;
      n.vy *= 0.88;
    });
  }

  function draw() {
    simulate();
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    ctx.save();
    ctx.translate(cameraX, cameraY);

    // Draw connecting edges
    graphEdges.forEach(e => {
      ctx.strokeStyle = "rgba(255, 255, 255, 0.08)";
      ctx.lineWidth = 0.8;
      ctx.beginPath();
      ctx.moveTo(e.source.x, e.source.y);
      ctx.lineTo(e.target.x, e.target.y);
      ctx.stroke();
    });

    // Draw nodes
    graphNodes.forEach(n => {
      ctx.fillStyle = n.color;
      ctx.shadowColor = n.color;
      ctx.shadowBlur = 8;
      ctx.beginPath();
      ctx.arc(n.x, n.y, n.radius, 0, Math.PI * 2);
      ctx.fill();
      ctx.shadowBlur = 0;
    });

    ctx.restore();
    requestAnimationFrame(draw);
  }
  draw();
}

window.toggleView = function(view) {
  document.querySelectorAll(".btn-view-tab").forEach(b => b.classList.remove("active"));
  if (view === "grid") {
    document.getElementById("btn-view-grid").classList.add("active");
    document.getElementById("books-grid").style.display = "grid";
    document.getElementById("graph-viewport").classList.remove("active");
  } else {
    document.getElementById("btn-view-graph").classList.add("active");
    document.getElementById("books-grid").style.display = "none";
    document.getElementById("graph-viewport").classList.add("active");
  }
};

function setupEventListeners() {
  document.getElementById("search-input").addEventListener("input", renderBooks);
  document.getElementById("theme-toggle").addEventListener("click", toggleTheme);
  
  // Keyboard Shortcut: Cmd/Ctrl + K focuses search
  window.addEventListener("keydown", (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === "k") {
      e.preventDefault();
      document.getElementById("search-input").focus();
    }
  });
}

function initTheme() {
  const saved = localStorage.getItem("vault-theme") || "dark";
  document.documentElement.setAttribute("data-theme", saved);
  document.getElementById("theme-toggle").textContent = saved === "dark" ? "☀️" : "🌙";
}

function toggleTheme() {
  const current = document.documentElement.getAttribute("data-theme") || "dark";
  const next = current === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", next);
  localStorage.setItem("vault-theme", next);
  document.getElementById("theme-toggle").textContent = next === "dark" ? "☀️" : "🌙";
}
