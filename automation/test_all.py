from __future__ import annotations

import json
import sys
from pathlib import Path

from automation.core.colors import C, blue, bold, cyan, dim, green, magenta, red, yellow
from automation.core.config import ROOT, load_settings
from automation.core.manifest import load_manifest
from automation.core.validate import validate_book_directory
from automation.engines.quiz import build_quiz_prompt
from automation.exporters.fetch_covers import fetch_book_metadata_and_cover


def run_all_tests() -> int:
    print(f"\n{C.BRIGHT_CYAN}{'=' * 65}{C.RESET}")
    print(f"{C.BOLD}{C.BRIGHT_CYAN} 🧪 UNIVERSAL BOOK VAULT — FULL SYSTEM VERIFICATION{C.RESET}")
    print(f"{C.BRIGHT_CYAN}{'=' * 65}{C.RESET}\n")

    failures = []

    # 1. Config & Settings
    print(f"{cyan('[1/6]')} {bold('Testing Configuration & Token Limits...')}")
    try:
        s = load_settings()
        assert s.max_tokens >= 65536, f"max_tokens is {s.max_tokens}, expected >= 65536"
        assert s.llm_retries == 10, f"llm_retries is {s.llm_retries}, expected 10"
        print(f"  {green('✓')} Settings loaded: max_tokens={bold(str(s.max_tokens))}, llm_retries={bold(str(s.llm_retries))}, primary={magenta(s.primary_provider)}")
    except Exception as e:
        print(f"  {red('❌ Config error:')} {e}")
        failures.append("Configuration")

    # 2. Cover & Metadata Resolver
    print(f"\n{cyan('[2/6]')} {bold('Testing Intelligent Cover & Metadata Resolver...')}")
    test_cases = [
        ("Make It Stick", "Peter C. Brown; Henry L. Roediger III", "2014"),
        ("Atomic Habits", "James Clear", "2018"),
        ("Thinking, Fast and Slow", "Daniel Kahneman", "2011"),
    ]
    for title, auth, yr in test_cases:
        try:
            meta = fetch_book_metadata_and_cover(title, auth, yr)
            assert meta["cover_url"], f"No cover URL for {title}"
            conf_c = green if meta["confidence"] == "high" else yellow
            print(f"  {green('✓')} {bold(title)} -> {cyan(meta['cover_url'][:45])}... | conf: {conf_c(meta['confidence'])} | ISBN: {meta['isbn']}")
        except Exception as e:
            print(f"  {red(f'❌ Cover resolution error for {title}:')} {e}")
            failures.append(f"Cover ({title})")

    # 3. Book Directory Validator
    print(f"\n{cyan('[3/6]')} {bold('Testing Book Directory Validator...')}")
    try:
        book_dir = ROOT / "md" / "01-Learning-Thinking-and-Knowledge" / "01-LEARNING-SCIENCE" / "Make-It-Stick"
        if not book_dir.exists():
            book_dir = ROOT / "md" / "01-Learning-Cognition-and-Meta-Skills" / "01-Learning-Science-Cognitive-Load" / "Make-It-Stick"
        if not book_dir.exists():
            # Find any existing book directory in the vault
            existing = list(ROOT.glob("md/*/*/*"))
            if existing:
                book_dir = existing[0]
            else:
                # Mock a directory for the validator test
                book_dir.mkdir(parents=True, exist_ok=True)
                (book_dir / "README.md").write_text("---\ntitle: Make It Stick\nnote_type: book-summary\nstatus: complete\n---\n# Summary\n" + ("Word " * 1200), encoding="utf-8")
        rep = validate_book_directory(book_dir)
        assert len(rep["errors"]) == 0, f"Validation errors: {rep['errors']}"
        print(f"  {green('✓')} {book_dir.name} validation: 0 errors, {len(rep['warnings'])} warnings")
    except Exception as e:
        print(f"  {red('❌ Validation error:')} {e}")
        failures.append("Directory Validator")

    # 4. Quiz Prompt Generator
    print(f"\n{cyan('[4/6]')} {bold('Testing Quiz Prompt Generator...')}")
    try:
        sample_book = {"title": "Make It Stick", "author": "Peter C. Brown", "slug": "Make-It-Stick", "category": "Learning Science"}
        prompt = build_quiz_prompt(sample_book, "Sample summary text...")
        assert len(prompt) == 2, "Quiz prompt must have system and user roles"
        assert "```quiz" in prompt[1]["content"], "Prompt must request ```quiz code block"
        print(f"  {green('✓')} Quiz prompt generator structured correctly (system + user roles verified)")
    except Exception as e:
        print(f"  {red('❌ Quiz prompt error:')} {e}")
        failures.append("Quiz Prompt")

    # 5. Obsidian Quiz Plugin Files
    print(f"\n{cyan('[5/6]')} {bold('Testing Obsidian Quiz Plugin Integration...')}")
    try:
        plugin_dir = Path("c:/g/book-vault/.obsidian/plugins/book-vault-quiz")
        manifest = json.loads((plugin_dir / "manifest.json").read_text(encoding="utf-8"))
        main_js = (plugin_dir / "main.js").read_text(encoding="utf-8")
        styles = (plugin_dir / "styles.css").read_text(encoding="utf-8")
        assert manifest["id"] == "book-vault-quiz", "Plugin ID mismatch"
        assert "registerMarkdownCodeBlockProcessor" in main_js, "main.js missing code block processor"
        assert "bvq-container" in styles, "styles.css missing quiz classes"
        print(f"  {green('✓')} Plugin '{manifest['id']}' v{manifest['version']} verified ({len(main_js)} bytes JS, {len(styles)} bytes CSS)")
    except Exception as e:
        print(f"  {red('❌ Obsidian plugin error:')} {e}")
        failures.append("Obsidian Plugin")

    # 6. Web Catalog Exporter
    print(f"\n{cyan('[6/6]')} {bold('Testing Web Catalog & Search Index...')}")
    try:
        site_data = Path("c:/g/book-vault/site/data")
        v_json = site_data / "vault_data.json"
        s_json = site_data / "search_index.json"
        assert v_json.exists() and v_json.stat().st_size > 100000, "vault_data.json missing or too small"
        assert s_json.exists() and s_json.stat().st_size > 10000, "search_index.json missing or too small"
        print(f"  {green('✓')} Web catalog verified: {cyan(str(v_json.stat().st_size))} bytes data, {cyan(str(s_json.stat().st_size))} bytes search index")
    except Exception as e:
        print(f"  {red('❌ Web catalog error:')} {e}")
        failures.append("Web Catalog")

    # Final Summary
    print(f"\n{C.BRIGHT_CYAN}{'=' * 65}{C.RESET}")
    if not failures:
        print(f"{green('✨ ALL 6/6 SYSTEM VERIFICATION TESTS PASSED PERFECTLY!')}")
        print(f"{C.BRIGHT_CYAN}{'=' * 65}{C.RESET}\n")
        return 0
    else:
        print(f"{red(f'❌ {len(failures)} test(s) failed:')} {', '.join(failures)}")
        print(f"{C.BRIGHT_CYAN}{'=' * 65}{C.RESET}\n")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
