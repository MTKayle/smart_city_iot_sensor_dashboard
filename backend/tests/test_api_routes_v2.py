"""
Tests for Task 10 — New API Endpoints.

10.1 Location endpoints
10.2 Cluster endpoints
10.3 Sensor registry endpoints
10.4 Updated telemetry endpoints (PM2.5, Humidity, AQI, cluster/geo filtering)
"""

import pytest
from datetime import datetime, date, timedelta, timezone
from unittest.mock import Mock, patch, MagicMock

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# ---------------------------------------------------------------------------
# Shared fixture data
# ---------------------------------------------------------------------------

LOCATION_ROW = {
    "locationid": "ward_q1_01", "name": "Ward 1",
    "parentid": "district_q1", "type": "Ward",
    "centerlat": 10.776, "centerlng": 106.701,
    "area": 0.89, "population": 18500,
}

SENSOR_ROW = {
    "sensorid": "sen_01", "locationid": "ward_q1_01",
    "clusterid": "cluster_01", "latitude": 10.776, "longitude": 106.701,
    "altitude": 5.0, "sensormodel": "EnviroX", "firmwareversion": "v2.1",
    "status": "Active", "installdate": date(2025, 1, 15),
    "registeredat": datetime(2025, 1, 15, 0, 0, 0),
}

CLUSTER_ROW = {
    "clusterid": "cluster_01", "locationid": "ward_q1_01",
    "clustername": "North Cluster", "centerlat": 10.777, "centerlng": 106.702,
    "radius": 300.0, "sensorcount": 3, "algorithm": "GRID",
}

CAPABILITY_ROW = {
    "capabilityid": "cap_01", "sensorid": "sen_01",
    "metrictype": "CO2", "unit": "ppm",
    "minrange": 0.0, "maxrange": 5000.0, "accuracy": 2.0,
    "calibrationdate": date(2025, 1, 1), "nextcalibration": date(2025, 7, 1),
    "isactive": True,
}

TELEMETRY_DOC_V2 = {
    "sensorId": "sen_01", "locationId": "ward_q1_01", "clusterId": "cluster_01",
    "timestamp": datetime(2026, 5, 3, 10, 0, 0, tzinfo=timezone.utc),
    "data": {"co2": 480.0, "noise": 62.0, "temperature": 27.0, "pm25": 22.5, "humidity": 72.0},
}


# ===========================================================================
# 10.1 — Location endpoints
# ===========================================================================

class TestLocationEndpoints:

    @patch("app.api.routes.get_oracle_client")
    def test_get_locations(self, mock_oracle):
        mock_oracle.return_value.get_location_hierarchy.return_value = [LOCATION_ROW]
        resp = client.get("/api/locations")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["locationId"] == "ward_q1_01"
        assert data[0]["type"] == "Ward"

    @patch("app.api.routes.get_oracle_client")
    def test_get_locations_db_error(self, mock_oracle):
        mock_oracle.return_value.get_location_hierarchy.side_effect = RuntimeError("DB down")
        resp = client.get("/api/locations")
        assert resp.status_code == 500

    @patch("app.api.routes.get_oracle_client")
    def test_get_location_by_id(self, mock_oracle):
        mock_oracle.return_value.get_location.return_value = LOCATION_ROW
        resp = client.get("/api/locations/ward_q1_01")
        assert resp.status_code == 200
        assert resp.json()["locationId"] == "ward_q1_01"

    @patch("app.api.routes.get_oracle_client")
    def test_get_location_not_found(self, mock_oracle):
        mock_oracle.return_value.get_location.return_value = None
        resp = client.get("/api/locations/bad_id")
        assert resp.status_code == 404

    @patch("app.api.routes.get_oracle_client")
    def test_get_location_hierarchy_endpoint(self, mock_oracle):
        parent_row = {"locationid": "district_q1", "name": "District 1",
                      "parentid": None, "type": "District"}
        mock_oracle.return_value.get_location.return_value = LOCATION_ROW
        mock_oracle.return_value.get_location_hierarchy.return_value = [parent_row, LOCATION_ROW]
        resp = client.get("/api/locations/ward_q1_01/hierarchy")
        assert resp.status_code == 200
        data = resp.json()
        assert "location" in data
        assert "ancestors" in data
        assert "children" in data

    @patch("app.api.routes.get_oracle_client")
    def test_get_location_sensors(self, mock_oracle):
        mock_oracle.return_value.get_sensors.return_value = [SENSOR_ROW]
        resp = client.get("/api/locations/ward_q1_01/sensors")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["locationId"] == "ward_q1_01"

    @patch("app.api.routes.get_oracle_client")
    def test_get_location_sensors_status_filter(self, mock_oracle):
        offline_row = {**SENSOR_ROW, "sensorid": "sen_off", "status": "Offline"}
        mock_oracle.return_value.get_sensors.return_value = [SENSOR_ROW, offline_row]
        resp = client.get("/api/locations/ward_q1_01/sensors?status=Active")
        assert resp.status_code == 200
        data = resp.json()
        assert all(s["status"] == "Active" for s in data)


