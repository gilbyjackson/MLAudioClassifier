## 1. Recommended Strategy For Archive Regeneration

### Core Idea
Split the pipeline into two explicit phases:

1. Inference & Index Build (pure read + metadata write):
   - Traverse original complete_drum_archive.
   - For every audio file, produce one immutable JSONL (newline‑delimited JSON) record capturing:
     - Stable file identity: absolute path, relative path, size, modified time, content hash (md5 or xxhash64).
     - Raw model output: probability vector, top-N predictions (e.g., top3).
     - Chosen label (post-filter rules) + confidence + reason flags (e.g., low_confidence => misc, non_target => misc).
     - Audio attributes: duration, RMS, spectral centroid/rolloff (optional for later heuristics).
     - Processing status flags (too_short, load_error, etc.).
   - Output: `runs/<ts>/index.jsonl` plus `summary.json`.

2. Archive Reconstruction (idempotent, transform):
   - Consumes a selected `index.jsonl`.
   - Applies deterministic mapping rules (confidence threshold, allowed label subset, misc routing, canonical label renames).
   - Materializes a regenerated “clean” archive tree:
     ```
     RegeneratedArchive/
       Crash/
         <original relative path preserved OR normalized naming>
       Hihat/
       ...
       misc/
     ```
   - Optionally: generate per-class manifest files (`Crash_manifest.txt`), dataset stats, and a reversible mapping log for traceability.

### Why Split?
- Re-run reconstruction instantly with different thresholds, label subsets, or naming conventions without recomputing MFCCs or inference.
- Supports audit and human re-label passes (active learning).
- Enables version control of classification decisions separately from model weights.

### File Formats
- Use JSONL (append-friendly, streamable, robust for large sets).
- Provide a compact secondary index (SQLite or Parquet) for rapid querying if dataset grows (optional phase 2).

### Minimal Schema (per JSONL line)
```json
{
  "relative_path": "Akai/Layered/BD_019.wav",
  "abs_path": "/.../complete_drum_archive/Akai/Layered/BD_019.wav",
  "hash": "d41d8cd98f...",
  "size": 12345,
  "mtime": 1730723456.123,
  "duration_sec": 0.412,
  "rms": -24.7,
  "label_top1": "Kick",
  "conf_top1": 0.93,
  "topk": [["Kick",0.93],["Snare",0.04],["Tom",0.01]],
  "probs": [ ... full vector ... ],
  "assigned_label": "Kick",
  "assigned_reason": "top1",
  "misc_routed": false,
  "below_misc_threshold": false,
  "out_of_target": false,
  "errors": null
}
```

### Regeneration Algorithm (Pseudo)
```
for record in jsonl:
   if record.errors: skip -> errors_manifest
   label = record.assigned_label
   if user_override_map.get(hash): label = override
   if label not in allowed_labels and not force_all:
       label = 'misc'
   copy_or_symlink(abs_path -> RegeneratedArchive/label/<relative_path or normalized>)
```

---

## 2. Codebase Changes to Implement

### a. Notebook Refactor → Library + CLI
Extract current logic into reusable modules inside `scripts/` or a new `classifier/` package:
- `classifier/io.py`: file discovery, hashing, JSONL writer.
- `classifier/features.py`: audio load + MFCC + (optional) extra descriptors.
- `classifier/model.py`: model loader, label mapping, calibration utilities.
- `classifier/infer.py`: batching, probability post-processing, thresholding.
- `classifier/rebuild.py`: regeneration logic.

Add a CLI entrypoint (e.g., `python -m classifier.cli infer` / `rebuild`) using `argparse` or `typer`.

### b. JSONL Writer
Stream writes to avoid huge in-memory results. Each batch flushes records:
```python
with open(index_path, 'a') as f:
    for rec in batch_records:
        f.write(json.dumps(rec) + '\n')
```

### c. Parallel Feature Extraction (True)
Current threading hook is unused. Implement:
- ThreadPool (I/O bound) for audio loading & MFCC.
- Or use multiprocessing with a shared model in inference only if CPU compute is a bottleneck (careful: Keras thread safety).
Simpler: Pre-load & preprocess concurrently, queue into a prediction worker.

### d. Probability Calibration & Threshold Module
Add temperature scaling / Platt scaling evaluation on a validation split to produce better confidence semantics. Store `calibration.json` (temperature factor) and apply at inference time:
```
probs = softmax(logits / T)
```

### e. Label Mapping Management
Add:
- `models/label_mapping.json` (source of truth).
- `scripts/validate_mapping.py` to assert mapping vs. model outputs length.
- Automatic stub writer if absent (only created once to avoid accidental override).

### f. Override & Feedback Loop
Add an optional `overrides.jsonl`:
```
{"hash":"abc123","correct_label":"Snare","note":"rim artifact misclassified"}
```
During regeneration, apply overrides (improves dataset for next training cycle). Provide a script to merge overrides into a curated training manifest.

### g. Manifest Generation
In regeneration step:
- `RegeneratedArchive/_manifests/<label>.txt` listing relative paths.
- `RegeneratedArchive/_stats.json` summarizing counts, avg duration, confidence histograms.

