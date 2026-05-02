-- ============================================================================
-- SMART CITY IOT DATABASE SEED DATA - PRODUCTION READY v2.0
-- Date: May 2, 2026
-- Description: Realistic seed data for Ho Chi Minh City with geolocation
-- ============================================================================

-- ============================================================================
-- LOCATIONS: City > Districts > Wards
-- ============================================================================

-- City level
INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type, CenterLat, CenterLng, Area, Population)
VALUES ('city_hcmc', 'Ho Chi Minh City', NULL, 'City', 10.8231, 106.6297, 2095.0, 9000000);

-- District 1
INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type, CenterLat, CenterLng, Area, Population)
VALUES ('district_q1', 'District 1', 'city_hcmc', 'District', 10.7756, 106.7019, 7.73, 204899);

-- District 3
INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type, CenterLat, CenterLng, Area, Population)
VALUES ('district_q3', 'District 3', 'city_hcmc', 'District', 10.7866, 106.6828, 4.92, 188029);

-- District 5
INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type, CenterLat, CenterLng, Area, Population)
VALUES ('district_q5', 'District 5', 'city_hcmc', 'District', 10.7545, 106.6664, 4.27, 179262);

-- Wards in District 1
INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type, CenterLat, CenterLng, Area, Population)
VALUES ('ward_q1_ben_nghe', 'Ben Nghe Ward', 'district_q1', 'Ward', 10.7756, 106.7019, 0.89, 18500);

INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type, CenterLat, CenterLng, Area, Population)
VALUES ('ward_q1_ben_thanh', 'Ben Thanh Ward', 'district_q1', 'Ward', 10.7721, 106.6983, 0.52, 15200);

INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type, CenterLat, CenterLng, Area, Population)
VALUES ('ward_q1_nguyen_thai_binh', 'Nguyen Thai Binh Ward', 'district_q1', 'Ward', 10.7689, 106.6945, 0.48, 14800);

-- Wards in District 3
INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type, CenterLat, CenterLng, Area, Population)
VALUES ('ward_q3_01', 'Ward 1', 'district_q3', 'Ward', 10.7866, 106.6828, 0.45, 16500);

INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type, CenterLat, CenterLng, Area, Population)
VALUES ('ward_q3_02', 'Ward 2', 'district_q3', 'Ward', 10.7823, 106.6789, 0.38, 14200);

INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type, CenterLat, CenterLng, Area, Population)
VALUES ('ward_q3_03', 'Ward 3', 'district_q3', 'Ward', 10.7901, 106.6856, 0.42, 15800);

-- Wards in District 5
INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type, CenterLat, CenterLng, Area, Population)
VALUES ('ward_q5_01', 'Ward 1', 'district_q5', 'Ward', 10.7545, 106.6664, 0.35, 13500);

INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type, CenterLat, CenterLng, Area, Population)
VALUES ('ward_q5_02', 'Ward 2', 'district_q5', 'Ward', 10.7512, 106.6623, 0.32, 12800);

INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type, CenterLat, CenterLng, Area, Population)
VALUES ('ward_q5_03', 'Ward 3', 'district_q5', 'Ward', 10.7578, 106.6701, 0.38, 14100);

COMMIT;


-- ============================================================================
-- SENSOR_CLUSTERS: Spatial clustering
-- ============================================================================

-- District 1 clusters
INSERT INTO SENSOR_CLUSTERS (ClusterID, LocationID, ClusterName, CenterLat, CenterLng, Radius, Algorithm)
VALUES ('cluster_q1_north', 'district_q1', 'District 1 North Cluster', 10.7780, 106.7030, 300, 'GRID');

INSERT INTO SENSOR_CLUSTERS (ClusterID, LocationID, ClusterName, CenterLat, CenterLng, Radius, Algorithm)
VALUES ('cluster_q1_south', 'district_q1', 'District 1 South Cluster', 10.7720, 106.6990, 300, 'GRID');

-- District 3 clusters
INSERT INTO SENSOR_CLUSTERS (ClusterID, LocationID, ClusterName, CenterLat, CenterLng, Radius, Algorithm)
VALUES ('cluster_q3_central', 'district_q3', 'District 3 Central Cluster', 10.7866, 106.6828, 300, 'GRID');

