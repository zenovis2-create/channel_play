# Khufu V5 PlayMode UI Capture Manifest

- Verdict: **passed**
- Unity: `6000.0.76f1`
- Capture source: Unity MCP `manage_camera` Game View / `ScreenCapture`
- Proof viewport: `1102x577`
- Scene SHA256: `7606cfb305d7b0269af5db6f35544583765a56ebee2bb68844b5b239bf5e65ff`
- Session SHA256: `ac076ff0e37595224fef7e61cb4907301e4203a74c9c676cb5add78e9d0ba9e2`
- Manual HUD SHA256: `0690438af32de032120a0ec29561bb8c79246c5182e2a7f47dd64d14eadcae4f`

## Runtime Preparation

The ready-state captures called `DiagnosticPrepareVisualProof`, which delegates to the production
physical-key collection, mission-terminal confirmation, exit-opening, shop, and operator paths.
The observed state marker was `3/True/True`: three physical keys, terminal confirmed, extraction
authorized. No operator key assist was counted.

## Captures

| Capture | Runtime state | SHA256 | Bytes | Verdict |
| --- | --- | --- | ---: | --- |
| `playmode_ui_initial_final.png` | Keys `0/3`, exit `LOCKED`, participant HUD and manual recorder visible | `2d912f25507ebba394307ffc3dc0e1c02e8a335460a7091c1b0aab1c1c92ea03` | 214999 | passed |
| `playmode_ui_ready_shop_final.png` | Keys `3/3`, terminal confirmed, exit `OPEN`, shop visible | `448899951ae70021c487e5b2975a48b6305c89879e6ba345e2283da1aaf4dfca` | 203142 | passed |
| `playmode_ui_ready_operator_final.png` | Keys `3/3`, exit `OPEN`, operator panel and full surface map visible | `ec0b51c58b3ae4545a4e884ff618b6b3cf17428c0467608d4ad9ff93f785a1a2` | 440413 | passed |

## UI Fit

- Left participant HUD, centre contextual panel, and right scoreboard occupy separate columns.
- The manual traversal panel uses the centre lower region only in participant mode.
- Shop and operator modes hide the redundant manual panel.
- No text or panel overlap is visible at the recorded viewport.
- A `1536x1024` Windows Development Player regression remains part of Gate 6.

PLAYMODE_UI_CAPTURE: passed
