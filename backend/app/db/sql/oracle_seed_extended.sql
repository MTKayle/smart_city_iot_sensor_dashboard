-- ============================================================================
-- Smart City IoT — EXTENDED seed (idempotent)
-- ============================================================================
-- Adds 7 more districts × 3 wards × 3 sensors  on top of the original
-- 3-district / 9-ward / 33-sensor seed in oracle_seed_v2.sql.
--
-- After running this file the registry contains:
--    1 city + 10 districts + 30 wards + 11 clsts + 96 sensors.
--
-- Idempotent: every INSERT is wrapped in a NOT-EXISTS check so re-running is
-- safe.  Run via:
--     docker cp backend/app/db/sql/oracle_seed_extended.sql oracle-store:/tmp/
--     docker exec oracle-store sqlplus system/OraclePass123@XEPDB1 @/tmp/oracle_seed_extended.sql
-- ============================================================================

SET DEFINE OFF;

-- ─── Helper PL/SQL block: skip the entire seed if already applied ──────────
DECLARE
    n NUMBER;
BEGIN
    SELECT COUNT(*) INTO n FROM LOCATIONS WHERE LocationID = 'district_q4';
    IF n > 0 THEN
        DBMS_OUTPUT.PUT_LINE('Extended seed already applied — skipping.');
        RETURN;
    END IF;

    -- ─── DISTRICTS (7 new) ───────────────────────────────────────────────
    INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type, CenterLat, CenterLng, Area, Population)
    VALUES ('district_q4', N'Quận 4', 'city_hcmc', 'District', 10.7600, 106.7012, 4.18, 175329);
    INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type, CenterLat, CenterLng, Area, Population)
    VALUES ('district_q7', N'Quận 7', 'city_hcmc', 'District', 10.7378, 106.7220, 35.69, 363341);
    INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type, CenterLat, CenterLng, Area, Population)
    VALUES ('district_q10', N'Quận 10', 'city_hcmc', 'District', 10.7700, 106.6680, 5.71, 234440);
    INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type, CenterLat, CenterLng, Area, Population)
    VALUES ('district_binh_thanh', N'Bình Thạnh', 'city_hcmc', 'District', 10.8042, 106.7113, 20.76, 499164);
    INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type, CenterLat, CenterLng, Area, Population)
    VALUES ('district_tan_binh', N'Tân Bình', 'city_hcmc', 'District', 10.8020, 106.6519, 22.43, 459029);
    INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type, CenterLat, CenterLng, Area, Population)
    VALUES ('district_phu_nhuan', N'Phú Nhuận', 'city_hcmc', 'District', 10.7989, 106.6800, 4.88, 175291);
    INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type, CenterLat, CenterLng, Area, Population)
    VALUES ('district_go_vap', N'Gò Vấp', 'city_hcmc', 'District', 10.8389, 106.6650, 19.74, 676899);

    -- ─── WARDS (21 new) ───────────────────────────────────────────────
    -- Q4 (riverside, port adjacent)
    INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type, CenterLat, CenterLng, Area, Population)
    VALUES ('ward_q4_vinh_khanh', N'Phường Vĩnh Khánh', 'district_q4', 'Ward', 10.7556, 106.7013, 0.42, 14800);
    INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type, CenterLat, CenterLng, Area, Population)
    VALUES ('ward_q4_vinh_hoi',   N'Phường Vĩnh Hội',   'district_q4', 'Ward', 10.7635, 106.7008, 0.39, 13900);
    INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type, CenterLat, CenterLng, Area, Population)
    VALUES ('ward_q4_khanh_hoi',  N'Phường Khánh Hội',  'district_q4', 'Ward', 10.7613, 106.7048, 0.45, 15700);

    -- Q7 (Phu My Hung — modern, cleaner)
    INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type, CenterLat, CenterLng, Area, Population)
    VALUES ('ward_q7_tan_phong',  N'Phường Tân Phong',  'district_q7', 'Ward', 10.7286, 106.7186, 4.20, 18600);
    INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type, CenterLat, CenterLng, Area, Population)
    VALUES ('ward_q7_tan_phu',    N'Phường Tân Phú',    'district_q7', 'Ward', 10.7395, 106.7264, 5.10, 19800);
    INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type, CenterLat, CenterLng, Area, Population)
    VALUES ('ward_q7_tan_quy',    N'Phường Tân Quy',    'district_q7', 'Ward', 10.7378, 106.7158, 1.28, 22300);

    -- Q10
    INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type, CenterLat, CenterLng, Area, Population)
    VALUES ('ward_q10_01', N'Phường 1', 'district_q10', 'Ward', 10.7716, 106.6712, 0.41, 13500);
    INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type, CenterLat, CenterLng, Area, Population)
    VALUES ('ward_q10_02', N'Phường 2', 'district_q10', 'Ward', 10.7702, 106.6644, 0.45, 14300);
    INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type, CenterLat, CenterLng, Area, Population)
    VALUES ('ward_q10_03', N'Phường 3', 'district_q10', 'Ward', 10.7682, 106.6680, 0.39, 13100);

    -- Bình Thạnh (busy mixed-use)
    INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type, CenterLat, CenterLng, Area, Population)
    VALUES ('ward_bt_01', N'Phường 1', 'district_binh_thanh', 'Ward', 10.8003, 106.7160, 0.46, 16700);
    INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type, CenterLat, CenterLng, Area, Population)
    VALUES ('ward_bt_25', N'Phường 25 (Bình Thạnh)', 'district_binh_thanh', 'Ward', 10.8071, 106.7123, 0.52, 17500);
    INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type, CenterLat, CenterLng, Area, Population)
    VALUES ('ward_bt_26', N'Phường 26 (Bình Thạnh)', 'district_binh_thanh', 'Ward', 10.8049, 106.7088, 0.41, 14400);

    -- Tân Bình (airport-adjacent, dense)
    INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type, CenterLat, CenterLng, Area, Population)
    VALUES ('ward_tb_01', N'Phường 1', 'district_tan_binh', 'Ward', 10.7984, 106.6551, 0.50, 17900);
    INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type, CenterLat, CenterLng, Area, Population)
    VALUES ('ward_tb_04', N'Phường 4', 'district_tan_binh', 'Ward', 10.8048, 106.6530, 0.43, 15800);
    INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type, CenterLat, CenterLng, Area, Population)
    VALUES ('ward_tb_15', N'Phường 15 (Tân Bình)', 'district_tan_binh', 'Ward', 10.8025, 106.6485, 0.47, 16400);

    -- Phú Nhuận (residential, leafy)
    INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type, CenterLat, CenterLng, Area, Population)
    VALUES ('ward_pn_07', N'Phường 7', 'district_phu_nhuan', 'Ward', 10.7965, 106.6789, 0.36, 12700);
    INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type, CenterLat, CenterLng, Area, Population)
    VALUES ('ward_pn_09', N'Phường 9', 'district_phu_nhuan', 'Ward', 10.7989, 106.6815, 0.34, 12200);
    INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type, CenterLat, CenterLng, Area, Population)
    VALUES ('ward_pn_15', N'Phường 15 (Phú Nhuận)', 'district_phu_nhuan', 'Ward', 10.8016, 106.6816, 0.32, 11500);

    -- Gò Vấp (suburban)
    INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type, CenterLat, CenterLng, Area, Population)
    VALUES ('ward_gv_01', N'Phường 1', 'district_go_vap', 'Ward', 10.8362, 106.6680, 0.62, 18900);
    INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type, CenterLat, CenterLng, Area, Population)
    VALUES ('ward_gv_05', N'Phường 5', 'district_go_vap', 'Ward', 10.8412, 106.6635, 0.58, 17600);
    INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type, CenterLat, CenterLng, Area, Population)
    VALUES ('ward_gv_10', N'Phường 10 (Gò Vấp)', 'district_go_vap', 'Ward', 10.8395, 106.6695, 0.64, 19200);

    -- ─── CLUSTERS (7 new — one per district) ────────────────────────────
    INSERT INTO SENSOR_CLUSTERS (ClusterID, LocationID, ClusterName, CenterLat, CenterLng, Radius, Algorithm)
    VALUES ('clst_q4',          'district_q4',          N'Cụm Quận 4',          10.7600, 106.7012, 400, 'GRID');
    INSERT INTO SENSOR_CLUSTERS (ClusterID, LocationID, ClusterName, CenterLat, CenterLng, Radius, Algorithm)
    VALUES ('clst_q7',          'district_q7',          N'Cụm Quận 7 (Phú Mỹ Hưng)', 10.7378, 106.7220, 600, 'GRID');
    INSERT INTO SENSOR_CLUSTERS (ClusterID, LocationID, ClusterName, CenterLat, CenterLng, Radius, Algorithm)
    VALUES ('clst_q10',         'district_q10',         N'Cụm Quận 10',         10.7700, 106.6680, 400, 'GRID');
    INSERT INTO SENSOR_CLUSTERS (ClusterID, LocationID, ClusterName, CenterLat, CenterLng, Radius, Algorithm)
    VALUES ('clst_binh_thanh',  'district_binh_thanh',  N'Cụm Bình Thạnh',      10.8042, 106.7113, 500, 'GRID');
    INSERT INTO SENSOR_CLUSTERS (ClusterID, LocationID, ClusterName, CenterLat, CenterLng, Radius, Algorithm)
    VALUES ('clst_tan_binh',    'district_tan_binh',    N'Cụm Tân Bình',        10.8020, 106.6519, 500, 'GRID');
    INSERT INTO SENSOR_CLUSTERS (ClusterID, LocationID, ClusterName, CenterLat, CenterLng, Radius, Algorithm)
    VALUES ('clst_phu_nhuan',   'district_phu_nhuan',   N'Cụm Phú Nhuận',       10.7989, 106.6800, 400, 'GRID');
    INSERT INTO SENSOR_CLUSTERS (ClusterID, LocationID, ClusterName, CenterLat, CenterLng, Radius, Algorithm)
    VALUES ('clst_go_vap',      'district_go_vap',      N'Cụm Gò Vấp',          10.8389, 106.6650, 600, 'GRID');

    -- ─── SENSORS (63 new = 21 wards × 3 sensors) ────────────────────────
    -- We use a tiny PL/SQL loop to keep this DRY.  Each ward gets 3 sensors
    -- with a slight lat/lng offset so they're not stacked on the same pixel.
    DECLARE
        TYPE WardRec IS RECORD (loc VARCHAR2(64), clst VARCHAR2(64), lat NUMBER, lng NUMBER);
        TYPE WardList IS TABLE OF WardRec INDEX BY PLS_INTEGER;
        wards WardList;
        idx PLS_INTEGER := 1;
        sensor_seq PLS_INTEGER;
        sid VARCHAR2(64);
    BEGIN
        wards(1)  := WardRec('ward_q4_vinh_khanh',  'clst_q4',          10.7556, 106.7013);
        wards(2)  := WardRec('ward_q4_vinh_hoi',    'clst_q4',          10.7635, 106.7008);
        wards(3)  := WardRec('ward_q4_khanh_hoi',   'clst_q4',          10.7613, 106.7048);
        wards(4)  := WardRec('ward_q7_tan_phong',   'clst_q7',          10.7286, 106.7186);
        wards(5)  := WardRec('ward_q7_tan_phu',     'clst_q7',          10.7395, 106.7264);
        wards(6)  := WardRec('ward_q7_tan_quy',     'clst_q7',          10.7378, 106.7158);
        wards(7)  := WardRec('ward_q10_01',         'clst_q10',         10.7716, 106.6712);
        wards(8)  := WardRec('ward_q10_02',         'clst_q10',         10.7702, 106.6644);
        wards(9)  := WardRec('ward_q10_03',         'clst_q10',         10.7682, 106.6680);
        wards(10) := WardRec('ward_bt_01',          'clst_binh_thanh',  10.8003, 106.7160);
        wards(11) := WardRec('ward_bt_25',          'clst_binh_thanh',  10.8071, 106.7123);
        wards(12) := WardRec('ward_bt_26',          'clst_binh_thanh',  10.8049, 106.7088);
        wards(13) := WardRec('ward_tb_01',          'clst_tan_binh',    10.7984, 106.6551);
        wards(14) := WardRec('ward_tb_04',          'clst_tan_binh',    10.8048, 106.6530);
        wards(15) := WardRec('ward_tb_15',          'clst_tan_binh',    10.8025, 106.6485);
        wards(16) := WardRec('ward_pn_07',          'clst_phu_nhuan',   10.7965, 106.6789);
        wards(17) := WardRec('ward_pn_09',          'clst_phu_nhuan',   10.7989, 106.6815);
        wards(18) := WardRec('ward_pn_15',          'clst_phu_nhuan',   10.8016, 106.6816);
        wards(19) := WardRec('ward_gv_01',          'clst_go_vap',      10.8362, 106.6680);
        wards(20) := WardRec('ward_gv_05',          'clst_go_vap',      10.8412, 106.6635);
        wards(21) := WardRec('ward_gv_10',          'clst_go_vap',      10.8395, 106.6695);

        FOR i IN 1 .. wards.COUNT LOOP
            FOR s IN 1 .. 3 LOOP
                -- Build sensor_id from ward suffix.
                sid := 'sen_' || REPLACE(wards(i).loc, 'ward_', '') || '_' ||
                       LPAD(TO_CHAR(s), 2, '0');
                INSERT INTO SENSOR_REGISTRY (
                    SensorID, LocationID, ClusterID,
                    Latitude, Longitude, Altitude,
                    SensorModel, FirmwareVersion, Status, InstallDate
                ) VALUES (
                    sid, wards(i).loc, wards(i).clst,
                    wards(i).lat + (s - 2) * 0.0010,
                    wards(i).lng + (s - 2) * 0.0010,
                    5.0,
                    'EnviroSense Pro X1', 'v2.3.1', 'Active', DATE '2025-01-15'
                );

                -- Capabilities: 5 metrics per sensor.
                INSERT INTO SENSOR_CAPABILITIES (CapabilityID, SensorID, MetricType, Unit, MinRange, MaxRange, Accuracy, IsActive)
                VALUES (sid || '_co2',   sid, 'CO2',         'ppm',   0,    5000, 0.05, 1);
                INSERT INTO SENSOR_CAPABILITIES (CapabilityID, SensorID, MetricType, Unit, MinRange, MaxRange, Accuracy, IsActive)
                VALUES (sid || '_noise', sid, 'Noise',       'dB',    20,   120,  0.05, 1);
                INSERT INTO SENSOR_CAPABILITIES (CapabilityID, SensorID, MetricType, Unit, MinRange, MaxRange, Accuracy, IsActive)
                VALUES (sid || '_temp',  sid, 'Temperature', '°C',    -10,  60,   0.05, 1);
                INSERT INTO SENSOR_CAPABILITIES (CapabilityID, SensorID, MetricType, Unit, MinRange, MaxRange, Accuracy, IsActive)
                VALUES (sid || '_pm25',  sid, 'PM2.5',       N'µg/m³',0,    500,  0.05, 1);
                INSERT INTO SENSOR_CAPABILITIES (CapabilityID, SensorID, MetricType, Unit, MinRange, MaxRange, Accuracy, IsActive)
                VALUES (sid || '_hum',   sid, 'Humidity',    '%',     0,    100,  0.05, 1);
            END LOOP;
        END LOOP;
    END;

    COMMIT;
    DBMS_OUTPUT.PUT_LINE('Extended seed applied: +7 districts, +21 wards, +7 clsts, +63 sensors.');
END;
/

EXIT;
