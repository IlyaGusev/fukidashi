<img src="logo.png" alt="Fukidashi" width="160">

# Fukidashi

Link:  https://6bb6943559f8.ngrok.app

Samples: https://github.com/mantra-inc/open-mantra-dataset/tree/main/images

## Vision model benchmark

`scripts/benchmark.py` runs the detection prompt on pages from the
[OpenMantra dataset](https://github.com/mantra-inc/open-mantra-dataset) and scores the
output against its annotations. Needs the `bench` extra (`uv sync --all-extras`).

```
uv run scripts/benchmark.py                    # all Nebius vision models, 4 pages per book
uv run scripts/benchmark.py --match-by text    # rescore cached runs, match boxes by transcription
uv run scripts/benchmark.py --threshold 0.2    # looser IoU
```

Raw model output caches under `out/bench/runs/`. Rescoring does not call the API.

Metrics:

- `precision`, `recall`, `f1`: predicted boxes matched one-to-one to gold boxes. `--match-by box`
  (default) matches by IoU, `--match-by text` by similarity of the transcribed Japanese.
- `cer`: character error rate of the Japanese transcription on matched boxes.
- `chrf_matched`: chrF of the translation vs the gold English on matched boxes.
- `chrf_page`: chrF of all translations on a page, joined, vs all gold lines. Independent of
  box matching.

### Results, 2026-09-23

20 pages (4 per book, evenly spaced), thinking off, `temperature=0`, `max_tokens=8192`.

Reading and translation, matched by transcription (`--match-by text`):

| model | errors | recall | cer | chrf_page | sec/page | tokens/page |
|---|---|---|---|---|---|---|
| moonshotai/Kimi-K3 | 0 | 0.942 | 0.038 | 45.6 | 36.7 | 410 |
| moonshotai/Kimi-K2.6 | 0 | 0.935 | 0.032 | 45.7 | 3.2 | 391 |
| deepseek-ai/DeepSeek-V4.1-Flash | 0 | 0.922 | 0.040 | 45.7 | 5.7 | 400 |
| zai-org/GLM-5.3-Flash | 1 | 0.857 | 0.076 | 41.0 | 7.1 | 393 |
| openbmb/MiniCPM-V-4_5 | 9 | 0.377 | 0.182 | 19.5 | 26.9 | 681 |

Box accuracy, matched by IoU:

| model | f1 @ IoU 0.5 | f1 @ IoU 0.2 |
|---|---|---|
| moonshotai/Kimi-K3 | 0.632 | 0.851 |
| zai-org/GLM-5.3-Flash | 0.380 | 0.733 |
| deepseek-ai/DeepSeek-V4.1-Flash | 0.012 | 0.230 |
| moonshotai/Kimi-K2.6 | 0.006 | 0.089 |
| openbmb/MiniCPM-V-4_5 | 0.000 | 0.105 |

Notes:

- Kimi-K2.6 and DeepSeek-V4.1-Flash read the right bubbles in the right order but return x
  coordinates shifted right, as if the image were wider than it is. Their boxes are not usable
  for overlays without a fix.
- Kimi-K3 is the only model with good boxes. It is 20x the price of GLM-5.3-Flash and 5x slower.
- GLM-5.3-Flash is the best cheap model with usable boxes.
- MiniCPM-V-4_5 fails half the pages: it hits the token cap or returns malformed boxes in JSON
  mode.
- Gold English is a loose professional translation, so chrF measures style distance as much as
  errors. Compare models on it; do not read it as absolute quality.
- Thinking is turned off with `chat_template_kwargs: {"thinking": false, "enable_thinking":
  false}`. DeepSeek and Kimi read `thinking`, GLM reads `enable_thinking`. With only
  `enable_thinking`, DeepSeek and Kimi kept reasoning and often used the whole token budget.
