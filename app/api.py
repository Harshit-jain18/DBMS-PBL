"""Application tier: validation, business rules, transactions, error mapping.
Pure functions: handle(conn, method, path, query, body) -> (http_status, json_payload)."""
import os, re, sqlite3, datetime, logging
from contextlib import contextmanager

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA = os.path.join(ROOT, 'sql', 'sqlite_schema.sql')
SEED = os.path.join(ROOT, 'sql', 'seed.sql')
log = logging.getLogger('airline')

class ApiError(Exception):
    def __init__(self, status, message):
        super().__init__(message); self.status = status; self.message = message

# ---------- database helpers ----------
def connect(path):
    conn = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON')
    return conn

def build_database(conn, with_seed=True):
    conn.executescript(open(SCHEMA).read())
    if with_seed:
        conn.executescript(open(SEED).read())

@contextmanager
def tx(conn):
    conn.execute('BEGIN IMMEDIATE')
    try:
        yield
        conn.execute('COMMIT')
    except BaseException:
        conn.execute('ROLLBACK'); raise

def rows(conn, sql, args=()):
    return [dict(r) for r in conn.execute(sql, args).fetchall()]

def one(conn, sql, args=()):
    r = conn.execute(sql, args).fetchone()
    return dict(r) if r else None

def map_db_error(e, ctx=''):
    m = str(e)
    if 'Seat already locked' in m: return ApiError(409, 'Seat already locked')
    if 'Aircraft schedule overlap' in m: return ApiError(409, 'Aircraft schedule overlap')
    if 'Payment below fare' in m: return ApiError(422, 'Payment below fare')
    if 'Seat does not belong' in m: return ApiError(422, 'Seat does not belong to the flight aircraft')
    if 'Booking is cancelled' in m: return ApiError(409, 'Booking is cancelled')
    if 'not confirmed' in m: return ApiError(409, 'Booking is not confirmed')
    if 'UNIQUE constraint failed: passenger' in m: return ApiError(409, 'Passenger already registered')
    if 'UNIQUE constraint failed: check_in' in m: return ApiError(409, 'Passenger already checked in')
    if 'FOREIGN KEY' in m: return ApiError(409, ctx or 'Operation blocked: related records exist or a reference is invalid')
    if 'CHECK constraint' in m: return ApiError(422, 'A value breaks a data rule (check constraint)')
    if 'UNIQUE constraint' in m: return ApiError(409, 'Duplicate value')
    log.exception('unexpected database error: %s', m)
    return ApiError(500, 'Internal error. The request was rolled back.')

# ---------- validation ----------
def need(body, *fields):
    if not isinstance(body, dict): raise ApiError(400, 'JSON object required')
    miss = [f for f in fields if body.get(f) in (None, '')]
    if miss: raise ApiError(400, 'Missing fields: %s' % miss)

def as_int(v, name):
    try:
        if isinstance(v, bool): raise ValueError
        return int(v)
    except (TypeError, ValueError): raise ApiError(400, '%s must be an integer' % name)

def as_num(v, name):
    try:
        x = float(v)
        if x != x or x in (float('inf'), float('-inf')): raise ValueError
        return x
    except (TypeError, ValueError): raise ApiError(400, '%s must be a number' % name)

def as_date(v, name, fmt='%Y-%m-%d'):
    try: return datetime.datetime.strptime(str(v), fmt)
    except ValueError: raise ApiError(400, '%s must look like %s' % (name, fmt.replace('%Y','YYYY').replace('%m','MM').replace('%d','DD').replace('%H','HH').replace('%M','mm')))

def text(v, name, maxlen=100):
    s = str(v).strip()
    if not s or len(s) > maxlen: raise ApiError(400, '%s must be 1-%d characters' % (name, maxlen))
    return s