# ===========================================================================
# 10.2 — Cluster endpoints
# ===========================================================================

class TestClusterEndpoints:

    @patch("app.api.routes.get_oracle_client")
    def test_get_clusters(self, mock_oracle):
        mock_oracle.return_value.get_all_clusters.return_value = [CLUSTER_ROW]
        resp = client.get("/api/clusters")
        assert resp.status_code == 200
        assert resp.json()[0]["clusterId"] == "cluster_01"

    @patch("app.api.routes.get_oracle_client")
    def test_get_clusters_location_filter(self, mock_oracle):
        other = {**CLUSTER_ROW, "clusterid": "c_other", "locationid": "other_loc"}
        mock_oracle.return_value.get_all_clusters.return_value = [CLUSTER_ROW, other]
        resp = client.get("/api/clusters?location_id=ward_q1_01")
        assert resp.status_code == 200
        data = resp.json()
        assert all(c["locationId"] == "ward_q1_01" for c in data)

    @patch("app.api.routes.get_oracle_client")
    def test_get_cluster_by_id(self, mock_oracle):
        mock_oracle.return_value.get_cluster.return_value = CLUSTER_ROW
        resp = client.get("/api/clusters/cluster_01")
        assert resp.status_code == 200
        assert resp.json()["clusterId"] == "cluster_01"

    @patch("app.api.routes.get_oracle_client")
    def test_get_cluster_not_found(self, mock_oracle):
        mock_oracle.return_value.get_cluster.return_value = None
        resp = client.get("/api/clusters/no_such")
        assert resp.status_code == 404

    @patch("app.api.routes.get_oracle_client")
    def test_get_cluster_sensors(self, mock_oracle):
        mock_oracle.return_value.get_sensors_by_cluster.return_value = [SENSOR_ROW]
        resp = client.get("/api/clusters/cluster_01/sensors")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    @patch("app.api.routes.get_analytics_service")
    def test_get_cluster_telemetry(self, mock_svc):
        from app.models.analytics import ClusterAnalytics
        ca = ClusterAnalytics(
            clusterId="cluster_01", sensorCount=2, readingCount=20,
            avgCO2=500.0, avgNoise=65.0, avgTemperature=27.0,
            avgPM25=25.0, aqi=82, aqi_category="Moderate", cleanScore=72.0,
        )
        mock_svc.return_value.calculate_cluster_analytics.return_value = ca
        resp = client.get("/api/clusters/cluster_01/telemetry")
        assert resp.status_code == 200
        data = resp.json()
        assert data["clusterId"] == "cluster_01"
        assert data["aqi"] == 82

    @patch("app.api.routes.get_analytics_service")
    def test_get_cluster_telemetry_not_found(self, mock_svc):
        mock_svc.return_value.calculate_cluster_analytics.return_value = None
        resp = client.get("/api/clusters/bad/telemetry")
        assert resp.status_code == 404

    @patch("app.api.routes.identify_hotspots")
    def test_get_hotspots(self, mock_hotspots):
        mock_hotspots.return_value = [
            {"cell_id": "10:106", "center_lat": 10.77, "center_lng": 106.70,
             "avg_value": 1200.0, "reading_count": 5, "sensor_ids": ["s1"], "metric_type": "co2"}
        ]
        resp = client.get("/api/clusters/hotspots?metric=co2&threshold=1000")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 1
        assert data["hotspots"][0]["avg_value"] == 1200.0

    def test_get_hotspots_invalid_metric(self):
        resp = client.get("/api/clusters/hotspots?metric=invalid_metric")
        assert resp.status_code == 400


# ===========================================================================
# 10.3 — Sensor registry endpoints
# ===========================================================================

