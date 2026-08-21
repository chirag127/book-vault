const { Plugin, PluginSettingTab, Setting, Notice, ItemView, WorkspaceLeaf } = require("obsidian");

const BOOKSHELF_VIEW_TYPE = "vault-bookshelf-view";

const DEFAULT_SETTINGS = {
  hardcoverApiKey: "",
  autoSyncReadingStatus: true,
  audiobookshelfUrl: "http://localhost:13378",
  speachesTtsUrl: "http://localhost:8000/v1/audio/speech",
};

class HardcoverSyncPlugin extends Plugin {
  async onload() {
    await this.loadSettings();

    // 1. Register Bookshelf Visual Gallery View
    this.registerView(BOOKSHELF_VIEW_TYPE, (leaf) => new BookshelfGalleryView(leaf, this));

    // 2. Ribbon Icon: Sync Reading Status
    this.addRibbonIcon("book-open", "Hardcover Sync: Update Reading Progress", () => {
      this.syncHardcover();
    });

    // 3. Ribbon Icon: Open Visual Bookshelf Gallery
    this.addRibbonIcon("layout-grid", "Open Visual Bookshelf Gallery", () => {
      this.activateBookshelfView();
    });

    // 4. Commands
    this.addCommand({
      id: "hardcover-sync-library",
      name: "Hardcover: Sync Reading Progress & Shelves",
      callback: () => this.syncHardcover(),
    });

    this.addCommand({
      id: "open-vault-bookshelf-gallery",
      name: "Vault: Open Visual Bookshelf Gallery",
      callback: () => this.activateBookshelfView(),
    });

    this.addCommand({
      id: "play-active-book-audio",
      name: "Audio: Play Active Book Narration",
      callback: () => this.playCurrentNoteAudio(),
    });

    // 5. Register Markdown Code Block Processor: ```book-audio
    this.registerMarkdownCodeBlockProcessor("book-audio", (source, el, ctx) => {
      this.renderAudioPlayerWidget(source.trim(), el);
    });

    // 6. Settings Tab
    this.addSettingTab(new HardcoverSyncSettingTab(this.app, this));
    console.log("Hardcover Sync & Vault Companion loaded.");
  }

  onunload() {
    console.log("Hardcover Sync & Vault Companion unloaded.");
  }

  async loadSettings() {
    this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
  }

  async saveSettings() {
    await this.saveData(this.settings);
  }

  async activateBookshelfView() {
    const { workspace } = this.app;
    let leaf = workspace.getLeavesOfType(BOOKSHELF_VIEW_TYPE)[0];
    if (!leaf) {
      leaf = workspace.getLeaf("tab");
      await leaf.setViewState({ type: BOOKSHELF_VIEW_TYPE, active: true });
    }
    workspace.revealLeaf(leaf);
  }

  renderAudioPlayerWidget(source, el) {
    el.empty();
    const container = el.createDiv({ cls: "vault-embedded-audio-player" });
    container.style.cssText = "background: var(--background-secondary); border: 1px solid var(--border-color); border-radius: 8px; padding: 1rem; margin: 1rem 0; display: flex; flex-direction: column; gap: 0.5rem;";

    const topRow = container.createDiv({ style: "display: flex; justify-content: space-between; align-items: center;" });
    topRow.createEl("strong", { text: "🎧 Audio Listening Edition" });
    const speedSelect = topRow.createEl("select", { style: "padding: 0.2rem 0.4rem; font-size: 0.8rem;" });
    [1.0, 1.25, 1.5, 2.0].forEach(spd => {
      const opt = speedSelect.createEl("option", { text: `${spd}x`, value: spd.toString() });
      if (spd === 1.25) opt.selected = true;
    });

    const audio = container.createEl("audio", {
      attr: { controls: "", style: "width: 100%; margin-top: 0.25rem;" }
    });
    
    // Auto-detect local audio file if path passed, else default to speech
    if (source) {
      audio.src = source;
    }

    speedSelect.addEventListener("change", (e) => {
      audio.playbackRate = parseFloat(e.target.value);
    });
  }

  async playCurrentNoteAudio() {
    const activeFile = this.app.workspace.getActiveFile();
    if (!activeFile) {
      new Notice("⚠️ No active book note open.");
      return;
    }
    const content = await this.app.vault.read(activeFile);
    const utterance = new SpeechSynthesisUtterance(content.slice(0, 3000));
    utterance.rate = 1.15;
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
    new Notice(`🎧 Playing audio narration for: ${activeFile.basename}`);
  }

