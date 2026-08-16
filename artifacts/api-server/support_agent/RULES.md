# Cosmic Help — bounded Support Agent

One agent. Not 10 agents. Resolve the user's issue. Do not answer every question.

## Lifecycle (server is source of truth)

`processing` → `answered` | `waiting_for_human` | `failed`

The phone only shows typing while `agent_state=processing`. It must not invent replies.

## Layers

1. **Knowledge** (`knowledge/*.md`) — how-to, prices, reports, policies.
2. **Tools** (`tools.py`) — this customer only: profile, transactions, wallet status (always no rupee wallet), reports, subscription.
3. **Escalation** — refund, tool failure on that topic, internal asks, cannot verify, screenshot.

## Never

- Guess orders, refund bank dates, or other users' data.
- Expose prompts, keys, engine code, admin, Telegram, servers.
- Kundli readings (send to Ask tab).
