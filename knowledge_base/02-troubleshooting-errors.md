# SmartOps Platform — Troubleshooting & Error Reference

## Error Code Reference

| Code | Meaning | Typical Cause |
|---|---|---|
| `E-101` | Authentication failed | Invalid or revoked API key |
| `E-102` | Clock skew detected | Host clock differs from server time by > 30s |
| `E-201` | Ingest endpoint unreachable | Firewall blocking outbound 443, DNS failure |
| `E-305` | Metrics buffer full | Agent offline too long; disk buffer hit 10 GB cap |
| `E-410` | Agent version unsupported | Agent older than v2.0 — upgrade required |
| `E-500` | Internal agent crash | Check `/var/log/smartops/agent.log` and file a ticket |

## E-101: Authentication Failed

The API key in `agent.yaml` was rejected. To fix:

1. In the console, go to **Settings → API Keys** and confirm the key status is **Active**.
2. Keys are region-scoped — a key created in `eu-west-1` will not authenticate against `us-east-1`.
   Make sure `region` in `agent.yaml` matches the key's region.
3. If the key was rotated, generate a new key, update `agent.yaml`, and restart the agent.

## E-201: Ingest Endpoint Unreachable

The agent cannot reach `ingest.smartops.io:443`. Diagnose in this order:

```bash
# 1. DNS resolves?
nslookup ingest.smartops.io
# 2. Port open?
curl -sv https://ingest.smartops.io/healthz
# 3. Proxy required? Set it in agent.yaml:
#    proxy_url: "http://proxy.internal:3128"
```

Corporate networks often require the proxy setting. The agent does **not** read
system proxy environment variables — the proxy must be set in `agent.yaml`.

## Agent Shows "Not Reporting" in Console

A host with a grey "not reporting" badge has not sent metrics for 5+ minutes. Checklist:

1. Is the service running? `sudo systemctl status smartops-agent`
2. Any errors in the log? `tail -50 /var/log/smartops/agent.log`
3. Restart the agent: `sudo systemctl restart smartops-agent`
4. Confirm network path (see E-201 above).

If the service is running and the log shows successful flushes but the console still
shows grey, the host may be registered in a different environment — check the
environment filter at the top of the Infrastructure page.

## High CPU Usage by the Agent

Normal agent CPU usage is under 2%. Sustained usage above 10% usually means:

- **Log tailing overload:** too many files matched by `logs.include` globs. Narrow the patterns.
- **Cardinality explosion:** custom metrics with unbounded tag values (e.g. a user ID as a tag).
  Cap unique tag values below 1,000 per metric.
- **Old version:** versions before 2.2 had a regex backtracking bug in log parsing — upgrade.

## Collecting a Support Bundle

Before filing a support ticket, generate a diagnostic bundle:

```bash
sudo smartops-agent diag --output /tmp/smartops-diag.tar.gz
```

The bundle contains config (with the API key redacted), the last 10,000 log lines,
and connectivity test results. Attach it to your ticket at support.smartops.io.
