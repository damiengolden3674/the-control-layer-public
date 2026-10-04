# Pi Live Verification Inventory

Verified 2026-10-04 through the authorized Mac → Tailscale → TheControlLayer path.

- Host: TheControlLayer
- OS: Debian GNU/Linux 13 (trixie)
- Architecture: aarch64
- Kernel: 6.18.50+rpt-rpi-v8
- Root volume: 28 GiB; ~70.4% used at verification
- External storage: 3.6 TiB mounted at `/mnt/storage`; ~3.5 TiB free
- Docker root: `/mnt/storage/docker`
- Containers running: 14
- Governance services verified active: core Control Layer, authoritative telemetry, AI control plane, anomaly detector, Docker, Prometheus, Alertmanager, auditd
- Policy: OPA 1.10.0
- Observability: OpenTelemetry Collector, Prometheus, Grafana, Loki, Tempo
- Security/proof tools present: Trivy, Syft, Grype, Cosign, Restic, rclone
- Backup SHA-256 verification: true
- Second physical backup: verified SD boot media
- Public projection: read-only, sanitized only, synthetic telemetry false
- Google AI provider: removed

## Verified production verifier

`controllayer/verify-node:14.1-golden-governance-live`

Image ID: `sha256:56fa163e658d93df50a8c76c8a85cc8af416701ebf5947daad5194c72b1aff62`

Hardening remains: non-root UID 10001, read-only root filesystem, all Linux capabilities dropped, no-new-privileges, memory ceiling, host-network binding only where required by the verifier architecture.

## Known HOLD / limitation

The external USB storage bridge does not expose usable SMART identity data to smartmontools. Storage is operational, but physical-drive SMART health is not claimed as verified.

## Governance rule

`INTELLIGENCE != AUTHORITY`

Validated + authorized may execute. Uncertainty holds. Material risk or ambiguity escalates. Human gates remain human.