# ---------- passengers (Intake) ----------
def passenger_create(conn, b):
    need(b, 'full_name', 'email', 'phone', 'passport_no', 'dob')
    name = text(b['full_name'], 'full_name')
    email = text(b['email'], 'email').lower()
    if not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', email): raise ApiError(400, 'email is not valid')
    phone = str(b['phone']).strip()
    if not re.fullmatch(r'\+?\d{7,15}', phone): raise ApiError(400, 'phone must be 7-15 digits')
    passport = str(b['passport_no']).strip().upper()
    if not re.fullmatch(r'[A-Z0-9]{6,15}', passport): raise ApiError(400, 'passport_no must be 6-15 letters or digits')
    dob = as_date(b['dob'], 'dob')
    if dob > datetime.datetime.now(): raise ApiError(400, 'dob cannot be in the future')
    try:
        with tx(conn):
            cur = conn.execute('INSERT INTO passenger(full_name,email,phone,passport_no,dob) VALUES(?,?,?,?,?)',
                               (name, email, phone, passport, dob.strftime('%Y-%m-%d')))
    except sqlite3.Error as e: raise map_db_error(e)
    return 201, {'passenger_id': cur.lastrowid}

def passenger_update(conn, pid, b):
    if not one(conn, 'SELECT 1 x FROM passenger WHERE passenger_id=?', (pid,)): raise ApiError(404, 'Passenger not found')
    sets, args = [], []
    for f in ('full_name', 'email', 'phone'):
        if f in b:
            v = text(b[f], f)
            if f == 'email' and not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', v): raise ApiError(400, 'email is not valid')
            if f == 'phone' and not re.fullmatch(r'\+?\d{7,15}', v): raise ApiError(400, 'phone must be 7-15 digits')
            sets.append('%s=?' % f); args.append(v.lower() if f == 'email' else v)
    if not sets: raise ApiError(400, 'Nothing to update (allowed: full_name, email, phone)')
    try:
        with tx(conn): conn.execute('UPDATE passenger SET %s WHERE passenger_id=?' % ','.join(sets), args + [pid])
    except sqlite3.Error as e: raise map_db_error(e)
    return 200, {'updated': pid}

def passenger_delete(conn, pid):
    if not one(conn, 'SELECT 1 x FROM passenger WHERE passenger_id=?', (pid,)): raise ApiError(404, 'Passenger not found')
    try:
        with tx(conn): conn.execute('DELETE FROM passenger WHERE passenger_id=?', (pid,))
    except sqlite3.Error as e: raise map_db_error(e, 'Cannot delete: bookings exist')
    return 200, {'deleted': pid}

# ---------- flights ----------
FLIGHT_SQL = """SELECT f.flight_id, f.flight_no, f.origin_code, o.city AS origin_city, f.dest_code, d.city AS dest_city,
  f.dep_time, f.arr_time, f.base_fare, f.status, a.model, a.total_seats,
  a.total_seats-(SELECT COUNT(*) FROM booking b WHERE b.flight_id=f.flight_id AND b.status<>'CANCELLED') AS open_seats
  FROM flight f JOIN airport o ON o.airport_code=f.origin_code JOIN airport d ON d.airport_code=f.dest_code
  JOIN aircraft a USING(aircraft_id)"""

def flights_search(conn, q):
    where, args = [], []
    for key, col_code, col_city in (('from', 'f.origin_code', 'o.city'), ('to', 'f.dest_code', 'd.city')):
        v = (q.get(key) or '').strip()
        if v:
            if len(v) > 50: raise ApiError(400, '%s is too long' % key)
            where.append('(%s=? OR lower(%s)=lower(?))' % (col_code, col_city)); args += [v.upper(), v]
    d = (q.get('date') or '').strip()
    if d:
        as_date(d, 'date'); where.append('date(f.dep_time)=?'); args.append(d)
    sql = FLIGHT_SQL + (' WHERE ' + ' AND '.join(where) if where else '') + ' ORDER BY f.dep_time'
    return 200, rows(conn, sql, args)

