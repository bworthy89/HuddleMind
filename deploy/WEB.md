# Private web headquarters: first functional slice

`/app` runs Next.js with TypeScript. `/preview/` remains the public sample design.
This release provides single-owner sign-in and a live read-only Overview with
snapshot freshness, next game, record, roster/recruiting counts, and bridge status.
The full roster/schedule/recruiting screens and multi-dynasty selector are pending.

## Authentication

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

- `npm test`: password/setup/session and schedule summary tests.
- `npm run build`: production build and TypeScript checks.
- `node tests/http-smoke.mjs`: starts an isolated production web server and tests
  unauthenticated redirects, origin checks, setup replay, wrong/correct login,
  secure cookie flags, receiver-unavailable display, and logout.
- Python suite: read/upload credential separation, owner/dynasty scoping,
  latest-capture selection, and empty snapshots.

Architecture uses Next.js [basePath](https://nextjs.org/docs/app/api-reference/config/next-config-js/basePath)
for `/app` and server-side route handlers for sign-in.
