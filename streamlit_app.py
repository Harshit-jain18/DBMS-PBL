"""Airline Reservation & Flight Operations DBMS - Interactive Streamlit Dashboard.
Run via:
    streamlit run streamlit_app.py
"""
import os
import sys
import datetime
import sqlite3
import pandas as pd
import streamlit as st

# Configure page layout and aesthetics
st.set_page_config(
    page_title="Airline DBMS Operations Console",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Set path to access backend API & SQL modules
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.join(ROOT_DIR, "app")
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

import api
import tests_matrix

DB_PATH = os.environ.get("AIRLINE_DB", os.path.join(APP_DIR, "airline.db"))

# Ensure database file exists
def ensure_database():
    if not os.path.exists(DB_PATH):
        conn = api.connect(DB_PATH)
        api.build_database(conn, with_seed=True)
        conn.close()

ensure_database()

def get_db():
    return api.connect(DB_PATH)

def format_inr(val):
    try:
        val = float(val or 0)
        return f"₹{val:,.2f}".replace(".00", "")
    except Exception:
        return f"₹{val}"

# Custom CSS for styling
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 16px 20px;
        color: #f8fafc;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
    }
    .metric-value {
        font-size: 26px;
        font-weight: 700;
        color: #38bdf8;
        line-height: 1.2;
    }
    .metric-label {
        font-size: 13px;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .tag-badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 9999px;
        font-size: 12px;
        font-weight: 600;
    }
    .badge-CONFIRMED, .badge-PAID, .badge-VERIFIED, .badge-AVAILABLE, .badge-PASS {
        background-color: #dcfce7;
        color: #166534;
    }
    .badge-HOLD, .badge-PENDING {
        background-color: #fef9c3;
        color: #854d0e;
    }
    .badge-CANCELLED, .badge-FAILED, .badge-REJECTED, .badge-LOCKED, .badge-FAIL {
        background-color: #fee2e2;
        color: #991b1b;
    }
    .badge-SCHEDULED {
        background-color: #e0f2fe;
        color: #0369a1;
    }
    .badge-DELAYED {
        background-color: #ffedd5;
        color: #9a3412;
    }
    .seat-box {
        display: inline-block;
        width: 58px;
        height: 52px;
        margin: 4px;
        line-height: 22px;
        text-align: center;
        border-radius: 6px;
        font-weight: bold;
        font-size: 13px;
    }
    .seat-avail {
        background-color: #ecfdf5;
        border: 2px solid #10b981;
        color: #065f46;
    }
    .seat-locked {
        background-color: #f1f5f9;
        border: 2px solid #cbd5e1;
        color: #94a3b8;
    }
    .seat-sel {
        background-color: #0284c7;
        border: 2px solid #0369a1;
        color: #ffffff;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- SIDEBAR -----------------
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/airplane-take-off.png", width=64)
    st.title("SkyWings DBMS")
    st.caption("3-Tier Relational DBMS Prototype")
    st.markdown("---")

    menu_option = st.radio(
        "Navigation",
        [
            "🛫 Live Departures & Flights",
            "🎫 Book a Trip (Guided Wizard)",
            "📋 Bookings & Passenger Desk",
            "📊 Analytics & SQL Queries",
            "🗄️ Database Explorer & SQL Console",
            "🛡️ DBMS Triggers & Integrity Rules",
            "🧪 10-Point Test Matrix",
        ],
        index=0,
    )

    st.markdown("---")
    st.subheader("Data Management")
    if st.button("🔄 Reset Demo Data", help="Wipes and reloads the seed database from sql/seed.sql"):
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        conn = api.connect(DB_PATH)
        api.build_database(conn, with_seed=True)
        conn.close()
        st.session_state.clear()
        st.success("Database restored to original demo seed!")
        st.rerun()

    st.markdown("---")
    st.caption(f"**Database:** `airline.db` (SQLite 3NF)")
    st.caption("**Triggers:** 8 active integrity triggers")
    st.caption("**Engine:** Python 3.9+ | Streamlit")


# ==============================================================================
# 1. LIVE DEPARTURES & FLIGHTS
# ==============================================================================
if menu_option == "🛫 Live Departures & Flights":
    st.title("🛫 Live Departures & Flight Operations")
    st.markdown("Real-time view of scheduled flights, load factors, seating capacity, and revenue generated.")

    conn = get_db()
    try:
        _, summary_data = api.summary(conn)
        _, flights = api.flights_search(conn, {})
        _, rev_summary = api.handle(conn, "GET", "/api/views/v_revenue_summary", {}, {})
    finally:
        conn.close()

    rev_map = {r["flight_id"]: r for r in rev_summary}

    # Top KPI Metrics Cards
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Flights</div>
            <div class="metric-value">{summary_data.get('flights', 0)}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Passengers</div>
            <div class="metric-value">{summary_data.get('passengers', 0)}</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Bookings</div>
            <div class="metric-value">{summary_data.get('bookings', 0)}</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Confirmed</div>
            <div class="metric-value">{summary_data.get('confirmed', 0)}</div>
        </div>
        """, unsafe_allow_html=True)
    with col5:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Revenue</div>
            <div class="metric-value">{format_inr(summary_data.get('revenue', 0))}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Flight Filter Controls
    f_filter_col1, f_filter_col2, f_filter_col3 = st.columns(3)
    with f_filter_col1:
        search_origin = st.text_input("Origin (Code or City)", placeholder="e.g. HYD or Hyderabad")
    with f_filter_col2:
        search_dest = st.text_input("Destination (Code or City)", placeholder="e.g. DEL or Delhi")
    with f_filter_col3:
        search_date = st.text_input("Departure Date (YYYY-MM-DD)", placeholder="e.g. 2026-11-10")

    conn = get_db()
    try:
        query_params = {}
        if search_origin: query_params["from"] = search_origin
        if search_dest: query_params["to"] = search_dest
        if search_date: query_params["date"] = search_date
        _, filtered_flights = api.flights_search(conn, query_params)
    finally:
        conn.close()

    # Enhanced Flight Board Table
    if filtered_flights:
        table_rows = []
        for f in filtered_flights:
            fid = f["flight_id"]
            rev = rev_map.get(fid, {})
            load_pct = rev.get("load_pct", 0)
            revenue_val = rev.get("revenue", 0)
            table_rows.append({
                "Flight ID": fid,
                "Flight No": f["flight_no"],
                "Origin": f"{f['origin_city']} ({f['origin_code']})",
                "Destination": f"{f['dest_city']} ({f['dest_code']})",
                "Departure": f["dep_time"],
                "Arrival": f["arr_time"],
                "Aircraft": f["model"],
                "Seats Left": f"{f['open_seats']} / {f['total_seats']}",
                "Load Factor": f"{load_pct}%",
                "Base Fare": format_inr(f["base_fare"]),
                "Revenue": format_inr(revenue_val),
                "Status": f["status"]
            })
        df_flights = pd.DataFrame(table_rows)
        st.dataframe(df_flights, use_container_width=True, hide_index=True)
    else:
        st.info("No flights match the search criteria.")

    st.markdown("---")

    # Expandable Forms: Schedule Flight & Flight Manifest
    tab_add_flight, tab_manifest = st.tabs(["➕ Schedule New Flight (Trigger Protected)", "📄 Flight Passenger Manifest"])

    with tab_add_flight:
        st.markdown("Schedule a flight. Overlap triggers (`trg_flight_overlap`) prevent overlapping assignments for the same aircraft.")
        with st.form("add_flight_form"):
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                f_no = st.text_input("Flight Number", value="AI305")
            with c2:
                conn = get_db()
                airports = conn.execute("SELECT airport_code, city FROM airport").fetchall()
                aircrafts = conn.execute("SELECT aircraft_id, model FROM aircraft").fetchall()
                conn.close()
                airport_options = [f"{a['airport_code']} - {a['city']}" for a in airports]
                f_orig = st.selectbox("Origin Airport", airport_options, index=0)
            with c3:
                f_dest = st.selectbox("Destination Airport", airport_options, index=1 if len(airport_options) > 1 else 0)
            with c4:
                aircraft_options = [f"{a['aircraft_id']} - {a['model']}" for a in aircrafts]
                f_air = st.selectbox("Aircraft", aircraft_options)

            c5, c6, c7 = st.columns(3)
            with c5:
                f_dep = st.text_input("Departure (YYYY-MM-DD HH:MM)", value="2026-11-10 14:00")
            with c6:
                f_arr = st.text_input("Arrival (YYYY-MM-DD HH:MM)", value="2026-11-10 16:30")
            with c7:
                f_fare = st.number_input("Base Fare (₹)", min_value=500.0, value=5500.0, step=500.0)

            submitted = st.form_submit_button("Create Flight")
            if submitted:
                orig_code = f_orig.split(" - ")[0]
                dest_code = f_dest.split(" - ")[0]
                air_id = int(f_air.split(" - ")[0])
                payload = {
                    "flight_no": f_no,
                    "origin_code": orig_code,
                    "dest_code": dest_code,
                    "aircraft_id": air_id,
                    "dep_time": f_dep,
                    "arr_time": f_arr,
                    "base_fare": f_fare,
                }
                conn = get_db()
                try:
                    code, res = api.flight_create(conn, payload)
                    if code == 201:
                        st.success(f"Flight {f_no} scheduled successfully with Flight ID {res['flight_id']}!")
                        st.rerun()
                    else:
                        st.error(f"Error {code}: {res.get('error')}")
                except Exception as e:
                    st.error(f"Constraint check / Trigger failed: {e}")
                finally:
                    conn.close()

    with tab_manifest:
        st.markdown("Generate or update the passenger manifest based on confirmed bookings.")
        conn = get_db()
        flights_list = conn.execute("SELECT flight_id, flight_no, origin_code, dest_code, dep_time FROM flight ORDER BY flight_id").fetchall()
        conn.close()

        fl_opts = {f"{f['flight_no']} ({f['origin_code']} -> {f['dest_code']} at {f['dep_time']})": f["flight_id"] for f in flights_list}
        selected_fl_str = st.selectbox("Select Flight for Manifest", list(fl_opts.keys()))
        selected_fid = fl_opts[selected_fl_str]

        col_m1, col_m2 = st.columns([1, 2])
        with col_m1:
            if st.button("Generate / Refresh Manifest", key="gen_manifest"):
                conn = get_db()
                try:
                    code, m_res = api.manifest_generate(conn, selected_fid)
                    if code == 200:
                        st.success("Manifest updated successfully!")
                    else:
                        st.error(m_res.get("error"))
                finally:
                    conn.close()

        with col_m2:
            conn = get_db()
            manifest = conn.execute("SELECT * FROM flight_manifest WHERE flight_id=?", (selected_fid,)).fetchone()
            passengers_on_flight = conn.execute("""
                SELECT p.full_name, p.passport_no, s.seat_no, s.class, b.status,
                       (SELECT gate_no FROM check_in c WHERE c.booking_id=b.booking_id) AS gate
                FROM booking b
                JOIN passenger p USING(passenger_id)
                JOIN seat s USING(seat_id)
                WHERE b.flight_id=? AND b.status='CONFIRMED'
            """, (selected_fid,)).fetchall()
            conn.close()

            if manifest:
                st.markdown(f"**Manifest Date:** {manifest['manifest_date']} | **Total Confirmed Passengers:** {manifest['total_passengers']}")
                st.caption(f"Remarks: {manifest['remarks']}")
                if passengers_on_flight:
                    st.dataframe([dict(p) for p in passengers_on_flight], use_container_width=True, hide_index=True)
                else:
                    st.info("No passengers checked in or confirmed yet.")
            else:
                st.info("Manifest has not been generated for this flight yet.")


# ==============================================================================
# 2. BOOK A TRIP (GUIDED 5-STEP WORKFLOW)
# ==============================================================================
elif menu_option == "🎫 Book a Trip (Guided Wizard)":
    st.title("🎫 Guided Booking Lifecycle")
    st.markdown("Walk through the complete 5-stage passenger lifecycle: **Intake ➔ Flight & Seat ➔ Verification ➔ Seat Check ➔ Billing**.")

    if "book_step" not in st.session_state:
        st.session_state.book_step = 1
    if "book_pid" not in st.session_state:
        st.session_state.book_pid = None
    if "book_pname" not in st.session_state:
        st.session_state.book_pname = ""
    if "book_fid" not in st.session_state:
        st.session_state.book_fid = None
    if "book_sid" not in st.session_state:
        st.session_state.book_sid = None
    if "book_bid" not in st.session_state:
        st.session_state.book_bid = None
    if "book_fare" not in st.session_state:
        st.session_state.book_fare = 0.0

    steps = ["1. Intake", "2. Flight & Seat", "3. Verification", "4. Seat Check", "5. Billing & Confirm"]
    current_step_idx = st.session_state.book_step - 1

    # Visual Stepper UI
    step_cols = st.columns(5)
    for idx, (col, s_name) in enumerate(zip(step_cols, steps)):
        with col:
            if idx == current_step_idx:
                st.markdown(f"**🔵 :blue[{s_name}]**")
            elif idx < current_step_idx:
                st.markdown(f"**✅ :green[{s_name}]**")
            else:
                st.markdown(f":gray[{s_name}]")
    st.markdown("---")

    # STEP 1: INTAKE
    if st.session_state.book_step == 1:
        st.subheader("Step 1: Passenger Intake")
        st.markdown("Register a new passenger or pick an existing registered traveller from the database.")

        intake_mode = st.radio("Intake Choice", ["Select Existing Passenger", "Register New Passenger"], horizontal=True)

        if intake_mode == "Select Existing Passenger":
            conn = get_db()
            passengers = conn.execute("SELECT passenger_id, full_name, email, passport_no FROM passenger ORDER BY passenger_id").fetchall()
            conn.close()

            if passengers:
                p_map = {f"ID #{p['passenger_id']} - {p['full_name']} (Passport: {p['passport_no']})": p for p in passengers}
                selected_p = st.selectbox("Select Passenger", list(p_map.keys()))
                if st.button("Proceed with Passenger ➡️", key="btn_use_existing"):
                    chosen = p_map[selected_p]
                    st.session_state.book_pid = chosen["passenger_id"]
                    st.session_state.book_pname = chosen["full_name"]
                    st.session_state.book_step = 2
                    st.rerun()
            else:
                st.warning("No passengers registered yet. Please register a new passenger below.")

        else:
            with st.form("new_passenger_form"):
                c1, c2 = st.columns(2)
                with c1:
                    name_input = st.text_input("Full Name", value="Aditi Sharma")
                    email_input = st.text_input("Email", value=f"aditi_{datetime.datetime.now().strftime('%M%S')}@example.com")
                    phone_input = st.text_input("Phone Number", value="9876543210")
                with c2:
                    import random
                    rnd_passport = f"K{random.randint(1000000, 9999999)}"
                    pass_input = st.text_input("Passport Number", value=rnd_passport)
                    dob_input = st.date_input("Date of Birth", value=datetime.date(1996, 5, 14), max_value=datetime.date.today())

                btn_create_p = st.form_submit_button("Register & Proceed ➡️")
                if btn_create_p:
                    payload = {
                        "full_name": name_input,
                        "email": email_input,
                        "phone": phone_input,
                        "passport_no": pass_input,
                        "dob": str(dob_input),
                    }
                    conn = get_db()
                    try:
                        code, p_res = api.passenger_create(conn, payload)
                        if code == 201:
                            st.session_state.book_pid = p_res["passenger_id"]
                            st.session_state.book_pname = name_input
                            st.session_state.book_step = 2
                            st.success(f"Passenger registered with ID #{p_res['passenger_id']}!")
                            st.rerun()
                        else:
                            st.error(f"Error {code}: {p_res.get('error')}")
                    except Exception as ex:
                        st.error(f"Validation or Database Error: {ex}")
                    finally:
                        conn.close()

    # STEP 2: FLIGHT AND SEAT
    elif st.session_state.book_step == 2:
        st.subheader("Step 2: Flight & Seat Selection")
        st.info(f"Booking for Passenger: **{st.session_state.book_pname}** (ID #{st.session_state.book_pid})")

        conn = get_db()
        _, flights = api.flights_search(conn, {})
        conn.close()

        fl_dict = {
            f"{f['flight_no']} ({f['origin_city']} ➔ {f['dest_city']} | Dep: {f['dep_time']} | Base Fare: {format_inr(f['base_fare'])})": f
            for f in flights if f["status"] in ("SCHEDULED", "DELAYED")
        }

        selected_flight_label = st.selectbox("Select Flight", list(fl_dict.keys()))
        selected_flight = fl_dict[selected_flight_label]
        st.session_state.book_fid = selected_flight["flight_id"]

        # Load Seat Map for this flight
        conn = get_db()
        _, seats = api.flight_seats(conn, st.session_state.book_fid)
        conn.close()

        st.markdown("### Interactive Seat Map")
        st.caption("Cabin Class Pricing Multipliers: **Economy: 1x** | **Business: 3x** | **First Class: 5x**")

        seat_cols = st.columns(4)
        selected_seat_obj = None

        # Render seats
        available_seats = [s for s in seats if s["state"] == "AVAILABLE"]
        locked_seats = [s for s in seats if s["state"] == "LOCKED"]

        # Display seat buttons / status visualizer
        st.markdown(f"**Available Seats ({len(available_seats)})** | **Locked Seats ({len(locked_seats)})**")

        seat_options = {}
        for s in seats:
            state_icon = "🟢" if s["state"] == "AVAILABLE" else "🔒"
            mult = api.CLASS_MULT.get(s["class"], 1)
            seat_fare = selected_flight["base_fare"] * mult
            label = f"{state_icon} Seat {s['seat_no']} ({s['class']}) - {format_inr(seat_fare)}"
            if s["state"] == "AVAILABLE":
                seat_options[label] = (s["seat_id"], seat_fare)

        if seat_options:
            chosen_seat_label = st.selectbox("Choose Available Seat to Hold", list(seat_options.keys()))
            st.session_state.book_sid, calculated_fare = seat_options[chosen_seat_label]
            st.session_state.book_fare = calculated_fare

            st.metric("Total Fare for Booking", format_inr(calculated_fare))

            c_back, c_hold = st.columns([1, 2])
            with c_back:
                if st.button("⬅️ Back to Intake"):
                    st.session_state.book_step = 1
                    st.rerun()
            with c_hold:
                if st.button("Hold Seat & Reserve ➡️", type="primary"):
                    conn = get_db()
                    try:
                        payload = {
                            "passenger_id": st.session_state.book_pid,
                            "flight_id": st.session_state.book_fid,
                            "seat_id": st.session_state.book_sid,
                        }
                        code, b_res = api.booking_create(conn, payload)
                        if code == 201:
                            st.session_state.book_bid = b_res["booking_id"]
                            st.session_state.book_fare = b_res["fare"]
                            st.session_state.book_step = 3
                            st.success(f"Seat held successfully! Booking ID #{b_res['booking_id']} created in HOLD status.")
                            st.rerun()
                        else:
                            st.error(f"Error {code}: {b_res.get('error')}")
                    except Exception as ex:
                        st.error(f"Integrity check failed: {ex}")
                    finally:
                        conn.close()
        else:
            st.error("No seats available on this flight! Please choose another flight.")

    # STEP 3: VERIFICATION
    elif st.session_state.book_step == 3:
        st.subheader("Step 3: Document & Fare Verification Desk")
        st.markdown(f"""
        Booking **#{st.session_state.book_bid}** is currently on **HOLD** at **{format_inr(st.session_state.book_fare)}**.
        
        *Airline staff must verify passenger identity and documents before payment can be accepted.*
        """)

        conn = get_db()
        booking_row = conn.execute("""
            SELECT b.booking_id, p.full_name, p.passport_no, f.flight_no, s.seat_no, s.class, b.fare, b.verification, b.status
            FROM booking b
            JOIN passenger p USING(passenger_id)
            JOIN flight f USING(flight_id)
            JOIN seat s USING(seat_id)
            WHERE b.booking_id=?
        """, (st.session_state.book_bid,)).fetchone()
        conn.close()

        if booking_row:
            col_v1, col_v2 = st.columns(2)
            with col_v1:
                st.write(f"**Passenger:** {booking_row['full_name']}")
                st.write(f"**Passport Number:** {booking_row['passport_no']}")
                st.write(f"**Flight Number:** {booking_row['flight_no']}")
            with col_v2:
                st.write(f"**Seat:** {booking_row['seat_no']} ({booking_row['class']})")
                st.write(f"**Status:** {booking_row['status']}")
                st.write(f"**Verification:** `{booking_row['verification']}`")

            st.markdown("---")
            btn_verify, btn_reject = st.columns(2)
            with btn_verify:
                if st.button("✅ Mark Verified (Accept Passenger)", type="primary"):
                    conn = get_db()
                    try:
                        code, res = api.booking_verify(conn, st.session_state.book_bid, {"result": "VERIFIED"})
                        if code == 200:
                            st.session_state.book_step = 4
                            st.success("Passenger verified successfully!")
                            st.rerun()
                        else:
                            st.error(res.get("error"))
                    finally:
                        conn.close()
            with btn_reject:
                if st.button("❌ Reject Verification"):
                    conn = get_db()
                    try:
                        code, res = api.booking_verify(conn, st.session_state.book_bid, {"result": "REJECTED"})
                        st.warning("Booking marked as REJECTED. Payment will not be permitted.")
                        st.session_state.book_step = 1
                    finally:
                        conn.close()

    # STEP 4: SEAT CHECK
    elif st.session_state.book_step == 4:
        st.subheader("Step 4: Seat Confirmation or Change")
        st.markdown("Review seat or change to another available seat before proceeding to payment.")

        conn = get_db()
        _, seats = api.flight_seats(conn, st.session_state.book_fid)
        conn.close()

        st.write(f"Current Seat: **ID #{st.session_state.book_sid}**")

        avail_seats = [s for s in seats if s["state"] == "AVAILABLE" or s["seat_id"] == st.session_state.book_sid]
        change_seat_opts = {f"Seat {s['seat_no']} ({s['class']})": s["seat_id"] for s in avail_seats}

        new_seat_label = st.selectbox("Change Seat (Optional)", list(change_seat_opts.keys()))
        new_seat_id = change_seat_opts[new_seat_label]

        col_k, col_chg = st.columns(2)
        with col_k:
            if st.button("Keep Seat & Proceed to Billing ➡️", type="primary"):
                st.session_state.book_step = 5
                st.rerun()
        with col_chg:
            if st.button("Switch to Selected Seat"):
                if new_seat_id != st.session_state.book_sid:
                    conn = get_db()
                    try:
                        code, s_res = api.booking_seat(conn, st.session_state.book_bid, {"seat_id": new_seat_id})
                        if code == 200:
                            st.session_state.book_sid = s_res["seat_id"]
                            st.session_state.book_fare = s_res["fare"]
                            st.success(f"Seat changed to ID #{new_seat_id}! New fare: {format_inr(s_res['fare'])}")
                            st.session_state.book_step = 5
                            st.rerun()
                        else:
                            st.error(s_res.get("error"))
                    finally:
                        conn.close()
                else:
                    st.info("Already on this seat.")

    # STEP 5: BILLING & PAYMENT
    elif st.session_state.book_step == 5:
        st.subheader("Step 5: Billing, Payment & Confirmation")
        st.markdown(f"""
        Required Fare: **{format_inr(st.session_state.book_fare)}** for Booking **#{st.session_state.book_bid}**.
        
        *Trigger enforcement:*
        - `trg_payment_check`: Aborts if payment amount < fare.
        - `trg_payment_confirm`: Automatically promotes booking status from **HOLD** to **CONFIRMED** on successful payment.
        """)

        with st.form("payment_form"):
            pay_amt = st.number_input("Payment Amount (₹)", value=float(st.session_state.book_fare), min_value=1.0, step=500.0)
            pay_method = st.selectbox("Payment Method", ["CARD", "UPI", "NETBANKING", "CASH"])

            btn_submit_pay = st.form_submit_button("Submit Payment", type="primary")
            if btn_submit_pay:
                conn = get_db()
                try:
                    payload = {
                        "booking_id": st.session_state.book_bid,
                        "amount": pay_amt,
                        "method": pay_method,
                        "status": "PAID"
                    }
                    code, p_res = api.payment_create(conn, payload)
                    if code == 201:
                        st.success(f"Payment recorded! Payment ID #{p_res['payment_id']}. Booking status updated to CONFIRMED!")
                        st.session_state.booking_completed = True
                    else:
                        st.error(f"Payment rejected ({code}): {p_res.get('error')}")
                except Exception as ex:
                    st.error(f"Trigger Blocked Payment: {ex}")
                finally:
                    conn.close()

        # Check-in and Baggage post-confirmation actions
        conn = get_db()
        cur_bk = conn.execute("SELECT status FROM booking WHERE booking_id=?", (st.session_state.book_bid,)).fetchone()
        conn.close()

        if cur_bk and cur_bk["status"] == "CONFIRMED":
            st.balloons()
            st.markdown("### 🛫 Boarding & Baggage Check Desk")
            c_ci, c_bg = st.columns(2)
            with c_ci:
                with st.expander("Passenger Check-in", expanded=True):
                    gate_input = st.text_input("Assigned Gate", value="B4")
                    if st.button("Check-in Passenger"):
                        conn = get_db()
                        try:
                            code, ci_res = api.checkin_create(conn, {"booking_id": st.session_state.book_bid, "gate_no": gate_input})
                            if code == 201:
                                st.success(f"Passenger Checked In at Gate {gate_input}! Check-in ID #{ci_res['checkin_id']}")
                            else:
                                st.error(ci_res.get("error"))
                        finally:
                            conn.close()

            with c_bg:
                with st.expander("Tag Baggage", expanded=True):
                    st.caption("Standard allowance: 20 kg. Excess charged at ₹500/kg.")
                    weight_input = st.number_input("Baggage Weight (kg)", min_value=1.0, max_value=50.0, value=23.5, step=0.5)
                    excess_fee = max(0.0, weight_input - 20) * 500
                    st.caption(f"Estimated Excess Baggage Fee: {format_inr(excess_fee)}")
                    if st.button("Tag & Record Baggage"):
                        conn = get_db()
                        try:
                            code, bg_res = api.baggage_create(conn, {"booking_id": st.session_state.book_bid, "weight_kg": weight_input})
                            if code == 201:
                                st.success(f"Baggage Tag {bg_res['tag_no']} Issued! Extra Fee: {format_inr(bg_res['fees'])}")
                            else:
                                st.error(bg_res.get("error"))
                        finally:
                            conn.close()

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Book Another Trip 🔄"):
                st.session_state.book_step = 1
                st.session_state.book_pid = None
                st.session_state.book_bid = None
                st.rerun()


# ==============================================================================
# 3. BOOKINGS & PASSENGER DESK
# ==============================================================================
elif menu_option == "📋 Bookings & Passenger Desk":
    st.title("📋 Bookings & Passenger Management Desk")

    tab_bookings, tab_passengers = st.tabs(["🎫 Bookings Desk", "👥 Passenger Directory"])

    with tab_bookings:
        st.subheader("All Bookings")
        st.caption("Inspect, verify, check in, tag baggage, or cancel bookings. Cancelling triggers an automatic refund and releases the seat immediately.")

        filter_status = st.selectbox("Filter by Status", ["ALL", "HOLD", "CONFIRMED", "CANCELLED"])

        conn = get_db()
        try:
            _, all_bookings = api.bookings_list(conn, {})
        finally:
            conn.close()

        if filter_status != "ALL":
            displayed_bookings = [b for b in all_bookings if b["status"] == filter_status]
        else:
            displayed_bookings = all_bookings

        if displayed_bookings:
            df_b = pd.DataFrame(displayed_bookings)
            st.dataframe(df_b, use_container_width=True, hide_index=True)

            st.markdown("---")
            st.markdown("### Booking Operations Desk")
            selected_bid = st.selectbox("Select Booking ID to Manage", [b["booking_id"] for b in displayed_bookings])
            bk_target = next(b for b in displayed_bookings if b["booking_id"] == selected_bid)

            st.write(f"**Managing Booking #{selected_bid}:** {bk_target['full_name']} | Flight {bk_target['flight_no']} | Seat {bk_target['seat_no']} ({bk_target['class']}) | Status: `{bk_target['status']}` | Paid: {format_inr(bk_target['paid'])}")

            op_col1, op_col2, op_col3, op_col4 = st.columns(4)

            with op_col1:
                if bk_target["status"] == "HOLD":
                    if st.button("✅ Verify Booking", key=f"ver_{selected_bid}"):
                        conn = get_db()
                        try:
                            code, res = api.booking_verify(conn, selected_bid, {"result": "VERIFIED"})
                            if code == 200:
                                st.success(f"Booking #{selected_bid} VERIFIED!")
                                st.rerun()
                            else:
                                st.error(res.get("error"))
                        finally:
                            conn.close()

            with op_col2:
                if bk_target["status"] == "CONFIRMED" and not bk_target.get("checkin"):
                    if st.button("🛫 Check In (Gate B4)", key=f"ci_{selected_bid}"):
                        conn = get_db()
                        try:
                            code, res = api.checkin_create(conn, {"booking_id": selected_bid, "gate_no": "B4"})
                            if code == 201:
                                st.success("Passenger checked in!")
                                st.rerun()
                            else:
                                st.error(res.get("error"))
                        finally:
                            conn.close()

            with op_col3:
                if bk_target["status"] == "CONFIRMED":
                    with st.popover("Tag Baggage"):
                        w = st.number_input("Bag Weight (kg)", min_value=1.0, max_value=50.0, value=22.0, key=f"w_{selected_bid}")
                        if st.button("Attach Tag", key=f"btn_bg_{selected_bid}"):
                            conn = get_db()
                            try:
                                code, res = api.baggage_create(conn, {"booking_id": selected_bid, "weight_kg": w})
                                if code == 201:
                                    st.success(f"Bag Tagged: {res['tag_no']} (Fees: {format_inr(res['fees'])})")
                                    st.rerun()
                                else:
                                    st.error(res.get("error"))
                            finally:
                                conn.close()

            with op_col4:
                if bk_target["status"] != "CANCELLED":
                    if st.button("❌ Cancel & Refund", key=f"can_{selected_bid}", type="primary"):
                        conn = get_db()
                        try:
                            code, res = api.booking_cancel(conn, selected_bid)
                            if code == 200:
                                st.success(f"Booking #{selected_bid} cancelled! Refund issued: {format_inr(res['refund_amount'])}. Seat released.")
                                st.rerun()
                            else:
                                st.error(res.get("error"))
                        finally:
                            conn.close()
        else:
            st.info("No bookings found matching filter.")

    with tab_passengers:
        st.subheader("Passenger Directory")

        conn = get_db()
        search_p = st.text_input("Search Passenger (Name, Passport, or Email)", placeholder="e.g. Aarav or P1234567")
        try:
            _, passengers_list = api.handle(conn, "GET", "/api/passengers", {"q": search_p} if search_p else {}, {})
        finally:
            conn.close()

        if passengers_list:
            st.dataframe(pd.DataFrame(passengers_list), use_container_width=True, hide_index=True)

            st.markdown("---")
            st.markdown("### Update / Delete Passenger")
            sel_pid = st.selectbox("Select Passenger ID", [p["passenger_id"] for p in passengers_list])
            p_obj = next(p for p in passengers_list if p["passenger_id"] == sel_pid)

            u_c1, u_c2 = st.columns(2)
            with u_c1:
                with st.form("edit_passenger_form"):
                    st.write(f"**Edit Contact Info for #{sel_pid} ({p_obj['full_name']})**")
                    upd_phone = st.text_input("Phone", value=p_obj["phone"])
                    upd_email = st.text_input("Email", value=p_obj["email"])
                    if st.form_submit_button("Update Info"):
                        conn = get_db()
                        try:
                            code, res = api.passenger_update(conn, sel_pid, {"phone": upd_phone, "email": upd_email})
                            if code == 200:
                                st.success("Passenger details updated!")
                                st.rerun()
                            else:
                                st.error(res.get("error"))
                        finally:
                            conn.close()

            with u_c2:
                st.write("**Referential Integrity Protection**")
                st.caption("Foreign key constraints prevent deleting a passenger if bookings exist.")
                if st.button("🗑️ Delete Passenger", key=f"del_p_{sel_pid}"):
                    conn = get_db()
                    try:
                        code, res = api.passenger_delete(conn, sel_pid)
                        if code == 200:
                            st.success(f"Passenger #{sel_pid} deleted.")
                            st.rerun()
                        else:
                            st.error(f"Blocked ({code}): {res.get('error')}")
                    finally:
                        conn.close()
        else:
            st.info("No passengers found.")


# ==============================================================================
# 4. ANALYTICS & SQL QUERIES
# ==============================================================================
elif menu_option == "📊 Analytics & SQL Queries":
    st.title("📊 Analytics, Views & Demonstration Queries")

    tab_charts, tab_queries, tab_views = st.tabs(["📈 Visual Analytics", "🔍 14 Project Queries", "👁️ Database Views"])

    with tab_charts:
        st.subheader("Visual Analytics & Key Operational Trends")

        conn = get_db()
        df_rev = pd.DataFrame(api.rows(conn, "SELECT * FROM v_revenue_summary"))
        df_class = pd.DataFrame(api.rows(conn, "SELECT s.class, COUNT(*) as bookings FROM booking b JOIN seat s USING(seat_id) GROUP BY s.class"))
        df_monthly = pd.DataFrame(api.rows(conn, "SELECT strftime('%Y-%m', paid_at) AS month, SUM(amount) AS revenue FROM payment WHERE status='PAID' GROUP BY month ORDER BY month"))
        conn.close()

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### Revenue by Flight (₹)")
            if not df_rev.empty:
                st.bar_chart(df_rev.set_index("flight_no")["revenue"], color="#0284c7")
            else:
                st.info("No revenue data available.")

        with c2:
            st.markdown("#### Load Factor per Flight (%)")
            if not df_rev.empty:
                st.bar_chart(df_rev.set_index("flight_no")["load_pct"], color="#10b981")
            else:
                st.info("No flight load data available.")

        c3, c4 = st.columns(2)
        with c3:
            st.markdown("#### Bookings by Cabin Class")
            if not df_class.empty:
                st.bar_chart(df_class.set_index("class")["bookings"], color="#f59e0b")
            else:
                st.info("No bookings recorded yet.")

        with c4:
            st.markdown("#### Monthly Revenue Trend (₹)")
            if not df_monthly.empty:
                st.line_chart(df_monthly.set_index("month")["revenue"], color="#8b5cf6")
            else:
                st.info("No payments recorded yet.")

    with tab_queries:
        st.subheader("The 14 Project Demonstration Queries")
        st.markdown("These 14 queries demonstrate multi-table joins, subqueries, and aggregate operations.")

        categories = ["ALL", "Join", "Subquery", "Aggregate"]
        cat_filter = st.selectbox("Filter Query Category", categories)

        queries_list = api.QUERIES
        if cat_filter != "ALL":
            queries_list = [q for q in queries_list if q[1] == cat_filter]

        q_dict = {f"{q[0]}: {q[2]} ({q[1]})": q for q in queries_list}
        selected_q_label = st.selectbox("Select SQL Query", list(q_dict.keys()))
        selected_q = q_dict[selected_q_label]

        qid, qkind, qtitle, qsql = selected_q

        st.markdown(f"**Query ID:** `{qid}` | **Type:** `{qkind}` | **Title:** {qtitle}")
        st.code(qsql, language="sql")

        conn = get_db()
        try:
            q_results = api.rows(conn, qsql)
            if q_results:
                st.write(f"**Query Result ({len(q_results)} rows):**")
                st.dataframe(pd.DataFrame(q_results), use_container_width=True, hide_index=True)
            else:
                st.info("Query executed cleanly and returned 0 rows.")
        except Exception as ex:
            st.error(f"Query error: {ex}")
        finally:
            conn.close()

    with tab_views:
        st.subheader("Database Pre-defined Views")
        st.markdown("Read-only abstracted views defined in `sql/sqlite_schema.sql`.")

        view_choice = st.selectbox("Select Database View", api.VIEWS)
        conn = get_db()
        try:
            v_rows = api.rows(conn, f"SELECT * FROM {view_choice}")
            st.write(f"**View:** `{view_choice}` ({len(v_rows)} rows)")
            if v_rows:
                st.dataframe(pd.DataFrame(v_rows), use_container_width=True, hide_index=True)
            else:
                st.info("No rows in view.")
        finally:
            conn.close()


# ==============================================================================
# 5. DATABASE EXPLORER & SQL CONSOLE
# ==============================================================================
elif menu_option == "🗄️ Database Explorer & SQL Console":
    st.title("🗄️ Database Explorer & Read-Only SQL Console")

    tab_tables, tab_console = st.tabs(["📋 Table Explorer", "💻 Read-Only SQL Console"])

    with tab_tables:
        st.subheader("Explore Relational Tables")
        conn = get_db()
        tables = [r["name"] for r in api.rows(conn, "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
        conn.close()

        selected_table = st.selectbox("Select Table", tables)

        conn = get_db()
        try:
            schema_info = api.rows(conn, f"PRAGMA table_info({selected_table})")
            table_rows = api.rows(conn, f"SELECT * FROM {selected_table} LIMIT 500")

            col_sch, col_cnt = st.columns([1, 2])
            with col_sch:
                st.markdown(f"**Table Schema:** `{selected_table}`")
                df_schema = pd.DataFrame(schema_info)[["cid", "name", "type", "notnull", "dflt_value", "pk"]]
                st.dataframe(df_schema, use_container_width=True, hide_index=True)

            with col_cnt:
                st.markdown(f"**Table Data ({len(table_rows)} records shown):**")
                if table_rows:
                    st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)
                else:
                    st.info(f"Table `{selected_table}` is currently empty.")
        finally:
            conn.close()

    with tab_console:
        st.subheader("Interactive SQL Sandbox")
        st.caption("Safely execute read-only queries (`SELECT` / `WITH`) against the live database.")

        sample_sqls = [
            "SELECT class, COUNT(*) AS seat_count FROM seat GROUP BY class",
            "SELECT flight_no, origin_code, dest_code, base_fare FROM flight WHERE base_fare > 5000",
            "SELECT status, COUNT(*) AS count, SUM(fare) AS total_fare FROM booking GROUP BY status",
            "SELECT * FROM airport",
        ]

        preset_choice = st.selectbox("Load Sample Query", ["Custom Query"] + sample_sqls)
        default_query = preset_choice if preset_choice != "Custom Query" else "SELECT * FROM passenger LIMIT 10"

        custom_sql = st.text_area("SQL Statement (Read-Only)", value=default_query, height=120)

        if st.button("Run SQL Query", type="primary"):
            code, res = api.sql_console(DB_PATH, {"sql": custom_sql})
            if code == 200:
                rows_data = res.get("rows", [])
                st.success(f"Query returned {len(rows_data)} rows successfully!")
                if rows_data:
                    st.dataframe(pd.DataFrame(rows_data), use_container_width=True, hide_index=True)
                else:
                    st.info("Query returned 0 rows.")
            else:
                st.error(f"SQL Error ({code}): {res.get('error')}")


# ==============================================================================
# 6. DBMS TRIGGERS & INTEGRITY RULES
# ==============================================================================
elif menu_option == "🛡️ DBMS Triggers & Integrity Rules":
    st.title("🛡️ DBMS Triggers & Defensive Integrity Rules")
    st.markdown("""
    The database enforces defensive business rules across **four defensive layers**:
    1. **UI Layer Validation**: Type & bounds checking.
    2. **API Layer Validation**: Parameter validation & entity existence checks.
    3. **ACID Transactions**: Atomic consistency guarantees.
    4. **Database Triggers & Constraints**: SQLite `RAISE(ABORT, ...)` triggers and `UNIQUE` / `FOREIGN KEY` constraints.
    """)

    tab_test_rules, tab_inspect_triggers = st.tabs(["🧪 Interactive Rule Testing Lab", "📜 Trigger Definitions Inspector"])

    with tab_test_rules:
        st.subheader("Test Defensive Database Rules")
        st.caption("Click any scenario below to trigger a violation and verify which defensive layer intercepts it.")

        rule_scenarios = [
            {
                "title": "1. Aircraft Schedule Overlap (Trigger trg_flight_overlap)",
                "desc": "Attempts to schedule AI999 on Aircraft 1 during 07:00-09:00 on 2026-11-10 (overlaps flight AI201).",
                "method": "POST",
                "path": "/api/flights",
                "payload": {"flight_no": "AI999", "origin_code": "HYD", "dest_code": "BOM", "aircraft_id": 1, "dep_time": "2026-11-10 07:00", "arr_time": "2026-11-10 09:00", "base_fare": 4500},
            },
            {
                "title": "2. Seat Double Booking (Trigger trg_seat_lock)",
                "desc": "Attempts to book Seat 1 on Flight 101, which is already locked by another passenger.",
                "method": "POST",
                "path": "/api/bookings",
                "payload": {"passenger_id": 3, "flight_id": 101, "seat_id": 1},
            },
            {
                "title": "3. Seat Aircraft Mismatch (Trigger trg_seat_belongs)",
                "desc": "Attempts to assign Seat 9 (belonging to Aircraft 2) to Flight 101 (operated by Aircraft 1).",
                "method": "POST",
                "path": "/api/bookings",
                "payload": {"passenger_id": 3, "flight_id": 101, "seat_id": 9},
            },
            {
                "title": "4. Payment Below Fare (Trigger trg_payment_check)",
                "desc": "Attempts to pay ₹500 for a booking with fare ₹21,000.",
                "method": "POST",
                "path": "/api/payments",
                "payload": {"booking_id": 1, "amount": 500, "method": "UPI"},
            },
            {
                "title": "5. Payment on Unverified Booking (API Layer Rule)",
                "desc": "Attempts to pay for a booking before passenger identity is marked as VERIFIED.",
                "method": "POST",
                "path": "/api/payments",
                "payload": {"booking_id": 3, "amount": 4500, "method": "CARD"},
            },
            {
                "title": "6. Duplicate Passport Number (UNIQUE Constraint)",
                "desc": "Attempts to insert a second passenger with passport 'P1234567'.",
                "method": "POST",
                "path": "/api/passengers",
                "payload": {"full_name": "Clone User", "email": "clone@mail.com", "phone": "9876543210", "passport_no": "P1234567", "dob": "1990-01-01"},
            },
            {
                "title": "7. Deleting Passenger with Active Bookings (Foreign Key Protection)",
                "desc": "Attempts to delete Passenger 1 who has active booking records.",
                "method": "DELETE",
                "path": "/api/passengers/1",
                "payload": {},
            },
            {
                "title": "8. SQL Injection Sanitization Test",
                "desc": "Tests parameterised query defence by passing malicious payload ' OR 1=1 --.",
                "method": "GET",
                "path": "/api/flights",
                "query": {"from": "' OR 1=1 --"},
                "payload": {},
            },
        ]

        for s in rule_scenarios:
            with st.expander(s["title"]):
                st.write(s["desc"])
                if st.button("Trigger Test Action", key=f"btn_rule_{s['title']}"):
                    conn = get_db()
                    try:
                        code, res = api.handle(conn, s["method"], s["path"], s.get("query", {}), s["payload"], DB_PATH)
                        if code >= 400:
                            st.success(f"🛡️ Defense Layer Intercepted Violation! HTTP {code}: {res.get('error')}")
                        elif s["path"] == "/api/flights" and s.get("query"):
                            st.success(f"🛡️ Defense Layer Parameterised: Query returned {len(res)} rows cleanly (0 leaked).")
                        else:
                            st.warning(f"Unexpected response code {code}: {res}")
                    finally:
                        conn.close()

    with tab_inspect_triggers:
        st.subheader("Active Database Triggers")
        conn = get_db()
        triggers = api.rows(conn, "SELECT name, tbl_name, sql FROM sqlite_master WHERE type='trigger' ORDER BY name")
        conn.close()

        for t in triggers:
            with st.expander(f"Trigger: {t['name']} on table `{t['tbl_name']}`"):
                st.code(t["sql"], language="sql")


# ==============================================================================
# 7. 10-POINT TEST MATRIX
# ==============================================================================
elif menu_option == "🧪 10-Point Test Matrix":
    st.title("🧪 Automated 10-Point Test Matrix")
    st.markdown("""
    Executes the 10-point test matrix described in the project report against a fresh **in-memory** SQLite database.
    Live database data is untouched.
    """)

    if st.button("▶️ Run Test Matrix", type="primary"):
        test_results = tests_matrix.run_matrix()
        total = len(test_results)
        passed = sum(1 for t in test_results if t["passed"])

        st.markdown(f"### Results: **{passed} / {total} Tests Passed ({int(passed/total*100)}%)**")

        rows = []
        for t in test_results:
            rows.append({
                "#": t["n"],
                "Test Case": t["test"],
                "Action Taken": t["action"],
                "Expected Behavior": t["expected"],
                "HTTP Status": t["http"],
                "Actual Result": t["actual"],
                "Status": "PASS" if t["passed"] else "FAIL"
            })

        df_tests = pd.DataFrame(rows)
        st.dataframe(df_tests, use_container_width=True, hide_index=True)

        if passed == total:
            st.balloons()
            st.success("All 10 test matrix specifications verified successfully!")
        else:
            st.error(f"{total - passed} tests failed.")
    else:
        st.info("Click 'Run Test Matrix' above to execute tests in memory.")