def flight_create(conn, b):
    need(b, 'flight_no', 'origin_code', 'dest_code', 'aircraft_id', 'dep_time', 'arr_time', 'base_fare')
    dep = as_date(b['dep_time'], 'dep_time', '%Y-%m-%d %H:%M'); arr = as_date(b['arr_time'], 'arr_time', '%Y-%m-%d %H:%M')
    if arr <= dep: raise ApiError(422, 'arr_time must be after dep_time')
    fare = as_num(b['base_fare'], 'base_fare')
    if fare < 0: raise ApiError(422, 'base_fare cannot be negative')
    o, d = str(b['origin_code']).upper(), str(b['dest_code']).upper()
    if o == d: raise ApiError(422, 'origin and destination must differ')
    try:
        with tx(conn):
            cur = conn.execute('INSERT INTO flight(flight_no,origin_code,dest_code,aircraft_id,dep_time,arr_time,base_fare) VALUES(?,?,?,?,?,?,?)',
                (text(b['flight_no'], 'flight_no', 8), o, d, as_int(b['aircraft_id'], 'aircraft_id'),
                 dep.strftime('%Y-%m-%d %H:%M'), arr.strftime('%Y-%m-%d %H:%M'), fare))
    except sqlite3.Error as e: raise map_db_error(e, 'Unknown airport or aircraft')
    return 201, {'flight_id': cur.lastrowid}

def flight_seats(conn, fid):
    if not one(conn, 'SELECT 1 x FROM flight WHERE flight_id=?', (fid,)): raise ApiError(404, 'Flight not found')
    return 200, rows(conn, 'SELECT * FROM v_seat_availability WHERE flight_id=? ORDER BY seat_id', (fid,))

def manifest_generate(conn, fid):
    f = one(conn, 'SELECT * FROM flight WHERE flight_id=?', (fid,))
    if not f: raise ApiError(404, 'Flight not found')
    n = one(conn, "SELECT COUNT(*) n FROM booking WHERE flight_id=? AND status='CONFIRMED'", (fid,))['n']
    with tx(conn):
        conn.execute("""INSERT INTO flight_manifest(flight_id,manifest_date,total_passengers,remarks) VALUES(?,date('now'),?,?)
          ON CONFLICT(flight_id) DO UPDATE SET manifest_date=date('now'), total_passengers=excluded.total_passengers""",
          (fid, n, 'Generated from confirmed bookings'))
    return 200, one(conn, 'SELECT * FROM flight_manifest WHERE flight_id=?', (fid,))

# ---------- bookings (Booking, Verification, Seat, Billing) ----------
CLASS_MULT = {'ECO': 1, 'BUS': 3, 'FIRST': 5}

def booking_get(conn, bid):
    b = one(conn, 'SELECT * FROM booking WHERE booking_id=?', (bid,))
    if not b: raise ApiError(404, 'Booking not found')
    return b

def booking_create(conn, b):
    need(b, 'passenger_id', 'flight_id', 'seat_id')
    pid, fid, sid = (as_int(b[k], k) for k in ('passenger_id', 'flight_id', 'seat_id'))
    if not one(conn, 'SELECT 1 x FROM passenger WHERE passenger_id=?', (pid,)): raise ApiError(404, 'Passenger not found')
    f = one(conn, 'SELECT * FROM flight WHERE flight_id=?', (fid,))
    if not f: raise ApiError(404, 'Flight not found')
    if f['status'] not in ('SCHEDULED', 'DELAYED'): raise ApiError(409, 'Flight is not open for booking (%s)' % f['status'])
    s = one(conn, 'SELECT * FROM seat WHERE seat_id=?', (sid,))
    if not s: raise ApiError(404, 'Seat not found')
    fare = f['base_fare'] * CLASS_MULT[s['class']]       # fare is never taken from the client
    try:
        with tx(conn):
            cur = conn.execute("INSERT INTO booking(passenger_id,flight_id,seat_id,fare,status) VALUES(?,?,?,?, 'HOLD')", (pid, fid, sid, fare))
    except sqlite3.Error as e: raise map_db_error(e)
    return 201, {'booking_id': cur.lastrowid, 'status': 'HOLD', 'fare': fare, 'verification': 'PENDING'}

