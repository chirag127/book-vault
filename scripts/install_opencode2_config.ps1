<#
.SYNOPSIS
  One-shot installer for OpenCode configuration.
  Configures global opencode.json, cli.json, AGENTS.md, and skills.

.USAGE
  pwsh -ExecutionPolicy Bypass -File scripts\install_opencode2_config.ps1
#>

$ErrorActionPreference = "Stop"
$ConfigDir = "$env:USERPROFILE\.config\opencode"
$SkillsDir = "$ConfigDir\skills"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   OpenCode Configuration Installer                       " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# ── 1. Create Directory Hierarchy ─────────────────────────────────────────────
Write-Host "`n[1/4] Creating directory tree in $ConfigDir..." -ForegroundColor Yellow
$dirs = @(
  $ConfigDir,
  "$SkillsDir\book-researcher",
  "$SkillsDir\book-synthesizer",
  "$SkillsDir\git-workflow",
  "$SkillsDir\code-reviewer",
  "$SkillsDir\daily-planner"
)
foreach ($d in $dirs) {
  if (-not (Test-Path $d)) {
    New-Item -ItemType Directory -Force -Path $d | Out-Null
    Write-Host "  + Created: $d" -ForegroundColor DarkGray
  }
}

# ── 2. Install MCP NPM Packages ───────────────────────────────────────────────
Write-Host "`n[2/4] Installing Node & Python MCP servers..." -ForegroundColor Yellow
$nodePackages = @(
  "@playwright/mcp@latest",
  "@modelcontextprotocol/server-memory",
  "@modelcontextprotocol/server-filesystem",
  "@modelcontextprotocol/server-sequential-thinking"
)
foreach ($pkg in $nodePackages) {
  Write-Host "  -> npm install -g $pkg" -ForegroundColor DarkCyan
  try {
    npm install -g $pkg | Out-Null
  } catch {
    Write-Warning "  ! Failed to install $pkg globally; it will be auto-downloaded on first npx run."
  }
}

# Pre-cache Python MCP servers via uvx
Write-Host "  -> uvx pre-caching mcp-server-git & mcp-server-fetch..." -ForegroundColor DarkCyan
try {
  uvx mcp-server-git --help | Out-Null
  uvx mcp-server-fetch --help | Out-Null
} catch {}

# ── 3. Write opencode.json (Verified Compatible Schema) ──────────────────────
Write-Host "`n[3/4] Writing $ConfigDir\opencode.json..." -ForegroundColor Yellow
$opencodeJson = @'
{
  "$schema": "https://opencode.ai/config.json",
  "model": "opencode/x-preview-f-free",
  "providers": {
    "opencode": {
      "package": "aisdk:@ai-sdk/openai-compatible",
      "settings": {
        "baseURL": "https://opencode.ai/zen/v1"
      }
    }
  },
  "permissions": [
    { "action": "read", "resource": "*", "effect": "allow" },
    { "action": "shell", "resource": "git status*", "effect": "allow" },
    { "action": "shell", "resource": "git log*", "effect": "allow" },
    { "action": "shell", "resource": "git diff*", "effect": "allow" },
    { "action": "shell", "resource": "git add*", "effect": "allow" },
    { "action": "shell", "resource": "git commit*", "effect": "allow" },
    { "action": "shell", "resource": "pytest*", "effect": "allow" },
    { "action": "shell", "resource": "python -m automation*", "effect": "allow" },
    { "action": "shell", "resource": "git push*", "effect": "ask" },
    { "action": "shell", "resource": "rm -rf*", "effect": "deny" },
    { "action": "shell", "resource": "del /f*", "effect": "deny" },
    { "action": "shell", "resource": "format*", "effect": "deny" },
    { "action": "*", "resource": "*", "effect": "ask" }
  ],
  "mcp": {
    "playwright": {
      "type": "local",
      "command": ["cmd", "/c", "npx", "-y", "@playwright/mcp@latest", "--extension"],
      "environment": {
        "PLAYWRIGHT_MCP_EXTENSION_TOKEN": "-fSbO8uJ9HgSiDElFNNNAjGLMBI86ns0AGmreNXOudA"
      },
      "enabled": true
    },
    "memory": {
      "type": "local",
      "command": ["cmd", "/c", "npx", "-y", "@modelcontextprotocol/server-memory"],
      "enabled": true
    },
    "filesystem": {
      "type": "local",
      "command": ["cmd", "/c", "npx", "-y", "@modelcontextprotocol/server-filesystem", "c:/g"],
      "enabled": true
    },
    "git": {
      "type": "local",
      "command": ["uvx", "mcp-server-git"],
      "enabled": true
    },
    "sequential-thinking": {
      "type": "local",
      "command": ["cmd", "/c", "npx", "-y", "@modelcontextprotocol/server-sequential-thinking"],
      "enabled": true
    },
    "fetch": {
      "type": "local",
      "command": ["uvx", "mcp-server-fetch"],
      "enabled": true
    },
    "codebase-memory": {
      "type": "local",
      "command": ["codebase-memory-mcp"],
      "enabled": true
    }
  },
  "rules": [
    "ALWAYS use sequential-thinking MCP for tasks with 3+ ambiguous steps.",
    "ALWAYS prefer codebase-memory search_graph over reading raw files.",
    "Use Playwright MCP for browser interactions, visual rendering, and web scraping.",
    "Use Fetch MCP for static URLs and documentation pages.",
    "NEVER execute destructive shell commands without explicit confirmation.",
    "Before writing code, outline the plan in 2-3 concise bullet points.",
    "All Python code must include 'from __future__ import annotations' at top of file.",
    "Follow Conventional Commits: feat/fix/docs/chore(scope): description."
  ]
}
'@
[System.IO.File]::WriteAllText("$ConfigDir\opencode.json", $opencodeJson, [System.Text.Encoding]::UTF8)

