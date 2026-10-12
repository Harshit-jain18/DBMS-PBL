# Airline Reservation and Flight Operations DBMS: Working Prototype

A complete, runnable 3-tier prototype of the relational database designed in the project report. Includes an **interactive Streamlit Python dashboard**, the original standard-library REST API & HTML console, normalized 3NF schema, defensive integrity triggers, and automated test matrix.

Python 3.9+ is required.

---

## Quick Start: Run the Streamlit Dashboard

Install requirements:
```bash
pip install -r requirements.txt
```

Launch the Streamlit dashboard:
```bash
python -m streamlit run app.py
```
*(or `python -m streamlit run streamlit_app.py`)*

*On Windows, you can also simply double-click `run_dashboard.bat` (or `./run_dashboard.sh` on Linux/macOS).*

The dashboard will open automatically in your browser at `http://localhost:8501`.

---

## Run the Classic Server & Tests

You can also run the built-in zero-dependency HTTP server and test suite:

```bash
# 1. Classic HTML & REST API Console (standard library only)
cd app
python server.py            # opens http://localhost:8000

# 2. Terminal Test Matrix
python tests_matrix.py      # executes the 10-point test matrix in the terminal
```

The database file (`app/airline.db`) is automatically initialized and seeded on first run.  
Use the **"Reset demo data"** button in either interface to restore the initial sample dataset at any time.

---

## Streamlit Dashboard Features

The Streamlit app (`streamlit_app.py`) provides an operational console with 7 modules:

1. **🛫 Live Departures & Flights**:
   - Real-time KPI summary cards: Total Flights, Registered Passengers, Total Bookings, Confirmed Tickets, Total Revenue (₹).
   - Flight schedule board with dynamic filters for Origin, Destination, and Departure Date.
   - Schedule New Flight form protected by trigger-based schedule overlap validation (`trg_flight_overlap`).
   - Passenger Manifest Generator to generate and review confirmed passenger manifests for any flight.

2. **🎫 Book a Trip (5-Step Guided Lifecycle)**:
   - **Step 1 - Intake**: Register new passenger with validation or select an existing traveller.
   - **Step 2 - Flight & Seat**: Search flights, view visual seat maps with cabin class multipliers (Economy 1x, Business 3x, First 5x), and hold seats.
   - **Step 3 - Verification Desk**: Airline staff review identity and mark bookings `VERIFIED` or `REJECTED`.
   - **Step 4 - Seat Check**: Option to modify or retain seat allocation before payment.
   - **Step 5 - Billing & Confirmation**: Make payments with payment method support (`CARD`, `UPI`, `NETBANKING`, `CASH`). Triggers automatically reject underpayment and promote status to `CONFIRMED`.
   - **Post-Booking Operations**: Assign boarding gates (Check-in) and record baggage with automatic excess fee calculation (>20 kg @ ₹500/kg).

3. **📋 Bookings & Passenger Desk**:
   - Filter and inspect bookings by status (`ALL`, `HOLD`, `CONFIRMED`, `CANCELLED`).
   - Operational actions: Verify bookings, Check-in passengers, Tag baggage, and Cancel & Refund (frees seat immediately).
   - Passenger Directory: Search travellers, update contact numbers/emails, and test deletion with referential integrity protection.

4. **📊 Analytics & SQL Queries**:
   - Visual trend charts: Revenue by Flight, Load Factor (%) per flight, Cabin Class distribution, and Monthly Revenue trends.
   - The **14 Project Queries** (Joins, Subqueries, Aggregates) with SQL source code and live execution results.
   - Database Views browser (`v_flight_schedule`, `v_passenger_itinerary`, `v_seat_availability`, `v_revenue_summary`, `v_crew_roster`).

5. **🗄️ Database Explorer & SQL Console**:
   - Table Explorer: Inspect schema metadata and live records across all 12 tables.
   - Read-only SQL Sandbox: Interactive execution environment for custom `SELECT` / `WITH` statements with error handling.

