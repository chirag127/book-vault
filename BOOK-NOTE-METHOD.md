# Book Note Method

> The goal of a book note is not to preserve every sentence. It is to preserve the book’s structure, argument, evidence, limitations, applications, and connections so that the ideas can be recalled and used later.

## The three layers of a useful note

Every book note should have three layers. It should also be assigned exactly one primary subcategory from [[SUBCATEGORY-MAP]] and placed at the appropriate point in [[READING-ORDER]].

Every book note should have three layers:

1. **Source layer:** What does the author actually argue, and what evidence or examples does the author use?
2. **Evaluation layer:** Which claims are well supported, disputed, outdated, incomplete, or limited to a particular context?
3. **Transfer layer:** What can the reader do with the ideas, and which other books should be read next?

Do not mix these layers carelessly. Use phrases such as “The author argues,” “The evidence supports,” “Critics dispute,” and “A practical implication is” to make the distinction audible.

## Before reading

### 1. Inspect the book

Use [[How-to-Read-a-Book|How to Read a Book]]:

- Read the title and subtitle.
- Identify the author and publication year.
- Inspect the table of contents, preface, index, and conclusion.
- Classify the work as practical, theoretical, historical, scientific, philosophical, biographical, or mixed.
- Write the problem you think the author is trying to solve.

### 2. Define the purpose

Decide whether you are reading for:

- Orientation.
- Information.
- Deep understanding.
- A practical skill.
- Research on a specific question.
- Comparison with other books.

The purpose determines the depth of notes. Not every book needs the same amount of analysis.

### 3. Create a research brief

Before writing the final note, collect:

- The official author or publisher page.
- Bibliographic metadata.
- Primary studies or documents used by the book.
- Serious expert reviews.
- Major criticisms or later evidence.
- Sources that explain whether important claims remain supported.

Never treat a single summary website as sufficient research.

## While reading

### Use question-driven notes

Turn headings and claims into questions:

- What problem is being addressed?
- What is the author’s answer?
- What assumptions are required?
- What evidence supports the answer?
- What would count against it?
- Where does this idea apply?
- Where might it fail?

Question-driven notes are better for later retrieval than copying highlighted sentences.

### Capture arguments, not just quotes

For each major idea, record:

1. The claim.
2. The reason or evidence.
3. The author’s example.
4. The assumption behind the claim.
5. A limitation or counterargument.
6. A practical implication.

Use original wording. Do not reproduce long copyrighted passages.

### Separate evidence types

Label evidence as:

- Primary research.
- Historical document.
- Statistical analysis.
- Expert interpretation.
- Anecdote.
- Authorial example.
- Personal experience.
- Speculation.

A story may illustrate an idea without proving it. A study may support a narrow claim without validating the entire book.

### Record uncertainty immediately

Use notes such as:

- “The author presents this as a general rule, but the evidence appears domain-specific.”
- “This example is memorable but does not establish causation.”
- “The source should be checked against later research.”
- “This claim is philosophical rather than empirically testable.”

Do not wait until the final edit to remember what was uncertain.

## After reading

### 1. Close the book and retrieve

Before checking the source, write or speak:

- The central question.
- The core thesis.
- The three to eight major ideas.
- The strongest evidence.
- The strongest criticism.
- One practical application.

This is retrieval practice. It reveals what you understood rather than what still looks familiar on the page. See [[Make-It-Stick|Make It Stick]].

### 2. Write the quick take

The Quick Take should explain the book in a few paragraphs. It should answer:

- What is the book about?
- Why does it matter?
- What is the main argument?
- What should the reader be cautious about?

It should be useful to someone with only five minutes.

### 3. Write the central question and thesis

The central question is the problem the author is trying to address. The core thesis is the author’s answer in plain language.

Do not confuse the book’s topic with its question. “This book is about habits” is a topic. “How can behavior change become more reliable?” is a question.

