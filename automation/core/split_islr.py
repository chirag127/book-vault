import re
from pathlib import Path

p = Path(r"c:\g\book-vault\md\04-Mathematics-Statistics-and-Quantitative-Logic\03-Statistical-Inference-Modeling\An-Introduction-to-Statistical-Learning")
readme_text = (p / "README.md").read_text(encoding="utf-8")

sections = re.split(r"\n(?=# An Introduction to Statistical Learning — )", readme_text)
print(f"Found {len(sections)} sections in concatenated file.")

slug_mapping = {
    "The Statistical Learning Framework": "01-Statistical-Learning-Framework.md",
    "The Bias-Variance Tradeoff": "02-Bias-Variance-Tradeoff.md",
    "Regression & Classification Methods": "03-Regression-and-Classification.md",
    "Resampling & Model Selection": "04-Resampling-and-Model-Selection.md",
    "Tree-Based Methods": "05-Tree-Based-Methods.md",
    "Unsupervised Learning": "06-Unsupervised-Learning.md",
}

# The first section is the README hub
(p / "README.md").write_text(sections[0].strip() + "\n", encoding="utf-8")
print("Saved clean README.md")

for s in sections[1:]:
    header_m = re.search(r"# An Introduction to Statistical Learning — (.*?)\n", s)
    if header_m:
        title = header_m.group(1).strip()
        matched_file = None
        for k, fname in slug_mapping.items():
            if k.lower() in title.lower() or title.lower() in k.lower():
                matched_file = fname
                break
        if not matched_file:
            matched_file = f"0{len(list(p.glob('0*.md')))+1}-{title.replace(' ', '-')}.md"

        fm = f"""---
title: "An Introduction to Statistical Learning — {title}"
author: "Gareth James, Daniela Witten, Trevor Hastie, Robert Tibshirani"
book_slug: "An-Introduction-to-Statistical-Learning"
parent_hub: "[[README]]"
note_type: summary-chapter
tags: [machine-learning, statistics, data-science, modeling]
---

"""
        out_f = p / matched_file
        out_f.write_text(fm + s.strip() + "\n", encoding="utf-8")
        print(f"Extracted: {matched_file}")
