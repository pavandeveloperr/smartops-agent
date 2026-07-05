# SmartOps Platform — Installation & Setup Guide

## System Requirements

SmartOps Agent v2.4 requires:

- **OS:** Ubuntu 20.04+, Debian 11+, RHEL 8+, or Windows Server 2019+
- **CPU/RAM:** 2 vCPUs and 4 GB RAM minimum (8 GB recommended for production)
- **Disk:** 10 GB free space for logs and the local metrics buffer
- **Network:** outbound HTTPS (port 443) to `ingest.smartops.io`

## Installing the Agent (Linux)

Install via the official install script:

```bash
curl -fsSL https://get.smartops.io/install.sh | sudo bash
```

This installs the `smartops-agent` systemd service. Verify the installation:

```bash
smartops-agent --version
sudo systemctl status smartops-agent
```

## Installing the Agent (Windows)

Download the MSI from the SmartOps console (**Settings → Agents → Download**), then run:

```powershell
msiexec /i SmartOpsAgent-2.4.msi /qn SMARTOPS_API_KEY=<your-key>
```

The agent registers itself as the Windows service `SmartOpsAgent`.

## Initial Configuration

The main configuration file lives at `/etc/smartops/agent.yaml` (Linux) or
`C:\ProgramData\SmartOps\agent.yaml` (Windows). Minimum required fields:

```yaml
api_key: "sk-ops-xxxxxxxxxxxx"   # from Console → Settings → API Keys
environment: "production"        # free-form label shown in dashboards
region: "us-east-1"              # nearest ingest region: us-east-1, eu-west-1, ap-south-1
```

After editing the config, restart the agent: `sudo systemctl restart smartops-agent`.

## Registering the Agent with the Console

1. Log in to the SmartOps console at `https://console.smartops.io`.
2. Go to **Settings → Agents → Register New Agent**.
3. Copy the generated API key into `agent.yaml` as shown above.
4. Within 60 seconds the host should appear on the **Infrastructure** page with a green "reporting" badge.

If the host does not appear after 5 minutes, see the Troubleshooting guide
(common causes: firewall blocking port 443, wrong region, or clock skew greater than 30 seconds).

## Upgrading

Upgrades are in-place and keep your configuration:

```bash
sudo smartops-agent upgrade --channel stable
```

Use `--channel beta` only on non-production hosts. Downgrades require uninstalling
and reinstalling the target version; configuration in `/etc/smartops` is preserved.
