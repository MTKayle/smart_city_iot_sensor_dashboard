"""
Tests for Task 5 – Oracle Client Methods (5.1, 5.2, 5.3)

Tests all new methods using unittest.mock — no live DB required.

Run:
    python -m pytest backend/app/db/test_oracle_client_task5.py -v
"""

import sys, os
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime, date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

def _make_client():
    """Build an OracleClient with _connect() and create_indexes() no-ops."""
    with patch("app.db.oracle_client.oracledb.create_pool"), \
         patch.object(
             __import__("app.db.oracle_client", fromlist=["OracleClient"]).OracleClient,
             "_connect",
             lambda self: None,
         ):
        from app.db.oracle_client import OracleClient
        client = OracleClient.__new__(OracleClient)
        client._pool = MagicMock()
        return client


def _fake_execute_with_retry(operation_name, operation_func):
    """Call operation_func with a fake connection immediately (no retry loop)."""
    fake_conn = MagicMock()
    return operation_func(fake_conn)


def _cursor_returning(rows, columns):
    """Return a mock cursor that yields `rows` and has `description` for `columns`."""
    cursor = MagicMock()
    cursor.description = [(col, None, None, None, None, None, None) for col in columns]
    cursor.fetchone.return_value = rows[0] if rows else None
    cursor.__iter__ = MagicMock(return_value=iter(rows))
    return cursor


# ---------------------------------------------------------------------------
# 5.1 – Sensor Registry
# ---------------------------------------------------------------------------

SENSOR_COLS = [
    "SENSORID", "LOCATIONID", "CLUSTERID",
    "LATITUDE", "LONGITUDE", "ALTITUDE",
    "SENSORMODEL", "FIRMWAREVERSION", "STATUS",
    "INSTALLDATE", "LASTMAINTENANCE", "NEXTMAINTENANCE",
    "REGISTEREDAT", "UPDATEDAT",
    "LOCATIONNAME", "LOCATIONTYPE", "CLUSTERNAME",
]

SENSOR_ROW = (
    "sen_q1_01", "ward_q1_01", "cluster_q1_n",
    10.7756, 106.7019, 5.0,
    "EnviroSense X1", "v2.3.1", "Active",
    date(2025, 1, 15), None, None,
    datetime(2025, 1, 15), datetime(2026, 5, 1),
    "Ben Nghe Ward", "Ward", "Q1 North",
)

CAP_COLS = [
    "CAPABILITYID", "SENSORID", "METRICTYPE", "UNIT",
    "MINRANGE", "MAXRANGE", "ACCURACY",
    "CALIBRATIONDATE", "NEXTCALIBRATION", "ISACTIVE",
]
CAP_ROW = ("cap_001", "sen_q1_01", "CO2", "ppm", 0, 5000, 2.0, None, None, 1)


def test_get_sensor_found():
    print("\n[5.1] test_get_sensor_found")
    client = _make_client()
    client._execute_with_retry = _fake_execute_with_retry

    cursor = _cursor_returning([SENSOR_ROW], SENSOR_COLS)
    client._pool.acquire.return_value.__enter__ = MagicMock(return_value=MagicMock())
    # Patch connection.cursor() inside operation
    def patched_op(name, func):
        conn = MagicMock()
        conn.cursor.return_value = cursor
        return func(conn)

    client._execute_with_retry = patched_op
    result = client.get_sensor("sen_q1_01")

    assert result is not None
    assert result["sensorid"] == "sen_q1_01"
    assert result["status"] == "Active"
    assert result["latitude"] == 10.7756
    print("  ✓ PASS")


def test_get_sensor_not_found():
    print("\n[5.1] test_get_sensor_not_found")
    client = _make_client()

    cursor = _cursor_returning([], SENSOR_COLS)
    def patched_op(name, func):
        conn = MagicMock()
        conn.cursor.return_value = cursor
        return func(conn)

    client._execute_with_retry = patched_op
    result = client.get_sensor("nonexistent")
    assert result is None
    print("  ✓ PASS")


