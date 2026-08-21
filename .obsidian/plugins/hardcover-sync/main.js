const { Plugin, PluginSettingTab, Setting, Notice } = require("obsidian");

const DEFAULT_SETTINGS = {
  hardcoverApiKey: "",
  autoSyncReadingStatus: true,
  syncShelves: true,
};

class HardcoverSyncPlugin extends Plugin {
  async onload() {
    await this.loadSettings();

    // Ribbon Icon for Quick Sync
    this.addRibbonIcon("book-open", "Hardcover Sync: Update Reading Progress", () => {
      this.syncHardcover();
    });

    // Command: Hardcover Sync
    this.addCommand({
      id: "hardcover-sync-library",
      name: "Hardcover: Sync Reading Progress & Shelves",
      callback: () => this.syncHardcover(),
    });

    // Settings Tab
    this.addSettingTab(new HardcoverSyncSettingTab(this.app, this));
    console.log("Hardcover Sync Plugin loaded.");
  }

  onunload() {
    console.log("Hardcover Sync Plugin unloaded.");
  }

  async loadSettings() {
    this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
  }

  async saveSettings() {
    await this.saveData(this.settings);
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
      new Notice(`✅ Hardcover Synced! ${userBooks.length} books tracked on your profile.`);
    } catch (err) {
      console.error("Hardcover sync failed:", err);
      new Notice(`❌ Hardcover sync failed: ${err.message}`);
    }
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

    containerEl.createEl("h2", { text: "Hardcover Sync Settings" });

    new Setting(containerEl)
      .setName("Hardcover API Key")
      .setDesc("Get your free personal GraphQL API key from https://hardcover.app/account/api")
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
      .setDesc("Automatically pull your currently reading, want to read, and finished shelves.")
      .addToggle((toggle) =>
        toggle
          .setValue(this.plugin.settings.autoSyncReadingStatus)
          .onChange(async (value) => {
            this.plugin.settings.autoSyncReadingStatus = value;
            await this.plugin.saveSettings();
          })
      );
  }
}

module.exports = HardcoverSyncPlugin;
