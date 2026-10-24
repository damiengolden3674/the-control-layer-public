# Wix integration material

The existing career portal remains the canonical destination:
https://damiengolden3674.github.io/the-control-layer-public/career-verification.html

`wix-career-embed.html` is generated from that portal with absolute public links and top-level navigation. It contains no scripts, runtime calls, account details or private operational records. This file is integration material, not a published Wix site.

Use the same navigation labels and targets on an established Wix site:

| Label | Target |
| --- | --- |
| Portfolio | https://damiengolden3674.github.io/the-control-layer-public/ |
| Career & verification | https://damiengolden3674.github.io/the-control-layer-public/career-verification.html |
| Credentials catalogue | https://damiengolden3674.github.io/the-control-layer-public/credentials.html |
| Resume PDF | https://damiengolden3674.github.io/the-control-layer-public/resume/Damien_Golden_Executive_Resume.pdf |
| Evidence status | https://damiengolden3674.github.io/the-control-layer-public/verify.html |
| GitHub | https://github.com/damiengolden3674/the-control-layer-public |

Brand: Golden Governance LLC · The Control Layer™ · Where Intelligence Becomes Governable.

Use Founder / Architect as the project role. AI Governance Director is a career goal. Preserve the document-reviewed credential label and historical build/test limits. Keep issuer links in the catalogue instead of creating an independently maintained list.

Run `python3 scripts/export_wix.py` after editing the portal and `python3 scripts/check_public_portfolio.py` before a release. After integrating into a real Wix site, verify its published URL, mobile navigation, resume download and all outbound destinations. A replacement or domain cutover requires an explicit destination decision; this package assumes no cutover.
