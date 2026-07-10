# Khufu V5 Performance Validation

- Verdict: **failed**
- Budget: `runs/khufu-mega-labyrinth-v5/performance-budget.json`
- Performance receipt: `runs/khufu-v6-visual-slice/performance-final/v6-final-performance.md`
- Observed: `{"frame_p95_ms": 8.34, "gpu_p95_ms": 2.598, "main_thread_p95_ms": 3.073, "maximum_allocated_mb": 147.4, "maximum_managed_mb": 2.8, "maximum_reserved_mb": 262.6, "maximum_visible_renderers": 792, "maximum_visible_triangles": 17292, "maximum_visible_vertices": 24230, "profiler_raw_bytes": 867109562, "quality": "Ultra", "render_thread_p95_ms": 3.258, "resolution": "1536x1024", "samples": 3592}`
- Failure: profiler raw bytes 867109562 outside accepted range

PERFORMANCE_VERDICT: failed
