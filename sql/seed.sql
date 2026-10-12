INSERT INTO airport VALUES
 ('HYD','Rajiv Gandhi International','Hyderabad','India'),
 ('DEL','Indira Gandhi International','Delhi','India'),
 ('BOM','Chhatrapati Shivaji Maharaj International','Mumbai','India');
INSERT INTO aircraft VALUES (1,'Airbus A320',6,'ACTIVE'),(2,'Boeing 737-800',6,'ACTIVE');
INSERT INTO seat (seat_id,aircraft_id,seat_no,class) VALUES
 (1,1,'1A','BUS'),(2,1,'1B','BUS'),(3,1,'2A','ECO'),(4,1,'2B','ECO'),(5,1,'2C','ECO'),(6,1,'2D','ECO'),
 (7,2,'1A','BUS'),(8,2,'1B','BUS'),(9,2,'2A','ECO'),(10,2,'2B','ECO'),(11,2,'2C','ECO'),(12,2,'2D','ECO');
INSERT INTO flight VALUES
 (101,'AI201','HYD','DEL',1,'2026-11-10 06:00','2026-11-10 08:30',7000,'SCHEDULED'),
 (102,'AI202','DEL','HYD',1,'2026-11-10 10:00','2026-11-10 12:30',7200,'SCHEDULED'),
 (103,'6E301','HYD','BOM',2,'2026-11-10 07:00','2026-11-10 08:45',4500,'SCHEDULED'),
 (104,'AI205','HYD','DEL',2,'2026-11-11 06:00','2026-11-11 08:30',5000,'SCHEDULED');
INSERT INTO passenger VALUES
 (1,'Aarav Mehta','aarav@mail.com','9876500001','P1234567','1998-04-12'),
 (2,'Sneha Rao','sneha@mail.com','9876500002','P2345678','1995-09-30'),
 (3,'Rohan Gupta','rohan@mail.com','9876500003','P3456789','2000-01-18'),
 (4,'Isha Nair','isha@mail.com','9876500004','P4567890','1992-06-05');
INSERT INTO booking (booking_id,passenger_id,flight_id,seat_id,booking_date,status,verification,fare) VALUES
 (1,1,101,1,'2026-10-01 10:00','CONFIRMED','VERIFIED',21000),
 (2,2,101,3,'2026-10-02 11:00','CONFIRMED','VERIFIED',7000),
 (3,3,103,9,'2026-10-03 12:00','HOLD','PENDING',4500),
 (4,1,104,8,'2026-10-05 09:00','CONFIRMED','VERIFIED',15000);
INSERT INTO payment VALUES
 (1,1,21000,'CARD','PAID','2026-10-01 10:05'),
 (2,2,7000,'UPI','PAID','2026-10-02 11:03'),
 (3,4,15000,'CARD','PAID','2026-10-05 09:02');
INSERT INTO crew VALUES (1,'Capt. Vikram Singh','PILOT','LIC-1001'),(2,'Anita Das','CABIN','LIC-2001'),(3,'Capt. Meera Iyer','PILOT','LIC-1002');
INSERT INTO flight_crew VALUES (101,1,'CAPTAIN'),(101,2,'PURSER'),(103,3,'CAPTAIN');
