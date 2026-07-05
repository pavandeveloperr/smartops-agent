# SmartOps Platform — Alerts & Monitoring How-To

## How Monitors Work

A **monitor** evaluates a metric query on a schedule (default: every 60 seconds) and
transitions between states: `OK → WARN → ALERT`. Each transition can trigger
**notification channels** (email, Slack, PagerDuty, webhook).

## Creating a CPU Alert (walkthrough)

1. In the console, go to **Monitors → New Monitor → Metric Monitor**.
2. Query: `avg(last_5m):avg:system.cpu.utilization{env:production} by {host}`
3. Set thresholds: **WARN** above `0.80`, **ALERT** above `0.95`.
4. Under **Notify**, pick a channel and write the message template:

```text
{{host.name}} CPU is {{value}} — runbook: https://wiki.internal/runbooks/high-cpu
```

5. Click **Create**. The monitor evaluates within one minute.

## Notification Channels

Channels are configured under **Settings → Integrations**:

- **Slack:** install the SmartOps Slack app, then map monitors to channels with the
  `@slack-<channel-name>` handle in the notify field.
- **PagerDuty:** paste the Events API v2 integration key. ALERT creates an incident;
  recovery auto-resolves it.
- **Webhook:** SmartOps POSTs a JSON payload; endpoints must respond 2xx within 10 seconds
  or the delivery is retried 3 times with exponential backoff.

## Muting and Downtimes

To silence alerts during planned maintenance, schedule a **downtime**:
**Monitors → Downtimes → Schedule Downtime**, scope it by tag (e.g. `host:web-*`),
and set the window. Monitors still evaluate during a downtime — they just don't notify.
Expired downtimes un-mute automatically.

## Alert Fatigue: Recommended Practices

- Alert on **symptoms** (error rate, latency) rather than causes (CPU) for user-facing services.
- Use `avg(last_5m)` or longer windows to avoid flapping on momentary spikes.
- Every ALERT-level monitor should link a runbook in its message template.
- Route WARN to Slack and reserve PagerDuty for ALERT.

## Custom Metrics

Applications can submit custom metrics to the local agent on UDP port 8125
(StatsD-compatible):

```python
import statsd
client = statsd.StatsClient("localhost", 8125, prefix="checkout")
client.incr("orders.completed")
client.timing("payment.duration_ms", 187)
```

Custom metrics appear in the console under the `custom.` namespace within 2 minutes.
Keep tag cardinality below 1,000 unique values per metric to avoid ingestion throttling.
