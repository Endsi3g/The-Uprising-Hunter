# Skills OpenAI installes

Date: 2026-02-13
Source: https://github.com/openai/skills.git

## Resume
- Skills curated detectes dans le repo: 30
- Skills curated installes localement: 30/30
- Skills system disponibles: 2 (preinstalles par Codex)
- Total des skills disponibles localement: 32

Note: le dossier skills/.experimental n'existe pas dans openai/skills au moment de l'installation.

## Skills telecharges (curated)
| Skill | Etat | Description courte |
|---|---|---|
| cloudflare-deploy | installe | Deploy applications and infrastructure to Cloudflare using Workers, Pages, and related platform services. Use when the user asks to deploy, host, publish, or set up a project on Cloudflare. |
| develop-web-game | installe | Use when Codex is building or iterating on a web game (HTML/JS) and needs a reliable development + testing loop: implement small changes, run a Playwright-based test script with short input bursts and intentional pauses, inspect screenshots/text, and review console errors with render_game_to_text. |
| doc | installe | Use when the task involves reading, creating, or editing `.docx` documents, especially when formatting or layout fidelity matters; prefer `python-docx` plus the bundled `scripts/render_docx.py` for visual checks. |
| figma | installe | Use the Figma MCP server to fetch design context, screenshots, variables, and assets from Figma, and to translate Figma nodes into production code. Trigger when a task involves Figma URLs, node IDs, design-to-code implementation, or Figma MCP setup and troubleshooting. |
| figma-implement-design | installe | Translate Figma nodes into production-ready code with 1:1 visual fidelity using the Figma MCP workflow (design context, screenshots, assets, and project-convention translation). Trigger when the user provides Figma URLs or node IDs, or asks to implement designs or components that must match Figma specs. Requires a working Figma MCP server connection. |
| gh-address-comments | installe | Help address review/issue comments on the open GitHub PR for the current branch using gh CLI; verify gh auth first and prompt the user to authenticate if not logged in. |
| gh-fix-ci | installe | Use when a user asks to debug or fix failing GitHub PR checks that run in GitHub Actions; use `gh` to inspect checks and logs, summarize failure context, draft a fix plan, and implement only after explicit approval. Treat external providers (for example Buildkite) as out of scope and report only the details URL. |
| imagegen | installe | Use when the user asks to generate or edit images via the OpenAI Image API (for example: generate image, edit/inpaint/mask, background removal or replacement, transparent background, product shots, concept art, covers, or batch variants); run the bundled CLI (`scripts/image_gen.py`) and require `OPENAI_API_KEY` for live calls. |
| jupyter-notebook | installe | Use when the user asks to create, scaffold, or edit Jupyter notebooks (`.ipynb`) for experiments, explorations, or tutorials; prefer the bundled templates and run the helper script `new_notebook.py` to generate a clean starting notebook. |
| linear | installe | Manage issues, projects & team workflows in Linear. Use when the user wants to read, create or updates tickets in Linear. |
| netlify-deploy | installe | Deploy web projects to Netlify using the Netlify CLI (`npx netlify`). Use when the user asks to deploy, host, publish, or link a site/repo on Netlify, including preview and production deploys. |
| notion-knowledge-capture | installe | Capture conversations and decisions into structured Notion pages; use when turning chats/notes into wiki entries, how-tos, decisions, or FAQs with proper linking. |
| notion-meeting-intelligence | installe | Prepare meeting materials with Notion context and Codex research; use when gathering context, drafting agendas/pre-reads, and tailoring materials to attendees. |
| notion-research-documentation | installe | Research across Notion and synthesize into structured documentation; use when gathering info from multiple Notion sources to produce briefs, comparisons, or reports with citations. |
| notion-spec-to-implementation | installe | Turn Notion specs into implementation plans, tasks, and progress tracking; use when implementing PRDs/feature specs and creating Notion plans + tasks from them. |
| openai-docs | installe | Use when the user asks how to build with OpenAI products or APIs and needs up-to-date official documentation with citations (for example: Codex, Responses API, Chat Completions, Apps SDK, Agents SDK, Realtime, model capabilities or limits); prioritize OpenAI docs MCP tools and restrict any fallback browsing to official OpenAI domains. |
| pdf | installe | Use when tasks involve reading, creating, or reviewing PDF files where rendering and layout matter; prefer visual checks by rendering pages (Poppler) and use Python tools such as `reportlab`, `pdfplumber`, and `pypdf` for generation and extraction. |
| playwright | installe | Use when the task requires automating a real browser from the terminal (navigation, form filling, snapshots, screenshots, data extraction, UI-flow debugging) via `playwright-cli` or the bundled wrapper script. |
| render-deploy | installe | Deploy applications to Render by analyzing codebases, generating render.yaml Blueprints, and providing Dashboard deeplinks. Use when the user wants to deploy, host, publish, or set up their application on Render's cloud platform. |
| screenshot | installe | Use when the user explicitly asks for a desktop or system screenshot (full screen, specific app or window, or a pixel region), or when tool-specific capture capabilities are unavailable and an OS-level capture is needed. |
| security-best-practices | installe | Perform language and framework specific security best-practice reviews and suggest improvements. Trigger only when the user explicitly requests security best practices guidance, a security review/report, or secure-by-default coding help. Trigger only for supported languages (python, javascript/typescript, go). Do not trigger for general code review, debugging, or non-security tasks. |
| security-ownership-map | installe | Analyze git repositories to build a security ownership topology (people-to-file), compute bus factor and sensitive-code ownership, and export CSV/JSON for graph databases and visualization. Trigger only when the user explicitly wants a security-oriented ownership or bus-factor analysis grounded in git history (for example: orphaned sensitive code, security maintainers, CODEOWNERS reality checks for risk, sensitive hotspots, or ownership clusters). Do not trigger for general maintainer lists or non-security ownership questions. |
| security-threat-model | installe | Repository-grounded threat modeling that enumerates trust boundaries, assets, attacker capabilities, abuse paths, and mitigations, and writes a concise Markdown threat model. Trigger only when the user explicitly asks to threat model a codebase or path, enumerate threats/abuse paths, or perform AppSec threat modeling. Do not trigger for general architecture summaries, code review, or non-security design work. |
| sentry | installe | Use when the user asks to inspect Sentry issues or events, summarize recent production errors, or pull basic Sentry health data via the Sentry API; perform read-only queries with the bundled script and require `SENTRY_AUTH_TOKEN`. |
| sora | installe | Use when the user asks to generate, remix, poll, list, download, or delete Sora videos via OpenAI\u2019s video API using the bundled CLI (`scripts/sora.py`), including requests like \u201cgenerate AI video,\u201d \u201cSora,\u201d \u201cvideo remix,\u201d \u201cdownload video/thumbnail/spritesheet,\u201d and batch video generation; requires `OPENAI_API_KEY` and Sora API access. |
| speech | installe | Use when the user asks for text-to-speech narration or voiceover, accessibility reads, audio prompts, or batch speech generation via the OpenAI Audio API; run the bundled CLI (`scripts/text_to_speech.py`) with built-in voices and require `OPENAI_API_KEY` for live calls. Custom voice creation is out of scope. |
| spreadsheet | installe | Use when tasks involve creating, editing, analyzing, or formatting spreadsheets (`.xlsx`, `.csv`, `.tsv`) using Python (`openpyxl`, `pandas`), especially when formulas, references, and formatting need to be preserved and verified. |
| transcribe | installe | Transcribe audio files to text with optional diarization and known-speaker hints. Use when a user asks to transcribe speech from audio/video, extract text from recordings, or label speakers in interviews or meetings. |
| vercel-deploy | installe | Deploy applications and websites to Vercel. Use when the user requests deployment actions like "deploy my app", "deploy and give me the link", "push this live", or "create a preview deployment". |
| yeet | installe | Use only when the user explicitly asks to stage, commit, push, and open a GitHub pull request in one flow using the GitHub CLI (`gh`). |