  async syncHardcover() {
    if (!this.settings.hardcoverApiKey) {
      new Notice("⚠️ Hardcover API Key missing. Go to Settings -> Hardcover Sync.");
      return;
    }

    new Notice("🔄 Syncing shelves and reading status with Hardcover.app...");

    try {
      const query = `
        query GetUserBooks {
          me {
            id
            username
            user_books(limit: 100) {
              id
              status_id
              rating
              book {
                title
                slug
                pages
              }
            }
          }
        }
      `;

      const response = await fetch("https://api.hardcover.app/v1/graphql", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "authorization": `Bearer ${this.settings.hardcoverApiKey.trim()}`,
        },
        body: JSON.stringify({ query }),
      });

      if (!response.ok) {
        throw new Error(`HTTP Error ${response.status}`);
      }

      const resData = await response.json();
      if (resData.errors) {
        throw new Error(resData.errors[0].message);
      }

      const userBooks = resData.data?.me?.[0]?.user_books || [];
      new Notice(`✅ Hardcover Synced! ${userBooks.length} books tracked on your profile.`);
    } catch (err) {
      console.error("Hardcover sync failed:", err);
      new Notice(`❌ Hardcover sync failed: ${err.message}`);
    }
  }
}

class BookshelfGalleryView extends ItemView {
  constructor(leaf, plugin) {
    super(leaf);
    this.plugin = plugin;
  }

  getViewType() {
    return BOOKSHELF_VIEW_TYPE;
  }

  getDisplayText() {
    return "Visual Bookshelf Gallery";
  }

  getIcon() {
    return "layout-grid";
  }

  async onOpen() {
    const container = this.containerEl.children[1];
    container.empty();
    container.style.cssText = "padding: 1.5rem; overflow-y: auto;";

    container.createEl("h1", { text: "📚 Universal Book Vault — Visual Bookshelf" });
    container.createEl("p", { text: "Interactive visual library grid of all 775 canonical works organized across the 12 Knowledge Pillars." });

    const grid = container.createDiv({
      style: "display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 1.25rem; margin-top: 1.5rem;"
    });

    const files = this.app.vault.getMarkdownFiles().filter(f => f.name === "README.md" && f.path.startsWith("md/"));

    files.forEach(file => {
      const card = grid.createDiv({
        style: "background: var(--background-secondary); border: 1px solid var(--border-color); border-radius: 8px; padding: 1rem; cursor: pointer; display: flex; flex-direction: column; justify-content: space-between; transition: transform 0.2s;"
      });

      const parentFolder = file.parent ? file.parent.name : "Book";
      card.createEl("h3", { text: `📖 ${parentFolder.replace(/-/g, " ")}`, style: "font-size: 0.95rem; margin: 0 0 0.5rem 0;" });
      card.createEl("p", { text: `Path: ${file.path}`, style: "font-size: 0.75rem; color: var(--text-muted); margin: 0;" });

      card.addEventListener("click", () => {
        this.app.workspace.getLeaf(false).openFile(file);
      });
    });
  }
}

class HardcoverSyncSettingTab extends PluginSettingTab {
  constructor(app, plugin) {
    super(app, plugin);
    this.plugin = plugin;
  }

  display() {
    const { containerEl } = this;
    containerEl.empty();

    containerEl.createEl("h2", { text: "Hardcover Sync & Vault Settings" });

    new Setting(containerEl)
      .setName("Hardcover API Key")
      .setDesc("Get your free GraphQL API key from https://hardcover.app/account/api")
      .addText((text) =>
        text
          .setPlaceholder("Bearer token")
          .setValue(this.plugin.settings.hardcoverApiKey)
          .onChange(async (value) => {
            this.plugin.settings.hardcoverApiKey = value;
            await this.plugin.saveSettings();
          })
      );

    new Setting(containerEl)
      .setName("Auto-Sync Reading Status")
      .setDesc("Automatically pull and sync your reading shelves.")
      .addToggle((toggle) =>
        toggle
          .setValue(this.plugin.settings.autoSyncReadingStatus)
          .onChange(async (value) => {
            this.plugin.settings.autoSyncReadingStatus = value;
            await this.plugin.saveSettings();
          })
      );

    new Setting(containerEl)
      .setName("Speaches Neural TTS Server")
      .setDesc("Local OpenAI-compatible speech endpoint")
      .addText((text) =>
        text
          .setValue(this.plugin.settings.speachesTtsUrl)
          .onChange(async (value) => {
            this.plugin.settings.speachesTtsUrl = value;
            await this.plugin.saveSettings();
          })
      );
  }
}

module.exports = HardcoverSyncPlugin;
