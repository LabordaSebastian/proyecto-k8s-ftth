#!/usr/bin/env python3
"""Query .codegraph/codegraph.db and print a structured project summary.

Usage: python3 .opencode/scripts/codegraph-summary.py
"""
import sqlite3
import os
import sys

DB_PATH = os.path.join(
    os.path.dirname(__file__), "../../.codegraph/codegraph.db"
)

if not os.path.exists(DB_PATH):
    print("⚠️  .codegraph/codegraph.db not found. Run the project indexer first.")
    sys.exit(1)

conn = sqlite3.connect(DB_PATH)

# Files
cur = conn.execute(
    "SELECT path, language, size FROM files ORDER BY path"
)
files = cur.fetchall()
print(f"📁 Files indexed: {len(files)}")
for path, lang, size in files:
    print(f"   {path} ({lang}, {size} bytes)")

# Nodes by kind
cur = conn.execute(
    "SELECT kind, COUNT(*) FROM nodes GROUP BY kind ORDER BY COUNT(*) DESC"
)
nodes_by_kind = cur.fetchall()
print(f"\n📊 Nodes by type: {sum(n for _, n in nodes_by_kind)} total")
for kind, count in nodes_by_kind:
    print(f"   {kind}: {count}")

# All nodes
cur = conn.execute(
    "SELECT kind, name, file_path, start_line, end_line "
    "FROM nodes ORDER BY file_path, start_line"
)
nodes = cur.fetchall()
if nodes:
    print(f"\n📍 All nodes:")
    for kind, name, fpath, sl, el in nodes:
        loc = f"{fpath}:{sl}-{el}"
        print(f"   {kind}: {name} at {loc}")

# Edges
cur = conn.execute(
    "SELECT kind, COUNT(*) FROM edges GROUP BY kind ORDER BY COUNT(*) DESC"
)
edges = cur.fetchall()
if edges:
    print(f"\n🔗 Relationships: {sum(n for _, n in edges)} total")
    for kind, count in edges:
        print(f"   {kind}: {count}")

# Unresolved refs
cur = conn.execute("SELECT COUNT(*) FROM unresolved_refs")
unresolved = cur.fetchone()[0]
if unresolved:
    print(f"\n⚠️  Unresolved references: {unresolved}")

conn.close()
print()