6. **🛡️ DBMS Triggers & Integrity Rules**:
   - Interactive testing lab demonstrating the 4 defensive layers (UI validation, API checks, ACID transactions, and database triggers).
   - One-click trigger verification for: Aircraft Overlap, Double Booking / Seat Lock, Seat-Aircraft Mismatch, Underpayment, Payment Before Verification, Duplicate Passport (`UNIQUE`), Foreign Key deletion constraint, and SQL Injection resilience.
   - Trigger DDL Inspector displaying active SQLite triggers.

7. **🧪 10-Point Test Matrix**:
   - One-click runner executing all 10 test scenarios on a fresh in-memory SQLite database without modifying live data.

---

## What is in the Box

| Tier | Files | What it does |
|------|-------|--------------|
| **Streamlit Dashboard** | `streamlit_app.py`, `run_dashboard.bat`, `run_dashboard.sh`, `requirements.txt` | Complete interactive Python dashboard with analytics, visual seat maps, guided booking wizard, operations desk, SQL console, and rules lab |
| **Classic Presentation** | `app/static/index.html` | Departure board, guided booking workflow, bookings desk, tables and views browser, 14 queries plus read-only SQL console, rules and errors demo, test runner |
| **Application** | `app/api.py`, `app/server.py` | REST API, validation, business rules, transactions, error mapping. Standard library only |
| **Data** | `sql/sqlite_schema.sql`, `sql/seed.sql` | 12 tables, 8 triggers, 5 views, constraints, indexes |
| **MySQL Edition** | `sql/mysql_schema.sql` | The same design in MySQL 8 syntax with the 14 queries |
| **Tests** | `app/tests_matrix.py` | Ten automated tests run against a fresh in-memory database |

---

## Report Components and Where They Live

- **Normalised 3NF Schema & Data Dictionary**: `sql/sqlite_schema.sql`, `sql/mysql_schema.sql`
- **Triggers**: Overlap (`trg_flight_overlap`), seat lock (`trg_seat_lock`), payment check (`trg_payment_check`), auto-confirm (`trg_payment_confirm`), seat ownership (`trg_seat_belongs`), and check-in confirmation rules
- **14 Demonstration Queries & 5 Views**: Available in Analytics & SQL Queries tab, `app/api.py` (`QUERIES`, `VIEWS`)
- **5-Stage CRUD Workflow**: Intake ➔ Booking ➔ Verification ➔ Seat ➔ Billing in "Book a Trip" wizard and API
- **Defensive Error Handling**: 4 layers (browser UI, API validation, ACID transactions, database triggers). See "DBMS Triggers & Integrity Rules"
- **10-Point Test Matrix**: "10-Point Test Matrix" tab and `app/tests_matrix.py`

---

## REST API Reference

- `GET /api/summary`, `/api/flights?from=&to=&date=`, `/api/flights/{id}/seats`, `/api/bookings`, `/api/passengers`, `/api/views/{name}`, `/api/queries/{Qn}`, `/api/triggers`, `/api/tables/{name}`
- `POST /api/passengers`, `/api/flights`, `/api/bookings`, `/api/bookings/{id}/verify`, `/api/payments`, `/api/checkin`, `/api/baggage`, `/api/flights/{id}/manifest`, `/api/sql` (SELECT only), `/api/tests/run`
- `PUT /api/bookings/{id}/seat`, `/api/passengers/{id}`
- `DELETE /api/bookings/{id}` (cancel and refund), `/api/passengers/{id}`

---

## Schema Highlights & Business Rules

- **Zero-Setup SQLite Engine**: Runs locally with zero database daemon setup. Triggers use `RAISE(ABORT, ...)` and ENUM columns use `TEXT` with `CHECK` constraints.
- **Verification Stage**: `booking.verification` (`PENDING`, `VERIFIED`, `REJECTED`). Payments are rejected until a booking is `VERIFIED`.
- **Dynamic Cabin Class Pricing**: Base fare multiplied by 1x (Economy), 3x (Business), and 5x (First Class).
- **Excess Baggage Policy**: Bags up to 20 kg are free of additional baggage charge; excess weight is billed at ₹500/kg.
- **Cancellation & Automatic Refund**: Cancelling a booking marks payments as `REFUNDED` and releases the seat immediately.
