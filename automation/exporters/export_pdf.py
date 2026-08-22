"""PDF Exporter for Universal Book Vault.

Converts Audio-Listening-Edition.md and Complete Book Editions into
high-readability, publication-styled PDF documents.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from ..core.config import ROOT


def _sanitize_for_pdf(text: str) -> str:
    """Normalize Unicode characters to clean ASCII/Latin-1 for standard PDF fonts."""
    replacements = {
        "—": " - ",
        "–": " - ",
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
        "…": "...",
        "•": "*",
        "→": "->",
        "←": "<-",
        "★": "*",
        "☆": "*",
        "™": "(TM)",
        "©": "(c)",
        "®": "(R)",
        "🧠": "",
        "📚": "",
        "🧭": "",
        "🎧": "",
        "🎯": "",
        "⚠️": "[Warning]",
        "💡": "[Tip]",
        "✨": "",
        "✓": "[OK]",
        "📖": "",
        "➡️": "->",
        "⬅️": "<-",
        "🏠": "[Hub]",
        "🧩": "",
    }
    for orig, repl in replacements.items():
        text = text.replace(orig, repl)
    # Strip any remaining non-latin1 characters
    return text.encode("latin-1", "replace").decode("latin-1")


class BookVaultPDF:
    """PDF Generator for Book Vault summaries and audio editions."""

    def __init__(self, title: str, author: str, subtitle: str = "Audio Listening Edition"):
        self.title = _sanitize_for_pdf(title)
        self.author = _sanitize_for_pdf(author)
        self.subtitle = _sanitize_for_pdf(subtitle)

    def render_markdown_to_pdf(self, markdown_text: str, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            from fpdf import FPDF
            return self._render_fpdf2(markdown_text, output_path)
        except ImportError:
            html_path = output_path.with_suffix(".html")
            self._render_html(markdown_text, html_path)
            print(f"[pdf] fpdf2 not available; created print-ready HTML -> {html_path.name}")
            return html_path

    def _render_fpdf2(self, markdown_text: str, output_path: Path) -> Path:
        from fpdf import FPDF

        class VaultPDF(FPDF):
            def header(self):
                if self.page_no() > 1:
                    self.set_font("helvetica", "I", 8)
                    self.set_text_color(128, 128, 128)
                    header_text = _sanitize_for_pdf(f"{self.vault_title} - {self.vault_subtitle}")
                    self.set_xy(20, 10)
                    self.cell(170, 8, header_text, align="L")
                    self.ln(10)

            def footer(self):
                self.set_y(-15)
                self.set_font("helvetica", "I", 8)
                self.set_text_color(128, 128, 128)
                self.set_x(20)
                self.cell(170, 10, f"Page {self.page_no()}", align="C")

        pdf = VaultPDF(orientation="P", unit="mm", format="A4")
        pdf.vault_title = self.title
        pdf.vault_subtitle = self.subtitle
        pdf.set_auto_page_break(auto=True, margin=18)
        pdf.set_margins(20, 20, 20)
        pdf.add_page()

        # Title Block
        pdf.set_x(20)
        pdf.set_font("helvetica", "B", 20)
        pdf.set_text_color(24, 30, 42)
        pdf.multi_cell(170, 10, self.title, align="L")
        pdf.ln(2)

        pdf.set_x(20)
        pdf.set_font("helvetica", "I", 12)
        pdf.set_text_color(70, 80, 95)
        byline = f"By {self.author} | {self.subtitle}"
        pdf.multi_cell(170, 6, byline, align="L")
        pdf.ln(6)

        # Divider line
        pdf.set_draw_color(200, 210, 225)
        pdf.set_line_width(0.5)
        pdf.line(20, pdf.get_y(), 190, pdf.get_y())
        pdf.ln(6)

        # Clean markdown of YAML frontmatter
        cleaned = re.sub(r"^---[\s\S]*?---\n", "", markdown_text).strip()
        lines = cleaned.split("\n")

        pdf.set_text_color(30, 35, 45)

        for raw_line in lines:
            line = raw_line.strip()
            if not line:
                pdf.ln(3)
                continue

            safe_text = _sanitize_for_pdf(line)
            pdf.set_x(20)

            # Headings
            if safe_text.startswith("# "):
                pdf.ln(4)
                pdf.set_font("helvetica", "B", 16)
                pdf.set_text_color(18, 28, 48)
                pdf.multi_cell(170, 8, safe_text.lstrip("# ").strip())
                pdf.set_font("helvetica", "", 10)
                pdf.set_text_color(30, 35, 45)
                pdf.ln(2)
            elif safe_text.startswith("## "):
                pdf.ln(3)
                pdf.set_font("helvetica", "B", 13)
                pdf.set_text_color(35, 55, 85)
                pdf.multi_cell(170, 7, safe_text.lstrip("# ").strip())
                pdf.set_font("helvetica", "", 10)
                pdf.set_text_color(30, 35, 45)
                pdf.ln(2)
            elif safe_text.startswith("### "):
                pdf.ln(2)
                pdf.set_font("helvetica", "B", 11)
                pdf.set_text_color(50, 70, 100)
                pdf.multi_cell(170, 6, safe_text.lstrip("# ").strip())
                pdf.set_font("helvetica", "", 10)
                pdf.set_text_color(30, 35, 45)
                pdf.ln(1)
            elif safe_text.startswith("> [!"):
                # Callout block header
                pdf.ln(2)
                pdf.set_fill_color(240, 244, 250)
                pdf.set_font("helvetica", "B", 10)
                pdf.set_text_color(20, 50, 90)
                callout_title = re.sub(r"^>\s*\[!.*?\]-?\s*", "", safe_text)
                pdf.multi_cell(170, 6, f"  Notice: {callout_title}", fill=True)
                pdf.set_font("helvetica", "", 10)
                pdf.set_text_color(30, 35, 45)
            elif safe_text.startswith(">"):
                # Callout body
                pdf.set_fill_color(245, 248, 252)
                pdf.set_font("helvetica", "I", 9.5)
                pdf.multi_cell(170, 5, f"  {safe_text.lstrip('> ').strip()}", fill=True)
                pdf.set_font("helvetica", "", 10)
            elif safe_text.startswith("- ") or safe_text.startswith("* "):
                # List bullet
                clean_bullet = re.sub(r"\[\[([^\|\]]+)\|?([^\]]*)\]\]", lambda m: m.group(2) or m.group(1), safe_text[2:].strip())
                pdf.multi_cell(170, 5.5, f"  * {clean_bullet}")
            elif re.match(r"^\d+\.\s", safe_text):
                # Numbered list
                clean_num = re.sub(r"\[\[([^\|\]]+)\|?([^\]]*)\]\]", lambda m: m.group(2) or m.group(1), safe_text)
                pdf.multi_cell(170, 5.5, f"  {clean_num}")
            elif safe_text.startswith("---"):
                pdf.ln(2)
                pdf.set_draw_color(220, 225, 235)
                pdf.line(20, pdf.get_y(), 190, pdf.get_y())
                pdf.ln(3)
            elif safe_text.startswith("|"):
                # Simple table row formatting
                cells = [c.strip() for c in safe_text.split("|")[1:-1]]
                if cells and not all(c.startswith("-") for c in cells):
                    row_text = " | ".join(cells)
                    clean_row = re.sub(r"\[\[([^\|\]]+)\|?([^\]]*)\]\]", lambda m: m.group(2) or m.group(1), row_text)
                    pdf.set_font("helvetica", "", 9)
                    pdf.multi_cell(170, 5, clean_row)
                    pdf.set_font("helvetica", "", 10)
            else:
                # Standard paragraph
                clean_p = re.sub(r"\[\[([^\|\]]+)\|?([^\]]*)\]\]", lambda m: m.group(2) or m.group(1), safe_text)
                clean_p = re.sub(r"\*\*([^*]+)\*\*", r"\1", clean_p)
                clean_p = re.sub(r"\*([^*]+)\*", r"\1", clean_p)
                clean_p = re.sub(r"`([^`]+)`", r"\1", clean_p)
                pdf.multi_cell(170, 5.5, clean_p)
                pdf.ln(1)

        pdf.output(str(output_path))
        print(f"[pdf] Generated PDF -> {output_path.relative_to(ROOT)}")
        return output_path

    def _render_html(self, markdown_text: str, output_path: Path) -> Path:
        cleaned = re.sub(r"^---[\s\S]*?---\n", "", markdown_text).strip()
        html_body = cleaned.replace("\n\n", "</p><p>").replace("\n", "<br>")
        html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{self.title} - {self.subtitle}</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; line-height: 1.6; max-width: 800px; margin: 40px auto; padding: 0 20px; color: #1e293b; }}
h1 {{ color: #0f172a; border-bottom: 2px solid #e2e8f0; padding-bottom: 8px; }}
h2 {{ color: #1e3a8a; margin-top: 24px; }}
p {{ margin: 12px 0; }}
blockquote {{ background: #f8fafc; border-left: 4px solid #3b82f6; margin: 16px 0; padding: 12px 16px; border-radius: 4px; }}
</style>
</head>
<body>
<h1>{self.title}</h1>
<p><em>By {self.author} | {self.subtitle}</em></p>
<p>{html_body}</p>
</body>
</html>"""
        output_path.write_text(html, encoding="utf-8")
        return output_path