### h. Performance Optimizations
| Concern | Change |
|---------|--------|
| Redundant re-hash per run | Maintain persistent `hash->record` index (skip reprocessing) |
| Slow file I/O on large trees | Early size+mtime+hash check; reuse record if unchanged |
| Large probability vectors | Optionally store compressed (quantize to 8-bit) in JSONL or keep separate `.npy` probs matrix |
| Multi-run aggregation | Provide `scripts/aggregate_runs.py` producing a consolidated catalog |

### i. Configuration Standardization
Introduce a `config.yml`:
```yaml
model_path: ../models/model1.keras
label_map: ../models/label_mapping.json
batch_size: 64
target_labels: ["Crash","Hihat","Kick","Ride","Snare","Tom"]
misc:
  threshold: 0.50
  label: misc
paths:
  archive_root: ../complete_drum_archive
  runs_root: ../ClassifiedArchive
  regenerated_root: ../RegeneratedArchive
```
Notebook reads this instead of hard-coded constants (makes CI/testing easier).

---

## 3. ML Optimization Roadmap

### a. Confirm Taxonomy & Class Granularity
If the model outputs far more indices than the 6 canonical drums, decide:
- Collapse certain nuanced categories (e.g., multiple cymbal types) into canonical classes for archive organization.
- Maintain a secondary “fine class” attribute for future percussive specificity.

Implement a mapping file:
```json
{
  "model_class_to_canonical": {
    "Splash": "Crash",
    "China": "Crash",
    "Rim": "Snare",
    "LowTom": "Tom",
    ...
  }
}
```
Apply it post-prediction before assignment.

### b. Active Learning Loop
1. Sort records by (entropy or margin) low confidence.
2. Present top-N uncertain samples in a lightweight UI / simple CSV export for human labeling.
3. Incorporate those corrections into next training cycle.

### c. Class Imbalance Handling
- Compute per-class effective sample size from training set.
- Use focal loss or class-weighting if minority classes (e.g., Kick vs. Crash imbalance) degrade quality.
- Add synthesized augmentation (pitch shift within ±1 semitone, transient emphasis) for under-represented classes.

### d. Model Architecture Refinements
If currently using a simple CNN:
- Try 1D conv front-end on raw waveform + MFCC fusion (parallel branch).
- Add channel attention (SE blocks) to emphasize discriminative frequency bands.
- Evaluate lightweight architectures (EfficientNet-ish 2D conv on MFCC) vs. bespoke conv stack.
- Export best model with quantization-aware training if inference speed becomes a bottleneck.

### e. Confidence Calibration
- Split strict validation subset.
- Fit temperature scaling (very small overhead, big interpretability gain).
- Store temperature in `calibration.json` and reapply at inference.

### f. Ensemble Averaging
Combine Model1 (baseline) + Model2 (autoencoder classifier) by averaging probabilities:
```
probs = (p1 ** w1) * (p2 ** w2); normalize
```
Or simple arithmetic mean; evaluate improvement in top-1 accuracy and confidence reliability.

### g. Error Pattern Mining
Add a script:
- Load `index.jsonl`
- Compute confusion pairs (when top2 probabilities are close and final assignment differs from canonical mapping).
- Surface systematic mix-ups (e.g., Snare vs. Rim vs. Clap) → targeted augmentation / specialized sub-model.

### h. Misc Routing Strategy
Misc is currently low confidence or out-of-target. Consider:
- Two-stage gating model (binary: “is canonical class vs. other percussive”).
- If gating rejects, skip main classifier or treat as unsorted.

---

## 4. Implementation Roadmap (Concrete Steps)

Order and effort (approx):

1. Extract inference logic to `classifier/` package + JSONL streaming writer.  
2. Add label mapping validator + stub generator.  
3. Implement regeneration script using JSONL index to build `RegeneratedArchive/`.  
4. Add override mechanism + apply canonical collapse mapping.  
5. Introduce configuration file and unify parameter loading.  
6. Implement proper parallel audio load & feature extraction queue.  
7. Add calibration script (temperature scaling) + integrate.  
8. Produce manifest + stats generator.  
9. Build active learning uncertainty sampler script.  
10. Optional: ensemble integration & gating model.

---

## 5. Example: New CLI Sketch

`scripts/classifier_cli.py`
```python
import argparse
from classifier import infer, rebuild, calibrate, stats

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)

    p_inf = sub.add_parser('infer')
    p_inf.add_argument('--config', default='config.yml')

    p_reb = sub.add_parser('rebuild')
    p_reb.add_argument('--index', required=True)
    p_reb.add_argument('--out', required=True)
    p_reb.add_argument('--allow-all', action='store_true')

    p_cal = sub.add_parser('calibrate')
    p_cal.add_argument('--val-manifest', required=True)

    p_stat = sub.add_parser('stats')
    p_stat.add_argument('--index', required=True)

    args = ap.parse_args()
    if args.cmd == 'infer':
        infer.run(args.config)
    elif args.cmd == 'rebuild':
        rebuild.run(args.index, args.out, allow_all=args.allow_all)
    elif args.cmd == 'calibrate':
        calibrate.run(args.val_manifest)
    elif args.cmd == 'stats':
        stats.run(args.index)

if __name__ == '__main__':
    main()
```