def booking_verify(conn, bid, b):
    need(b, 'result')
    bk = booking_get(conn, bid)
    if bk['status'] == 'CANCELLED': raise ApiError(409, 'Booking is cancelled')
    res = str(b['result']).upper()
    if res not in ('VERIFIED', 'REJECTED'): raise ApiError(400, "result must be 'VERIFIED' or 'REJECTED'")
    with tx(conn): conn.execute('UPDATE booking SET verification=? WHERE booking_id=?', (res, bid))
    return 200, {'booking_id': bid, 'verification': res}

def booking_seat(conn, bid, b):
    need(b, 'seat_id'); sid = as_int(b['seat_id'], 'seat_id')
    bk = booking_get(conn, bid)
    if bk['status'] == 'CANCELLED': raise ApiError(409, 'Booking is cancelled')
    new = one(conn, 'SELECT * FROM seat WHERE seat_id=?', (sid,))
    if not new: raise ApiError(404, 'Seat not found')
    old = one(conn, 'SELECT * FROM seat WHERE seat_id=?', (bk['seat_id'],))
    f = one(conn, 'SELECT base_fare FROM flight WHERE flight_id=?', (bk['flight_id'],))
    if new['class'] != old['class'] and bk['status'] == 'CONFIRMED':
        raise ApiError(409, 'Paid booking cannot change cabin class; cancel and rebook')
    fare = bk['fare'] if bk['status'] == 'CONFIRMED' else f['base_fare'] * CLASS_MULT[new['class']]
    try:
        with tx(conn): conn.execute('UPDATE booking SET seat_id=?, fare=? WHERE booking_id=?', (sid, fare, bid))
    except sqlite3.Error as e: raise map_db_error(e)
    return 200, {'booking_id': bid, 'seat_id': sid, 'fare': fare}

def booking_cancel(conn, bid):
    bk = booking_get(conn, bid)
    if bk['status'] == 'CANCELLED': raise ApiError(409, 'Booking already cancelled')
    fl = one(conn, 'SELECT status FROM flight WHERE flight_id=?', (bk['flight_id'],))
    if fl['status'] in ('DEPARTED', 'ARRIVED'): raise ApiError(409, 'Flight has already departed')
    with tx(conn):
        paid = one(conn, "SELECT COALESCE(SUM(amount),0) s FROM payment WHERE booking_id=? AND status='PAID'", (bid,))['s']
        conn.execute("UPDATE payment SET status='REFUNDED' WHERE booking_id=? AND status='PAID'", (bid,))
        conn.execute("UPDATE booking SET status='CANCELLED' WHERE booking_id=?", (bid,))
    return 200, {'booking_id': bid, 'status': 'CANCELLED', 'refund_amount': paid}

def bookings_list(conn, q):
    sql = """SELECT b.booking_id, p.full_name, p.passenger_id, f.flight_no, f.flight_id, s.seat_no, s.class, b.status, b.verification, b.fare,
      COALESCE((SELECT SUM(amount) FROM payment y WHERE y.booking_id=b.booking_id AND y.status='PAID'),0) AS paid,
      (SELECT status FROM check_in c WHERE c.booking_id=b.booking_id) AS checkin
      FROM booking b JOIN passenger p USING(passenger_id) JOIN flight f USING(flight_id) JOIN seat s USING(seat_id)"""
    args = []
    if q.get('passenger_id'): sql += ' WHERE b.passenger_id=?'; args.append(as_int(q['passenger_id'], 'passenger_id'))
    return 200, rows(conn, sql + ' ORDER BY b.booking_id DESC', args)