def test_get_sensors_by_location_all():
    print("\n[5.1] test_get_sensors_by_location_all")
    client = _make_client()

    cursor = _cursor_returning([SENSOR_ROW, SENSOR_ROW], SENSOR_COLS)
    def patched_op(name, func):
        conn = MagicMock()
        conn.cursor.return_value = cursor
        return func(conn)

    client._execute_with_retry = patched_op
    results = client.get_sensors_by_location("ward_q1_01")
    assert len(results) == 2
    print("  ✓ PASS")


def test_get_sensors_by_location_with_status_filter():
    print("\n[5.1] test_get_sensors_by_location_with_status_filter")
    client = _make_client()

    cursor = _cursor_returning([SENSOR_ROW], SENSOR_COLS)
    executed_sql = []
    def patched_op(name, func):
        conn = MagicMock()
        cur = _cursor_returning([SENSOR_ROW], SENSOR_COLS)
        cur.execute = lambda sql, params: executed_sql.append((sql, params))
        conn.cursor.return_value = cur
        return func(conn)

    client._execute_with_retry = patched_op
    client.get_sensors_by_location("ward_q1_01", status="Active")
    assert any("status" in str(p) for _, p in executed_sql), "status param passed"
    print("  ✓ PASS")


def test_get_sensors_by_cluster():
    print("\n[5.1] test_get_sensors_by_cluster")
    client = _make_client()

    cursor = _cursor_returning([SENSOR_ROW], SENSOR_COLS)
    def patched_op(name, func):
        conn = MagicMock()
        conn.cursor.return_value = cursor
        return func(conn)

    client._execute_with_retry = patched_op
    results = client.get_sensors_by_cluster("cluster_q1_n")
    assert len(results) == 1
    assert results[0]["clusterid"] == "cluster_q1_n"
    print("  ✓ PASS")


def test_get_sensor_capabilities():
    print("\n[5.1] test_get_sensor_capabilities")
    client = _make_client()

    cursor = _cursor_returning([CAP_ROW, CAP_ROW], CAP_COLS)
    def patched_op(name, func):
        conn = MagicMock()
        conn.cursor.return_value = cursor
        return func(conn)

    client._execute_with_retry = patched_op
    caps = client.get_sensor_capabilities("sen_q1_01")
    assert len(caps) == 2
    assert caps[0]["metrictype"] == "CO2"
    print("  ✓ PASS")


def test_get_sensor_capabilities_empty():
    print("\n[5.1] test_get_sensor_capabilities_empty")
    client = _make_client()

    cursor = _cursor_returning([], CAP_COLS)
    def patched_op(name, func):
        conn = MagicMock()
        conn.cursor.return_value = cursor
        return func(conn)

    client._execute_with_retry = patched_op
    caps = client.get_sensor_capabilities("nonexistent")
    assert caps == []
    print("  ✓ PASS")


# ---------------------------------------------------------------------------
# 5.2 – Location Hierarchy
# ---------------------------------------------------------------------------

LOC_COLS = [
    "LOCATIONID", "NAME", "PARENTID", "TYPE",
    "CENTERLAT", "CENTERLNG", "AREA", "POPULATION",
    "CREATEDAT", "UPDATEDAT", "HIERARCHYLEVEL", "PATH",
]
LOC_ROW = (
    "ward_q1_01", "Ben Nghe", "district_q1", "Ward",
    10.7756, 106.7019, 0.89, 18500,
    datetime(2026, 1, 1), datetime(2026, 5, 1), 2, "city_hcm > district_q1 > ward_q1_01",
)


def test_get_location_found():
    print("\n[5.2] test_get_location_found")
    client = _make_client()

    cursor = _cursor_returning([LOC_ROW], LOC_COLS)
    def patched_op(name, func):
        conn = MagicMock()
        conn.cursor.return_value = cursor
        return func(conn)

    client._execute_with_retry = patched_op
    loc = client.get_location("ward_q1_01")
    assert loc is not None
    assert loc["locationid"] == "ward_q1_01"
    assert loc["type"] == "Ward"
    assert loc["hierarchylevel"] == 2
    print("  ✓ PASS")


