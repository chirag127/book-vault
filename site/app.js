// Universal Book Vault — Interactive Web Application

let vaultData = null;
let currentPillar = "ALL";
let currentBook = null;
let currentChapterIndex = 0;
let synth = window.speechSynthesis;
let speechUtterance = null;
let isPlaying = false;
let playbackRate = 1.0;
let userReadingStatus = JSON.parse(localStorage.getItem("user-reading-status") || "{}");

// Initialize App
document.addEventListener("DOMContentLoaded", async () => {
  await loadVaultData();
  setupEventListeners();
  initTheme();
  initGraph();
});

async function loadVaultData() {
  try {
    const res = await fetch("data/vault_data.json");
    vaultData = await res.json();
    renderStats();
    renderPillarTabs();
    renderBooks();
  } catch (err) {
    console.error("Failed to load vault data:", err);
    document.getElementById("books-grid").innerHTML = `
      <div style="grid-column: 1/-1; text-align: center; padding: 3rem; color: var(--text-muted);">
        <h3>⚠️ Vault data not found.</h3>
        <p>Please run <code>python -m automation.build_site_data</code> to compile the library.</p>
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
  container.innerHTML = `<button class="pillar-tab active" data-pillar="ALL">🏛️ All Pillars</button>`;

  for (const [name, folder] of Object.entries(vaultData.pillars)) {
    const btn = document.createElement("button");
    btn.className = "pillar-tab";
    btn.dataset.pillar = name;
    btn.textContent = name;
    btn.addEventListener("click", () => {
      document.querySelectorAll(".pillar-tab").forEach(t => t.classList.remove("active"));
      btn.classList.add("active");
      currentPillar = name;
      renderBooks();
    });
    container.appendChild(btn);
  }

  container.querySelector('[data-pillar="ALL"]').addEventListener("click", (e) => {
    document.querySelectorAll(".pillar-tab").forEach(t => t.classList.remove("active"));
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
    const matchesQuery = !query || 
      b.title.toLowerCase().includes(query) || 
      b.author.toLowerCase().includes(query) || 
      b.category.toLowerCase().includes(query);
    return matchesPillar && matchesQuery;
  });

  if (filtered.length === 0) {
    grid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; padding: 3rem; color: var(--text-muted);">No books match your search.</div>`;
    return;
  }

  grid.innerHTML = filtered.map(b => {
    const status = userReadingStatus[b.slug] || "Unread";
    return `
    <div class="book-card">
      <div>
        <div class="book-number">#${b.number} • ${b.pillar}</div>
        <div class="book-title">${b.title}</div>
        <div class="book-author">By ${b.author} (${b.published})</div>
        <div class="book-meta-tags">
          <span class="meta-tag difficulty-${b.difficulty}">${b.difficulty}</span>
          <span class="meta-tag">${b.category}</span>
          <span class="meta-tag" style="color: ${b.status === 'Generated' ? 'var(--accent-emerald)' : 'var(--text-muted)'}">${b.status}</span>
        </div>
        <select class="status-select" onchange="updateBookStatus('${b.slug}', this.value)">
          <option value="Unread" ${status === 'Unread' ? 'selected' : ''}>⏳ Unread</option>
          <option value="Want to Read" ${status === 'Want to Read' ? 'selected' : ''}>🎯 Want to Read</option>
          <option value="Reading" ${status === 'Reading' ? 'selected' : ''}>📖 Reading</option>
          <option value="Completed" ${status === 'Completed' ? 'selected' : ''}>✅ Completed</option>
        </select>
      </div>
      <div class="card-actions" style="margin-top: 1rem;">
        <button class="btn-read" onclick="openReader('${b.slug}')">📖 Read</button>
        <button class="btn-audio" onclick="playAudioEdition('${b.slug}')">🎧 Listen</button>
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

// Markdown Parser for reader view
function parseMarkdown(md) {
  if (!md) return "";
  let html = md.replace(/^---[\s\S]*?---\n/, ""); // strip frontmatter
  html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
  html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
  html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');
  html = html.replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>');
  html = html.replace(/\*(.*?)\*/gim, '<em>$1</em>');
  html = html.replace(/\[\[(?:[^\]|]+\|)?([^\]]+)\]\]/gim, '<span class="wikilink">🔗 $1</span>');
  html = html.replace(/^> \[\!(.*?)\]\s*(.*$)/gim, '<div class="callout"><strong style="text-transform:uppercase;">$1</strong><br>$2</div>');
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
  document.getElementById("modal-book-author").textContent = `By ${book.author} (${book.published})`;

  const sidebar = document.getElementById("reader-sidebar-links");
  if (book.chapters && book.chapters.length > 0) {
    sidebar.innerHTML = book.chapters.map((ch, idx) => `
      <div class="chapter-link ${idx === 0 ? 'active' : ''}" onclick="switchChapter(${idx})">
        ${ch.title}
      </div>
    `).join("") + `
      <div class="chapter-link" onclick="openFlashcardTab()" style="margin-top: 1rem; border: 1px dashed var(--accent-cyan); color: var(--accent-cyan);">
        🧠 Active Recall Quiz
      </div>
    `;
    displayChapter(0);
  } else {
    sidebar.innerHTML = `<div class="chapter-link active">Complete Overview</div>`;
    document.getElementById("reader-content").innerHTML = `
      <div style="text-align: center; padding: 2rem; color: var(--text-muted);">
        <h3>Pending Generation</h3>
        <p>This book is in the curriculum queue. Run <code>python -m automation.generate --slug ${book.slug}</code> to generate it.</p>
      </div>
    `;
  }

  document.getElementById("reader-modal").classList.add("active");
};

window.switchChapter = function(index) {
  currentChapterIndex = index;
  document.querySelectorAll(".chapter-link").forEach((el, idx) => {
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
  document.querySelectorAll(".chapter-link").forEach(el => el.classList.remove("active"));
  
  let allText = currentBook.chapters.map(c => c.content).join("\n\n");
  let regex = /Q:\s*(.+?)\s*\n+A:\s*(.+?)(?=\n\s*(?:Q:|#|$))/g;
  let matches = [...allText.matchAll(regex)];

  if (matches.length === 0) {
    document.getElementById("reader-content").innerHTML = `
      <div style="text-align: center; padding: 3rem; color: var(--text-muted);">
        <h3>🧠 Spaced Repetition Flashcards</h3>
        <p>No flashcards found for this note yet. Generate the full note to enable active recall.</p>
      </div>
    `;
    return;
  }

  let cardsHtml = matches.map((m, i) => `
    <div class="flashcard-card" onclick="this.classList.toggle('revealed')">
      <div class="flashcard-q">Card ${i+1}: ${m[1].trim()}</div>
      <div class="flashcard-a"><strong>Answer:</strong> ${m[2].trim()}</div>
      <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.5rem;">(Click to flip / reveal answer)</div>
    </div>
  `).join("");

  document.getElementById("reader-content").innerHTML = `
    <h2>🧠 Active Recall & Spaced Repetition Practice</h2>
    <p style="color: var(--text-muted); margin-bottom: 1.5rem;">Test your retention of core concepts before revealing the answers:</p>
    <div class="flashcards-container">${cardsHtml}</div>
  `;
};

window.closeReader = function() {
  document.getElementById("reader-modal").classList.remove("active");
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
    alert("Audio content for this book has not been generated yet.");
    return;
  }

  textToRead = textToRead.replace(/^---[\s\S]*?---\n/, "")
    .replace(/[#*`_>]/g, " ")
    .replace(/\[\[(?:[^\]|]+\|)?([^\]]+)\]\]/g, "$1");

  document.getElementById("audio-bar").classList.add("active");
  document.getElementById("audio-bar-title").textContent = `${book.title} (Audio Narration)`;
  document.getElementById("audio-bar-status").textContent = "Speaking...";
  document.getElementById("btn-play-icon").textContent = "⏸️";
  isPlaying = true;

  speechUtterance = new SpeechSynthesisUtterance(textToRead);
  speechUtterance.rate = playbackRate;

  speechUtterance.onend = () => {
    isPlaying = false;
    document.getElementById("btn-play-icon").textContent = "▶️";
    document.getElementById("audio-bar-status").textContent = "Completed";
  };

  speechUtterance.onerror = (e) => {
    console.error("Speech synthesis error:", e);
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
  const rates = [1.0, 1.25, 1.5, 2.0];
  let nextIdx = (rates.indexOf(playbackRate) + 1) % rates.length;
  playbackRate = rates[nextIdx];
  document.getElementById("btn-speed").textContent = `${playbackRate}x`;
  if (synth.speaking && isPlaying) {
    window.playAudioEdition(currentBook ? currentBook.slug : vaultData.books[0].slug);
  }
};