def payment_create(conn, b):
    need(b, 'booking_id', 'amount', 'method')
    bid = as_int(b['booking_id'], 'booking_id'); amt = as_num(b['amount'], 'amount')
    if amt <= 0: raise ApiError(422, 'amount must be greater than zero')
    method = str(b['method']).upper()
    if method not in ('CARD', 'UPI', 'NETBANKING', 'CASH'): raise ApiError(400, 'method must be CARD, UPI, NETBANKING or CASH')
    status = str(b.get('status', 'PAID')).upper()
    if status not in ('PAID', 'FAILED'): raise ApiError(400, "status must be 'PAID' or 'FAILED'")
    bk = booking_get(conn, bid)
    if bk['status'] == 'CONFIRMED': raise ApiError(409, 'Booking is already paid')
    if status == 'PAID' and bk['verification'] != 'VERIFIED': raise ApiError(409, 'Booking must be VERIFIED before payment')
    try:
        with tx(conn):
            cur = conn.execute('INSERT INTO payment(booking_id,amount,method,status) VALUES(?,?,?,?)', (bid, amt, method, status))
    except sqlite3.Error as e: raise map_db_error(e)
    return 201, {'payment_id': cur.lastrowid, 'booking_status': booking_get(conn, bid)['status']}

# ---------- operations extension ----------
def checkin_create(conn, b):
    need(b, 'booking_id'); bid = as_int(b['booking_id'], 'booking_id'); booking_get(conn, bid)
    gate = str(b.get('gate_no') or 'TBA')[:5]
    try:
        with tx(conn): cur = conn.execute('INSERT INTO check_in(booking_id,gate_no) VALUES(?,?)', (bid, gate))
    except sqlite3.Error as e: raise map_db_error(e)
    return 201, {'checkin_id': cur.lastrowid, 'gate_no': gate}

def baggage_create(conn, b):
    need(b, 'booking_id', 'weight_kg'); bid = as_int(b['booking_id'], 'booking_id'); w = as_num(b['weight_kg'], 'weight_kg')
    if not 0 < w <= 50: raise ApiError(422, 'weight_kg must be between 0 and 50')
    if booking_get(conn, bid)['status'] != 'CONFIRMED': raise ApiError(409, 'Booking is not confirmed')
    fee = max(0.0, w - 20) * 500
    try:
        with tx(conn):
            n = one(conn, 'SELECT COALESCE(MAX(baggage_id),0)+1 n FROM baggage')['n']
            tag = 'BG%06d' % n
            cur = conn.execute('INSERT INTO baggage(booking_id,tag_no,weight_kg,fees) VALUES(?,?,?,?)', (bid, tag, w, fee))
    except sqlite3.Error as e: raise map_db_error(e)
    return 201, {'baggage_id': cur.lastrowid, 'tag_no': tag, 'fees': fee}

