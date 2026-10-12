-- Airline Reservation & Flight Operations DBMS : SQLite edition (runs with zero installs)
PRAGMA foreign_keys = ON;

CREATE TABLE airport (
  airport_code TEXT PRIMARY KEY CHECK (length(airport_code)=3),
  name TEXT NOT NULL, city TEXT NOT NULL, country TEXT NOT NULL);

CREATE TABLE aircraft (
  aircraft_id INTEGER PRIMARY KEY AUTOINCREMENT,
  model TEXT NOT NULL,
  total_seats INTEGER NOT NULL CHECK (total_seats > 0),
  status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE','MAINTENANCE','RETIRED')));

CREATE TABLE seat (
  seat_id INTEGER PRIMARY KEY AUTOINCREMENT,
  aircraft_id INTEGER NOT NULL REFERENCES aircraft(aircraft_id),
  seat_no TEXT NOT NULL,
  class TEXT NOT NULL CHECK (class IN ('ECO','BUS','FIRST')),
  UNIQUE (aircraft_id, seat_no));

CREATE TABLE flight (
  flight_id INTEGER PRIMARY KEY AUTOINCREMENT,
  flight_no TEXT NOT NULL,
  origin_code TEXT NOT NULL REFERENCES airport(airport_code),
  dest_code TEXT NOT NULL REFERENCES airport(airport_code),
  aircraft_id INTEGER NOT NULL REFERENCES aircraft(aircraft_id),
  dep_time TEXT NOT NULL, arr_time TEXT NOT NULL,
  base_fare REAL NOT NULL CHECK (base_fare >= 0),
  status TEXT NOT NULL DEFAULT 'SCHEDULED' CHECK (status IN ('SCHEDULED','DELAYED','DEPARTED','ARRIVED','CANCELLED')),
  CHECK (arr_time > dep_time), CHECK (origin_code <> dest_code));

CREATE TABLE passenger (
  passenger_id INTEGER PRIMARY KEY AUTOINCREMENT,
  full_name TEXT NOT NULL,
  email TEXT NOT NULL UNIQUE,
  phone TEXT NOT NULL,
  passport_no TEXT NOT NULL UNIQUE,
  dob TEXT NOT NULL);

CREATE TABLE booking (
  booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
  passenger_id INTEGER NOT NULL REFERENCES passenger(passenger_id),
  flight_id INTEGER NOT NULL REFERENCES flight(flight_id),
  seat_id INTEGER NOT NULL REFERENCES seat(seat_id),
  booking_date TEXT NOT NULL DEFAULT (datetime('now')),
  status TEXT NOT NULL DEFAULT 'HOLD' CHECK (status IN ('HOLD','CONFIRMED','CANCELLED')),
  verification TEXT NOT NULL DEFAULT 'PENDING' CHECK (verification IN ('PENDING','VERIFIED','REJECTED')),
  fare REAL NOT NULL CHECK (fare >= 0));

CREATE TABLE payment (
  payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
  booking_id INTEGER NOT NULL REFERENCES booking(booking_id),
  amount REAL NOT NULL CHECK (amount > 0),
  method TEXT NOT NULL CHECK (method IN ('CARD','UPI','NETBANKING','CASH')),
  status TEXT NOT NULL CHECK (status IN ('PAID','FAILED','REFUNDED')),
  paid_at TEXT NOT NULL DEFAULT (datetime('now')));

CREATE TABLE crew (
  crew_id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('PILOT','CABIN')),
  license_no TEXT NOT NULL UNIQUE);

CREATE TABLE flight_crew (
  flight_id INTEGER NOT NULL REFERENCES flight(flight_id),
  crew_id INTEGER NOT NULL REFERENCES crew(crew_id),
  assigned_role TEXT NOT NULL,
  PRIMARY KEY (flight_id, crew_id));

-- extension tables (ER entities Baggage, Check_In, Flight_Manifest)
CREATE TABLE baggage (
  baggage_id INTEGER PRIMARY KEY AUTOINCREMENT,
  booking_id INTEGER NOT NULL REFERENCES booking(booking_id),
  tag_no TEXT NOT NULL UNIQUE,
  weight_kg REAL NOT NULL CHECK (weight_kg > 0),
  fees REAL NOT NULL DEFAULT 0);

CREATE TABLE check_in (
  checkin_id INTEGER PRIMARY KEY AUTOINCREMENT,
  booking_id INTEGER NOT NULL UNIQUE REFERENCES booking(booking_id),
  checkin_time TEXT NOT NULL DEFAULT (datetime('now')),
  gate_no TEXT,
  status TEXT NOT NULL DEFAULT 'CHECKED_IN' CHECK (status IN ('CHECKED_IN','BOARDED','NO_SHOW')));

CREATE TABLE flight_manifest (
  manifest_id INTEGER PRIMARY KEY AUTOINCREMENT,
  flight_id INTEGER NOT NULL UNIQUE REFERENCES flight(flight_id),
  manifest_date TEXT NOT NULL,
  total_passengers INTEGER NOT NULL,
  remarks TEXT);

CREATE INDEX idx_booking_flight ON booking(flight_id, seat_id);
CREATE INDEX idx_flight_route ON flight(origin_code, dest_code, dep_time);

-- ================= TRIGGERS =================
CREATE TRIGGER trg_flight_overlap BEFORE INSERT ON flight
BEGIN
  SELECT RAISE(ABORT,'Aircraft schedule overlap')
  WHERE EXISTS (SELECT 1 FROM flight WHERE aircraft_id=NEW.aircraft_id AND status<>'CANCELLED'
                AND NEW.dep_time < arr_time AND NEW.arr_time > dep_time);
