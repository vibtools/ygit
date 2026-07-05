# YGIT Public Premium UI Runtime Verification

Status: PASS
Step: 19H / 19I
Commit: f6f711a Polish dashboard and admin UI premium pass
Verified At: 2026-07-05T10:32:42-07:00
Environment: VPS test runtime behind public HTTPS domain

## Scope

This report records the public HTTPS verification for the premium UI polish pass.

Verified public surfaces:

- relayo.shop API health
- relayo.shop API version
- relayo.shop dashboard
- relayo.shop dashboard assets
- relayo.shop admin
- relayo.shop admin assets
- www.relayo.shop dashboard
- www.relayo.shop admin

## Public HTTPS Route Checks

````text
https://relayo.shop/api/v1/platform/health STATUS=200
https://relayo.shop/api/v1/platform/version STATUS=200
https://relayo.shop/dashboard STATUS=200
https://relayo.shop/dashboard/assets/styles.css STATUS=200
https://relayo.shop/dashboard/assets/app.js STATUS=200
https://relayo.shop/dashboard/assets/logo-mark.svg STATUS=200
https://relayo.shop/dashboard/assets/logo-full.svg STATUS=200
https://relayo.shop/dashboard/assets/favicon.svg STATUS=200
https://relayo.shop/admin STATUS=200
https://relayo.shop/admin/assets/styles.css STATUS=200
https://relayo.shop/admin/assets/app.js STATUS=200
https://relayo.shop/admin/assets/logo-mark.svg STATUS=200
https://relayo.shop/admin/assets/logo-full.svg STATUS=200
https://relayo.shop/admin/assets/favicon.svg STATUS=200
https://www.relayo.shop/dashboard STATUS=200
https://www.relayo.shop/admin STATUS=200
````

Result: PASS

## Premium UI Marker Checks

````text
STEP_19H_PUBLIC_MARKER_FIX_START
PUBLIC_DASHBOARD_PREMIUM_MARKER_PASS
PUBLIC_ADMIN_PREMIUM_MARKER_PASS
PUBLIC_TEMPLATES_BETA_BADGE_PASS
PUBLIC_CONTENT_LENGTHS
dashboard_css_length=16148
admin_css_length=16910
dashboard_html_length=12190
STEP_19H_PUBLIC_MARKER_FIX_PASS
LOG_WRITTEN=operations\runtime-reports\STEP_19H_PUBLIC_HTTPS_PREMIUM_UI_MARKER_FIX.log

````

Result: PASS

## Notes

- The first marker check script produced a false fail because PowerShell treated curl output as an array.
- The corrected marker check joined curl output into a single string before checking markers.
- Public HTTPS route checks returned HTTP 200.
- Premium UI markers were present publicly.
- Templates Beta badge marker was present publicly.

## Architecture Boundary

This verification did not modify backend, Docker, API, worker, migrations, providers, engines, or database schema.

Dashboard and Admin remain presentation-layer surfaces only.
