-- ============================================================================
-- Translate location names to Vietnamese (idempotent — safe to re-run)
-- ============================================================================

UPDATE LOCATIONS SET Name = N'Thành phố Hồ Chí Minh' WHERE LocationID = 'city_hcmc';

UPDATE LOCATIONS SET Name = N'Quận 1' WHERE LocationID = 'district_q1';
UPDATE LOCATIONS SET Name = N'Quận 3' WHERE LocationID = 'district_q3';
UPDATE LOCATIONS SET Name = N'Quận 5' WHERE LocationID = 'district_q5';

UPDATE LOCATIONS SET Name = N'Phường Bến Nghé'         WHERE LocationID = 'ward_q1_ben_nghe';
UPDATE LOCATIONS SET Name = N'Phường Bến Thành'        WHERE LocationID = 'ward_q1_ben_thanh';
UPDATE LOCATIONS SET Name = N'Phường Nguyễn Thái Bình' WHERE LocationID = 'ward_q1_nguyen_thai_binh';

UPDATE LOCATIONS SET Name = N'Phường 1' WHERE LocationID = 'ward_q3_01';
UPDATE LOCATIONS SET Name = N'Phường 2' WHERE LocationID = 'ward_q3_02';
UPDATE LOCATIONS SET Name = N'Phường 3' WHERE LocationID = 'ward_q3_03';

UPDATE LOCATIONS SET Name = N'Phường 1' WHERE LocationID = 'ward_q5_01';
UPDATE LOCATIONS SET Name = N'Phường 2' WHERE LocationID = 'ward_q5_02';
UPDATE LOCATIONS SET Name = N'Phường 3' WHERE LocationID = 'ward_q5_03';

UPDATE SENSOR_CLUSTERS SET ClusterName = N'Cụm Bắc Quận 1'        WHERE ClusterID = 'cluster_q1_north';
UPDATE SENSOR_CLUSTERS SET ClusterName = N'Cụm Nam Quận 1'        WHERE ClusterID = 'cluster_q1_south';
UPDATE SENSOR_CLUSTERS SET ClusterName = N'Cụm Trung Tâm Quận 3'  WHERE ClusterID = 'cluster_q3_central';
UPDATE SENSOR_CLUSTERS SET ClusterName = N'Cụm Tây Quận 5'        WHERE ClusterID = 'cluster_q5_west';

COMMIT;

-- Verify
SELECT LocationID, Name, Type FROM LOCATIONS ORDER BY Type, LocationID;
SELECT ClusterID, ClusterName FROM SENSOR_CLUSTERS;

EXIT;
