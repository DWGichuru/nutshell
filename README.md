# Nutshell

A local tool that turns a YouTube video into a trimmed, transcribed,
AI-summarized text asset - paste a link, get a searchable summary.

See `blueprint/project-plan.md` for the full problem statement and
`blueprint/context/project-overview.md` for the current project context.

## Commands

Activate the virtual environment first: `source venv/bin/activate`.

- Install deps: `pip install -r requirements.txt`
- Dev server: `uvicorn backend.main:app --reload` (http://localhost:8000)

## Workflow

This project uses the [AI Blueprint](blueprint/README.md) workflow. See
`AGENTS.md` for the AI agent instructions.
