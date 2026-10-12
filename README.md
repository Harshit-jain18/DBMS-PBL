# Airline Reservation and Flight Operations DBMS: working prototype

A complete, runnable 3-tier prototype of the database designed in the project report.
Python 3.9+ is the only requirement. There is nothing to install.

## Run it
    cd app
    python server.py            # then open http://localhost:8000
    python tests_matrix.py      # the 10-point test matrix in the terminal

The database file (`app/airline.db`) is created and seeded on first start.
"Reset demo data" in the sidebar restores the sample data.

## What is in the box
| Tier | Files | What it does |
|------|-------|--------------|
| Presentation | `app/static/index.html` | Departure board, guided booking workflow, bookings desk, tables and views browser, 14 queries plus read-only SQL console, rules and errors demo, test runner |
| Application | `app/api.py`, `app/server.py` | REST API, validation, business rules, transactions, error mapping. Standard library only |
| Data | `sql/sqlite_schema.sql`, `sql/seed.sql` | 12 tables, 8 triggers, 5 views, constraints, indexes |
| MySQL edition | `sql/mysql_schema.sql` | The same design in MySQL 8 syntax with the 14 queries (not executed in the build environment) |
| Tests | `app/tests_matrix.py` | Ten tests on a fresh in-memory database |

## Report components and where they live
- Normalised 3NF schema, data dictionary: `sql/*_schema.sql`
- Triggers: overlap (`trg_flight_overlap`), seat/bed lock (`trg_seat_lock`), payment check (`trg_payment_check`), auto-confirm (`trg_payment_confirm`), plus seat-ownership and check-in rules
- 14 queries and 5 views: Queries page, `app/api.py` (`QUERIES`, `VIEWS`)
- CRUD workflow Intake, Booking, Verification, Seat, Billing: "Book a trip" page and the API
- Defensive error handling: four layers (browser, API validation, transactions, database). See "Rules and errors"
- 10-point test matrix: "Test matrix" page

## REST API
GET /api/summary, /api/flights?from=&to=&date=, /api/flights/{id}/seats, /api/bookings, /api/passengers, /api/views/{name}, /api/queries/{Qn}, /api/triggers, /api/tables/{name}
POST /api/passengers, /api/flights, /api/bookings, /api/bookings/{id}/verify, /api/payments, /api/checkin, /api/baggage, /api/flights/{id}/manifest, /api/sql (SELECT only), /api/tests/run
PUT /api/bookings/{id}/seat, /api/passengers/{id}   DELETE /api/bookings/{id} (cancel and refund), /api/passengers/{id}

## Differences from the report
- Runs on SQLite so it works with no setup. Triggers use `RAISE(ABORT, ...)` instead of `SIGNAL`, and ENUM columns are TEXT with CHECK constraints.
- `booking.verification` (PENDING, VERIFIED, REJECTED) was added to support the verification stage. Payment is refused until a booking is VERIFIED.
- Fares are computed on the server: base fare x 1 (ECO), 3 (BUS), 5 (FIRST). Baggage over 20 kg costs 500 per extra kg.
- Cancelling a booking refunds its payments (status REFUNDED) and frees the seat.