def test_get_location_not_found():
    print("\n[5.2] test_get_location_not_found")
    client = _make_client()

    cursor = _cursor_returning([], LOC_COLS)
    def patched_op(name, func):
        conn = MagicMock()
        conn.cursor.return_value = cursor
        return func(conn)

    client._execute_with_retry = patched_op
    loc = client.get_location("missing")
    assert loc is None
    print("  ✓ PASS")


def test_get_all_locations_unfiltered():
    print("\n[5.2] test_get_all_locations_unfiltered")
    client = _make_client()

    rows = [LOC_ROW, LOC_ROW, LOC_ROW]
    cursor = _cursor_returning(rows, LOC_COLS)
    def patched_op(name, func):
        conn = MagicMock()
        conn.cursor.return_value = cursor
        return func(conn)

    client._execute_with_retry = patched_op
    locs = client.get_all_locations()
    assert len(locs) == 3
    print("  ✓ PASS")


def test_get_all_locations_type_filter():
    print("\n[5.2] test_get_all_locations_type_filter — filter by 'Ward'")
    client = _make_client()

    executed = []
    def patched_op(name, func):
        conn = MagicMock()
        cur = _cursor_returning([LOC_ROW], LOC_COLS)
        cur.execute = lambda sql, params: executed.append(params)
        conn.cursor.return_value = cur
        return func(conn)

    client._execute_with_retry = patched_op
    client.get_all_locations(location_type="Ward")
    assert any("Ward" in str(p.values()) for p in executed), "type filter applied"
    print("  ✓ PASS")


def test_get_all_locations_parent_filter():
    print("\n[5.2] test_get_all_locations_parent_filter")
    client = _make_client()

    executed = []
    def patched_op(name, func):
        conn = MagicMock()
        cur = _cursor_returning([LOC_ROW], LOC_COLS)
        cur.execute = lambda sql, params: executed.append(params)
        conn.cursor.return_value = cur
        return func(conn)

    client._execute_with_retry = patched_op
    client.get_all_locations(parent_id="district_q1")
    assert any("district_q1" in str(p.values()) for p in executed), "parent filter applied"
    print("  ✓ PASS")


# ---------------------------------------------------------------------------
# 5.3 – Cluster Methods
# ---------------------------------------------------------------------------

CLUSTER_COLS = [
    "CLUSTERID", "LOCATIONID", "CLUSTERNAME",
    "CENTERLAT", "CENTERLNG", "RADIUS",
    "SENSORCOUNT", "ALGORITHM",
    "CREATEDAT", "UPDATEDAT",
    "LOCATIONNAME", "LOCATIONTYPE",
]
CLUSTER_ROW = (
    "cluster_q1_n", "district_q1", "Q1 North",
    10.778, 106.703, 300.0,
    5, "GRID",
    datetime(2026, 1, 1), datetime(2026, 5, 1),
    "District 1", "District",
)


def test_get_cluster_found():
    print("\n[5.3] test_get_cluster_found")
    client = _make_client()

    cursor = _cursor_returning([CLUSTER_ROW], CLUSTER_COLS)
    def patched_op(name, func):
        conn = MagicMock()
        conn.cursor.return_value = cursor
        return func(conn)

    client._execute_with_retry = patched_op
    cluster = client.get_cluster("cluster_q1_n")
    assert cluster is not None
    assert cluster["clusterid"] == "cluster_q1_n"
    assert cluster["sensorcount"] == 5
    assert cluster["algorithm"] == "GRID"
    print("  ✓ PASS")


