# Obsidian Setup

This vault works as plain Markdown without plugins. Plugins improve navigation, editing, metadata, and narration but are not required for essential content.

## Recommended plugins

1. **Read Aloud** or a maintained **Text to Speech** community plugin.
2. **Dataview** for optional indexes and category dashboards.
3. **Templater** for metadata and starter-note scaffolding.
4. **Linter** for YAML, headings, whitespace, and Markdown formatting.
5. **Obsidian Git** for local version control.
6. Built-in **Properties** for front matter editing.

Verify the exact maintained TTS plugin in Obsidian’s Community Plugins browser because plugin names and maintainers can change.

## TTS compatibility

Use Reading view with TTS. YAML front matter is normally treated as metadata and is not read as body text. Raw Markdown readers may speak YAML, so all important explanations remain in ordinary prose.

Every note must:

- Use complete sentences.
- Expand acronyms at first use.
- Explain tables and diagrams in prose.
- Include a natural spoken recap.
- Avoid making essential claims depend on visual layout.
- Keep headings descriptive enough to follow by ear.

## Flexible book structures

The vault does not force a biography, technical textbook, philosophy work, business book, and scientific work into identical headings. Each note may use a structure appropriate to its genre.

The universal core is small:

- Clear book identity and purpose.
- Author’s argument, question, or governing idea.
- Evidence and source quality.
- Strengths and contributions.
- Weaknesses, criticism, limitations, or counterarguments.
- Pros and cons or an equivalent treatment.
- Exactly five memorable points.
- TTS-friendly recap.
- Sources and navigation.

## Link policy

Use safe slug filenames:

```text
md/02-Thinking-Rationality-and-Mental-Models/01-Cognitive-Biases/Thinking-Fast-and-Slow.md
```

Use Obsidian aliases:

```markdown
[[Thinking-Fast-and-Slow|Thinking, Fast and Slow]]
```

Use relative Markdown links for central GitHub navigation:

```markdown
[Thinking, Fast and Slow](md/02-Thinking-Rationality-and-Mental-Models/01-Cognitive-Biases/Thinking-Fast-and-Slow.md)
```

Do not use Dataview as the only navigation system.