-- District 5 clusters
INSERT INTO SENSOR_CLUSTERS (ClusterID, LocationID, ClusterName, CenterLat, CenterLng, Radius, Algorithm)
VALUES ('cluster_q5_west', 'district_q5', 'District 5 West Cluster', 10.7545, 106.6664, 300, 'GRID');

COMMIT;


-- ============================================================================
-- SENSOR_REGISTRY: Multi-sensor deployment with geolocation
-- ============================================================================

-- Ben Nghe Ward (5 combo sensors)
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, ClusterID, Latitude, Longitude, Altitude, SensorModel, FirmwareVersion, Status, InstallDate)
VALUES ('sen_q1_ben_nghe_01', 'ward_q1_ben_nghe', 'cluster_q1_north', 10.7756, 106.7019, 5.0, 'EnviroSense Pro X1', 'v2.3.1', 'Active', DATE '2025-01-15');

INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, ClusterID, Latitude, Longitude, Altitude, SensorModel, FirmwareVersion, Status, InstallDate)
VALUES ('sen_q1_ben_nghe_02', 'ward_q1_ben_nghe', 'cluster_q1_north', 10.7765, 106.7028, 5.0, 'EnviroSense Pro X1', 'v2.3.1', 'Active', DATE '2025-01-15');

INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, ClusterID, Latitude, Longitude, Altitude, SensorModel, FirmwareVersion, Status, InstallDate)
VALUES ('sen_q1_ben_nghe_03', 'ward_q1_ben_nghe', 'cluster_q1_north', 10.7748, 106.7011, 5.0, 'EnviroSense Pro X1', 'v2.3.1', 'Active', DATE '2025-01-15');

INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, ClusterID, Latitude, Longitude, Altitude, SensorModel, FirmwareVersion, Status, InstallDate)
VALUES ('sen_q1_ben_nghe_04', 'ward_q1_ben_nghe', 'cluster_q1_north', 10.7770, 106.7035, 5.0, 'EnviroSense Pro X1', 'v2.3.1', 'Active', DATE '2025-01-15');

INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, ClusterID, Latitude, Longitude, Altitude, SensorModel, FirmwareVersion, Status, InstallDate)
VALUES ('sen_q1_ben_nghe_05', 'ward_q1_ben_nghe', 'cluster_q1_north', 10.7742, 106.7005, 5.0, 'EnviroSense Pro X1', 'v2.3.1', 'Active', DATE '2025-01-15');

-- Ben Thanh Ward (5 combo sensors)
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, ClusterID, Latitude, Longitude, Altitude, SensorModel, FirmwareVersion, Status, InstallDate)
VALUES ('sen_q1_ben_thanh_01', 'ward_q1_ben_thanh', 'cluster_q1_south', 10.7721, 106.6983, 5.0, 'EnviroSense Pro X1', 'v2.3.1', 'Active', DATE '2025-01-15');

INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, ClusterID, Latitude, Longitude, Altitude, SensorModel, FirmwareVersion, Status, InstallDate)
VALUES ('sen_q1_ben_thanh_02', 'ward_q1_ben_thanh', 'cluster_q1_south', 10.7728, 106.6991, 5.0, 'EnviroSense Pro X1', 'v2.3.1', 'Active', DATE '2025-01-15');

INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, ClusterID, Latitude, Longitude, Altitude, SensorModel, FirmwareVersion, Status, InstallDate)
VALUES ('sen_q1_ben_thanh_03', 'ward_q1_ben_thanh', 'cluster_q1_south', 10.7715, 106.6975, 5.0, 'EnviroSense Pro X1', 'v2.3.1', 'Active', DATE '2025-01-15');

INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, ClusterID, Latitude, Longitude, Altitude, SensorModel, FirmwareVersion, Status, InstallDate)
VALUES ('sen_q1_ben_thanh_04', 'ward_q1_ben_thanh', 'cluster_q1_south', 10.7733, 106.6998, 5.0, 'EnviroSense Pro X1', 'v2.3.1', 'Active', DATE '2025-01-15');

INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, ClusterID, Latitude, Longitude, Altitude, SensorModel, FirmwareVersion, Status, InstallDate)
VALUES ('sen_q1_ben_thanh_05', 'ward_q1_ben_thanh', 'cluster_q1_south', 10.7710, 106.6968, 5.0, 'EnviroSense Pro X1', 'v2.3.1', 'Active', DATE '2025-01-15');

-- Nguyen Thai Binh Ward (5 combo sensors)
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, ClusterID, Latitude, Longitude, Altitude, SensorModel, FirmwareVersion, Status, InstallDate)
VALUES ('sen_q1_ntb_01', 'ward_q1_nguyen_thai_binh', 'cluster_q1_south', 10.7689, 106.6945, 5.0, 'EnviroSense Pro X1', 'v2.3.1', 'Active', DATE '2025-01-15');

INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, ClusterID, Latitude, Longitude, Altitude, SensorModel, FirmwareVersion, Status, InstallDate)
VALUES ('sen_q1_ntb_02', 'ward_q1_nguyen_thai_binh', 'cluster_q1_south', 10.7695, 106.6952, 5.0, 'EnviroSense Pro X1', 'v2.3.1', 'Active', DATE '2025-01-15');

INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, ClusterID, Latitude, Longitude, Altitude, SensorModel, FirmwareVersion, Status, InstallDate)
VALUES ('sen_q1_ntb_03', 'ward_q1_nguyen_thai_binh', 'cluster_q1_south', 10.7683, 106.6938, 5.0, 'EnviroSense Pro X1', 'v2.3.1', 'Active', DATE '2025-01-15');

INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, ClusterID, Latitude, Longitude, Altitude, SensorModel, FirmwareVersion, Status, InstallDate)
VALUES ('sen_q1_ntb_04', 'ward_q1_nguyen_thai_binh', 'cluster_q1_south', 10.7700, 106.6959, 5.0, 'EnviroSense Pro X1', 'v2.3.1', 'Active', DATE '2025-01-15');

INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, ClusterID, Latitude, Longitude, Altitude, SensorModel, FirmwareVersion, Status, InstallDate)
VALUES ('sen_q1_ntb_05', 'ward_q1_nguyen_thai_binh', 'cluster_q1_south', 10.7678, 106.6931, 5.0, 'EnviroSense Pro X1', 'v2.3.1', 'Active', DATE '2025-01-15');

-- District 3 sensors (3 wards x 3 sensors = 9 sensors)
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, ClusterID, Latitude, Longitude, Altitude, SensorModel, FirmwareVersion, Status, InstallDate)
VALUES ('sen_q3_w1_01', 'ward_q3_01', 'cluster_q3_central', 10.7866, 106.6828, 5.0, 'EnviroSense Pro X1', 'v2.3.1', 'Active', DATE '2025-01-20');

INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, ClusterID, Latitude, Longitude, Altitude, SensorModel, FirmwareVersion, Status, InstallDate)
VALUES ('sen_q3_w1_02', 'ward_q3_01', 'cluster_q3_central', 10.7873, 106.6835, 5.0, 'EnviroSense Pro X1', 'v2.3.1', 'Active', DATE '2025-01-20');

INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, ClusterID, Latitude, Longitude, Altitude, SensorModel, FirmwareVersion, Status, InstallDate)
VALUES ('sen_q3_w1_03', 'ward_q3_01', 'cluster_q3_central', 10.7859, 106.6821, 5.0, 'EnviroSense Pro X1', 'v2.3.1', 'Active', DATE '2025-01-20');

INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, ClusterID, Latitude, Longitude, Altitude, SensorModel, FirmwareVersion, Status, InstallDate)
VALUES ('sen_q3_w2_01', 'ward_q3_02', 'cluster_q3_central', 10.7823, 106.6789, 5.0, 'EnviroSense Pro X1', 'v2.3.1', 'Active', DATE '2025-01-20');

INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, ClusterID, Latitude, Longitude, Altitude, SensorModel, FirmwareVersion, Status, InstallDate)
VALUES ('sen_q3_w2_02', 'ward_q3_02', 'cluster_q3_central', 10.7830, 106.6796, 5.0, 'EnviroSense Pro X1', 'v2.3.1', 'Active', DATE '2025-01-20');

INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, ClusterID, Latitude, Longitude, Altitude, SensorModel, FirmwareVersion, Status, InstallDate)
VALUES ('sen_q3_w2_03', 'ward_q3_02', 'cluster_q3_central', 10.7816, 106.6782, 5.0, 'EnviroSense Pro X1', 'v2.3.1', 'Active', DATE '2025-01-20');

INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, ClusterID, Latitude, Longitude, Altitude, SensorModel, FirmwareVersion, Status, InstallDate)
VALUES ('sen_q3_w3_01', 'ward_q3_03', 'cluster_q3_central', 10.7901, 106.6856, 5.0, 'EnviroSense Pro X1', 'v2.3.1', 'Active', DATE '2025-01-20');

INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, ClusterID, Latitude, Longitude, Altitude, SensorModel, FirmwareVersion, Status, InstallDate)
VALUES ('sen_q3_w3_02', 'ward_q3_03', 'cluster_q3_central', 10.7908, 106.6863, 5.0, 'EnviroSense Pro X1', 'v2.3.1', 'Active', DATE '2025-01-20');

INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, ClusterID, Latitude, Longitude, Altitude, SensorModel, FirmwareVersion, Status, InstallDate)
VALUES ('sen_q3_w3_03', 'ward_q3_03', 'cluster_q3_central', 10.7894, 106.6849, 5.0, 'EnviroSense Pro X1', 'v2.3.1', 'Active', DATE '2025-01-20');

-- District 5 sensors (3 wards x 3 sensors = 9 sensors)
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, ClusterID, Latitude, Longitude, Altitude, SensorModel, FirmwareVersion, Status, InstallDate)
VALUES ('sen_q5_w1_01', 'ward_q5_01', 'cluster_q5_west', 10.7545, 106.6664, 5.0, 'EnviroSense Pro X1', 'v2.3.1', 'Active', DATE '2025-01-25');

INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, ClusterID, Latitude, Longitude, Altitude, SensorModel, FirmwareVersion, Status, InstallDate)
VALUES ('sen_q5_w1_02', 'ward_q5_01', 'cluster_q5_west', 10.7552, 106.6671, 5.0, 'EnviroSense Pro X1', 'v2.3.1', 'Active', DATE '2025-01-25');

INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, ClusterID, Latitude, Longitude, Altitude, SensorModel, FirmwareVersion, Status, InstallDate)
VALUES ('sen_q5_w1_03', 'ward_q5_01', 'cluster_q5_west', 10.7538, 106.6657, 5.0, 'EnviroSense Pro X1', 'v2.3.1', 'Active', DATE '2025-01-25');

INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, ClusterID, Latitude, Longitude, Altitude, SensorModel, FirmwareVersion, Status, InstallDate)
VALUES ('sen_q5_w2_01', 'ward_q5_02', 'cluster_q5_west', 10.7512, 106.6623, 5.0, 'EnviroSense Pro X1', 'v2.3.1', 'Active', DATE '2025-01-25');

INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, ClusterID, Latitude, Longitude, Altitude, SensorModel, FirmwareVersion, Status, InstallDate)
VALUES ('sen_q5_w2_02', 'ward_q5_02', 'cluster_q5_west', 10.7519, 106.6630, 5.0, 'EnviroSense Pro X1', 'v2.3.1', 'Active', DATE '2025-01-25');

INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, ClusterID, Latitude, Longitude, Altitude, SensorModel, FirmwareVersion, Status, InstallDate)
VALUES ('sen_q5_w2_03', 'ward_q5_02', 'cluster_q5_west', 10.7505, 106.6616, 5.0, 'EnviroSense Pro X1', 'v2.3.1', 'Active', DATE '2025-01-25');

INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, ClusterID, Latitude, Longitude, Altitude, SensorModel, FirmwareVersion, Status, InstallDate)
VALUES ('sen_q5_w3_01', 'ward_q5_03', 'cluster_q5_west', 10.7578, 106.6701, 5.0, 'EnviroSense Pro X1', 'v2.3.1', 'Active', DATE '2025-01-25');

INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, ClusterID, Latitude, Longitude, Altitude, SensorModel, FirmwareVersion, Status, InstallDate)
VALUES ('sen_q5_w3_02', 'ward_q5_03', 'cluster_q5_west', 10.7585, 106.6708, 5.0, 'EnviroSense Pro X1', 'v2.3.1', 'Active', DATE '2025-01-25');

INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, ClusterID, Latitude, Longitude, Altitude, SensorModel, FirmwareVersion, Status, InstallDate)
VALUES ('sen_q5_w3_03', 'ward_q5_03', 'cluster_q5_west', 10.7571, 106.6694, 5.0, 'EnviroSense Pro X1', 'v2.3.1', 'Active', DATE '2025-01-25');

COMMIT;


-- ============================================================================
-- SENSOR_CAPABILITIES: Define what each sensor can measure
-- ============================================================================

-- Helper procedure to add capabilities for all sensors
DECLARE
    CURSOR sensor_cursor IS SELECT SensorID FROM SENSOR_REGISTRY;
    v_sensor_id VARCHAR2(50);
    v_cap_counter NUMBER := 1;
BEGIN
    FOR sensor_rec IN sensor_cursor LOOP
        v_sensor_id := sensor_rec.SensorID;
        
        -- CO2 capability
        INSERT INTO SENSOR_CAPABILITIES (CapabilityID, SensorID, MetricType, Unit, MinRange, MaxRange, Accuracy, IsActive)
        VALUES ('cap_' || v_cap_counter, v_sensor_id, 'CO2', 'ppm', 0, 5000, 2.0, 1);
        v_cap_counter := v_cap_counter + 1;
        
        -- Noise capability
        INSERT INTO SENSOR_CAPABILITIES (CapabilityID, SensorID, MetricType, Unit, MinRange, MaxRange, Accuracy, IsActive)
        VALUES ('cap_' || v_cap_counter, v_sensor_id, 'Noise', 'dB', 30, 120, 1.5, 1);
        v_cap_counter := v_cap_counter + 1;
        
        -- Temperature capability
        INSERT INTO SENSOR_CAPABILITIES (CapabilityID, SensorID, MetricType, Unit, MinRange, MaxRange, Accuracy, IsActive)
        VALUES ('cap_' || v_cap_counter, v_sensor_id, 'Temperature', '°C', -10, 50, 0.5, 1);
        v_cap_counter := v_cap_counter + 1;
        
        -- PM2.5 capability
        INSERT INTO SENSOR_CAPABILITIES (CapabilityID, SensorID, MetricType, Unit, MinRange, MaxRange, Accuracy, IsActive)
        VALUES ('cap_' || v_cap_counter, v_sensor_id, 'PM2.5', 'μg/m³', 0, 500, 3.0, 1);
        v_cap_counter := v_cap_counter + 1;
        
        -- Humidity capability
        INSERT INTO SENSOR_CAPABILITIES (CapabilityID, SensorID, MetricType, Unit, MinRange, MaxRange, Accuracy, IsActive)
        VALUES ('cap_' || v_cap_counter, v_sensor_id, 'Humidity', '%', 0, 100, 2.0, 1);
        v_cap_counter := v_cap_counter + 1;
    END LOOP;
    
    COMMIT;
END;
/


-- ============================================================================
-- VERIFICATION
-- ============================================================================
SELECT 'Seed data inserted successfully!' as Status FROM DUAL;

SELECT 'Locations' as Entity, COUNT(*) as Count FROM LOCATIONS
UNION ALL
SELECT 'Sensor Clusters', COUNT(*) FROM SENSOR_CLUSTERS
UNION ALL
SELECT 'Sensors', COUNT(*) FROM SENSOR_REGISTRY
UNION ALL
SELECT 'Capabilities', COUNT(*) FROM SENSOR_CAPABILITIES;

-- Show sensor distribution by ward
SELECT l.Name as Ward, COUNT(s.SensorID) as SensorCount
FROM LOCATIONS l
LEFT JOIN SENSOR_REGISTRY s ON l.LocationID = s.LocationID
WHERE l.Type = 'Ward'
GROUP BY l.Name
ORDER BY SensorCount DESC;
