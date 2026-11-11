# Nguồn và kết quả kiểm

- Common base đã đạt: `8a767314b654d39c1ddc2995b7919c44a5b7027a`.
- Backend source: `f4c19d44a33fe588046e0e974af9c18cbf8a1a12`, source tree sạch.
- Frontend source: `cfb612f05f6ae57952362580e35ad59d2aff0a3f`, source tree sạch.
- Cherry-pick local: `0e1e898de29faaedb6deb2a25119545b7912cc64` rồi
  `d5bb1b46e8893cdfbce0dd9f500620ca34fc42b9`; conflict duy nhất lịch sử ở `docs/PROGRESS.md`, giữ cả bằng chứng.
- RED: gateway 13 pass/1 fail do Technology 404; Python 8 fail do scenario/store/snapshot thiếu; wrapper 1 fail do
  thiếu tab Công nghệ. Raw: `red-gateway.log`, `red-python.log`, `red-wrapper.log`.
- GREEN cuối: gateway 14/14, Python harness 42/42, frontend focused 120/120; typecheck/lint/build exit 0,
  build 9/9 static pages. Ma trận HTTP 51 assertion.
- Browser OpenMausBot và viewport thật: UNVERIFIED; xem `BROWSER-STATUS.md`.

Allowlist mới duy nhất: `/api/assets/technologies` và `/api/assets/technologies/{positive-id}`. Gateway test còn
kiểm route gần đúng, dot-segment traversal và response hơn 1 MiB.
