"""10-point test execution matrix. Runs on a fresh in-memory database, so live data is never touched."""
from api import connect, build_database, handle, rows

def run_matrix():
    c = connect(':memory:'); build_database(c)
    H = lambda m, p, b=None, q=None: handle(c, m, p, q or {}, b)
    out = []
    def record(n, name, action, expected, status, payload, ok, note=''):
        out.append(dict(n=n, test=name, action=action, expected=expected, http=status,
                        actual=(payload.get('error') if isinstance(payload, dict) and 'error' in payload else note), passed=bool(ok)))
    new_p = dict(full_name='Test Traveller', email='t@mail.com', phone='9000000000', passport_no='T1234567', dob='1999-01-01')
    s, p = H('POST', '/api/passengers', new_p); pid = p.get('passenger_id')
    record(1, 'Register passenger', 'Valid name, email, passport', '201; row created', s, p, s == 201 and pid, 'passenger_id=%s' % pid)
    s, p = H('POST', '/api/passengers', dict(new_p, email='other@mail.com'))
    n = c.execute('SELECT COUNT(*) FROM passenger').fetchone()[0]
    record(2, 'Duplicate passport', 'Re-insert the same passport', '409; no new row', s, p, s == 409 and n == 5, 'rows=%d' % n)
    s, p = H('POST', '/api/bookings', dict(passenger_id=pid, flight_id=101, seat_id=2)); bid = p.get('booking_id')
    record(3, 'Valid booking', 'Free seat 1B on flight 101', '201; status HOLD', s, p, s == 201 and p.get('status') == 'HOLD', 'booking_id=%s fare=%s' % (bid, p.get('fare')))
    s, p = H('POST', '/api/bookings', dict(passenger_id=1, flight_id=101, seat_id=2))
    record(4, 'Seat lock', 'Book the same seat again', '409 Seat already locked', s, p, s == 409 and p.get('error') == 'Seat already locked')
    s, p = H('POST', '/api/flights', dict(flight_no='ZZ1', origin_code='HYD', dest_code='BOM', aircraft_id=1, dep_time='2026-11-10 07:00', arr_time='2026-11-10 09:00', base_fare=1000))
    record(5, 'Aircraft overlap', 'Flight overlapping 101 on aircraft 1', 'Rejected by trigger', s, p, s == 409 and 'overlap' in p.get('error', ''))
    H('POST', '/api/bookings/%s/verify' % bid, dict(result='VERIFIED'))
    s, p = H('POST', '/api/payments', dict(booking_id=bid, amount=1000, method='UPI'))
    k = c.execute('SELECT COUNT(*) FROM payment WHERE booking_id=?', (bid,)).fetchone()[0]
    record(6, 'Underpayment', 'Amount 1000 below fare 21000', '422; no payment row', s, p, s == 422 and k == 0, 'payment rows=%d' % k)
    s, p = H('POST', '/api/payments', dict(booking_id=bid, amount=21000, method='CARD'))
    st = c.execute('SELECT status FROM booking WHERE booking_id=?', (bid,)).fetchone()[0]
    record(7, 'Valid payment', 'Amount equals fare', 'Payment saved; booking CONFIRMED', s, p, s == 201 and st == 'CONFIRMED', 'booking=%s' % st)
    s, p = H('DELETE', '/api/bookings/%s' % bid)
    seat = c.execute("SELECT state FROM v_seat_availability WHERE flight_id=101 AND seat_id=2").fetchone()[0]
    rf = c.execute("SELECT status FROM payment WHERE booking_id=?", (bid,)).fetchone()[0]
    record(8, 'Cancel booking', 'DELETE /bookings/{id}', 'CANCELLED; seat available; payment refunded', s, p, s == 200 and seat == 'AVAILABLE' and rf == 'REFUNDED', 'seat=%s payment=%s' % (seat, rf))
    s, p = H('DELETE', '/api/passengers/1')
    n = c.execute('SELECT COUNT(*) FROM passenger WHERE passenger_id=1').fetchone()[0]
    record(9, 'Referential integrity', 'Delete passenger who has bookings', '409; passenger kept', s, p, s == 409 and n == 1, 'passenger kept=%d' % n)
    before = c.execute('SELECT COUNT(*) FROM passenger').fetchone()[0]
    s, p = H('GET', '/api/flights', q={'from': "' OR 1=1 --"})
    s2, p2 = H('GET', '/api/passengers', q={'q': "x' OR '1'='1"})
    after = c.execute('SELECT COUNT(*) FROM passenger').fetchone()[0]
    record(10, 'SQL injection', "' OR 1=1 -- in search boxes", 'Treated as text; 0 rows', s, {}, s == 200 and p == [] and p2 == [] and before == after, 'flights=%d passengers=%d tables intact' % (len(p), len(p2)))
    return out

if __name__ == '__main__':
    r = run_matrix()
    for t in r: print('%2d  %-22s %-5s HTTP %s  %s' % (t['n'], t['test'], 'PASS' if t['passed'] else 'FAIL', t['http'], t['actual']))
    print('\n%d / %d passed' % (sum(t['passed'] for t in r), len(r)))
