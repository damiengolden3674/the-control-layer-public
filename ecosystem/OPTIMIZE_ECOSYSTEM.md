# Control Layer — GitHub Capability Optimization

## Decision rule
The hierarchy is the control plane. GitHub is a capability source, not an authority source.

Every candidate must pass:
**DISCOVER → EVALUATE → DEDUPLICATE → INSTALL ONLY IF NET POSITIVE → VERIFY → PROVE**

### Current high-value capabilities
- OPA: policy decision engine already present; do not duplicate.
- OpenTelemetry Collector: telemetry pipeline already present; do not add another collector blindly.
- Grafana/Loki/Tempo: observability stack already present.
- Trivy: vulnerability, misconfiguration and secret scanning.
- Syft: SBOM generation.
- Grype: SBOM vulnerability matching.
- Cosign: artifact signature verification.
- Restic: encrypted backup/recovery.
- rclone: governed backup transport.
- DuckDB: local analytics where workload justifies it.
- Renovate: dependency drift automation; enable only after repository policy is ready.
- Grafana Alloy: evaluate as a possible collector consolidation target, not an additional collector.

## Efficiency rules
1. Prefer one capability per function.
2. Prefer deterministic host utilities for host health.
3. Prefer existing containers when they already provide the function.
4. Pin production images by digest after verification.
5. Remove temporary test containers.
6. Keep the recovery reserve.
7. Verify after mutation and record proof.
