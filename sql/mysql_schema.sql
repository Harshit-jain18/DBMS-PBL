-- Airline Reservation & Flight Operations DBMS : MySQL 8 edition (same design as the project report)
-- Run:  mysql -u root -p < mysql_schema.sql        (NOT executed in the build sandbox: no MySQL server available there)
DROP DATABASE IF EXISTS airline_db;
CREATE DATABASE airline_db CHARACTER SET utf8mb4;
USE airline_db;

CREATE TABLE airport (airport_code CHAR(3) PRIMARY KEY, name VARCHAR(100) NOT NULL, city VARCHAR(60) NOT NULL, country VARCHAR(60) NOT NULL);
CREATE TABLE aircraft (aircraft_id INT AUTO_INCREMENT PRIMARY KEY, model VARCHAR(50) NOT NULL,
  total_seats INT NOT NULL CHECK (total_seats > 0), status ENUM('ACTIVE','MAINTENANCE','RETIRED') NOT NULL DEFAULT 'ACTIVE');
CREATE TABLE seat (seat_id INT AUTO_INCREMENT PRIMARY KEY, aircraft_id INT NOT NULL, seat_no VARCHAR(4) NOT NULL,
  class ENUM('ECO','BUS','FIRST') NOT NULL, UNIQUE (aircraft_id, seat_no), FOREIGN KEY (aircraft_id) REFERENCES aircraft(aircraft_id));
CREATE TABLE flight (flight_id INT AUTO_INCREMENT PRIMARY KEY, flight_no VARCHAR(8) NOT NULL, origin_code CHAR(3) NOT NULL, dest_code CHAR(3) NOT NULL,
  aircraft_id INT NOT NULL, dep_time DATETIME NOT NULL, arr_time DATETIME NOT NULL, base_fare DECIMAL(10,2) NOT NULL CHECK (base_fare >= 0),
  status ENUM('SCHEDULED','DELAYED','DEPARTED','ARRIVED','CANCELLED') NOT NULL DEFAULT 'SCHEDULED',
  CHECK (arr_time > dep_time), CHECK (origin_code <> dest_code),
  FOREIGN KEY (origin_code) REFERENCES airport(airport_code), FOREIGN KEY (dest_code) REFERENCES airport(airport_code),
  FOREIGN KEY (aircraft_id) REFERENCES aircraft(aircraft_id));
CREATE TABLE passenger (passenger_id INT AUTO_INCREMENT PRIMARY KEY, full_name VARCHAR(100) NOT NULL, email VARCHAR(100) NOT NULL UNIQUE,
  phone VARCHAR(15) NOT NULL, passport_no VARCHAR(15) NOT NULL UNIQUE, dob DATE NOT NULL);
CREATE TABLE booking (booking_id INT AUTO_INCREMENT PRIMARY KEY, passenger_id INT NOT NULL, flight_id INT NOT NULL, seat_id INT NOT NULL,
  booking_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, status ENUM('HOLD','CONFIRMED','CANCELLED') NOT NULL DEFAULT 'HOLD',
  verification ENUM('PENDING','VERIFIED','REJECTED') NOT NULL DEFAULT 'PENDING', fare DECIMAL(10,2) NOT NULL CHECK (fare >= 0),
  FOREIGN KEY (passenger_id) REFERENCES passenger(passenger_id), FOREIGN KEY (flight_id) REFERENCES flight(flight_id), FOREIGN KEY (seat_id) REFERENCES seat(seat_id));
CREATE TABLE payment (payment_id INT AUTO_INCREMENT PRIMARY KEY, booking_id INT NOT NULL, amount DECIMAL(10,2) NOT NULL CHECK (amount > 0),
  method ENUM('CARD','UPI','NETBANKING','CASH') NOT NULL, status ENUM('PAID','FAILED','REFUNDED') NOT NULL,
  paid_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (booking_id) REFERENCES booking(booking_id));
CREATE TABLE crew (crew_id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100) NOT NULL, role ENUM('PILOT','CABIN') NOT NULL, license_no VARCHAR(20) NOT NULL UNIQUE);
CREATE TABLE flight_crew (flight_id INT NOT NULL, crew_id INT NOT NULL, assigned_role VARCHAR(20) NOT NULL, PRIMARY KEY (flight_id, crew_id),
  FOREIGN KEY (flight_id) REFERENCES flight(flight_id), FOREIGN KEY (crew_id) REFERENCES crew(crew_id));