// 2D Force-Directed Knowledge Graph Visualizer
function initGraph() {
  const canvas = document.getElementById("graphCanvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  function resize() {
    canvas.width = canvas.parentElement.clientWidth;
    canvas.height = canvas.parentElement.clientHeight;
  }
  resize();
  window.addEventListener("resize", resize);

  let nodes = [];
  const colors = ["#38bdf8", "#818cf8", "#34d399", "#fbbf24", "#f43f5e"];

  for (let i = 0; i < 40; i++) {
    nodes.push({
      x: Math.random() * (canvas.width || 800),
      y: Math.random() * (canvas.height || 600),
      vx: (Math.random() - 0.5) * 0.8,
      vy: (Math.random() - 0.5) * 0.8,
      radius: Math.random() * 4 + 3,
      color: colors[i % colors.length],
    });
  }

  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Draw edges
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const dx = nodes[i].x - nodes[j].x;
        const dy = nodes[i].y - nodes[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 130) {
          ctx.strokeStyle = `rgba(56, 189, 248, ${1 - dist / 130 * 0.85})`;
          ctx.lineWidth = 0.6;
          ctx.beginPath();
          ctx.moveTo(nodes[i].x, nodes[i].y);
          ctx.lineTo(nodes[j].x, nodes[j].y);
          ctx.stroke();
        }
      }
    }

    // Draw nodes
    nodes.forEach(n => {
      n.x += n.vx;
      n.y += n.vy;
      if (n.x < 0 || n.x > canvas.width) n.vx *= -1;
      if (n.y < 0 || n.y > canvas.height) n.vy *= -1;

      ctx.fillStyle = n.color;
      ctx.beginPath();
      ctx.arc(n.x, n.y, n.radius, 0, Math.PI * 2);
      ctx.fill();
    });

    requestAnimationFrame(draw);
  }
  draw();
}

window.toggleView = function(view) {
  document.querySelectorAll(".btn-view-toggle").forEach(b => b.classList.remove("active"));
  if (view === "grid") {
    document.getElementById("btn-view-grid").classList.add("active");
    document.getElementById("books-grid").style.display = "grid";
    document.getElementById("graph-container").classList.remove("active");
  } else {
    document.getElementById("btn-view-graph").classList.add("active");
    document.getElementById("books-grid").style.display = "none";
    document.getElementById("graph-container").classList.add("active");
  }
};

function setupEventListeners() {
  document.getElementById("search-input").addEventListener("input", renderBooks);
  document.getElementById("theme-toggle").addEventListener("click", toggleTheme);
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