def test_get_cluster_not_found():
    print("\n[5.3] test_get_cluster_not_found")
    client = _make_client()

    cursor = _cursor_returning([], CLUSTER_COLS)
    def patched_op(name, func):
        conn = MagicMock()
        conn.cursor.return_value = cursor
        return func(conn)

    client._execute_with_retry = patched_op
    cluster = client.get_cluster("missing")
    assert cluster is None
    print("  ✓ PASS")


def test_get_all_clusters_unfiltered():
    print("\n[5.3] test_get_all_clusters_unfiltered")
    client = _make_client()

    cursor = _cursor_returning([CLUSTER_ROW, CLUSTER_ROW], CLUSTER_COLS)
    def patched_op(name, func):
        conn = MagicMock()
        conn.cursor.return_value = cursor
        return func(conn)

    client._execute_with_retry = patched_op
    clusters = client.get_all_clusters()
    assert len(clusters) == 2
    print("  ✓ PASS")


def test_get_all_clusters_location_filter():
    print("\n[5.3] test_get_all_clusters_location_filter")
    client = _make_client()

    executed = []
    def patched_op(name, func):
        conn = MagicMock()
        cur = _cursor_returning([CLUSTER_ROW], CLUSTER_COLS)
        cur.execute = lambda sql, params: executed.append(params)
        conn.cursor.return_value = cur
        return func(conn)

    client._execute_with_retry = patched_op
    client.get_all_clusters(location_id="district_q1")
    assert any("district_q1" in str(p.values()) for p in executed)
    print("  ✓ PASS")


def test_update_cluster_sensor_count_success():
    print("\n[5.3] test_update_cluster_sensor_count_success")
    client = _make_client()

    def patched_op(name, func):
        conn = MagicMock()
        cur = MagicMock()
        cur.rowcount = 1  # 1 row updated
        conn.cursor.return_value = cur
        return func(conn)

    client._execute_with_retry = patched_op
    ok = client.update_cluster_sensor_count("cluster_q1_n")
    assert ok is True
    print("  ✓ PASS")


def test_update_cluster_sensor_count_not_found():
    print("\n[5.3] test_update_cluster_sensor_count_not_found — cluster absent")
    client = _make_client()

    def patched_op(name, func):
        conn = MagicMock()
        cur = MagicMock()
        cur.rowcount = 0  # nothing updated
        conn.cursor.return_value = cur
        return func(conn)

    client._execute_with_retry = patched_op
    ok = client.update_cluster_sensor_count("nonexistent")
    assert ok is False
    print("  ✓ PASS")


def test_update_cluster_sensor_count_db_error():
    print("\n[5.3] test_update_cluster_sensor_count_db_error — returns False")
    import oracledb

    client = _make_client()

    def patched_op(name, func):
        conn = MagicMock()
        cur = MagicMock()
        cur.execute.side_effect = oracledb.DatabaseError("ora error")
        conn.cursor.return_value = cur
        return func(conn)

    client._execute_with_retry = patched_op
    ok = client.update_cluster_sensor_count("cluster_q1_n")
    assert ok is False
    print("  ✓ PASS")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("Task 5 – Oracle Client Tests (5.1 / 5.2 / 5.3)")
    print("=" * 60)

    # 5.1
    test_get_sensor_found()
    test_get_sensor_not_found()
    test_get_sensors_by_location_all()
    test_get_sensors_by_location_with_status_filter()
    test_get_sensors_by_cluster()
    test_get_sensor_capabilities()
    test_get_sensor_capabilities_empty()

    # 5.2
    test_get_location_found()
    test_get_location_not_found()
    test_get_all_locations_unfiltered()
    test_get_all_locations_type_filter()
    test_get_all_locations_parent_filter()

    # 5.3
    test_get_cluster_found()
    test_get_cluster_not_found()
    test_get_all_clusters_unfiltered()
    test_get_all_clusters_location_filter()
    test_update_cluster_sensor_count_success()
    test_update_cluster_sensor_count_not_found()
    test_update_cluster_sensor_count_db_error()

    print("\n" + "=" * 60)
    print("All tests completed.")
    print("=" * 60)