CREATE TABLE baggage (baggage_id INT AUTO_INCREMENT PRIMARY KEY, booking_id INT NOT NULL, tag_no VARCHAR(12) NOT NULL UNIQUE,
  weight_kg DECIMAL(5,2) NOT NULL CHECK (weight_kg > 0), fees DECIMAL(8,2) NOT NULL DEFAULT 0, FOREIGN KEY (booking_id) REFERENCES booking(booking_id));
CREATE TABLE check_in (checkin_id INT AUTO_INCREMENT PRIMARY KEY, booking_id INT NOT NULL UNIQUE, checkin_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  gate_no VARCHAR(5), status ENUM('CHECKED_IN','BOARDED','NO_SHOW') NOT NULL DEFAULT 'CHECKED_IN', FOREIGN KEY (booking_id) REFERENCES booking(booking_id));
CREATE TABLE flight_manifest (manifest_id INT AUTO_INCREMENT PRIMARY KEY, flight_id INT NOT NULL UNIQUE, manifest_date DATE NOT NULL,
  total_passengers INT NOT NULL, remarks VARCHAR(200), FOREIGN KEY (flight_id) REFERENCES flight(flight_id));
CREATE INDEX idx_booking_flight ON booking(flight_id, seat_id);
CREATE INDEX idx_flight_route ON flight(origin_code, dest_code, dep_time);

-- ---------- sample data ----------
INSERT INTO airport VALUES ('HYD','Rajiv Gandhi International','Hyderabad','India'),('DEL','Indira Gandhi International','Delhi','India'),
 ('BOM','Chhatrapati Shivaji Maharaj International','Mumbai','India');
INSERT INTO aircraft VALUES (1,'Airbus A320',6,'ACTIVE'),(2,'Boeing 737-800',6,'ACTIVE');
INSERT INTO seat (seat_id,aircraft_id,seat_no,class) VALUES (1,1,'1A','BUS'),(2,1,'1B','BUS'),(3,1,'2A','ECO'),(4,1,'2B','ECO'),(5,1,'2C','ECO'),(6,1,'2D','ECO'),
 (7,2,'1A','BUS'),(8,2,'1B','BUS'),(9,2,'2A','ECO'),(10,2,'2B','ECO'),(11,2,'2C','ECO'),(12,2,'2D','ECO');
INSERT INTO flight VALUES (101,'AI201','HYD','DEL',1,'2026-11-10 06:00','2026-11-10 08:30',7000,'SCHEDULED'),
 (102,'AI202','DEL','HYD',1,'2026-11-10 10:00','2026-11-10 12:30',7200,'SCHEDULED'),(103,'6E301','HYD','BOM',2,'2026-11-10 07:00','2026-11-10 08:45',4500,'SCHEDULED'),
 (104,'AI205','HYD','DEL',2,'2026-11-11 06:00','2026-11-11 08:30',5000,'SCHEDULED');
INSERT INTO passenger VALUES (1,'Aarav Mehta','aarav@mail.com','9876500001','P1234567','1998-04-12'),(2,'Sneha Rao','sneha@mail.com','9876500002','P2345678','1995-09-30'),
 (3,'Rohan Gupta','rohan@mail.com','9876500003','P3456789','2000-01-18'),(4,'Isha Nair','isha@mail.com','9876500004','P4567890','1992-06-05');
INSERT INTO booking (booking_id,passenger_id,flight_id,seat_id,booking_date,status,verification,fare) VALUES
 (1,1,101,1,'2026-10-01 10:00','CONFIRMED','VERIFIED',21000),(2,2,101,3,'2026-10-02 11:00','CONFIRMED','VERIFIED',7000),
 (3,3,103,9,'2026-10-03 12:00','HOLD','PENDING',4500),(4,1,104,8,'2026-10-05 09:00','CONFIRMED','VERIFIED',15000);
