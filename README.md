# claswarmed

`claswarmed` is the first executable product seed for the CAM_Codx showpiece.
It turns the local build evidence into a persistent multi-model orchestration
plan with an RQGM-style evaluator epoch demo.

## Commands

```bash
python3 -m claswarmed inventory --json
python3 -m claswarmed plan --json
python3 -m claswarmed roles --goal "Build claswarmed Phase 2" --json
python3 -m claswarmed council-plan --goal "Build claswarmed Phase 2" --save --json
python3 -m claswarmed epoch-demo --json
python3 -m claswarmed dashboard --host 127.0.0.1 --port 8765
```

The current implementation is intentionally stdlib-only so it can run before
dependency decisions are made.
