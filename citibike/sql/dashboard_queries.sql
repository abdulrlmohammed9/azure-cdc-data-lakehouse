-- Citi Bike dashboard datasets. Run each query separately in Databricks AI/BI.
-- Latest status, not measured trip demand.
SELECT COUNT(*) AS reporting_stations,
       SUM(bikes_available) AS available_bikes,
       SUM(docks_available) AS available_docks,
       SUM(CASE WHEN can_rent THEN 1 ELSE 0 END) AS stations_with_rentals,
       MAX(captured_at) AS newest_snapshot_utc
FROM workspace.citibike_live.gold_station_availability;

-- Latest 20 stations by available bicycles
SELECT station_name, bikes_available, docks_available, is_renting, captured_at
FROM workspace.citibike_live.gold_station_availability
ORDER BY bikes_available DESC LIMIT 20;

-- Changes by observation time
SELECT DATE(captured_at) AS observation_date, change_type, COUNT(*) AS station_changes
FROM workspace.citibike_live.silver_station_changes
GROUP BY DATE(captured_at), change_type ORDER BY observation_date DESC, change_type;

-- Stations that report no available bicycles
SELECT station_id, station_name, docks_available, captured_at
FROM workspace.citibike_live.gold_station_availability
WHERE bikes_available = 0
ORDER BY station_name;
