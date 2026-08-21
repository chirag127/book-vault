# 📊 Universal Book Vault — Interactive Dashboard

Welcome to your **Universal Knowledge Vault Dashboard**. Track your reading progress, explore visual canvases, and toggle between the **Modular Reading Edition** and the **🎧 Audio Listening Edition**.

---

## 🏛️ Pillar Overview & Visual Canvas Mind-Maps

| # | Pillar | Reading Track | Visual Canvas Map |
|---|---|---|---|
| 01 | **Learning, Cognition & Meta-Skills** | [[01-Learning-Cognition-and-Meta-Skills/README\|Explore Pillar 01]] | `[[01-Learning-Cognition-and-Meta-Skills.canvas\|Open Canvas]]` |
| 02 | **Thinking, Rationality & Mental Models** | [[02-Thinking-Rationality-and-Mental-Models/README\|Explore Pillar 02]] | `[[02-Thinking-Rationality-and-Mental-Models.canvas\|Open Canvas]]` |
| 03 | **Psychology, Behavior & Neuroscience** | [[03-Psychology-Behavior-and-Neuroscience/README\|Explore Pillar 03]] | `[[03-Psychology-Behavior-and-Neuroscience.canvas\|Open Canvas]]` |
| 04 | **Mathematics, Statistics & Quantitative Logic** | [[04-Mathematics-Statistics-and-Quantitative-Logic/README\|Explore Pillar 04]] | `[[04-Mathematics-Statistics-and-Quantitative-Logic.canvas\|Open Canvas]]` |
| 05 | **Computer Science & Software Engineering** | [[05-Computer-Science-and-Software-Engineering/README\|Explore Pillar 05]] | `[[05-Computer-Science-and-Software-Engineering.canvas\|Open Canvas]]` |
| 06 | **Artificial Intelligence & Data Systems** | [[06-Artificial-Intelligence-and-Data-Systems/README\|Explore Pillar 06]] | `[[06-Artificial-Intelligence-and-Data-Systems.canvas\|Open Canvas]]` |
| 07 | **Economics, Markets & Investing** | [[07-Economics-Markets-and-Investing/README\|Explore Pillar 07]] | `[[07-Economics-Markets-and-Investing.canvas\|Open Canvas]]` |
| 08 | **Business, Strategy & Enterprise** | [[08-Business-Strategy-and-Enterprise/README\|Explore Pillar 08]] | `[[08-Business-Strategy-and-Enterprise.canvas\|Open Canvas]]` |
| 09 | **Leadership, Organizations & Management** | [[09-Leadership-Organizations-and-Management/README\|Explore Pillar 09]] | `[[09-Leadership-Organizations-and-Management.canvas\|Open Canvas]]` |
| 10 | **Natural Sciences, Health & Biology** | [[10-Natural-Sciences-Health-and-Biology/README\|Explore Pillar 10]] | `[[10-Natural-Sciences-Health-and-Biology.canvas\|Open Canvas]]` |
| 11 | **History, Geopolitics & Civilization** | [[11-History-Geopolitics-and-Civilization/README\|Explore Pillar 11]] | `[[11-History-Geopolitics-and-Civilization.canvas\|Open Canvas]]` |
| 12 | **Philosophy, Ethics & Exceptional Fiction** | [[12-Philosophy-Ethics-and-Human-Society/README\|Explore Pillar 12]] | `[[12-Philosophy-Ethics-and-Human-Society.canvas\|Open Canvas]]` |

---

## 📈 Real-Time Dataview Vault Index

> [!TIP]
> If you have the free **Dataview** Obsidian plugin enabled, the live tables below automatically index all generated summaries in real-time.

```dataview
TABLE WITHOUT ID
  file.link AS "Book Summary",
  author AS "Author",
  pillar AS "Pillar",
  difficulty AS "Difficulty",
  status AS "Status"
FROM "md"
WHERE file.name = "README" AND file.folder != "md"
SORT file.folder ASC
```

---

## 🎧 Audio Listening Editions

```dataview
TABLE WITHOUT ID
  file.link AS "Audio Edition",
  author AS "Author",
  edition AS "Format",
  status AS "Status"
FROM "md"
WHERE file.name = "Audio-Listening-Edition"
SORT file.folder ASC
```
