# Quick start Guide

This guide explains how to set up everything to use the app. The prerequisite to this giude is being in possesion of a machine connected to the internet with Docker installed.

## 1. Environment setup

There are several environmental variables needed to make the app work. These are stores in the `📁secrets` folder:
```
secrets/
├── db.env
├── mongo.env
└── pgadmin.env
```

Here you can find sample files:
  * `db.env`:
  ```
  DB_NAME=main_db
  DB_HOST=db
  DB_USER=postgres
  DB_PASSWORD=123!
  DATABASE_URL=postgresql://postgres:123!@db:5432/main_db # be consistent
  POSTGRES_PASSWORD=123!
  POSTGRES_DB=main_db # consistent with DB_NAME
  ```
  * `mongo.env`:
  ```
  MONGO_INITDB_ROOT_USERNAME=mongoadmin
  MONGO_INITDB_ROOT_PASSWORD=123!
  MONGO_INITDB_DATABASE=fantasy_mongo_db
  ```
  * `pgadmin.env`:
  ```
  PGADMIN_DEFAULT_EMAIL=admin@admin.com
  PGADMIN_DEFAULT_PASSWORD=admin123
  ```

## 2. Contaniner setp

The app is comprised of 5 Docker containers:
  1. `backend_app`: runs the game logic.
  2. `frontend_app`: visualises the game and interacts with the user.
  3. `postgres_db`: hosts part of the game's data in the form of an SQL database.
  4. `mongo_db`: hosts the rest of the game's data in the form of a no-SQL database.
  5. `pgadmin`: enables interaction with the Postgres database.

In order to run these containers (and thus the app), you can execute the following command in the project's root directory:
```
docker compose -f 'docker-compose.yml' up -d --build
```

## 3. Database setup

  1. Log into the PGAdmin console via http://localhost:5050, using the credentials specified in `secrets/pgadmin.env`.
  2. Register a server with the envirnonmental variables (as per the example):
  - hostname: db
  - port: 5432
  - maintenance database: main_db
  - username: postgres
  - password: 123!
  3. Load the database schema provided in the `resources/database_schema` via the following command (change the variables accordingly):
  ```
  chmod 777 resources/database_schema
  docker exec pgadmin mkdir /var/lib/pgadmin/storage/admin_admin.com/
  docker cp resources/database_schema pgadmin:/var/lib/pgadmin/storage/admin_admin.com/
  ```
  4. Restore the database. Right click on the databse in PGAdmin ➡️ restore. Choose the file you just copied to the container. Check `pre-data` and `post-data` in Data Options, and `Clean before restore` and `Include IF EXISTS clause` in Query Options.
  5. Install `unaccent` extension:
  ```
  docker exec -it postgres_db psql -U postgres -d main_db -c 'CREATE EXTENSION IF NOT EXISTS unaccent;'
  ```

## 4. Set up JWT security token

Set up a strong JWT secret key. You do not need to remeber it.
```
docker exec -it backend_app bash
export JWT_SECRET_KEY=any_string
exit
```

## 5. Create a default user and league

Go to http://localhost:5173 and create a user and a league, following the on-screen instructions.

## 6. Download footballer and fixture data

When the containers are created for the first time we need to populate the database with both footballer and games data. Run the following commands:
```
docker exec backend_app python scripts/insert_fixtures.py
docker exec backend_app python scripts/insert_team_crests.py
docker exec backend_app python scripts/insert_footballers.py
```
From this point onwards, any new league you create will contain the footballers by default.