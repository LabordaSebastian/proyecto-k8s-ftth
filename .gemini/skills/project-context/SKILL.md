---
name: project-context
description: "Use at the START of every session to load the indexed project structure from .codegraph/codegraph.db. Run before any other work. Trigger keywords: context, structure, project, codegraph, index, start, session, init."
---

# Project Context — CodeGraph Structure Loader

When this skill is loaded:

1. Run `python3 .harness/scripts/codegraph-summary.py` to query `.codegraph/codegraph.db` and display the indexed project structure (files, nodes, relationships).

2. Review the output to understand the current project layout without manually exploring directories.

The CodeGraph database is a SQLite file at `.codegraph/codegraph.db`. It is updated by the project's indexer whenever files change. Use this instead of directory listing or globbing for a quick structural overview.