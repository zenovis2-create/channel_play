# Khufu V8 Combine Spike And Selector Dry Run

- Verdict: **passed**
- ModelImporter Read/Write enabled: `False`
- FBX SHA256 before/after: `234d36eb688337a9461d0b892d6a6d1d8f8ad2c2571aaedbd57cc9de80c5e74d` / `234d36eb688337a9461d0b892d6a6d1d8f8ad2c2571aaedbd57cc9de80c5e74d`
- FBX meta SHA256 before/after: `6457410564068ea13f962237a9178321e5e608f4f5a482f68eeea4b064e2d094` / `6457410564068ea13f962237a9178321e5e608f4f5a482f68eeea4b064e2d094`
- Two-submesh spike: `252 vertices / 216 triangles / vertex ratio 1`
- Selected renderers/submeshes: `245 / 245`
- Forbidden selected: `0`
- Combined donor metrics: `9 renderers / 32110 vertices / 26460 triangles`

| Bucket | Source renderers | Submeshes | Source vertex refs | Combined vertices | Triangles | Bounds size |
|---|---:|---:|---:|---:|---:|---|
| `Basalt_Court` | 3 | 3 | 380 | 380 | 324 | `38, 0.33, 36.5` |
| `Core_Limestone` | 8 | 8 | 1019 | 1019 | 864 | `23.25, 4.84, 11.93` |
| `Door_Shadow` | 11 | 11 | 1403 | 1403 | 1188 | `22, 0.04, 15.128` |
| `Paint_Blue` | 9 | 9 | 1143 | 1143 | 972 | `22.65, 2.868, 8.878` |
| `Paint_Red` | 14 | 14 | 1787 | 1787 | 1512 | `23.25, 4.905, 9.06` |
| `Paint_Teal` | 1 | 1 | 127 | 127 | 108 | `7, 0.1, 0.06` |
| `Relief_Gold` | 192 | 192 | 25344 | 25344 | 20736 | `22.576, 2.378, 8.779` |
| `Tura_Limestone` | 6 | 6 | 778 | 778 | 648 | `23.2, 3.35, 9.5` |
| `Tura_Processional_Aisle` | 1 | 1 | 129 | 129 | 108 | `3, 0.18, 15.2` |

KHUFU_V8_PIPELINE_SPIKE: passed
