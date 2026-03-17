# Cloudflare Pages + Domain + Access

## Recommended target

- Public origin: `Cloudflare Pages`
- Public hostname: `dash.<your-domain>`
- Access control: `Cloudflare Access`
- Source of deploys: GitHub repository

This keeps the dashboard reachable from 4G at all times without depending on the home PC.

## Build settings in Cloudflare Pages

- Framework preset: `None`
- Build command: `node scripts/dashboard/build_public_site.mjs --output-dir dist`
- Build output directory: `dist`
- Root directory: `/`
- Production branch: `main`

## What the build produces

- Static dashboard files
- Sanitized `data/*.json` without local Windows paths
- `_headers` with security and cache rules
- `_redirects` for cleaner URLs
- `robots.txt` with `Disallow: /`

## Custom domain

- Use a subdomain, not the apex domain: `dash.<your-domain>`
- Add it as a custom domain inside the Pages project
- Wait until the domain status becomes `Active`

## Access policy

Apply `Cloudflare Access` only after the custom domain is active.

Recommended private policy:

- Application type: `Self-hosted`
- Hostname: `dash.<your-domain>`
- Path: `/*`
- Decision: `Allow`
- Include rule: your exact email address

Do not rely on a broad `Allow Everyone` policy if the dashboard should stay private.

## Recommended rollout order

1. Push the repository to GitHub.
2. Create the Pages project from that repository.
3. Confirm the site opens on `*.pages.dev`.
4. Attach `dash.<your-domain>` to the Pages project.
5. Confirm the site opens on your domain.
6. Add `Cloudflare Access` on that domain.
7. Optionally disable or ignore the `*.pages.dev` address for daily use.

## Operational model

- Update dashboard data locally.
- Push to GitHub.
- Cloudflare Pages rebuilds automatically.
- Open the dashboard from any phone over 4G using your domain.

## Current limitation

On the public static site, new ideas in the mindmap are stored only as browser-local drafts when the backend API is absent.
If you want shared write access from phone, add a small backend later.
