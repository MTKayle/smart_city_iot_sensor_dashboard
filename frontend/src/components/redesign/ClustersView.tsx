import React, { useEffect, useState } from 'react';
import { MapPin } from 'lucide-react';
import { fetchClusterTelemetry } from '../../services/api';
import { useAppContext } from '../../context/AppContext';
import type { SensorCluster, ClusterAnalytics } from '../../types';
import type { MapFocusTarget } from './types';

interface ClusterWithAnalytics extends SensorCluster {
  analytics?: ClusterAnalytics;
}

interface ClustersViewProps {
  onFocusOnMap?: (target: MapFocusTarget) => void;
}

const ClustersView: React.FC<ClustersViewProps> = ({ onFocusOnMap }) => {
  const { clusters: contextClusters } = useAppContext();
  const [clusters, setClusters] = useState<ClusterWithAnalytics[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    const loadAnalytics = async () => {
      if (contextClusters.length === 0) {
        setClusters([]);
        setLoading(false);
        return;
      }

      setLoading(true);

      // Load analytics for all clusters in parallel.
      const results = await Promise.allSettled(
        contextClusters.map((c) => fetchClusterTelemetry(c.clusterId)),
      );

      if (cancelled) return;

      const merged: ClusterWithAnalytics[] = contextClusters.map((c, idx) => {
        const r = results[idx];
        return r.status === 'fulfilled'
          ? { ...c, analytics: r.value }
          : { ...c };
      });

      setClusters(merged);
      setLoading(false);
    };
    loadAnalytics();
    return () => {
      cancelled = true;
    };
  }, [contextClusters]);

  const handleViewOnMap = (cluster: SensorCluster) => {
    if (!onFocusOnMap) return;
    onFocusOnMap({
      lat: cluster.centerLat,
      lng: cluster.centerLng,
      zoom: 14,
      clusterId: cluster.clusterId,
    });
  };

  const getStatusColor = (avgPm25?: number, avgCo2?: number) => {
    if (!avgPm25 && !avgCo2) return 'border-gray-500';
    if ((avgPm25 && avgPm25 > 100) || (avgCo2 && avgCo2 > 2000)) return 'border-red-500';
    if ((avgPm25 && avgPm25 > 50) || (avgCo2 && avgCo2 > 1000)) return 'border-yellow-500';
    return 'border-green-500';
  };

  if (loading) {
    return (
      <div className="clusters-view">
        <div className="view-header">
          <h1 className="view-title">Cụm Vùng</h1>
          <p className="view-subtitle">Đang tải...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="clusters-view">
      <div className="view-header">
        <div>
          <h1 className="view-title">Cụm Vùng</h1>
          <p className="view-subtitle">{clusters.length} cụm cảm biến đã xác định</p>
        </div>
      </div>

      <div className="clusters-grid">
        {clusters.map((cluster) => {
          const analytics = cluster.analytics;
          const avgPm25 = analytics?.avgPM25 || 0;
          const avgTemp = analytics?.avgTemperature || 0;
          const avgHumidity = analytics?.avgHumidity || 0;
          const avgCo2 = analytics?.avgCO2 || 0;
          const avgNoise = analytics?.avgNoise || 0;

          return (
            <div key={cluster.clusterId} className={`cluster-card ${getStatusColor(avgPm25, avgCo2)}`}>
              <div className="cluster-header">
                <h3 className="cluster-name">{cluster.clusterName || cluster.clusterId}</h3>
                <span className="cluster-count">{cluster.sensorCount} cảm biến</span>
              </div>

              <div className="cluster-metrics">
                <div className="cluster-metric-row">
                  <div className="cluster-metric">
                    <span className="metric-label">TB PM2.5</span>
                    <span className={`metric-value ${avgPm25 > 50 ? 'text-yellow-400' : 'text-green-400'}`}>
                      {avgPm25.toFixed(1)} <span className="metric-unit">µg/m³</span>
                    </span>
                  </div>
                  <div className="cluster-metric">
                    <span className="metric-label">TB Nhiệt Độ</span>
                    <span className="metric-value">
                      {avgTemp.toFixed(1)} <span className="metric-unit">°C</span>
                    </span>
                  </div>
                </div>

                <div className="cluster-metric-row">
                  <div className="cluster-metric">
                    <span className="metric-label">TB Độ Ẩm</span>
                    <span className="metric-value">
                      {avgHumidity.toFixed(0)} <span className="metric-unit">%</span>
                    </span>
                  </div>
                  <div className="cluster-metric">
                    <span className="metric-label">TB CO2</span>
                    <span className={`metric-value ${avgCo2 > 1000 ? 'text-yellow-400' : ''}`}>
                      {avgCo2.toFixed(0)} <span className="metric-unit">ppm</span>
                    </span>
                  </div>
                </div>

                <div className="cluster-metric-row">
                  <div className="cluster-metric">
                    <span className="metric-label">TB Tiếng Ồn</span>
                    <span className="metric-value">
                      {avgNoise.toFixed(0)} <span className="metric-unit">dB</span>
                    </span>
                  </div>
                  {analytics?.aqi && (
                    <div className="cluster-metric">
                      <span className="metric-label">AQI</span>
                      <span className={`metric-value ${analytics.aqi > 100 ? 'text-red-400' : 'text-green-400'}`}>
                        {analytics.aqi.toFixed(0)}
                      </span>
                    </div>
                  )}
                </div>
              </div>

              <button
                className="cluster-action-btn"
                onClick={() => handleViewOnMap(cluster)}
              >
                <MapPin className="w-4 h-4" />
                <span>Xem Trên Bản Đồ</span>
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ClustersView;
