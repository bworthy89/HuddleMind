# Private web headquarters: first functional slice

`/app` runs Next.js with TypeScript. `/preview/` remains the public sample design.
This release provides single-owner sign-in and a live read-only Overview with
snapshot freshness, next game, record, roster/recruiting counts, and bridge status.
The Roster screen now supports all synced players, name search, quick and complete
position filters, rating/name sorting, and player details. Detail navigation keeps
filters and restores focus to the selected row. Depth/injury matches use both
table and row ID; missing sections remain unavailable. In-game verification of
those fields remains pending and is labeled in the detail screen.

Schedule shows current-season fixtures in week order, team-relative W/L/T results,
next scheduled fixtures, and pending/completed/unknown filters. Completion comes
from status, not score values. Unknown statuses stay unknown; gaps do not imply
byes. Recruiting shows saved board totals and target hours separately, supports
name/position/stage filters and rank/hours/name sorting, and expands target details
including scholarship status. Missing boards, empty boards, and zero hours have
different displays. No commitment odds or star ratings are invented.
The dynasty selector appears on all four tabs and remembers the browser's choice
for 30 days in a secure, HttpOnly preference cookie. It only accepts IDs already
authorized by the receiver; selection never expands the allowlist. All tabs and
bridge health resolve the same choice. Missing snapshots remain selectable;
removed IDs fall back with a notice. Team names label choices, with IDs appended
only when names collide. Adding another real dynasty still requires explicit
bridge/receiver configuration; the selector does not create or capture saves.

## Authentication

Player details now include grouped saved ratings. See `docs/PLAYER_RATINGS.md` for
source evidence and compatibility. Deploy receiver and web together for this
release: older receivers reject the additive ratings field. Historical snapshots
remain unchanged and show ratings unavailable until a new enriched save is synced.

The web server alone holds `HUDDLEMIND_READ_TOKEN`, which can read
`GET /v1/dashboard` but cannot upload events. The bridge upload token cannot use
that read route. Both are scoped to the receiver's configured owner/allowlist.
The browser never receives either API credential.

A one-time setup key in a URL fragment lets the owner set a 14–128 character
password. The fragment is removed from browser history after loading and is not
sent in the URL to Nginx. Setup expires according to `HUDDLEMIND_SETUP_EXPIRES`
(Unix milliseconds), and exclusive account-file creation prevents a second
enrollment. Do not share the setup link. No self-service password reset or
multi-user registration exists yet.

The named `web-auth` volume stores a salted scrypt password hash. Signed session
cookies are Secure, HttpOnly, SameSite=Strict, scoped to `/app`, and expire in
12 hours. Sign-out clears the browser cookie. Rotate the session secret to revoke
all issued sessions. Mutation requests must match `HUDDLEMIND_WEB_ORIGIN`.
Nginx rate-limits sign-in, with an additional process-wide application limiter.

## Deployment

Use all three compose files for receiver/web operations:

```sh
docker compose --env-file deploy/.env -f deploy/compose.yaml -f deploy/compose.nginx.yaml -f deploy/compose.web.yaml up -d --build receiver web
```

Web listens only on `127.0.0.1:8766`; Nginx forwards `/app` paths without stripping
the prefix. API and sample preview routes remain separate. Keep `.env` private;
back up the web-auth volume alongside deployment secrets for account recovery.
Receiver SQLite backups include snapshots/health, but not web passwords or secrets.

The latest snapshot is chosen by event capture time, not arrival time. An older
queued event arriving late cannot replace newer captured data. The UI explicitly
labels empty, unreachable, and stale states; missing recruiting data is not zero.

## Verification

- `npm test`: password/setup/session, roster, schedule outcomes, and recruit filtering/sorting tests.
- `npm run build`: production build and TypeScript checks.
- `node tests/http-smoke.mjs`: starts an isolated production web server and tests
  unauthenticated redirects, origin checks, setup replay, wrong/correct login,
  secure cookie flags, populated/empty/missing snapshot sections, receiver-unavailable
  display, protected Schedule/Recruiting routes, and logout.
- Python suite: read/upload credential separation, owner/dynasty scoping,
  latest-capture selection, and empty snapshots.

Architecture uses Next.js [basePath](https://nextjs.org/docs/app/api-reference/config/next-config-js/basePath)
for `/app` and server-side route handlers for sign-in.
