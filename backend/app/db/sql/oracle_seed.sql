-- Oracle Database Seed Data — HCMC 10 Districts
-- Smart City IoT Sensor Dashboard
-- Structure: 1 City > 10 Districts > 30 Wards > 90 Sensors

-- ============================================================================
-- CLEANUP (safe — ignores errors if tables are empty)
-- ============================================================================
DELETE FROM ALERTS;
DELETE FROM SENSOR_REGISTRY;
DELETE FROM TELEMETRY_SUMMARY;
DELETE FROM LOCATIONS WHERE Type = 'Ward';
DELETE FROM LOCATIONS WHERE Type = 'District';
DELETE FROM LOCATIONS WHERE Type = 'City';

COMMIT;

-- ============================================================================
-- CITY
-- ============================================================================
INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type) VALUES ('city_hcm', 'TP. Hồ Chí Minh', NULL, 'City');

-- ============================================================================
-- 10 DISTRICTS
-- ============================================================================
INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type) VALUES ('dist_q1',  'Quận 1',           'city_hcm', 'District');
INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type) VALUES ('dist_q3',  'Quận 3',           'city_hcm', 'District');
INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type) VALUES ('dist_q5',  'Quận 5',           'city_hcm', 'District');
INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type) VALUES ('dist_q7',  'Quận 7',           'city_hcm', 'District');
INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type) VALUES ('dist_q10', 'Quận 10',          'city_hcm', 'District');
INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type) VALUES ('dist_q12', 'Quận 12',          'city_hcm', 'District');
INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type) VALUES ('dist_bth', 'Quận Bình Thạnh',  'city_hcm', 'District');
INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type) VALUES ('dist_gv',  'Quận Gò Vấp',      'city_hcm', 'District');
INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type) VALUES ('dist_tb',  'Quận Tân Bình',    'city_hcm', 'District');
INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type) VALUES ('dist_td',  'TP. Thủ Đức',      'city_hcm', 'District');

-- ============================================================================
-- 30 WARDS (3 per district)
-- ============================================================================
-- Quận 1
INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type) VALUES ('ward_q1_01', 'P. Bến Nghé',   'dist_q1', 'Ward');
INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type) VALUES ('ward_q1_02', 'P. Bến Thành',  'dist_q1', 'Ward');
INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type) VALUES ('ward_q1_03', 'P. Đa Kao',     'dist_q1', 'Ward');
-- Quận 3
INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type) VALUES ('ward_q3_01', 'P. Võ Thị Sáu', 'dist_q3', 'Ward');
INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type) VALUES ('ward_q3_02', 'P. 9',          'dist_q3', 'Ward');
INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type) VALUES ('ward_q3_03', 'P. 13',         'dist_q3', 'Ward');
-- Quận 5
INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type) VALUES ('ward_q5_01', 'P. 1',          'dist_q5', 'Ward');
INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type) VALUES ('ward_q5_02', 'P. 4',          'dist_q5', 'Ward');
INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type) VALUES ('ward_q5_03', 'P. 9',          'dist_q5', 'Ward');
-- Quận 7
INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type) VALUES ('ward_q7_01', 'P. Tân Phong',  'dist_q7', 'Ward');
INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type) VALUES ('ward_q7_02', 'P. Tân Kiểng',  'dist_q7', 'Ward');
INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type) VALUES ('ward_q7_03', 'P. Phú Mỹ',     'dist_q7', 'Ward');
-- Quận 10
INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type) VALUES ('ward_q10_01', 'P. 1',         'dist_q10', 'Ward');
INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type) VALUES ('ward_q10_02', 'P. 9',         'dist_q10', 'Ward');
INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type) VALUES ('ward_q10_03', 'P. 14',        'dist_q10', 'Ward');
-- Quận 12
INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type) VALUES ('ward_q12_01', 'P. Tân Chánh Hiệp', 'dist_q12', 'Ward');
INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type) VALUES ('ward_q12_02', 'P. An Phú Đông',     'dist_q12', 'Ward');
INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type) VALUES ('ward_q12_03', 'P. Thạnh Lộc',       'dist_q12', 'Ward');
-- Bình Thạnh
INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type) VALUES ('ward_bth_01', 'P. 1',         'dist_bth', 'Ward');
INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type) VALUES ('ward_bth_02', 'P. 13',        'dist_bth', 'Ward');
INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type) VALUES ('ward_bth_03', 'P. 25',        'dist_bth', 'Ward');
-- Gò Vấp
INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type) VALUES ('ward_gv_01', 'P. 1',          'dist_gv', 'Ward');
INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type) VALUES ('ward_gv_02', 'P. 5',          'dist_gv', 'Ward');
INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type) VALUES ('ward_gv_03', 'P. 12',         'dist_gv', 'Ward');
-- Tân Bình
INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type) VALUES ('ward_tb_01', 'P. 1',          'dist_tb', 'Ward');
INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type) VALUES ('ward_tb_02', 'P. 4',          'dist_tb', 'Ward');
INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type) VALUES ('ward_tb_03', 'P. 15',         'dist_tb', 'Ward');
-- Thủ Đức
INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type) VALUES ('ward_td_01', 'P. Thảo Điền',  'dist_td', 'Ward');
INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type) VALUES ('ward_td_02', 'P. An Phú',     'dist_td', 'Ward');
INSERT INTO LOCATIONS (LocationID, Name, ParentID, Type) VALUES ('ward_td_03', 'P. Linh Trung', 'dist_td', 'Ward');

