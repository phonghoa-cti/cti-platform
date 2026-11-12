# Correction for cleanup.log

`cleanup.log` is preserved as raw evidence, but its interpretation of Windows socket error `10035` as
"connection refused" is incorrect. `10035` is `WSAEWOULDBLOCK`; `10061` is `WSAECONNREFUSED`. Therefore the
old six-port probe is not used as proof that listeners were closed.

The three rework runs use OS listener ownership and exact owned resources instead:

- before close, every API/gateway/UI port is a listening socket whose owner PID matches the run's recorded
  Python/gateway/UI PID;
- after `LocalRun.close()`, those exact ports have no listeners, the exact gateway/UI PIDs are absent, the API
  thread is stopped, and the exact `temp_root` no longer exists;
- no wildcard process stop, port cleanup, or `w05-local-*` deletion is used.

See `save-refresh-retry-run.json`, `decision-refresh-retry-run.json`, and `sample-no-api-run.json`.
