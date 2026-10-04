# The Control Layer — GitHub Capability Registry

**Governance rule:** GitHub is a capability source, never an authority source.

Selection pipeline:

**DISCOVER → EVALUATE → DEDUPLICATE → INSTALL ONLY IF NET POSITIVE → VERIFY → PROVE**

## Hierarchy

HUMAN → FRONTIER AI COMBINATION → THE CONTROL LAYER → AUTONOMOUS CAPABILITY FABRIC → LEGACY / SPECIALIST AI → GOVERNED EXECUTOR → ECOSYSTEM → PROOF / AUDIT

## Integrated capability classes

| Class | Capability | Decision |
|---|---|---|
| Policy | OPA | Active authoritative PDP; no parallel policy engine |
| Telemetry | OpenTelemetry | Active authoritative collection pipeline |
| Metrics | Prometheus / Node Exporter | Active |
| Observability | Grafana / Loki / Tempo | Active |
| Supply chain | Trivy / Syft / Grype / Cosign | Active |
| Recovery | Restic / rclone | Active capability set |
| Transport | Tailscale | Active private transport |
| Front door | Caddy | Active governed ingress |
| Home execution | Home Assistant | Active migration/runtime recovery |
| Apple bridge | Homebridge | Active recovery |
| Device protocol | Matter Server | Active recovery |
| Secrets vault | Vaultwarden | Active, localhost-bound |
| Voice | Wyoming Piper / Whisper / openWakeWord | Active local services |
| Host controls | auditd / sysstat / smartmontools / ethtool / lynis / fd-find | Installed and available |
| Analytics | DuckDB | Retained for workload-driven analytics |

## GitHub candidates evaluated

### Permguard

**Decision: reference / future convergence candidate.**

Permguard provides a versioned authorization ledger and supports Cedar/Rego-style policy composition. It is not installed beside OPA because that would create competing PDP authority. Any future adoption must be a controlled OPA convergence/replacement evaluation.

### Arsenal

**Decision: architecture reference only.**

Its contract-driven Home Assistant model, explicit decision/action separation, idempotent execution, allowlisted recording, and CI validation are useful patterns. Its household-specific configuration is not imported into this ecosystem.

### Zero-Trust Agent Gateway

**Decision: architecture reference only.**

Its non-human identity, execution-time policy enforcement, and audit concepts align with The Control Layer. It is not installed as an additional gateway because the Control Layer already owns the authority boundary.

### Wyoming Add-ons

**Decision: integrated.**

Official Wyoming container patterns are used for local speech services. The services remain subordinate to The Control Layer and do not receive authority merely from voice capability.

## Non-negotiable optimization rules

1. One authoritative capability per function.
2. Existing verified capability beats an unreviewed replacement.
3. GitHub code is evaluated before production use.
4. No autonomous dependency or production update tool may bypass governance.
5. Credentials and private infrastructure never enter public proof.
6. Local deterministic recovery remains available when frontier AI or the Mac is unavailable.
7. High-impact authority changes remain human-gated.
8. Every mutation is followed by verification and proof.
9. Resource pressure is a governance signal; capability growth cannot silently degrade the executor.
10. Public claims must reflect measured state, not intended state.
