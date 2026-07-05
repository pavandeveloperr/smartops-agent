# SmartOps Platform — REST API & Integrations Guide

## Authentication

All API requests require two headers:

```text
SO-API-KEY: <your api key>            # identifies the org, from Settings → API Keys
SO-APP-KEY: <your application key>    # identifies the user/service, from user profile
```

Keys are region-scoped. Use the base URL matching your region:

- `https://api.us-east-1.smartops.io/v2`
- `https://api.eu-west-1.smartops.io/v2`
- `https://api.ap-south-1.smartops.io/v2`

## Rate Limits

| Endpoint group | Limit |
|---|---|
| Metric queries (`/query`) | 300 requests / hour / org |
| Monitor CRUD | 60 requests / minute |
| Event submission | 1,000 requests / minute |

Exceeding a limit returns HTTP `429` with a `Retry-After` header. SDKs retry
automatically with exponential backoff; raw HTTP clients should honor `Retry-After`.

## Querying Metrics

```bash
curl -G "https://api.us-east-1.smartops.io/v2/query" \
  -H "SO-API-KEY: $SO_API_KEY" -H "SO-APP-KEY: $SO_APP_KEY" \
  --data-urlencode "query=avg:system.cpu.utilization{env:production}" \
  --data-urlencode "from=now-1h" --data-urlencode "to=now"
```

The response contains one `series` object per unique tag combination, with
`[timestamp, value]` pairs at automatically chosen rollup intervals.

## Submitting Events

Events annotate dashboards and can trigger event monitors:

```bash
curl -X POST "https://api.us-east-1.smartops.io/v2/events" \
  -H "SO-API-KEY: $SO_API_KEY" -H "Content-Type: application/json" \
  -d '{"title": "Deployed checkout v3.1.0", "tags": ["service:checkout", "type:deploy"]}'
```

Recommended: fire a deploy event from CI on every release. Deploy markers make
incident correlation ("did the deploy cause the error spike?") trivial.

## Terraform Provider

Manage monitors and dashboards as code with the official provider:

```hcl
terraform {
  required_providers {
    smartops = { source = "smartops/smartops", version = "~> 1.8" }
  }
}

resource "smartops_monitor" "high_error_rate" {
  name    = "checkout error rate"
  query   = "sum(last_5m):sum:checkout.errors{*}.as_rate() > 5"
  message = "Checkout errors elevated — @pagerduty-checkout"
}
```

Import existing monitors with `terraform import smartops_monitor.<name> <monitor-id>`.

## Webhook Payload Format

Outbound webhooks POST this JSON shape:

```json
{
  "monitor_id": 4211,
  "monitor_name": "checkout error rate",
  "state": "ALERT",
  "value": 12.4,
  "timestamp": "2026-07-01T12:34:56Z",
  "tags": ["service:checkout"]
}
```

Verify authenticity via the `SO-Signature` header — an HMAC-SHA256 of the raw body
using your org's webhook secret (**Settings → Integrations → Webhooks**).
