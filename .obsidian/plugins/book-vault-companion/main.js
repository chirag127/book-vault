const { Plugin, PluginSettingTab, Setting, Notice } = require("obsidian");

const DEFAULT_SETTINGS = {
  hardcoverApiKey: "",
  autoSyncWeb: true,
  enablePdfIndexing: true,
};

class BookVaultCompanionPlugin extends Plugin {
  async onload() {
    await this.loadSettings();

    // Add Left Ribbon Icon
    this.addRibbonIcon("book-open", "Book Vault Companion: Hardcover Sync", (evt) => {
      this.syncHardcover();
    });

    // Add Command: Sync Hardcover
    this.addCommand({
      id: "sync-hardcover-progress",
      name: "Hardcover: Sync Reading Progress & Shelves",
      callback: () => this.syncHardcover(),
    });

    // Add Command: Open Web Explorer
    this.addCommand({
      id: "open-vault-web-app",
      name: "Book Vault: Open Web App Explorer",
      callback: () => {
        window.open("https://chirag127.github.io/book-vault/", "_blank");
      },
    });

    // Add Settings Tab
    this.addSettingTab(new BookVaultCompanionSettingTab(this.app, this));
    console.log("Book Vault Companion Plugin loaded.");
  }

  onunload() {
    console.log("Book Vault Companion Plugin unloaded.");
  }

  async loadSettings() {
    this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
  }

  async saveSettings() {
    await this.saveData(this.settings);
  }

  async syncHardcover() {
    if (!this.settings.hardcoverApiKey) {
      new Notice("⚠️ Hardcover API Key missing. Please set it in Settings -> Book Vault Companion.");
      return;
    }

    new Notice("🔄 Syncing library with Hardcover.app GraphQL API...");

    try {
      const query = `
        query GetUserBooks {
          me {
            id
            username
            user_books(limit: 50) {
              id
              status_id
              rating
              book {
                title
                slug
                pages
                cached_contributors
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
      new Notice(`✅ Successfully synced ${userBooks.length} books from Hardcover!`);
    } catch (err) {
      console.error("Hardcover sync failed:", err);
      new Notice(`❌ Hardcover sync failed: ${err.message}`);
    }
  }
}

class BookVaultCompanionSettingTab extends PluginSettingTab {
  constructor(app, plugin) {
    super(app, plugin);
    this.plugin = plugin;
  }

  display() {
    const { containerEl } = this;
    containerEl.empty();

    containerEl.createEl("h2", { text: "Book Vault Companion Settings" });

    new Setting(containerEl)
      .setName("Hardcover API Key")
      .setDesc("Get your free personal GraphQL API key from https://hardcover.app/account/api for automated reading sync")
      .addText((text) =>
        text
          .setPlaceholder("Bearer token or API key")
          .setValue(this.plugin.settings.hardcoverApiKey)
          .onChange(async (value) => {
            this.plugin.settings.hardcoverApiKey = value;
            await this.plugin.saveSettings();
          })
      );

    new Setting(containerEl)
      .setName("Auto-Sync Web Catalog")
      .setDesc("Automatically compile web application data when book notes are updated.")
      .addToggle((toggle) =>
        toggle
          .setValue(this.plugin.settings.autoSyncWeb)
          .onChange(async (value) => {
            this.plugin.settings.autoSyncWeb = value;
            await this.plugin.saveSettings();
          })
      );

    new Setting(containerEl)
      .setName("PDF & E-Book Attachments")
      .setDesc("Enable viewing and search indexing of book PDF files placed in book folders.")
      .addToggle((toggle) =>
        toggle
          .setValue(this.plugin.settings.enablePdfIndexing)
          .onChange(async (value) => {
            this.plugin.settings.enablePdfIndexing = value;
            await this.plugin.saveSettings();
          })
      );
  }
}

module.exports = BookVaultCompanionPlugin;