def export_audio_to_pdf(book_dir: Path, output_dir: Path | None = None) -> Path | None:
    """Convert a book's Audio-Listening-Edition.md to a clean PDF."""
    audio_md = book_dir / "Audio-Listening-Edition.md"
    if not audio_md.exists():
        return None

    content = audio_md.read_text(encoding="utf-8")
    title_match = re.search(r"^title:\s*[\"']?(.*?)[\"']?$", content, re.M)
    author_match = re.search(r"^author:\s*[\"']?(.*?)[\"']?$", content, re.M)

    title = title_match.group(1).replace("(Audio Listening Edition)", "").strip() if title_match else book_dir.name
    author = author_match.group(1).strip() if author_match else "Author"

    out_dir = output_dir or book_dir
    out_pdf = out_dir / "Audio-Listening-Edition.pdf"

    exporter = BookVaultPDF(title=title, author=author, subtitle="Audio Listening Edition")
    return exporter.render_markdown_to_pdf(content, out_pdf)


def export_complete_book_to_pdf(book_dir: Path, output_dir: Path | None = None) -> Path | None:
    """Convert full multi-file book reading notes into a single bundled PDF."""
    md_files = sorted([f for f in book_dir.glob("*.md") if f.name not in {"Audio-Listening-Edition.md", "Quiz.md", "Flashcards.md"}])
    if not md_files:
        return None

    compiled_text = []
    title = book_dir.name
    author = "Author"

    for f in md_files:
        content = f.read_text(encoding="utf-8").strip()
        if f.name == "README.md":
            t_m = re.search(r"^title:\s*[\"']?(.*?)[\"']?$", content, re.M)
            a_m = re.search(r"^author:\s*[\"']?(.*?)[\"']?$", content, re.M)
            if t_m:
                title = t_m.group(1)
            if a_m:
                author = a_m.group(1)
        else:
            content = re.sub(r"^---[\s\S]*?---\n", "", content)
        compiled_text.append(content)

    full_md = "\n\n---\n\n".join(compiled_text)
    out_dir = output_dir or book_dir
    out_pdf = out_dir / f"{book_dir.name}-Complete-Reading-Edition.pdf"

    exporter = BookVaultPDF(title=title, author=author, subtitle="Complete Reading Edition")
    return exporter.render_markdown_to_pdf(full_md, out_pdf)


def main() -> int:
    parser = argparse.ArgumentParser(description="Export Book Vault summaries & audio editions to PDF.")
    parser.add_argument("--slug", help="Book slug to export.")
    parser.add_argument("--all", action="store_true", help="Export all generated books to PDF.")
    parser.add_argument("--out", help="Optional output directory.")
    args = parser.parse_args()

    out_path = Path(args.out) if args.out else None

    if args.slug:
        matches = list(ROOT.glob(f"md/*/*/{args.slug}"))
        if not matches:
            print(f"[pdf] Book slug '{args.slug}' not found.")
            return 1
        book_dir = matches[0]
        export_audio_to_pdf(book_dir, out_path)
        export_complete_book_to_pdf(book_dir, out_path)
    elif args.all:
        for book_dir in sorted(ROOT.glob("md/*/*/*")):
            if book_dir.is_dir() and (book_dir / "Audio-Listening-Edition.md").exists():
                export_audio_to_pdf(book_dir, out_path)
                export_complete_book_to_pdf(book_dir, out_path)
    else:
        parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
