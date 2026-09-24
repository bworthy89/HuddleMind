# Hostinger VPS deployment preparation

Target selected by the owner: the second VPS, `srv1391279.hstgr.cloud`.
Existing stopped website containers must be preserved. These files are prepared;
they have not been deployed. The production HTTP adapter passes local tests,
including actual Waitress requests. Docker image build, Compose startup, Linux
volume permissions, external TLS, and restart persistence still require validation.

## Before deployment

1. Inspect listening ports and non-Docker services over authorized SSH. Do not
   replace any service already using ports 80/443; adapt its proxy instead.
2. Choose an API hostname and verify its DNS points to the selected VPS.
3. Confirm a usable backup. The Hostinger API reported a September 23 backup
   during the initial inspection; refresh this before deployment.
4. Build and validate the image. The deployment uses `waitress==3.0.2`, a
   non-root runtime user, and a named SQLite volume. The receiver has no public
   host port. Caddy publishes 80/443. This is a single-owner, single-replica setup.
5. Copy `.env.example` to a private `.env` and configure a newly generated token,
   owner ID, authorized dynasty UUIDs (space separated), and hostname. Do not
   reuse the token printed in the local-learning conversation. Keep `.env` private.

## Deployment commands (after server checks and configuration)

The selected VPS was inspected over SSH: Nginx already serves port 80, a Newt
tunnel is running with host networking, and UFW permits 22/80/443. Preserve these
services. On this server, use both `-f deploy/compose.yaml` and
`-f deploy/compose.nginx.yaml` for all Compose commands. This disables the Caddy
service by profile and binds the receiver to `127.0.0.1:8765`. Install
`deploy/nginx.conf` as a separate site after checking `nginx -t`. Provision TLS
for `huddlemind-api.worthymedia.tech` using Certbot's Nginx integration. Deployment
and certificate issuance require the owner's final approval; neither has run.

Run from a checked-out, reviewed release of the repository:

```sh
docker compose --env-file deploy/.env -f deploy/compose.yaml build
docker compose --env-file deploy/.env -f deploy/compose.yaml up -d
docker compose --env-file deploy/.env -f deploy/compose.yaml ps
```

The build context excludes local saves, databases, credentials, and test data.
The API implements the existing version-1 sender contract using the existing
validator and transactional store. Waitress limits request size and concurrency;
Caddy handles HTTPS. Its certificate state and the database persist in named
volumes. Neither the database nor the receiver port is published to the host.

Keep one receiver instance while using SQLite. Deployment updates must retain
the `huddlemind` project name and volumes. Never use `down --volumes` on stored
observations. Set up scheduled SQLite-consistent backups and test recovery before
treating hosted history as durable production storage. VPS snapshots alone are
not proof that an application-level restore has been tested.

Validate authentication, a synthetic delivery and identical retry over HTTPS,
receiver restart persistence, and failure responses before sending real history.
The bridge outbox is currently tied to one destination: the user's observation
was already delivered locally. Do not clear delivery markers to switch hosts;
plan destination migration or queue a new observation for the hosted test.

## Local verification

```powershell
python -m pip install -r deploy/requirements.txt
python -m unittest bridge.test_hosted_receiver -v
```

Without the optional deployment dependency, the Waitress integration test skips.
The full suite with it installed passed 200 tests. Hosted deployment is pending
hostname selection and server access checks.