class TestSensorEndpoints:

    @patch("app.api.routes.get_oracle_client")
    def test_get_sensors(self, mock_oracle):
        mock_oracle.return_value.get_sensors.return_value = [SENSOR_ROW]
        resp = client.get("/api/sensors")
        assert resp.status_code == 200
        data = resp.json()
        assert data[0]["sensorId"] == "sen_01"
        assert data[0]["latitude"] == 10.776

    @patch("app.api.routes.get_oracle_client")
    def test_get_sensors_by_cluster(self, mock_oracle):
        mock_oracle.return_value.get_sensors_by_cluster.return_value = [SENSOR_ROW]
        resp = client.get("/api/sensors?cluster_id=cluster_01")
        assert resp.status_code == 200
        mock_oracle.return_value.get_sensors_by_cluster.assert_called_once_with(
            "cluster_01", status=None
        )

    @patch("app.api.routes.get_oracle_client")
    def test_get_sensor_by_id(self, mock_oracle):
        mock_oracle.return_value.get_sensor.return_value = SENSOR_ROW
        resp = client.get("/api/sensors/sen_01")
        assert resp.status_code == 200
        assert resp.json()["sensorId"] == "sen_01"
        assert resp.json()["sensorModel"] == "EnviroX"

    @patch("app.api.routes.get_oracle_client")
    def test_get_sensor_not_found(self, mock_oracle):
        mock_oracle.return_value.get_sensor.return_value = None
        resp = client.get("/api/sensors/no_such")
        assert resp.status_code == 404

    @patch("app.api.routes.get_oracle_client")
    def test_get_sensor_capabilities(self, mock_oracle):
        mock_oracle.return_value.get_sensor_capabilities.return_value = [CAPABILITY_ROW]
        resp = client.get("/api/sensors/sen_01/capabilities")
        assert resp.status_code == 200
        data = resp.json()
        assert data[0]["metricType"] == "CO2"
        assert data[0]["unit"] == "ppm"

    @patch("app.api.routes.get_oracle_client")
    def test_get_sensor_health(self, mock_oracle):
        oracle = Mock()
        oracle.get_sensor.return_value = {**SENSOR_ROW, "lastmaintenance": None, "nextmaintenance": None}
        oracle.get_sensor_health_logs = Mock(return_value=[])
        mock_oracle.return_value = oracle
        resp = client.get("/api/sensors/sen_01/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["sensorId"] == "sen_01"
        assert data["status"] == "Active"
        assert "healthLogs" in data

    @patch("app.api.routes.get_oracle_client")
    def test_get_sensor_health_not_found(self, mock_oracle):
        mock_oracle.return_value.get_sensor.return_value = None
        resp = client.get("/api/sensors/bad/health")
        assert resp.status_code == 404

    @patch("app.api.routes.find_nearby_sensors")
    def test_get_nearby_sensors(self, mock_nearby):
        mock_nearby.return_value = [
            {"sensorId": "sen_01", "distance_km": 0.25, "latitude": 10.776, "longitude": 106.701}
        ]
        resp = client.get("/api/sensors/nearby?lat=10.776&lng=106.701&radius_km=1.0")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 1
        assert data["sensors"][0]["sensorId"] == "sen_01"

    def test_get_nearby_sensors_missing_params(self):
        resp = client.get("/api/sensors/nearby")  # lat/lng required
        assert resp.status_code == 422

    @patch("app.api.routes.get_analytics_service")
    def test_get_sensor_analytics(self, mock_svc):
        from app.models.analytics import Analytics, MovingAverage
        mock_analytics = Analytics(
            sensorId="sen_01",
            co2_moving_avg=MovingAverage(metric="CO2", values=[480.0], average=480.0, window_size=1),
            noise_moving_avg=MovingAverage(metric="Noise", values=[62.0], average=62.0, window_size=1),
            temperature_moving_avg=MovingAverage(metric="Temperature", values=[27.0], average=27.0, window_size=1),
            pm25_moving_avg=MovingAverage(metric="PM25", values=[22.5], average=22.5, window_size=1),
            aqi=75, aqi_category="Moderate",
        )
        mock_svc.return_value.calculate_moving_average.return_value = mock_analytics
        resp = client.get("/api/sensors/sen_01/analytics")
        assert resp.status_code == 200
        data = resp.json()
        assert data["aqi"] == 75
        assert data["pm25_moving_avg"]["average"] == 22.5


# ===========================================================================
# 10.4 — Updated telemetry endpoints
# ===========================================================================

class TestTelemetryEndpoints:

    @patch("app.api.routes.get_mongodb_client")
    def test_get_telemetry_v2_fields(self, mock_mongo):
        """PM2.5, Humidity, and AQI are included in the response."""
        mock_mongo.return_value.query_telemetry_aggregated.return_value = [TELEMETRY_DOC_V2]
        resp = client.get("/api/telemetry/sen_01")
        assert resp.status_code == 200
        data = resp.json()[0]
        assert data["pm25"] == 22.5
        assert data["humidity"] == 72.0
        assert data["aqi"] is not None
        assert data["aqi_category"] is not None

    @patch("app.api.routes.get_mongodb_client")
    def test_get_telemetry_backward_compat(self, mock_mongo):
        """Legacy flat-layout docs still return co2/noise/temperature."""
        flat_doc = {
            "sensorId": "sen_01", "locationId": "ward_q1_01",
            "timestamp": datetime(2026, 5, 3, 10, 0, 0, tzinfo=timezone.utc),
            "co2": 450.0, "noise": 60.0, "temperature": 26.0,
        }
        mock_mongo.return_value.query_telemetry_aggregated.return_value = [flat_doc]
        resp = client.get("/api/telemetry/sen_01")
        assert resp.status_code == 200
        data = resp.json()[0]
        assert data["co2"] == 450.0
        assert data["noise"] == 60.0

    def test_get_telemetry_invalid_time_range(self):
        end = datetime.now(timezone.utc)
        start = end + timedelta(hours=1)
        s_str = start.isoformat().replace("+", "%2B")
        e_str = end.isoformat().replace("+", "%2B")
        resp  = client.get(f"/api/telemetry/sen_01?start_time={s_str}&end_time={e_str}")
        assert resp.status_code == 400
        assert "start_time must be less than end_time" in resp.json()["detail"]

    @patch("app.api.routes.get_mongodb_client")
    def test_get_telemetry_defaults_to_24h(self, mock_mongo):
        mock_mongo.return_value.query_telemetry_aggregated.return_value = []
        resp = client.get("/api/telemetry/sen_01")
        assert resp.status_code == 200
        call_kw = mock_mongo.return_value.query_telemetry_aggregated.call_args[1]
        assert call_kw["start_time"] is not None
        assert call_kw["end_time"] is not None

    @patch("app.api.routes.get_oracle_client")
    @patch("app.api.routes.get_mongodb_client")
    def test_get_telemetry_cluster_filter_match(self, mock_mongo, mock_oracle):
        """Cluster filter passes when sensor belongs to the given cluster."""
        mock_oracle.return_value.get_sensor.return_value = SENSOR_ROW
        mock_mongo.return_value.query_telemetry_aggregated.return_value = [TELEMETRY_DOC_V2]
        resp = client.get("/api/telemetry/sen_01?cluster_id=cluster_01")
        assert resp.status_code == 200

    @patch("app.api.routes.get_oracle_client")
    @patch("app.api.routes.get_mongodb_client")
    def test_get_telemetry_cluster_filter_mismatch(self, mock_mongo, mock_oracle):
        """Cluster filter blocks when sensor is in a different cluster."""
        mock_oracle.return_value.get_sensor.return_value = SENSOR_ROW  # clusterid = cluster_01
        resp = client.get("/api/telemetry/sen_01?cluster_id=other_cluster")
        assert resp.status_code == 404

    @patch("app.api.routes.get_oracle_client")
    @patch("app.api.routes.get_mongodb_client")
    def test_get_telemetry_geospatial_filter_inside(self, mock_mongo, mock_oracle):
        """Geo filter passes when sensor is within radius."""
        mock_oracle.return_value.get_sensor.return_value = SENSOR_ROW
        mock_mongo.return_value.query_telemetry_aggregated.return_value = [TELEMETRY_DOC_V2]
        # same lat/lng as SENSOR_ROW → distance = 0
        resp = client.get("/api/telemetry/sen_01?near_lat=10.776&near_lng=106.701&near_km=1.0")
        assert resp.status_code == 200

    @patch("app.api.routes.get_oracle_client")
    @patch("app.api.routes.get_mongodb_client")
    def test_get_telemetry_geospatial_filter_outside(self, mock_mongo, mock_oracle):
        """Geo filter blocks when sensor is beyond radius."""
        mock_oracle.return_value.get_sensor.return_value = SENSOR_ROW  # at 10.776, 106.701
        resp = client.get("/api/telemetry/sen_01?near_lat=21.0&near_lng=105.8&near_km=1.0")
        assert resp.status_code == 404


# ===========================================================================
# Backward-compat: pre-existing endpoints still work
# ===========================================================================

class TestBackwardCompat:

    def test_health(self):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

    @patch("app.api.routes.get_oracle_client")
    def test_alerts_still_work(self, mock_oracle):
        mock_oracle.return_value.get_alerts.return_value = [
            {"alertid": "a1", "sensorid": "s1", "metrictype": "CO2",
             "value": 1500.0, "alertlevel": "HIGH", "createdat": datetime.now(),
             "locationid": "w1"}
        ]
        resp = client.get("/api/alerts")
        assert resp.status_code == 200

    @patch("app.api.routes.get_oracle_client")
    def test_leaderboard_still_works(self, mock_oracle):
        mock_oracle.return_value.get_leaderboard.return_value = [
            {"locationid": "w1", "locationname": "Ward 1", "avgco2": 400.0,
             "avgnoise": 55.0, "avgtemperature": 26.0, "cleanscore": 78.0, "rank": 1}
        ]
        resp = client.get("/api/leaderboard")
        assert resp.status_code == 200
        data = resp.json()
        assert data[0]["cleanScore"] == 78.0

    def test_invalid_alert_level_rejected(self):
        resp = client.get("/api/alerts?level=INVALID")
        assert resp.status_code == 400
