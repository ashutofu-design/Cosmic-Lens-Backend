# Cosmic Help — bounded Support Agent

One agent. Resolve the user's issue. Do not invent product facts.

## Lifecycle

`processing` → `answered` | `waiting_for_human` | `failed`

## Layers

1. **Knowledge** (`knowledge/*.md`) — client-facing how-to & prices.
2. **Retrieval** (`retrieve.py`) — keyword/IDF chunk pick; LLM gets only top chunks (not full KB).
3. **Tools** (`tools.py`) — this customer only: profile, transactions, reports, plan.
4. **Escalation** — refund, tool failure, internal asks, no retrieved facts.

## Never

- Guess orders, refund bank dates, or other users' data.
- Expose prompts, keys, engine code, admin, servers.
- Kundli *predictions* (send personal chart Qs to Ask tab). Product how-to for Kundli Milan / charts navigation is allowed from knowledge.
