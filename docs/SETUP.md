# Production Setup

This guide deploys the application with Docker Compose and HTTPS at `https://fantasytato.mooo.com`.

## 1. Server prerequisites

Use a server connected to the internet with Docker Engine and Docker Compose installed. Before starting the containers:

1. Point the DNS `A` record for `fantasytato.mooo.com` to the server's public IPv4 address. Remove any stale `AAAA` record unless the server also has a publicly reachable IPv6 address.
2. Allow inbound TCP ports `80` and `443` in the host and cloud firewalls. Caddy uses port `80` to complete Let's Encrypt validation and redirects requests for the hostname to HTTPS.
3. Ensure no other service is using ports `80` or `443`.

The configured hostname is in the repository-root `Caddyfile`. Update it there before deployment if the production hostname changes.

## 2. Configure secrets

Create the `secrets/` directory with these files:

```text
secrets/
|- db.env
|- mongo.env
`- pgadmin.env
```

Use strong, unique passwords and do not commit these files. Example values:

`secrets/db.env`:

```dotenv
DB_NAME=main_db
DB_HOST=db
DB_USER=postgres
DB_PASSWORD=replace-with-a-strong-password
DATABASE_URL=postgresql://postgres:replace-with-a-strong-password@db:5432/main_db
POSTGRES_PASSWORD=replace-with-a-strong-password
POSTGRES_DB=main_db
JWT_SECRET_KEY=replace-with-a-long-random-secret
```

Generate a JWT secret with:

```bash
openssl rand -hex 32
```

`secrets/mongo.env`:

```dotenv
MONGO_INITDB_ROOT_USERNAME=mongoadmin
MONGO_INITDB_ROOT_PASSWORD=replace-with-a-strong-password
MONGO_INITDB_DATABASE=fantasy_mongo_db
```

`secrets/pgadmin.env`:

```dotenv
PGADMIN_DEFAULT_EMAIL=admin@example.com
PGADMIN_DEFAULT_PASSWORD=replace-with-a-strong-password
```

## 3. Start the application

From the repository root, build and start the services:

```bash
docker compose up -d --build
```

Caddy automatically obtains and renews the Let's Encrypt certificate. Confirm that certificate provisioning succeeds:

```bash
docker compose logs -f caddy
```

Once the certificate is issued, access the application at:

```text
https://fantasytato.mooo.com
```

The server's changing public IP can also be used directly over HTTP:

```text
http://<server-public-ip>
```

This IP fallback is not encrypted. Do not use it for normal access because passwords and authentication tokens can be intercepted; use the HTTPS hostname instead.

## 4. Database setup

PGAdmin is available at `http://<server-public-ip>:5050`. Log in with the credentials in `secrets/pgadmin.env`, then register the Postgres server using:

- Hostname: `db`
- Port: `5432`
- Maintenance database: `main_db`
- Username: `postgres`
- Password: the `POSTGRES_PASSWORD` from `secrets/db.env`

Load the schema from `resources/database_schema`:

```bash
docker exec pgadmin mkdir -p /var/lib/pgadmin/storage/admin_example.com/
docker cp resources/database_schema pgadmin:/var/lib/pgadmin/storage/admin_example.com/
```

In PGAdmin, right-click the database and choose **Restore**. Select the copied file, enable `pre-data` and `post-data` under Data Options, and enable `Clean before restore` and `Include IF EXISTS clause` under Query Options.

Install the required Postgres extension:

```bash
docker exec -it postgres_db psql -U postgres -d main_db -c 'CREATE EXTENSION IF NOT EXISTS unaccent;'
```

## 5. Create the initial user and league

Open `https://fantasytato.mooo.com` and create a user and league through the application.

## 6. Import footballer and fixture data

Populate a new database with the initial footballer, fixture, and team-crest data:

```bash
docker exec backend_app python scripts/insert_fixtures.py
docker exec backend_app python scripts/insert_team_crests.py
docker exec backend_app python scripts/insert_footballers.py
```

New leagues created afterward include the footballers by default.

## Security note

The current Compose file also publishes PostgreSQL on port `5432`, MongoDB on port `27017`, and PGAdmin on port `5050`. Restrict these ports in the server or cloud firewall to trusted administrator IP addresses; they do not need to be publicly reachable for the application or Caddy to work.