### 4. Explain the big picture

Show how the ideas fit together. Use transitions such as:

- “The book begins by…”
- “This leads to…”
- “The next distinction matters because…”
- “Taken together…”
- “The limitation of this move is…”

Do not produce a disconnected list of slogans.

### 5. Write key ideas consistently

For each major idea, explain:

- What it means.
- Why it matters.
- How the author supports it.
- A concrete example.
- A limitation.
- A connection to another book.

The number of ideas should follow the book. Do not invent extra ideas to reach a target count.

## Pros, cons, strengths, and criticism

Use separate but related sections.

### Strengths and Contributions

Describe what the book does especially well:

- A useful framework.
- Original research.
- Historical importance.
- Clear explanation.
- Strong synthesis.
- Practical usefulness.

### Weaknesses, Criticism, and Limitations

Discuss:

- Unsupported or disputed claims.
- Missing perspectives.
- Outdated evidence.
- Overgeneralization.
- Methodological limitations.
- Contexts where the advice fails.
- Ethical or misuse risks.

### Pros and Cons

Use a short summary:

| Pros | Cons |
|---|---|
| What the book contributes | What limits its use |

Immediately explain the table in prose. For TTS, say what the main advantages are and what the main disadvantages are. Never make the table the only discussion.

## How to write for text-to-speech

- Use complete sentences.
- Keep paragraphs short enough to follow by ear.
- Expand an acronym the first time it appears.
- Avoid relying on a table for essential meaning.
- Explain every diagram immediately afterward.
- Explain every equation in words.
- Use descriptive headings.
- Avoid excessive parenthetical statements.
- Put caveats next to the claims they qualify.
- Use natural transitions rather than abrupt bullet chains.
- Include a spoken recap near the end.

Front matter is metadata. Essential meaning must remain in body prose because raw Markdown TTS tools may read YAML differently from Obsidian Reading view.

## How to create meaningful wikilinks

Link a book when the relationship is one of these:

- Prerequisite.
- Extension.
- Contradiction.
- Historical influence.
- Shared evidence.
- Alternative method.
- Practical application.

Use slug aliases:

```markdown
[[Thinking-Fast-and-Slow|Thinking, Fast and Slow]]
```

For central GitHub navigation, also add a relative Markdown link:

```markdown
[Thinking, Fast and Slow](md/02-Thinking-Rationality-and-Mental-Models/01-Cognitive-Biases/Thinking-Fast-and-Slow.md)
```

Do not add links merely to make the graph look dense.

## Retrieval prompts for every book

At the end of the reading process, create five to ten questions such as:

1. What problem is the author trying to solve?
2. What is the core thesis?
3. What are the three strongest supporting ideas?
4. What evidence is weakest or most disputed?
5. Where would the advice fail?
6. Which book provides the strongest alternative?
7. What action follows from the book?

Use these questions in a spaced review system. A note that is never retrieved becomes an archive rather than knowledge.

## Subcategory and learning-path checklist

Before writing, identify:

- The book’s primary category.
- The book’s primary subcategory.
- Its learning stage.
- Prerequisite books or concepts.
- The next useful book or subcategory.

Do not create a duplicate note when a book touches several subcategories. Keep one primary location and use tags and wikilinks for secondary relationships.

## Final checklist

Before marking a book `status: complete`, verify:

- Metadata is valid.
- Title and author are canonical.
- The book has exactly one primary category.
- Sources include official and critical material where available.
- The author’s argument is separated from the editor’s evaluation.
- Strengths and contributions are present.
- Weaknesses, criticism, and limitations are present.
- Pros and cons are present and explained in prose.
- Practical applications are concrete.
- The note contains meaningful wikilinks.
- Every visual has an audio description.
- The TTS recap sounds natural aloud.
- Exactly five points appear in the five-things section.
- Navigation links resolve.
- No invented quotations, studies, statistics, or chapter claims remain.
