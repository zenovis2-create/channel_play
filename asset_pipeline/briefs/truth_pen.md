# Asset Brief: truth_pen

Status: briefed
Source Gate A: blocked
Target: Unity prefab
Scale reference: 0.22m handheld prop; player height 2m
Poly budget: 3,000 triangles maximum
Texture style: broadcast-readable gold, charcoal, and cyan emissive accents
Source/license: Blocked; see `asset_pipeline/manifests/truth_pen_source_gate_a.json`

## Use

Shop inventory icon, world pickup, and held prop for the Truth Pen item. The
gameplay effect reveals one participant as traitor or clear, so the silhouette
must remain recognizable in the shop UI and on an OBS program feed.

## Generation Prompt

Create a compact game-ready truth-detection pen for a stylized Egyptian
gameshow. Use a chunky gold-and-charcoal body, a cyan glowing nib, a strong
asymmetric clip, beveled low-poly forms, and no text, logos, or watermark.
Orthographic three-quarter view on a plain background; show the entire object.

## Review Notes

- Run `python tools/channelctl asset gate-a-check truth_pen`; source creation
  must remain blocked until the Gate A receipt is `PASS`.
- After the source exists, bind its path/hash and the selected 3D provider in
  Gate B. Production remains blocked until `asset gate-b-check` passes.
- Separate the body, clip, and emissive nib for material control.
- Keep a collider-friendly outline with no fragile floating pieces.
- Validate readability from the gameplay camera before acceptance.