## Skills system (preinstalles)
| Skill | Description courte |
|---|---|
| skill-creator | Guide for creating effective skills. This skill should be used when users want to create a new skill (or update an existing skill) that extends Codex's capabilities with specialized knowledge, workflows, or tool integrations. |
| skill-installer | Install Codex skills into $CODEX_HOME/skills from a curated list or a GitHub repo path. Use when a user asks to list installable skills, install a curated skill, or install a skill from another repo (including private repos). |

## Comment utiliser les skills
1. Redemarrer Codex pour charger les nouveaux skills.
2. Appeler un skill explicitement dans la demande avec son nom, par exemple: `$playwright teste la page d'accueil` ou `$pdf extrait le texte de contrat.pdf`.
3. Vous pouvez aussi decrire votre besoin en langage naturel: Codex active le skill adapte si la demande correspond a sa description.
4. Pour forcer un skill precis, preferez toujours la forme explicite `$nom-du-skill`.
5. Verifier les skills installes: `python C:/Users/Karl/.codex/skills/.system/skill-installer/scripts/list-skills.py --format json`.

## Exemples rapides
- `$vercel-deploy deploie cette application en preview`
- `$gh-fix-ci analyse les checks GitHub en echec et propose un plan de correction`
- `$doc cree un fichier .docx avec un plan projet`
- `$speech genere une voix off a partir de ce texte`
- `$yeet commit, push et ouvre une PR`

