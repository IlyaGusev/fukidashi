<img src="logo.png" alt="Fukidashi" width="160">

# Fukidashi

App (demo, studio, reader): https://fukidashi.lovable.app

Backend: https://6bb6943559f8.ngrok.app

Samples: https://github.com/mantra-inc/open-mantra-dataset/tree/main/images

## Vision model benchmark

`scripts/benchmark.py` runs the detection prompt on pages from the
[OpenMantra dataset](https://github.com/mantra-inc/open-mantra-dataset) and scores the
output against its annotations. Needs the `bench` extra (`uv sync --all-extras`).

```
uv run scripts/benchmark.py                           # all vision models, 10 pages per book
uv run scripts/benchmark.py --efforts off             # skip the thinking runs
uv run scripts/benchmark.py --models zai-org/GLM-5.3-Flash --pages-per-book 4
uv run scripts/benchmark.py --threshold 0.2           # rescore cached runs with a looser match
```

Every model runs with thinking off. Models that the Nebius catalog marks as reasoning also run
with `reasoning_effort` low and medium. Raw model output caches under `out/bench/runs/`, so a
rerun only calls the API for missing pages and rescoring is free. Each call is capped at
`FUKIDASHI_STEP_TIMEOUT` (600 s), the same cap the app uses.

Metrics, printed twice: once with predicted boxes matched to gold boxes by IoU, once matched by
similarity of the transcribed Japanese.

- `precision`, `recall`, `f1`: one-to-one matches at the threshold (default 0.5).
- `cer`: character error rate of the Japanese transcription on matched boxes.
- `chrf_matched`: chrF of the translation vs the gold English on matched boxes.
- `chrf_page`: chrF of all translations on a page, joined, vs all gold lines. Independent of
  matching.
- `errors`: pages where the model returned no parsable answer or hit the timeout.

### Results, 2026-09-23

50 pages (10 per book, evenly spaced, 5 books), `temperature=0`, `max_tokens=65536` (27904 for
MiniCPM, whose context is 32k), 64 calls in flight. Latency is inflated by that concurrency and
by calls that looped up to the token cap.

Of the vision models listed in the Nebius console, `Cosmos3-Super-Reasoner`,
`Qwen2.5-VL-72B-Instruct`, `Nemotron-Nano-V2-12b` and `qwen3-vl-32b` are not on the serverless
API any more (dedicated endpoints only), so they are not here.

Reading and translation, matched by transcription:

| model | effort | errors | recall | cer | chrf_page | sec/page | tokens/page |
|---|---|---|---|---|---|---|---|
| Kimi-K2.6 | off | 0 | 0.949 | 0.044 | 45.1 | 4.6 | 392 |
| Kimi-K3 | off | 1 | 0.938 | 0.050 | 44.8 | 6.0 | 417 |
| Kimi-K3 | low | 0 | 0.965 | 0.037 | 44.8 | 15.1 | 1236 |
| Kimi-K2.6 | medium | 0 | 0.949 | 0.051 | 44.7 | 71.1 | 9193 |
| Kimi-K2.6 | low | 0 | 0.946 | 0.043 | 44.6 | 81.3 | 10604 |
| Kimi-K3 | medium | 2 | 0.925 | 0.036 | 43.9 | 175.6 | 14866 |
| GLM-5.3-Flash | low | 0 | 0.943 | 0.082 | 43.8 | 7.6 | 538 |
| DeepSeek-V4.1-Flash | low | 3 | 0.887 | 0.069 | 43.4 | 56.9 | 4298 |
| DeepSeek-V4.1-Flash | off | 1 | 0.919 | 0.067 | 43.2 | 16.2 | 499 |
| DeepSeek-V4.1-Flash | medium | 2 | 0.887 | 0.062 | 42.4 | 33.1 | 1968 |
| GLM-5.3-Flash | off | 4 | 0.895 | 0.082 | 42.1 | 34.7 | 422 |
| gemma-3-27b-it | off | 1 | 0.801 | 0.157 | 37.8 | 17.1 | 400 |
| GLM-5.3-Flash | medium | 14 | 0.590 | 0.058 | 28.0 | 196.1 | 5746 |
| MiniCPM-V-4_5 | off | 18 | 0.447 | 0.212 | 24.1 | 171.6 | 899 |

Box accuracy, matched by IoU 0.5:

| model | effort | precision | recall | f1 |
|---|---|---|---|---|
| Kimi-K3 | low | 0.628 | 0.739 | 0.679 |
| Kimi-K3 | medium | 0.631 | 0.714 | 0.670 |
| Kimi-K3 | off | 0.572 | 0.671 | 0.618 |
| GLM-5.3-Flash | off | 0.313 | 0.329 | 0.321 |
| GLM-5.3-Flash | medium | 0.332 | 0.264 | 0.294 |
| GLM-5.3-Flash | low | 0.183 | 0.205 | 0.193 |
| Kimi-K2.6 | medium | 0.127 | 0.148 | 0.137 |
| Kimi-K2.6 | low | 0.084 | 0.100 | 0.091 |
| DeepSeek-V4.1-Flash | low | 0.053 | 0.059 | 0.056 |
| DeepSeek-V4.1-Flash | medium | 0.051 | 0.057 | 0.054 |
| Kimi-K2.6 | off | 0.017 | 0.019 | 0.018 |
| DeepSeek-V4.1-Flash | off | 0.011 | 0.016 | 0.013 |
| MiniCPM-V-4_5 | off | 0.007 | 0.011 | 0.009 |
| gemma-3-27b-it | off | 0.006 | 0.005 | 0.006 |

Notes:

- Kimi-K3 is the only model with usable boxes. Low effort helps it a little on boxes and
  transcription for 3x the tokens. Medium effort costs 12x the tokens of off and gains nothing.
- Kimi-K2.6 with thinking off is the best and cheapest reader, but its boxes are wrong: right
  bubbles, right order, x coordinates shifted right. Same for DeepSeek and gemma.
- Thinking does not improve translation for any model. chrF stays within a point of the
  thinking-off run.
- GLM-5.3-Flash low effort fixes the empty answers of the off run but makes its boxes worse.
  Medium effort returns an empty answer on 14 of 50 pages.
- MiniCPM-V-4_5 fails 18 of 50 pages with malformed JSON. Not usable.
- With a 64k budget, a model that loops keeps generating for up to 10 minutes. GLM off, DeepSeek
  off and gemma each did that on 1 to 4 pages. Those pages count as errors.
- Gold English is a loose professional translation, so chrF measures style distance as much as
  errors. Compare models on it; do not read it as absolute quality.
- Thinking is turned off with `chat_template_kwargs: {"thinking": false, "enable_thinking":
  false}` plus `reasoning_effort: none`. DeepSeek and Kimi read `thinking`, GLM reads
  `enable_thinking`. Efforts go through the top-level `reasoning_effort` field.