END;
CREATE TRIGGER trg_flight_overlap_upd BEFORE UPDATE OF aircraft_id, dep_time, arr_time ON flight
BEGIN
  SELECT RAISE(ABORT,'Aircraft schedule overlap')
  WHERE EXISTS (SELECT 1 FROM flight WHERE aircraft_id=NEW.aircraft_id AND flight_id<>NEW.flight_id
                AND status<>'CANCELLED' AND NEW.dep_time < arr_time AND NEW.arr_time > dep_time);
END;

CREATE TRIGGER trg_seat_belongs BEFORE INSERT ON booking
BEGIN
  SELECT RAISE(ABORT,'Seat does not belong to the flight aircraft')
  WHERE (SELECT aircraft_id FROM seat WHERE seat_id=NEW.seat_id)
     IS NOT (SELECT aircraft_id FROM flight WHERE flight_id=NEW.flight_id);
END;
CREATE TRIGGER trg_seat_lock BEFORE INSERT ON booking
BEGIN
  SELECT RAISE(ABORT,'Seat already locked')
  WHERE NEW.status<>'CANCELLED' AND EXISTS (SELECT 1 FROM booking WHERE flight_id=NEW.flight_id
        AND seat_id=NEW.seat_id AND status<>'CANCELLED');
END;
CREATE TRIGGER trg_seat_lock_upd BEFORE UPDATE OF seat_id, status ON booking
BEGIN
  SELECT RAISE(ABORT,'Seat already locked')
  WHERE NEW.status<>'CANCELLED' AND EXISTS (SELECT 1 FROM booking WHERE flight_id=NEW.flight_id
        AND seat_id=NEW.seat_id AND status<>'CANCELLED' AND booking_id<>NEW.booking_id);
END;
CREATE TRIGGER trg_seat_belongs_upd BEFORE UPDATE OF seat_id ON booking
BEGIN
  SELECT RAISE(ABORT,'Seat does not belong to the flight aircraft')
  WHERE (SELECT aircraft_id FROM seat WHERE seat_id=NEW.seat_id)
     IS NOT (SELECT aircraft_id FROM flight WHERE flight_id=NEW.flight_id);
END;

CREATE TRIGGER trg_payment_check BEFORE INSERT ON payment
BEGIN
  SELECT RAISE(ABORT,'Booking is cancelled')
  WHERE (SELECT status FROM booking WHERE booking_id=NEW.booking_id)='CANCELLED';
  SELECT RAISE(ABORT,'Payment below fare')
  WHERE NEW.status='PAID' AND NEW.amount < (SELECT fare FROM booking WHERE booking_id=NEW.booking_id);
END;
CREATE TRIGGER trg_payment_confirm AFTER INSERT ON payment
WHEN NEW.status='PAID'
BEGIN
  UPDATE booking SET status='CONFIRMED' WHERE booking_id=NEW.booking_id AND status='HOLD';
END;

CREATE TRIGGER trg_checkin_confirmed BEFORE INSERT ON check_in
BEGIN
  SELECT RAISE(ABORT,'Booking is not confirmed')
  WHERE (SELECT status FROM booking WHERE booking_id=NEW.booking_id)<>'CONFIRMED';
END;

-- ================= VIEWS =================
CREATE VIEW v_flight_schedule AS
SELECT f.flight_id, f.flight_no, o.city AS origin, d.city AS destination,
       f.dep_time, f.arr_time, a.model, f.status
FROM flight f
JOIN airport o ON f.origin_code=o.airport_code
JOIN airport d ON f.dest_code=d.airport_code
JOIN aircraft a USING (aircraft_id);

CREATE VIEW v_passenger_itinerary AS
SELECT b.booking_id, p.full_name, f.flight_no, s.seat_no, s.class, f.dep_time, b.status, b.verification
FROM booking b JOIN passenger p USING (passenger_id) JOIN flight f USING (flight_id) JOIN seat s USING (seat_id);

CREATE VIEW v_seat_availability AS
SELECT f.flight_id, s.seat_id, s.seat_no, s.class,
       CASE WHEN b.booking_id IS NULL THEN 'AVAILABLE' ELSE 'LOCKED' END AS state
FROM flight f JOIN seat s USING (aircraft_id)
LEFT JOIN booking b ON b.seat_id=s.seat_id AND b.flight_id=f.flight_id AND b.status<>'CANCELLED';

CREATE VIEW v_revenue_summary AS
SELECT f.flight_id, f.flight_no,
       COALESCE((SELECT SUM(y.amount) FROM payment y JOIN booking bb USING (booking_id)
                 WHERE bb.flight_id=f.flight_id AND y.status='PAID'),0) AS revenue,
       (SELECT COUNT(*) FROM booking b WHERE b.flight_id=f.flight_id AND b.status<>'CANCELLED') AS bookings,
       ROUND((SELECT COUNT(*) FROM booking b WHERE b.flight_id=f.flight_id AND b.status<>'CANCELLED')*100.0/a.total_seats,1) AS load_pct
FROM flight f JOIN aircraft a USING (aircraft_id);

CREATE VIEW v_crew_roster AS
SELECT f.flight_no, c.name, c.role, fc.assigned_role
FROM flight_crew fc JOIN crew c USING (crew_id) JOIN flight f USING (flight_id);
