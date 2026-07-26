# Khufu V12 Queen Circuit Rules

1. Baseline commit is `1dd7156b064a99eaa2d19ccca0ae605befae54fd`; the baseline scene SHA256 is
   `dbc0c5e3e4afc10397ed3b95bdb57118993a1ba3631b1952c585eb654eb1297b`.
2. No scene write is allowed until the read-only Unity audit and Python prewrite gate pass.
3. V12 owns exactly five new renderers. Because disabled components remain counted, the complete
   map renderer contract is exactly `834`, not the V11 ceiling of `829`.
4. V12 owns exactly 22 colliders (maximum 33); the complete map owns exactly 589
   collider components (maximum 600).
5. `V4_Glow_Queens` and the `V4_Route_Queens_Chamber` renderer remain V10-owned disabled states.
   V12 asserts them but never restores or owns them.
6. V4 Queen blockout renderers/colliders are disabled component-by-component. `SetActive(false)`,
   object deletion, and marker movement are forbidden.
7. `V4_Light_Queens` remains enabled as an inherited dependency and is disclosed in captures.
8. V12 input bindings may be only the V11-open or V12-open assets. Closed V10 input fails closed.
9. V12 limestone geometry equals V11-open limestone. V12 granite equals V11-open granite minus
   exactly `Queen_Ownership_Gate`; extra or missing omissions fail.
10. V11-open asset and `.meta` SHA256 values are immutable inputs:
    - limestone: `1ae211817170a9ae846853b6313c4bdb1277553b7bcd6bc7f30760762a980e67`
    - limestone meta: `2a579b2efd062b16370fe7e5a6f1aedc233fbd057b67de7c9a9fb8d3c8d2dd6c`
    - granite: `1c2cca3af61aaf68e003f813274fd5890d9a88078147e2cd8abb5012481f7d02`
    - granite meta: `4aa71b58e1cdccdc27409da5149aa936095be87c247fb9c5163205cafe652bda`
11. V11's committed signature is required only under restored V11 bindings. The V12 committed
    context gets a separate signature because V11 includes predecessor asset paths in its hash.
12. A V11 rebuild is incomplete until followed immediately by a V12 rebuild and V12 validation.
13. Boundary control starts at least 1.5 m outside the gate plane, has an empty pre-Move overlap
    set, moves at no more than 0.1 m per frame, and requires same-frame `Sides` plus the exact
    `OnControllerColliderHit` name. Proxy-only or overlap-promoted evidence fails.
14. Narrow-mouth object names must not contain the V5-forbidden token `Queens_Shaft`.
15. Rollback restores both V10 mesh bindings, Great Step and Queen proxy flags, all V4 Queen
    component states, generated assets, and scene bytes.
16. The inherited V10 Queen threshold west post, east post, and lintel proxies remain enabled,
    non-trigger colliders in both V11-restored and V12-committed contexts.
17. Runtime proof showed `V10_PROXY_Grand_Gallery_Gallery_Floor_Ramp` physically crosses the
    Queen branch and raises the controller into the preserved lintel. V12 therefore owns only
    this additional collider transition: enabled in restored V11 context, disabled in committed
    V12 context. Its renderer and limestone mesh remain untouched.
18. Built-player traces showed both `Historic_Service_Mouth` frame posts cross the Queen route;
    the first displaced the controller into a V12 wall and the second directly blocked the
    corrected route. V12 therefore disables the west-post, east-post, and lintel colliders as one
    frame transition. Its renderer and mesh remain untouched, and restored V11 context re-enables
    all three.
19. Three exact scene-hash migration bridges used during development are retired from executable
    code: `aad904717bade91e91a7839a3a5bb53ddd60c7380e3959e18320f3719cacd9c5`,
    `6b15448ade13932b6c9a968f4c44f421be56657272ab834e03bf4ab0b26c3644`, and
    `d23f207c2d621ff228e729dee826615b574820229b45d1db6377caf258241248`.
    The canonical scene is `eec9cc9c0b52cd75066c20caf1710ab458423de2eea073c7cfe36e88a782ec8c`;
    only complete V11-open or canonical V12-open component states are accepted from release onward.
