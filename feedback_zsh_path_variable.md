---
name: feedback-zsh-path-variable
description: "In zsh, never use `path` (lowercase) as a variable name — it's tied to `PATH` and reassigning it breaks subsequent commands."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: c35615d3-a5fa-4e7d-a5b9-7911bfd062d1
---

In zsh, the lowercase variable `path` is a tied array reflection of the `PATH` environment variable. Assigning a string to `path` (e.g., `for path in "/foo" "/bar"`) overwrites PATH and breaks subsequent commands (`wc`, `curl`, etc. become "command not found").

**Why:** Hit this on 2026-05-19 in a Bash probe loop on macOS zsh. Wasted a debugging round.

**How to apply:** In zsh `for` loops or variable assignments, use any name except `path`/`cdpath`/`fpath`/`manpath` (all are tied to their uppercase counterparts). `p`, `url`, `route`, `target` are fine.