# ---------- reporting ----------
VIEWS = ['v_flight_schedule', 'v_passenger_itinerary', 'v_seat_availability', 'v_revenue_summary', 'v_crew_roster']
QUERIES = [
 ('Q1','Join','Passenger itineraries (three-table join)',"SELECT p.full_name, f.flight_no, f.dep_time, b.status FROM booking b JOIN passenger p USING (passenger_id) JOIN flight f USING (flight_id)"),
 ('Q2','Join','Routes with city names (airport joined twice)',"SELECT f.flight_no, o.city AS origin, d.city AS destination FROM flight f JOIN airport o ON f.origin_code=o.airport_code JOIN airport d ON f.dest_code=d.airport_code"),
 ('Q3','Join','Crew roster per flight',"SELECT f.flight_no, c.name, c.role FROM flight_crew fc JOIN crew c USING (crew_id) JOIN flight f USING (flight_id) ORDER BY f.flight_no"),
 ('Q4','Join','Bookings with no payment (LEFT JOIN)',"SELECT b.booking_id, p.full_name FROM booking b JOIN passenger p USING (passenger_id) LEFT JOIN payment y USING (booking_id) WHERE y.payment_id IS NULL"),
 ('Q5','Join','Seat map of flight 101 with occupancy',"SELECT s.seat_no, s.class, b.booking_id FROM flight f JOIN seat s ON s.aircraft_id=f.aircraft_id LEFT JOIN booking b ON b.seat_id=s.seat_id AND b.flight_id=f.flight_id AND b.status<>'CANCELLED' WHERE f.flight_id=101"),
 ('Q6','Subquery','Flights priced above the average fare',"SELECT flight_no, base_fare FROM flight WHERE base_fare > (SELECT AVG(base_fare) FROM flight)"),
 ('Q7','Subquery','Passengers who never booked (NOT IN)',"SELECT full_name FROM passenger WHERE passenger_id NOT IN (SELECT passenger_id FROM booking)"),
 ('Q8','Subquery','Busiest flight by bookings',"SELECT flight_no FROM flight WHERE flight_id = (SELECT flight_id FROM booking GROUP BY flight_id ORDER BY COUNT(*) DESC LIMIT 1)"),
 ('Q9','Subquery','Passengers with a payment above 20,000 (EXISTS)',"SELECT full_name FROM passenger p WHERE EXISTS (SELECT 1 FROM booking b JOIN payment y USING (booking_id) WHERE b.passenger_id=p.passenger_id AND y.amount>20000)"),
 ('Q10','Aggregate','Revenue per flight',"SELECT b.flight_id, SUM(y.amount) AS revenue FROM booking b JOIN payment y USING (booking_id) WHERE y.status='PAID' GROUP BY b.flight_id"),
 ('Q11','Aggregate','Load factor (% seats sold)',"SELECT f.flight_no, ROUND(COUNT(b.booking_id)*100.0/a.total_seats,1) AS load_pct FROM flight f JOIN aircraft a USING (aircraft_id) LEFT JOIN booking b ON b.flight_id=f.flight_id AND b.status<>'CANCELLED' GROUP BY f.flight_id, f.flight_no, a.total_seats"),
 ('Q12','Aggregate','Bookings by cabin class',"SELECT s.class, COUNT(*) AS bookings FROM booking b JOIN seat s USING (seat_id) GROUP BY s.class"),
 ('Q13','Aggregate','Routes operated at least twice (HAVING)',"SELECT origin_code, dest_code, COUNT(*) AS trips FROM flight GROUP BY origin_code, dest_code HAVING COUNT(*) >= 2"),
 ('Q14','Aggregate','Monthly revenue trend',"SELECT strftime('%Y-%m', paid_at) AS month, SUM(amount) AS revenue FROM payment WHERE status='PAID' GROUP BY month ORDER BY month"),
]

def summary(conn):
    c = lambda t: one(conn, 'SELECT COUNT(*) n FROM %s' % t)['n']
    return 200, {'passengers': c('passenger'), 'flights': c('flight'), 'bookings': c('booking'),
      'confirmed': one(conn, "SELECT COUNT(*) n FROM booking WHERE status='CONFIRMED'")['n'],
      'revenue': one(conn, "SELECT COALESCE(SUM(amount),0) s FROM payment WHERE status='PAID'")['s']}

def sql_console(db_path, b):
    need(b, 'sql'); s = str(b['sql']).strip().rstrip(';').strip()
    if ';' in s or not re.match(r'(?is)^(select|with)\b', s): raise ApiError(400, 'Only a single SELECT statement is allowed')
    ro = sqlite3.connect('file:%s?mode=ro' % db_path, uri=True); ro.row_factory = sqlite3.Row
    try:
        ro.execute('PRAGMA query_only=ON')
        cur = ro.execute(s); data = [dict(r) for r in cur.fetchmany(500)]
        return 200, {'columns': [d[0] for d in cur.description or []], 'rows': data}
    except sqlite3.Error as e: raise ApiError(400, 'SQL error: %s' % e)
    finally: ro.close()

