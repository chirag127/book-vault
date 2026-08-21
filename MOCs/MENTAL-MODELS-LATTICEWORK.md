# 🧠 Mental Models & Frameworks Latticework

> "You've got to have models in your head. And you've got to array your experience on this latticework of models." — *Charlie Munger*

This index connects core mental models extracted across the 775 canonical works in the Universal Book Vault.

---

## 🔬 Learning, Cognition & Problem Solving
- **Retrieval Practice**: The cognitive act of reconstructing memories strengthens synaptic consolidation far more than passive recognition.
  - *Key Books*: [[Make-It-Stick]], [[A-Mind-for-Numbers]], [[Ultralearning]]
- **Interleaved Practice**: Mixing related problem types rather than blocking them builds problem-discrimination mastery.
  - *Key Books*: [[Make-It-Stick]], [[Range]]
- **Deliberate Practice**: Pushing beyond the comfort zone with targeted goals and immediate expert feedback.
  - *Key Books*: [[Peak]], [[Talent-is-Overrated]], [[Grit]]
- **First-Principles Thinking**: Breaking a problem down into its most fundamental, indisputable truths and reasoning upward.
  - *Key Books*: [[Thinking-in-Principles]], [[The-Beginning-of-Infinity]]
- **Inversion (Thinking Backwards)**: Solving complex problems by asking what would cause disaster and systematically avoiding it.
  - *Key Books*: [[Seeking-Wisdom]], [[Poor-Charlies-Almanack]]

---

## ⚡ Decision Making & Mental Clarity
- **Second-Order Thinking**: Considering the consequences of the consequences over time.
  - *Key Books*: [[Thinking-in-Bets]], [[The-Great-Mental-Models]]
- **Circle of Competence**: Knowing the exact boundaries of what you truly understand versus what you only think you understand.
  - *Key Books*: [[Poor-Charlies-Almanack]], [[The-Essays-of-Warren-Buffett]]
- **Opportunity Cost**: The hidden loss of the next best alternative when making any choice.
  - *Key Books*: [[Economics-in-One-Lesson]], [[Basic-Economics]]
- **Antifragility**: Systems and minds that gain strength and improve under disorder and stress.
  - *Key Books*: [[Antifragile]], [[The-Black-Swan]], [[Skin-in-the-Game]]

---

## 🛠️ Systems & Habit Engineering
- **Compounding / Atomic Improvements**: Tiny 1% daily increments compound exponentially over time.
  - *Key Books*: [[Atomic-Habits]], [[The-Compound-Effect]]
- **Friction Design (Choice Architecture)**: Increasing friction on bad habits and reducing friction to near-zero on good habits.
  - *Key Books*: [[Nudge]], [[Atomic-Habits]], [[Good-Habits-Bad-Habits]]
- **Deep Work / Cognitive Flow**: Uninterrupted, high-intensity focus on cognitively demanding tasks.
  - *Key Books*: [[Deep-Work]], [[Flow]], [[Hyperfocus]]

---

## 📊 Dataview Dynamic Query for Books with Mental Models

```dataview
TABLE WITHOUT ID
  file.link AS "Book",
  author AS "Author",
  pillar AS "Pillar",
  rating AS "Rating"
FROM "md"
WHERE contains(tags, "mental-models") OR contains(tags, "book-summary")
SORT file.name ASC
```

---
*Maintained by Universal Book Vault.*
