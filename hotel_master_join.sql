WITH service_rollup AS (
    SELECT booking_id, SUM(amount_pkr) AS service_spend, COUNT(*) AS service_count
    FROM ServiceCharges
    GROUP BY booking_id
),
booking_features AS (
    SELECT
        r.booking_id,
        r.guest_id,
        r.room_number,
        r.room_type,
        r.booking_status,
        r.booking_channel,
        r.payment_method,
        CAST(julianday(r.check_out) - julianday(r.check_in) AS INTEGER) AS stay_nights,
        r.nightly_rate_pkr,
        r.adults,
        r.children,
        COALESCE(sr.service_spend, 0) AS service_spend,
        COALESCE(sr.service_count, 0) AS service_count,
        ri.floor,
        ri.max_occupancy,
        ri.standard_rate_pkr AS inventory_rate_pkr,
        ri.room_condition,
        rg.included_breakfast
    FROM Reservations AS r
    LEFT JOIN service_rollup AS sr ON sr.booking_id = r.booking_id
    LEFT JOIN RoomInventory AS ri ON ri.room_number = r.room_number
    LEFT JOIN RateGuide AS rg ON rg.room_type = ri.room_type
)
SELECT
    g.guest_id,
    g.country,
    g.loyalty_tier,
    COUNT(b.booking_id) AS total_bookings,
    SUM(CASE WHEN b.booking_status = 'Checked-out' THEN 1 ELSE 0 END) AS completed_bookings,
    SUM(CASE WHEN b.booking_status = 'Cancelled' THEN 1 ELSE 0 END) AS cancelled_bookings,
    SUM(CASE WHEN b.booking_status = 'No-show' THEN 1 ELSE 0 END) AS no_show_bookings,
    SUM(CASE WHEN b.booking_status = 'Checked-out' THEN COALESCE(b.stay_nights, 0) ELSE 0 END) AS completed_nights,
    SUM(CASE WHEN b.booking_status = 'Checked-out' THEN COALESCE(b.nightly_rate_pkr * b.stay_nights, 0) ELSE 0 END) AS room_revenue,
    SUM(CASE WHEN b.booking_status = 'Checked-out' THEN COALESCE(b.service_spend, 0) ELSE 0 END) AS service_spend,
    AVG(CASE WHEN b.booking_status = 'Checked-out' THEN b.nightly_rate_pkr END) AS avg_nightly_rate,
    AVG(CASE WHEN b.booking_status = 'Checked-out' THEN b.adults + b.children END) AS avg_party_size,
    AVG(b.max_occupancy) AS avg_room_capacity,
    SUM(CASE WHEN b.booking_status = 'Checked-out' AND b.included_breakfast = 'Yes' THEN 1 ELSE 0 END) AS breakfast_stays,
    COUNT(DISTINCT CASE WHEN b.booking_status = 'Checked-out' THEN b.room_type END) AS room_type_variety,
    AVG(CASE WHEN b.booking_status = 'Checked-out' THEN b.service_count END) AS avg_services_per_stay
FROM GuestProfiles AS g
LEFT JOIN booking_features AS b ON b.guest_id = g.guest_id
GROUP BY g.guest_id, g.country, g.loyalty_tier
ORDER BY g.guest_id;