# ── 4. Write cli.json (Terminal Configuration) ───────────────────────────────
Write-Host "[4/4] Writing cli.json, AGENTS.md, and skills..." -ForegroundColor Yellow
$cliJson = @'
{
  "$schema": "https://opencode.ai/cli.json",
  "theme": "catppuccin",
  "keybinds": {
    "leader": "ctrl+x",
    "app_exit": "ctrl+x,q",
    "session_new": "ctrl+x,n",
    "session_compact": "ctrl+x,c",
    "session_list": "ctrl+x,s",
    "messages_copy": "ctrl+x,y",
    "editor_open": "ctrl+x,e",
    "theme_picker": "ctrl+x,t",
    "model_picker": "ctrl+x,m",
    "tool_auto_approve": "ctrl+x,a",
    "session_undo": "ctrl+x,u"
  }
}
'@
[System.IO.File]::WriteAllText("$ConfigDir\cli.json", $cliJson, [System.Text.Encoding]::UTF8)

$globalAgentsMd = @'
# Global Agent Instructions

## Identity
Senior research and software engineering assistant. Methodical, verified, and test-driven.

## Core Protocols
1. **Planning**: Use `sequential-thinking` MCP before multi-step tasks.
2. **Code Discovery**: Use `codebase-memory` (`search_graph`, `get_code_snippet`) before opening files.
3. **Web Interaction**: Use `playwright` for interactive pages and `fetch` for static docs/APIs.
4. **Safety**: Never execute destructive commands without explicit confirmation.
5. **Python Standards**: Include `from __future__ import annotations` at the top of all Python files.
'@
[System.IO.File]::WriteAllText("$ConfigDir\AGENTS.md", $globalAgentsMd, [System.Text.Encoding]::UTF8)

# Skill 1: book-researcher
$skill1 = @'
---
name: book-researcher
description: Research a nonfiction book and build a source dossier. Trigger on "research [book]", "find sources for [book]". Do NOT use for writing the note.
---
## Steps
1. OpenLibrary: https://openlibrary.org/search.json?q="{title}"+"{author}"
2. Run 12 DDGS + Wikipedia + Crossref queries via python -m automation.search_clients
3. Save: automation/cache/research/{slug}.json
4. Return dossier path + source count
'@
[System.IO.File]::WriteAllText("$SkillsDir\book-researcher\SKILL.md", $skill1, [System.Text.Encoding]::UTF8)

# Skill 2: book-synthesizer
$skill2 = @'
---
name: book-synthesizer
description: Draft a book vault note from an existing research dossier. Trigger on "write note", "synthesize [book]". Requires book-researcher to have run first.
---
## Steps
1. Load dossier: automation/cache/research/{slug}.json
2. Run: python -m automation.generate --slug {slug} --force
3. Validate: python -m automation.validate_vault --slug {slug}
4. Report: path, word count, provider, validation result
'@
[System.IO.File]::WriteAllText("$SkillsDir\book-synthesizer\SKILL.md", $skill2, [System.Text.Encoding]::UTF8)

# Skill 3: git-workflow
$skill3 = @'
---
name: git-workflow
description: Standard git workflow for staging, committing, pushing, and opening PRs. Trigger on "commit changes", "push this", "open PR".
---
## Steps
1. git status -> git diff -> git add -p -> commit -> git push origin HEAD -> gh pr create --fill
Commit format: feat(scope): description (72 chars, Conventional Commits)
'@
[System.IO.File]::WriteAllText("$SkillsDir\git-workflow\SKILL.md", $skill3, [System.Text.Encoding]::UTF8)

# Skill 4: code-reviewer
$skill4 = @'
---
name: code-reviewer
description: Structured code review covering correctness, style, security, performance, and test coverage. Trigger on "review my code", "check these changes".
---
## Output Format
### What is Good | Issues (Severity/Line/Issue/Fix table) | Optional Improvements
'@
[System.IO.File]::WriteAllText("$SkillsDir\code-reviewer\SKILL.md", $skill4, [System.Text.Encoding]::UTF8)

# Skill 5: daily-planner
$skill5 = @'
---
name: daily-planner
description: Break a complex multi-day project into a prioritised daily schedule. Trigger on "plan this project", "make a schedule for [task]".
---
## Steps
1. Use sequential-thinking MCP to decompose goal
2. Estimate: S (<1hr) M (1-4hr) L (>4hr) — max 6h L/M per day
3. Output Markdown checklist with Day headings + blockers at top
'@
[System.IO.File]::WriteAllText("$SkillsDir\daily-planner\SKILL.md", $skill5, [System.Text.Encoding]::UTF8)

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host "   OpenCode Configuration Successfully Applied!           " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "Global Config  : $ConfigDir\opencode.json" -ForegroundColor White
Write-Host "CLI Terminal   : $ConfigDir\cli.json" -ForegroundColor White
Write-Host "Global AGENTS  : $ConfigDir\AGENTS.md" -ForegroundColor White
Write-Host "Global Skills  : $SkillsDir" -ForegroundColor White
Write-Host "`nTo start OpenCode: run 'opencode2' or 'opencode'" -ForegroundColor Cyan
