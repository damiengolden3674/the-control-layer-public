# Tailscale Employer Verification

## Purpose
Provide an employer-readable, sanitized proof of the authorized Mac → Tailscale → Control Layer Pi path without publishing private device addresses, credentials, or personal endpoint data.

## Verified evidence
- Authorized Mac transport reached the Control Layer Pi over Tailscale.
- The public verifier boundary returned HTTP 200 through the Tailscale HTTPS endpoint.
- Pi runtime was independently reconciled with 14 running containers and no current reconciler findings.
- SHA-256 backup verification passed.
- Public projection is sanitized-only; unmeasured values are not presented as live.

## Governance interpretation
Tailscale is transport and identity-aware connectivity—not authority. The Control Layer remains above the executor. A connectivity proof does not imply permission to mutate production.

## Employer verification
1. Open the public verifier.
2. Confirm the live status and proof fields.
3. Use the portfolio's hierarchy to trace: Human → Frontier AI → Control Layer → Governed Executor → Proof.
4. Treat any missing/ambiguous evidence as HOLD rather than inference.

Tailscale supports identity-aware connectivity and policy-based access controls; its Serve feature can expose a local service privately within the tailnet, while HTTPS provides a browser-compatible certificate boundary.
