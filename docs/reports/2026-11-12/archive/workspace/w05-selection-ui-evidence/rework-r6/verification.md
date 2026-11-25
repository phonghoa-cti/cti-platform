# W05 Selection UI rework R6 verification

- Base: `812dae1ffbdc8e8866342cc075d925fdc99ef12d`
- R6 parent: `def7622676d43b8b13578edefb0bae063ad357df`
- Head: `43737c000561c4d676705dbb564223a7bfa3596e`
- Branch: `feat/w05-selection-ui-20261111`
- Tree status: clean
- Base → head: 12 files, 1014 insertions, 480 deletions
- R6 diff: 2 files, 59 insertions, 9 deletions
- Commit: `fix(portal): release stale pagination requests` (exit 0)
- R1–R5 probe SHA256: `10E2C8589B5935428F3E4D4DEC1AB018AD3C969BD6308E3D62EB97619150F93A`
- R6 probe SHA256: `9AE5EC4FFF3C6E7E1525ED3A0837C008745C41FC582CC58FFE8B462A205915F9`

## RED → GREEN and gates

| Check | Result | Exit | Raw evidence |
|---|---:|---:|---|
| Repo R6 RED | 3 failed, 12 passed / 15 | 1 | `repo-red.log`, `repo-red.xml` |
| Selection UI targeted GREEN | 15 passed / 15 | 0 | `targeted-green.log`, `.json`, `.xml` |
| Leader R1–R5 probe | 15 passed / 15 | 0 | `probe-r1-r5-green.log`, `.json`, `.xml` |
| Leader R6 probe | 2 passed / 2 | 0 | `probe-r6-green.log`, `.json`, `.xml` |
| TypeScript | pass | 0 | `typecheck.log` |
| ESLint | pass, 0 warning/error | 0 | `lint.log` |
| `git diff --check` | pass | 0 | `diff-check.log` |

The R6 scope only changes pagination lifecycle and its regression tests. Full Vitest 86/86 and build evidence from the accepted R1–R5 head were not repeated, per the R6 brief.

No browser/listener/gateway/JWKS/lab/OpenCTI run was performed. Component Vitest is not browser or gateway integration.
