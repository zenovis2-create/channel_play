# Khufu V9 Causeway Fidelity

V9 extends the accepted V8 Temple Hub along the real player approach from Valley Gate through Covered Causeway.
It replaces the visible V5 route graybox in this bounded corridor, preserves the established route and gameplay,
and makes every new structural visual surface either share an existing V5 floor collider or own an explicit,
simplified V9 collision proxy.

This is a production-art and collision-fidelity slice, not a claim that the full 11-district map is finished.

## Final Slice

- Open Valley Gate approach, roofed Covered Causeway, and a 12m open hub fanout.
- Five material-batched renderers and 23 explicit structural BoxCollider proxies.
- Two inherited V5 floor colliders retained as the authoritative walk surface.
- Static, idempotence, mutation, Gate 4, PlayMode, Windows D3D11 traversal, image, performance, and scene-scope
  evidence under `runs/khufu-v9-causeway-fidelity`.
- Independent route-anchor/minimum-distance and error-metric negative controls, inverse collider ownership,
  full PNG decode, and complete Windows payload binding.

Rebuild with `ChannelPlayKhufuV9CausewayFidelityBuilder.RunBatch`; run the full static gate with
`ChannelPlayKhufuV9CausewayFidelityValidator.RunAllStaticGatesBatch`.

Windows proof modes use `-khufu-v9-causeway-proof`, plus either
`-khufu-v9-causeway-proof-mutate-proxy` or `-khufu-v9-causeway-proof-mutate-error-metric` for the two negative
controls. Refresh and validate evidence with `tools/validate_khufu_v9_causeway_fidelity.py`.
