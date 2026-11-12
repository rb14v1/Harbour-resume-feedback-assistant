# Security: dependency CVE policy and accepted risks

Requirement: `sec.no_critical_cves`. No dependency may ship with a CRITICAL or HIGH
CVE that already has a fixed version. CVEs with no fix are listed below as accepted
risk, each with a justification and a review date.

## Pinning

- Backend: every direct dependency in `backend/requirements.txt` is pinned with `==`.
- Frontend: direct dependencies in `frontend/package.json` use exact versions. The
  generated `frontend/package-lock.json` pins the full transitive tree.
  `react-router-dom` uses `~6.30.1` so it picks up 6.30.x security patches. The
  lockfile fixes the exact version that gets installed.
- Docker: base images are pinned to exact releases (`python:3.12.12-slim`,
  `node:22.21.1-alpine`, `nginx:1.28.0-alpine`). The runtime images also apply OS
  package upgrades at build time.

## Remediated

| Package | Was | Now | CVE / advisory |
|---|---|---|---|
| djangorestframework-simplejwt | 5.3.1 | 5.5.1 | CVE-2024-22513 (disabled users keep access with issued tokens) |
| axios | ^1.7.9 | 1.12.2 | CVE-2025-27152 (SSRF / credential leak), CVE-2025-58754 (DoS) |
| vite (dev only) | ^5.4.11 | 5.4.21 | CVE-2025-30208, CVE-2025-31125, CVE-2025-31486, CVE-2025-32395, CVE-2025-46565, CVE-2025-62522 |
| react-router-dom | ^6.28.0 | ~6.30.1 | latest 6.30.x security patches |

## How to audit

Run these before every deployment. The build must fail on any fixable CRITICAL/HIGH finding:

```sh
pip install pip-audit && pip-audit -r backend/requirements.txt
(cd frontend && npm ci && npm audit --audit-level=high)
trivy fs --severity CRITICAL,HIGH --ignore-unfixed --exit-code 1 .
trivy image --severity CRITICAL,HIGH --ignore-unfixed --exit-code 1 <image>
```

## Accepted risks (no fix available, or not reachable in production)

| ID | Package | Severity | Justification | Review date |
|---|---|---|---|---|
| GHSA-67mh-4wv8-2f99 | esbuild <0.25.0 (transitive via vite 5, dev only) | Moderate | Only affects the local Vite dev server. The production image serves static files from nginx and does not include esbuild. The fix requires moving to Vite 6+, which is a major upgrade. | 2027-02-12 |
| OS packages with no upstream fix | Debian / Alpine base-image packages | Varies | `trivy image --ignore-unfixed` reports these only once a fix exists. Unfixed entries are reviewed when images are rebuilt. | 2027-02-12 |

Re-check every entry on or before its review date, and remove entries once a fix ships.