---

## 6. Risk & Mitigation

| Risk | Mitigation |
|------|------------|
| Wrong label order in mapping | Validator asserts length & optional checksum of raw training label list. |
| JSONL grows large | Support gzip (`index.jsonl.gz`) transparently. |
| Duplicate hashing cost | Use xxhash (faster) instead of md5; cache size/mtime to avoid re-hash unchanged files. |
| Out-of-memory on huge batches | Stream features; dynamic batch size adaptation if memory pressure detected (psutil). |
| Confidence drift after retraining | Always re-run calibration step; embed model version & calibration version in summary. |

---

## 7. ML “Are We Optimized?” Quick Audit Checklist

| Aspect | Current | Target |
|--------|---------|--------|
| Label taxonomy | Unknown superset | Explicit mapping + canonical collapse |
| Confidence calibration | None | Temperature scaling |
| Active learning | None | Uncertainty sampling every run |
| Class imbalance | Unassessed | Weighted loss / augmentation |
| Ensemble | Single model | Optional multi-model average |
| Misc routing | Threshold heuristic | Calibrated + gating model |
| Rebuild agility | Coupled to inference | Decoupled two-phase pipeline |
| Traceability | Limited per-file metadata | JSONL full provenance (hash, features meta) |

---

## 8. Immediate Low-Effort Wins

1. Generate stub `label_mapping_stub.json` if mapping absent (prompt user to fill).
2. Switch to JSONL streaming for results.
3. Add canonical collapse mapping (model classes → 6 kit classes) before misc routing.
4. Add temperature scaling script (fast; improves threshold reliability).
5. Replace md5 with xxhash64 for speed (if acceptable to add dep).

---

## 9. What I Can Implement Next (Pick One or Many)

- A) Add JSONL streaming + stub mapping cell to the current notebook.
- B) Create initial `classifier/` package skeleton with `io.py`, `model.py`, `infer.py`.
- C) Add a regeneration script from existing `results.json` (interim step).
- D) Implement confidence calibration (requires a validation manifest).
- E) Add override ingestion and canonical collapse mapping logic.

Let me know which you’d like prioritized and I’ll start implementing directly.

---

### Quick Recommendation
Start with A + B (foundation), then C (fast regeneration), then tackle calibration and active learning once label mapping is stable.

---

Let me know your chosen next step (or I can auto-start with foundation modules).---

## 6. Risk & Mitigation

| Risk | Mitigation |
|------|------------|
| Wrong label order in mapping | Validator asserts length & optional checksum of raw training label list. |
| JSONL grows large | Support gzip (`index.jsonl.gz`) transparently. |
| Duplicate hashing cost | Use xxhash (faster) instead of md5; cache size/mtime to avoid re-hash unchanged files. |
| Out-of-memory on huge batches | Stream features; dynamic batch size adaptation if memory pressure detected (psutil). |
| Confidence drift after retraining | Always re-run calibration step; embed model version & calibration version in summary. |

---

## 7. ML “Are We Optimized?” Quick Audit Checklist

| Aspect | Current | Target |
|--------|---------|--------|
| Label taxonomy | Unknown superset | Explicit mapping + canonical collapse |
| Confidence calibration | None | Temperature scaling |
| Active learning | None | Uncertainty sampling every run |
| Class imbalance | Unassessed | Weighted loss / augmentation |
| Ensemble | Single model | Optional multi-model average |
| Misc routing | Threshold heuristic | Calibrated + gating model |
| Rebuild agility | Coupled to inference | Decoupled two-phase pipeline |
| Traceability | Limited per-file metadata | JSONL full provenance (hash, features meta) |

---

## 8. Immediate Low-Effort Wins

1. Generate stub `label_mapping_stub.json` if mapping absent (prompt user to fill).
2. Switch to JSONL streaming for results.
3. Add canonical collapse mapping (model classes → 6 kit classes) before misc routing.
4. Add temperature scaling script (fast; improves threshold reliability).
5. Replace md5 with xxhash64 for speed (if acceptable to add dep).

---

## 9. What I Can Implement Next (Pick One or Many)

- A) Add JSONL streaming + stub mapping cell to the current notebook.
- B) Create initial `classifier/` package skeleton with `io.py`, `model.py`, `infer.py`.
- C) Add a regeneration script from existing `results.json` (interim step).
- D) Implement confidence calibration (requires a validation manifest).
- E) Add override ingestion and canonical collapse mapping logic.

Let me know which you’d like prioritized and I’ll start implementing directly.

---

### Quick Recommendation
Start with A + B (foundation), then C (fast regeneration), then tackle calibration and active learning once label mapping is stable.

---

Let me know your chosen next step (or I can auto-start with foundation modules).