# ---------- router ----------
def _int(s): return int(s)

def handle(conn, method, path, q, body, db_path=None):
    try:
        m = method.upper(); p = path.rstrip('/') or '/'
        if m == 'GET':
            if p == '/api/summary': return summary(conn)
            if p == '/api/passengers':
                term = (q.get('q') or '').strip()
                if term: return 200, rows(conn, 'SELECT * FROM passenger WHERE passport_no=upper(?) OR lower(email)=lower(?) OR full_name LIKE ?', (term, term, '%' + term + '%'))
                return 200, rows(conn, 'SELECT * FROM passenger ORDER BY passenger_id')
            if p == '/api/flights': return flights_search(conn, q)
            r = re.fullmatch(r'/api/flights/(\d+)/seats', p)
            if r: return flight_seats(conn, _int(r[1]))
            if p == '/api/bookings': return bookings_list(conn, q)
            if p == '/api/views': return 200, VIEWS
            r = re.fullmatch(r'/api/views/(\w+)', p)
            if r:
                if r[1] not in VIEWS: raise ApiError(404, 'Unknown view')
                return 200, rows(conn, 'SELECT * FROM %s' % r[1])
            if p == '/api/queries': return 200, [dict(id=a, kind=k, title=t, sql=s) for a, k, t, s in QUERIES]
            r = re.fullmatch(r'/api/queries/(Q\d+)', p)
            if r:
                hit = [x for x in QUERIES if x[0] == r[1]]
                if not hit: raise ApiError(404, 'Unknown query')
                return 200, rows(conn, hit[0][3])
            if p == '/api/triggers': return 200, rows(conn, "SELECT name, tbl_name AS on_table, sql FROM sqlite_master WHERE type='trigger' ORDER BY name")
            if p == '/api/tables': return 200, rows(conn, "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
            r = re.fullmatch(r'/api/tables/(\w+)', p)
            if r:
                if not one(conn, "SELECT 1 x FROM sqlite_master WHERE type='table' AND name=?", (r[1],)): raise ApiError(404, 'Unknown table')
                return 200, rows(conn, 'SELECT * FROM %s LIMIT 200' % r[1])
        if m == 'POST':
            if p == '/api/passengers': return passenger_create(conn, body)
            if p == '/api/flights': return flight_create(conn, body)
            if p == '/api/bookings': return booking_create(conn, body)
            if p == '/api/payments': return payment_create(conn, body)
            if p == '/api/checkin': return checkin_create(conn, body)
            if p == '/api/baggage': return baggage_create(conn, body)
            if p == '/api/sql':
                if not db_path: raise ApiError(400, 'SQL console unavailable')
                return sql_console(db_path, body)
            r = re.fullmatch(r'/api/bookings/(\d+)/verify', p)
            if r: return booking_verify(conn, _int(r[1]), body)
            r = re.fullmatch(r'/api/flights/(\d+)/manifest', p)
            if r: return manifest_generate(conn, _int(r[1]))
        if m == 'PUT':
            r = re.fullmatch(r'/api/bookings/(\d+)/seat', p)
            if r: return booking_seat(conn, _int(r[1]), body)
            r = re.fullmatch(r'/api/passengers/(\d+)', p)
            if r: return passenger_update(conn, _int(r[1]), body)
        if m == 'DELETE':
            r = re.fullmatch(r'/api/bookings/(\d+)', p)
            if r: return booking_cancel(conn, _int(r[1]))
            r = re.fullmatch(r'/api/passengers/(\d+)', p)
            if r: return passenger_delete(conn, _int(r[1]))
        raise ApiError(404, 'No such endpoint: %s %s' % (m, p))
    except ApiError as e:
        return e.status, {'error': e.message}
    except sqlite3.Error as e:
        err = map_db_error(e); return err.status, {'error': err.message}
    except Exception:
        log.exception('unhandled error')
        return 500, {'error': 'Internal error. The request was rolled back.'}