INSERT INTO payment VALUES (1,1,21000,'CARD','PAID','2026-10-01 10:05'),(2,2,7000,'UPI','PAID','2026-10-02 11:03'),(3,4,15000,'CARD','PAID','2026-10-05 09:02');
INSERT INTO crew VALUES (1,'Capt. Vikram Singh','PILOT','LIC-1001'),(2,'Anita Das','CABIN','LIC-2001'),(3,'Capt. Meera Iyer','PILOT','LIC-1002');
INSERT INTO flight_crew VALUES (101,1,'CAPTAIN'),(101,2,'PURSER'),(103,3,'CAPTAIN');

-- ---------- triggers ----------
DELIMITER $$
CREATE TRIGGER trg_flight_overlap BEFORE INSERT ON flight FOR EACH ROW
BEGIN
  IF EXISTS (SELECT 1 FROM flight WHERE aircraft_id=NEW.aircraft_id AND status<>'CANCELLED' AND NEW.dep_time < arr_time AND NEW.arr_time > dep_time) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Aircraft schedule overlap';
  END IF;
END$$
CREATE TRIGGER trg_seat_belongs BEFORE INSERT ON booking FOR EACH ROW
BEGIN
  IF (SELECT aircraft_id FROM seat WHERE seat_id=NEW.seat_id) <> (SELECT aircraft_id FROM flight WHERE flight_id=NEW.flight_id) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Seat does not belong to the flight aircraft';
  END IF;
END$$
CREATE TRIGGER trg_seat_lock BEFORE INSERT ON booking FOR EACH ROW
BEGIN
  IF NEW.status<>'CANCELLED' AND EXISTS (SELECT 1 FROM booking WHERE flight_id=NEW.flight_id AND seat_id=NEW.seat_id AND status<>'CANCELLED') THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Seat already locked';
  END IF;
END$$
CREATE TRIGGER trg_seat_lock_upd BEFORE UPDATE ON booking FOR EACH ROW
BEGIN
  IF NEW.status<>'CANCELLED' AND EXISTS (SELECT 1 FROM booking WHERE flight_id=NEW.flight_id AND seat_id=NEW.seat_id
        AND status<>'CANCELLED' AND booking_id<>NEW.booking_id) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Seat already locked';
  END IF;
END$$
CREATE TRIGGER trg_payment_check BEFORE INSERT ON payment FOR EACH ROW
BEGIN
  DECLARE v_fare DECIMAL(10,2); DECLARE v_status VARCHAR(10);
  SELECT fare, status INTO v_fare, v_status FROM booking WHERE booking_id=NEW.booking_id;
  IF v_status='CANCELLED' THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Booking is cancelled'; END IF;
  IF NEW.status='PAID' AND NEW.amount < v_fare THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Payment below fare'; END IF;
END$$
CREATE TRIGGER trg_payment_confirm AFTER INSERT ON payment FOR EACH ROW
BEGIN
  IF NEW.status='PAID' THEN UPDATE booking SET status='CONFIRMED' WHERE booking_id=NEW.booking_id AND status='HOLD'; END IF;
END$$
CREATE TRIGGER trg_checkin_confirmed BEFORE INSERT ON check_in FOR EACH ROW
BEGIN
  IF (SELECT status FROM booking WHERE booking_id=NEW.booking_id) <> 'CONFIRMED' THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Booking is not confirmed';
  END IF;
END$$
DELIMITER ;

-- ---------- views ----------
CREATE VIEW v_flight_schedule AS SELECT f.flight_id, f.flight_no, o.city AS origin, d.city AS destination, f.dep_time, f.arr_time, a.model, f.status
 FROM flight f JOIN airport o ON f.origin_code=o.airport_code JOIN airport d ON f.dest_code=d.airport_code JOIN aircraft a USING (aircraft_id);
CREATE VIEW v_passenger_itinerary AS SELECT b.booking_id, p.full_name, f.flight_no, s.seat_no, s.class, f.dep_time, b.status, b.verification
 FROM booking b JOIN passenger p USING (passenger_id) JOIN flight f USING (flight_id) JOIN seat s USING (seat_id);