-- ============================================================================
-- 90 SENSORS (3 per ward: CO2, Noise, Temperature)
-- ============================================================================
-- Quận 1 - Ward 1
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_q1_01_co2', 'ward_q1_01', 'CO2');
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_q1_01_noi', 'ward_q1_01', 'Noise');
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_q1_01_tmp', 'ward_q1_01', 'Temperature');
-- Quận 1 - Ward 2
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_q1_02_co2', 'ward_q1_02', 'CO2');
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_q1_02_noi', 'ward_q1_02', 'Noise');
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_q1_02_tmp', 'ward_q1_02', 'Temperature');
-- Quận 1 - Ward 3
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_q1_03_co2', 'ward_q1_03', 'CO2');
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_q1_03_noi', 'ward_q1_03', 'Noise');
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_q1_03_tmp', 'ward_q1_03', 'Temperature');
-- Quận 3 - Ward 1
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_q3_01_co2', 'ward_q3_01', 'CO2');
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_q3_01_noi', 'ward_q3_01', 'Noise');
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_q3_01_tmp', 'ward_q3_01', 'Temperature');
-- Quận 3 - Ward 2
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_q3_02_co2', 'ward_q3_02', 'CO2');
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_q3_02_noi', 'ward_q3_02', 'Noise');
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_q3_02_tmp', 'ward_q3_02', 'Temperature');
-- Quận 3 - Ward 3
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_q3_03_co2', 'ward_q3_03', 'CO2');
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_q3_03_noi', 'ward_q3_03', 'Noise');
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_q3_03_tmp', 'ward_q3_03', 'Temperature');
-- Quận 5 - Ward 1
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_q5_01_co2', 'ward_q5_01', 'CO2');
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_q5_01_noi', 'ward_q5_01', 'Noise');
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_q5_01_tmp', 'ward_q5_01', 'Temperature');
-- Quận 5 - Ward 2
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_q5_02_co2', 'ward_q5_02', 'CO2');
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_q5_02_noi', 'ward_q5_02', 'Noise');
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_q5_02_tmp', 'ward_q5_02', 'Temperature');
-- Quận 5 - Ward 3
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_q5_03_co2', 'ward_q5_03', 'CO2');
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_q5_03_noi', 'ward_q5_03', 'Noise');
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_q5_03_tmp', 'ward_q5_03', 'Temperature');
-- Quận 7 - Ward 1
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_q7_01_co2', 'ward_q7_01', 'CO2');
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_q7_01_noi', 'ward_q7_01', 'Noise');
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_q7_01_tmp', 'ward_q7_01', 'Temperature');
-- Quận 7 - Ward 2
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_q7_02_co2', 'ward_q7_02', 'CO2');
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_q7_02_noi', 'ward_q7_02', 'Noise');
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_q7_02_tmp', 'ward_q7_02', 'Temperature');
-- Quận 7 - Ward 3
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_q7_03_co2', 'ward_q7_03', 'CO2');
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_q7_03_noi', 'ward_q7_03', 'Noise');
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_q7_03_tmp', 'ward_q7_03', 'Temperature');
-- Quận 10 - Ward 1
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_q10_01_co2', 'ward_q10_01', 'CO2');
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_q10_01_noi', 'ward_q10_01', 'Noise');
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_q10_01_tmp', 'ward_q10_01', 'Temperature');
-- Quận 10 - Ward 2
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_q10_02_co2', 'ward_q10_02', 'CO2');
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_q10_02_noi', 'ward_q10_02', 'Noise');
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_q10_02_tmp', 'ward_q10_02', 'Temperature');
-- Quận 10 - Ward 3
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_q10_03_co2', 'ward_q10_03', 'CO2');
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_q10_03_noi', 'ward_q10_03', 'Noise');
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_q10_03_tmp', 'ward_q10_03', 'Temperature');
-- Quận 12 - Ward 1
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_q12_01_co2', 'ward_q12_01', 'CO2');
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_q12_01_noi', 'ward_q12_01', 'Noise');
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_q12_01_tmp', 'ward_q12_01', 'Temperature');
-- Quận 12 - Ward 2
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_q12_02_co2', 'ward_q12_02', 'CO2');
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_q12_02_noi', 'ward_q12_02', 'Noise');
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_q12_02_tmp', 'ward_q12_02', 'Temperature');
-- Quận 12 - Ward 3
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_q12_03_co2', 'ward_q12_03', 'CO2');
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_q12_03_noi', 'ward_q12_03', 'Noise');
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_q12_03_tmp', 'ward_q12_03', 'Temperature');
-- Bình Thạnh - Ward 1
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_bth_01_co2', 'ward_bth_01', 'CO2');
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_bth_01_noi', 'ward_bth_01', 'Noise');
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_bth_01_tmp', 'ward_bth_01', 'Temperature');
-- Bình Thạnh - Ward 2
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_bth_02_co2', 'ward_bth_02', 'CO2');
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_bth_02_noi', 'ward_bth_02', 'Noise');
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_bth_02_tmp', 'ward_bth_02', 'Temperature');
-- Bình Thạnh - Ward 3
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_bth_03_co2', 'ward_bth_03', 'CO2');
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_bth_03_noi', 'ward_bth_03', 'Noise');
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_bth_03_tmp', 'ward_bth_03', 'Temperature');
-- Gò Vấp - Ward 1
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_gv_01_co2', 'ward_gv_01', 'CO2');
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_gv_01_noi', 'ward_gv_01', 'Noise');
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_gv_01_tmp', 'ward_gv_01', 'Temperature');
-- Gò Vấp - Ward 2
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_gv_02_co2', 'ward_gv_02', 'CO2');
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_gv_02_noi', 'ward_gv_02', 'Noise');
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_gv_02_tmp', 'ward_gv_02', 'Temperature');
-- Gò Vấp - Ward 3
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_gv_03_co2', 'ward_gv_03', 'CO2');
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_gv_03_noi', 'ward_gv_03', 'Noise');
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_gv_03_tmp', 'ward_gv_03', 'Temperature');
-- Tân Bình - Ward 1
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_tb_01_co2', 'ward_tb_01', 'CO2');
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_tb_01_noi', 'ward_tb_01', 'Noise');
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_tb_01_tmp', 'ward_tb_01', 'Temperature');
-- Tân Bình - Ward 2
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_tb_02_co2', 'ward_tb_02', 'CO2');
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_tb_02_noi', 'ward_tb_02', 'Noise');
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_tb_02_tmp', 'ward_tb_02', 'Temperature');
-- Tân Bình - Ward 3
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_tb_03_co2', 'ward_tb_03', 'CO2');
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_tb_03_noi', 'ward_tb_03', 'Noise');
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_tb_03_tmp', 'ward_tb_03', 'Temperature');
-- Thủ Đức - Ward 1
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_td_01_co2', 'ward_td_01', 'CO2');
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_td_01_noi', 'ward_td_01', 'Noise');
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_td_01_tmp', 'ward_td_01', 'Temperature');
-- Thủ Đức - Ward 2
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_td_02_co2', 'ward_td_02', 'CO2');
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_td_02_noi', 'ward_td_02', 'Noise');
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_td_02_tmp', 'ward_td_02', 'Temperature');
-- Thủ Đức - Ward 3
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_td_03_co2', 'ward_td_03', 'CO2');
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_td_03_noi', 'ward_td_03', 'Noise');
INSERT INTO SENSOR_REGISTRY (SensorID, LocationID, SensorType) VALUES ('sen_td_03_tmp', 'ward_td_03', 'Temperature');

COMMIT;
