# Runbook — Local-lane (Ollama) tuning for the dev machine

**Applies to:** any GPU-less development machine running the local model lane
(`local-reasoning` = `qwen2.5:7b-instruct-q4_K_M`, `local-embeddings` = `bge-m3`).

**Symptom it fixes:** integration tests that pass individually but fail in the
full suite with `GatewayError: gateway call failed for model 'local-reasoning'`
and an HTTP **500** from the litellm proxy.

## Two corrections from task 12.2

- **The per-model `timeout:` on the Ollama lane does nothing.** litellm's Ollama
  path reads the global `litellm.request_timeout`, so a local call was dying at
  ~180s (3 attempts × the old 60s) no matter what the model block said — which
  means the `timeout: 300` this lane carried since Sprint 8 was never in effect.
  `request_timeout` is now 900s, matched by `FLEET_LITELLM_TIMEOUT` on the
  client.
- **Do not run a 14B on a card smaller than it.** With 14 GB resident against
  8 GB of VRAM, Ollama splits ~53/47 GPU/CPU; a first call ran in ~200s and
  sustained load degraded until a four-field extraction did not return inside
  600s. Check `ollama ps` — if the PROCESSOR column shows a CPU share, the model
  is too big for the card and you want the smaller one.

## Why this happens

The failure is *not* a client timeout, not our request metadata, and not a
connection leak — all three were measured and ruled out (see the 2026-09-01
entry in `docs/PROGRESS.md`). It is CPU-only Ollama contention, with two
compounding causes:

1. **Model swapping.** The suite alternates between embeddings (RAG tests) and
   reasoning (HR/invoice tests). With the default short `keep_alive`, Ollama
   evicts one model to load the other, and on CPU a cold load costs **~20s**
   versus **~1s** warm.
2. **Queue build-up.** Concurrent requests to a CPU-only instance queue almost
   linearly — four parallel `local-reasoning` calls were measured at
   **14s / 31s / 48s / 63s**.

Under that accumulated latency, aiohttp's timer inside
`litellm/llms/ollama.py` fires and the proxy returns 500.

## The settings

This machine runs Ollama as a **snap inside WSL Ubuntu** (not a Windows
service, not the repo's compose stack — `snap services ollama` shows
`ollama.listener`). Configure it with `snapctl`-backed keys:

```bash
wsl -d Ubuntu -u root -- snap set ollama \
    keep-alive=1h num-parallel=1 max-loaded-models=2 load-timeout=10m
wsl -d Ubuntu -u root -- snap restart ollama
```

| Key | Value | Why |
|---|---|---|
| `keep-alive` | `1h` | Stops the evict/reload cycle between embeddings and reasoning — the main win. |
| `max-loaded-models` | `2` | Lets both lane models stay resident at once (there are exactly two). |
| `num-parallel` | `1` | Serialises the queue. On CPU, concurrency does not add throughput; it only spreads the same work over longer individual requests. |
| `load-timeout` | `10m` | Headroom for a genuine cold load on slow disks. |

Verify the values actually reached the process (writing the config is not
enough — the service must be restarted):

```bash
wsl -d Ubuntu -u root -- snap get ollama -d
wsl -d Ubuntu -u root -- bash -c 'tr "\0" "\n" < /proc/$(pgrep -f "ollama serve")/environ | grep -a OLLAMA'
```

## Measured effect

Sequential alternation — which is what the suite actually does, since pytest
runs without `xdist`:

| Sequence | Before | After |
|---|---|---|
| embed → reason → embed | 20s / 12s / 1s | 1s / 16s / 1s |
| second reason call | — | 7s (warm) |

Both models stay resident afterwards (`curl localhost:11434/api/ps` lists two).

**Honest caveat:** `num-parallel=1` does *not* make the 4-way concurrent case
faster — it was re-measured at 22/30/50/85s, i.e. the tail got *longer*, not
shorter, because requests now strictly queue. That is an acceptable trade for
this suite (sequential, so it never pays the concurrency cost), but do not
expect it to help a genuinely concurrent workload. On CPU no configuration
does; that needs a GPU.

## Measured effect on the actual suite — partial, not a cure

Full integration suite before and after, same machine, same ordering:

| | Before | After |
|---|---|---|
| Result | 5 failed / 64 passed | **4 failed / 65 passed** |
| litellm HTTP 500s | several | **zero** |

So the tuning **did** eliminate the proxy-500 failure mode, and
`test_hr_agent_e2e_live` — the heaviest local-lane consumer — went green. It
did **not** fix the three RAG tests or `test_pii_logging_masked_live`, which
still fail in the full suite while passing in isolation, now with **no 500 in
the log at all**. That means those four have a *different* root cause from the
contention one documented above; the earlier diagnosis that lumped all five
together was incomplete. Their real cause is still open — see
`docs/PROGRESS.md`.

## What this is not

Not a production setting. Production runs the local lane on GPU hardware where
neither the swap cost nor the queueing behaviour applies. This runbook exists
so a new developer machine reproduces the same green suite without
rediscovering the root cause.