CREATE VIEW v_seat_availability AS SELECT f.flight_id, s.seat_id, s.seat_no, s.class, IF(b.booking_id IS NULL,'AVAILABLE','LOCKED') AS state
 FROM flight f JOIN seat s USING (aircraft_id) LEFT JOIN booking b ON b.seat_id=s.seat_id AND b.flight_id=f.flight_id AND b.status<>'CANCELLED';
CREATE VIEW v_revenue_summary AS SELECT f.flight_id, f.flight_no,
  COALESCE((SELECT SUM(y.amount) FROM payment y JOIN booking bb USING (booking_id) WHERE bb.flight_id=f.flight_id AND y.status='PAID'),0) AS revenue,
  (SELECT COUNT(*) FROM booking b WHERE b.flight_id=f.flight_id AND b.status<>'CANCELLED') AS bookings,
  ROUND((SELECT COUNT(*) FROM booking b WHERE b.flight_id=f.flight_id AND b.status<>'CANCELLED')*100/a.total_seats,1) AS load_pct
 FROM flight f JOIN aircraft a USING (aircraft_id);
CREATE VIEW v_crew_roster AS SELECT f.flight_no, c.name, c.role, fc.assigned_role FROM flight_crew fc JOIN crew c USING (crew_id) JOIN flight f USING (flight_id);

-- ---------- the 14 demonstration queries (MySQL syntax; identical logic to app/api.py) ----------
-- Q1
SELECT p.full_name, f.flight_no, f.dep_time, b.status FROM booking b JOIN passenger p USING (passenger_id) JOIN flight f USING (flight_id);
-- Q2
SELECT f.flight_no, o.city AS origin, d.city AS destination FROM flight f JOIN airport o ON f.origin_code=o.airport_code JOIN airport d ON f.dest_code=d.airport_code;
-- Q3
SELECT f.flight_no, c.name, c.role FROM flight_crew fc JOIN crew c USING (crew_id) JOIN flight f USING (flight_id) ORDER BY f.flight_no;
-- Q4
SELECT b.booking_id, p.full_name FROM booking b JOIN passenger p USING (passenger_id) LEFT JOIN payment y USING (booking_id) WHERE y.payment_id IS NULL;
-- Q5
SELECT s.seat_no, s.class, b.booking_id FROM flight f JOIN seat s ON s.aircraft_id=f.aircraft_id LEFT JOIN booking b ON b.seat_id=s.seat_id AND b.flight_id=f.flight_id AND b.status<>'CANCELLED' WHERE f.flight_id=101;
-- Q6
SELECT flight_no, base_fare FROM flight WHERE base_fare > (SELECT AVG(base_fare) FROM flight);
-- Q7
SELECT full_name FROM passenger WHERE passenger_id NOT IN (SELECT passenger_id FROM booking);
-- Q8
SELECT flight_no FROM flight WHERE flight_id = (SELECT flight_id FROM booking GROUP BY flight_id ORDER BY COUNT(*) DESC LIMIT 1);
-- Q9
SELECT full_name FROM passenger p WHERE EXISTS (SELECT 1 FROM booking b JOIN payment y USING (booking_id) WHERE b.passenger_id=p.passenger_id AND y.amount>20000);
-- Q10
SELECT b.flight_id, SUM(y.amount) AS revenue FROM booking b JOIN payment y USING (booking_id) WHERE y.status='PAID' GROUP BY b.flight_id;
-- Q11
SELECT f.flight_no, ROUND(COUNT(b.booking_id)*100/a.total_seats,1) AS load_pct FROM flight f JOIN aircraft a USING (aircraft_id) LEFT JOIN booking b ON b.flight_id=f.flight_id AND b.status<>'CANCELLED' GROUP BY f.flight_id, f.flight_no, a.total_seats;
-- Q12
SELECT s.class, COUNT(*) AS bookings FROM booking b JOIN seat s USING (seat_id) GROUP BY s.class;
-- Q13
SELECT origin_code, dest_code, COUNT(*) AS trips FROM flight GROUP BY origin_code, dest_code HAVING COUNT(*) >= 2;
-- Q14
SELECT DATE_FORMAT(paid_at,'%Y-%m') AS month, SUM(amount) AS revenue FROM payment WHERE status='PAID' GROUP BY month ORDER BY month;
