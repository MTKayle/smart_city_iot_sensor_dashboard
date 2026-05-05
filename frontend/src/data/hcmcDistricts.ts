/**
 * Ho Chi Minh City District Data — 10 Districts
 * 
 * Contains GPS coordinates, GeoJSON boundary polygons,
 * district-ward-sensor mappings, and threshold config.
 */

// ============================================================================
// THRESHOLD CONFIGURATION
// ============================================================================
export const THRESHOLDS = {
  co2: { warning: 800, danger: 1000, unit: 'ppm', label: 'CO₂' },
  noise: { warning: 70, danger: 85, unit: 'dB', label: 'Tiếng ồn' },
  temperature: { warning: 35, danger: 40, unit: '°C', label: 'Nhiệt độ' },
  pm25: { warning: 35.5, danger: 55.5, unit: 'μg/m³', label: 'PM2.5' },
  humidity: { warning: 80, danger: 90, unit: '%', label: 'Độ ẩm' },
};

// ============================================================================
// INTERFACES
// ============================================================================
export interface DistrictData {
  id: string;
  name: string;
  nameEn: string;
  center: [number, number]; // [lng, lat]
  wards: WardData[];
}

export interface WardData {
  id: string;
  name: string;
  sensors: SensorRef[];
}

export interface SensorRef {
  id: string;
  type: 'CO2' | 'Noise' | 'Temperature' | 'PM2.5' | 'Humidity';
}

// ============================================================================
// 10 DISTRICTS WITH WARDS AND SENSORS
// ============================================================================
export const HCMC_DISTRICTS: DistrictData[] = [
  {
    id: 'dist_q1', name: 'Quận 1', nameEn: 'District 1',
    center: [106.6955, 10.7765],
    wards: [
      { id: 'ward_q1_01', name: 'P. Bến Nghé', sensors: [
        { id: 'sen_q1_01_co2', type: 'CO2' }, { id: 'sen_q1_01_noi', type: 'Noise' }, { id: 'sen_q1_01_tmp', type: 'Temperature' },
      ]},
      { id: 'ward_q1_02', name: 'P. Bến Thành', sensors: [
        { id: 'sen_q1_02_co2', type: 'CO2' }, { id: 'sen_q1_02_noi', type: 'Noise' }, { id: 'sen_q1_02_tmp', type: 'Temperature' },
      ]},
      { id: 'ward_q1_03', name: 'P. Đa Kao', sensors: [
        { id: 'sen_q1_03_co2', type: 'CO2' }, { id: 'sen_q1_03_noi', type: 'Noise' }, { id: 'sen_q1_03_tmp', type: 'Temperature' },
      ]},
    ],
  },
  {
    id: 'dist_q3', name: 'Quận 3', nameEn: 'District 3',
    center: [106.6826, 10.7836],
    wards: [
      { id: 'ward_q3_01', name: 'P. Võ Thị Sáu', sensors: [
        { id: 'sen_q3_01_co2', type: 'CO2' }, { id: 'sen_q3_01_noi', type: 'Noise' }, { id: 'sen_q3_01_tmp', type: 'Temperature' },
      ]},
      { id: 'ward_q3_02', name: 'P. 9', sensors: [
        { id: 'sen_q3_02_co2', type: 'CO2' }, { id: 'sen_q3_02_noi', type: 'Noise' }, { id: 'sen_q3_02_tmp', type: 'Temperature' },
      ]},
      { id: 'ward_q3_03', name: 'P. 13', sensors: [
        { id: 'sen_q3_03_co2', type: 'CO2' }, { id: 'sen_q3_03_noi', type: 'Noise' }, { id: 'sen_q3_03_tmp', type: 'Temperature' },
      ]},
    ],
  },
  {
    id: 'dist_q5', name: 'Quận 5', nameEn: 'District 5',
    center: [106.6660, 10.7550],
    wards: [
      { id: 'ward_q5_01', name: 'P. 1', sensors: [
        { id: 'sen_q5_01_co2', type: 'CO2' }, { id: 'sen_q5_01_noi', type: 'Noise' }, { id: 'sen_q5_01_tmp', type: 'Temperature' },
      ]},
      { id: 'ward_q5_02', name: 'P. 4', sensors: [
        { id: 'sen_q5_02_co2', type: 'CO2' }, { id: 'sen_q5_02_noi', type: 'Noise' }, { id: 'sen_q5_02_tmp', type: 'Temperature' },
      ]},
      { id: 'ward_q5_03', name: 'P. 9', sensors: [
        { id: 'sen_q5_03_co2', type: 'CO2' }, { id: 'sen_q5_03_noi', type: 'Noise' }, { id: 'sen_q5_03_tmp', type: 'Temperature' },
      ]},
    ],
  },
  {
    id: 'dist_q7', name: 'Quận 7', nameEn: 'District 7',
    center: [106.7300, 10.7300],
    wards: [
      { id: 'ward_q7_01', name: 'P. Tân Phong', sensors: [
        { id: 'sen_q7_01_co2', type: 'CO2' }, { id: 'sen_q7_01_noi', type: 'Noise' }, { id: 'sen_q7_01_tmp', type: 'Temperature' },
      ]},
      { id: 'ward_q7_02', name: 'P. Tân Kiểng', sensors: [
        { id: 'sen_q7_02_co2', type: 'CO2' }, { id: 'sen_q7_02_noi', type: 'Noise' }, { id: 'sen_q7_02_tmp', type: 'Temperature' },
      ]},
      { id: 'ward_q7_03', name: 'P. Phú Mỹ', sensors: [
        { id: 'sen_q7_03_co2', type: 'CO2' }, { id: 'sen_q7_03_noi', type: 'Noise' }, { id: 'sen_q7_03_tmp', type: 'Temperature' },
      ]},
    ],
  },
  {
    id: 'dist_q10', name: 'Quận 10', nameEn: 'District 10',
    center: [106.6650, 10.7750],
    wards: [
      { id: 'ward_q10_01', name: 'P. 1', sensors: [
        { id: 'sen_q10_01_co2', type: 'CO2' }, { id: 'sen_q10_01_noi', type: 'Noise' }, { id: 'sen_q10_01_tmp', type: 'Temperature' },
      ]},
      { id: 'ward_q10_02', name: 'P. 9', sensors: [
        { id: 'sen_q10_02_co2', type: 'CO2' }, { id: 'sen_q10_02_noi', type: 'Noise' }, { id: 'sen_q10_02_tmp', type: 'Temperature' },
      ]},
      { id: 'ward_q10_03', name: 'P. 14', sensors: [
        { id: 'sen_q10_03_co2', type: 'CO2' }, { id: 'sen_q10_03_noi', type: 'Noise' }, { id: 'sen_q10_03_tmp', type: 'Temperature' },
      ]},
    ],
  },
  {
    id: 'dist_q12', name: 'Quận 12', nameEn: 'District 12',
    center: [106.6450, 10.8670],
    wards: [
      { id: 'ward_q12_01', name: 'P. Tân Chánh Hiệp', sensors: [
        { id: 'sen_q12_01_co2', type: 'CO2' }, { id: 'sen_q12_01_noi', type: 'Noise' }, { id: 'sen_q12_01_tmp', type: 'Temperature' },
      ]},
      { id: 'ward_q12_02', name: 'P. An Phú Đông', sensors: [
        { id: 'sen_q12_02_co2', type: 'CO2' }, { id: 'sen_q12_02_noi', type: 'Noise' }, { id: 'sen_q12_02_tmp', type: 'Temperature' },
      ]},
      { id: 'ward_q12_03', name: 'P. Thạnh Lộc', sensors: [
        { id: 'sen_q12_03_co2', type: 'CO2' }, { id: 'sen_q12_03_noi', type: 'Noise' }, { id: 'sen_q12_03_tmp', type: 'Temperature' },
      ]},
    ],
  },
  {
    id: 'dist_bth', name: 'Quận Bình Thạnh', nameEn: 'Binh Thanh',
    center: [106.7050, 10.8050],
    wards: [
      { id: 'ward_bth_01', name: 'P. 1', sensors: [
        { id: 'sen_bth_01_co2', type: 'CO2' }, { id: 'sen_bth_01_noi', type: 'Noise' }, { id: 'sen_bth_01_tmp', type: 'Temperature' },
      ]},
      { id: 'ward_bth_02', name: 'P. 13', sensors: [
        { id: 'sen_bth_02_co2', type: 'CO2' }, { id: 'sen_bth_02_noi', type: 'Noise' }, { id: 'sen_bth_02_tmp', type: 'Temperature' },
      ]},
      { id: 'ward_bth_03', name: 'P. 25', sensors: [
        { id: 'sen_bth_03_co2', type: 'CO2' }, { id: 'sen_bth_03_noi', type: 'Noise' }, { id: 'sen_bth_03_tmp', type: 'Temperature' },
      ]},
    ],
  },
  {
    id: 'dist_gv', name: 'Quận Gò Vấp', nameEn: 'Go Vap',
    center: [106.6750, 10.8250],
    wards: [
      { id: 'ward_gv_01', name: 'P. 1', sensors: [
        { id: 'sen_gv_01_co2', type: 'CO2' }, { id: 'sen_gv_01_noi', type: 'Noise' }, { id: 'sen_gv_01_tmp', type: 'Temperature' },
      ]},
      { id: 'ward_gv_02', name: 'P. 5', sensors: [
        { id: 'sen_gv_02_co2', type: 'CO2' }, { id: 'sen_gv_02_noi', type: 'Noise' }, { id: 'sen_gv_02_tmp', type: 'Temperature' },
      ]},
      { id: 'ward_gv_03', name: 'P. 12', sensors: [
        { id: 'sen_gv_03_co2', type: 'CO2' }, { id: 'sen_gv_03_noi', type: 'Noise' }, { id: 'sen_gv_03_tmp', type: 'Temperature' },
      ]},
    ],
  },
  {
    id: 'dist_tb', name: 'Quận Tân Bình', nameEn: 'Tan Binh',
    center: [106.6500, 10.8000],
    wards: [
      { id: 'ward_tb_01', name: 'P. 1', sensors: [
        { id: 'sen_tb_01_co2', type: 'CO2' }, { id: 'sen_tb_01_noi', type: 'Noise' }, { id: 'sen_tb_01_tmp', type: 'Temperature' },
      ]},
      { id: 'ward_tb_02', name: 'P. 4', sensors: [
        { id: 'sen_tb_02_co2', type: 'CO2' }, { id: 'sen_tb_02_noi', type: 'Noise' }, { id: 'sen_tb_02_tmp', type: 'Temperature' },
      ]},
      { id: 'ward_tb_03', name: 'P. 15', sensors: [
        { id: 'sen_tb_03_co2', type: 'CO2' }, { id: 'sen_tb_03_noi', type: 'Noise' }, { id: 'sen_tb_03_tmp', type: 'Temperature' },
      ]},
    ],
  },
  {
    id: 'dist_td', name: 'TP. Thủ Đức', nameEn: 'Thu Duc City',
    center: [106.7500, 10.8400],
    wards: [
      { id: 'ward_td_01', name: 'P. Thảo Điền', sensors: [
        { id: 'sen_td_01_co2', type: 'CO2' }, { id: 'sen_td_01_noi', type: 'Noise' }, { id: 'sen_td_01_tmp', type: 'Temperature' },
      ]},
      { id: 'ward_td_02', name: 'P. An Phú', sensors: [
        { id: 'sen_td_02_co2', type: 'CO2' }, { id: 'sen_td_02_noi', type: 'Noise' }, { id: 'sen_td_02_tmp', type: 'Temperature' },
      ]},
      { id: 'ward_td_03', name: 'P. Linh Trung', sensors: [
        { id: 'sen_td_03_co2', type: 'CO2' }, { id: 'sen_td_03_noi', type: 'Noise' }, { id: 'sen_td_03_tmp', type: 'Temperature' },
      ]},
    ],
  },
];

// ============================================================================
// GeoJSON BOUNDARIES — 10 Districts (simplified polygons)
// ============================================================================
export const HCMC_GEOJSON: GeoJSON.FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    // Quận 1
    { type: 'Feature', properties: { districtId: 'dist_q1', name: 'Quận 1' }, geometry: { type: 'Polygon', coordinates: [[
      [106.6888, 10.7850], [106.6950, 10.7870], [106.7020, 10.7850], [106.7080, 10.7780],
      [106.7080, 10.7700], [106.7050, 10.7630], [106.6970, 10.7600], [106.6910, 10.7640],
      [106.6870, 10.7720], [106.6860, 10.7790], [106.6888, 10.7850],
    ]]}},
    // Quận 3
    { type: 'Feature', properties: { districtId: 'dist_q3', name: 'Quận 3' }, geometry: { type: 'Polygon', coordinates: [[
      [106.6700, 10.7930], [106.6820, 10.7940], [106.6900, 10.7870], [106.6890, 10.7790],
      [106.6870, 10.7730], [106.6780, 10.7740], [106.6700, 10.7770], [106.6680, 10.7840],
      [106.6700, 10.7930],
    ]]}},
    // Quận 5
    { type: 'Feature', properties: { districtId: 'dist_q5', name: 'Quận 5' }, geometry: { type: 'Polygon', coordinates: [[
      [106.6520, 10.7660], [106.6700, 10.7670], [106.6700, 10.7560], [106.6780, 10.7480],
      [106.6720, 10.7420], [106.6560, 10.7430], [106.6500, 10.7520], [106.6490, 10.7600],
      [106.6520, 10.7660],
    ]]}},
    // Quận 7
    { type: 'Feature', properties: { districtId: 'dist_q7', name: 'Quận 7' }, geometry: { type: 'Polygon', coordinates: [[
      [106.7050, 10.7420], [106.7200, 10.7500], [106.7400, 10.7480], [106.7500, 10.7350],
      [106.7480, 10.7150], [106.7350, 10.7050], [106.7180, 10.7070], [106.7060, 10.7200],
      [106.7020, 10.7320], [106.7050, 10.7420],
    ]]}},
    // Quận 10
    { type: 'Feature', properties: { districtId: 'dist_q10', name: 'Quận 10' }, geometry: { type: 'Polygon', coordinates: [[
      [106.6530, 10.7830], [106.6680, 10.7840], [106.6700, 10.7770], [106.6780, 10.7680],
      [106.6700, 10.7600], [106.6580, 10.7600], [106.6500, 10.7660], [106.6490, 10.7760],
      [106.6530, 10.7830],
    ]]}},
    // Quận 12
    { type: 'Feature', properties: { districtId: 'dist_q12', name: 'Quận 12' }, geometry: { type: 'Polygon', coordinates: [[
      [106.6100, 10.8950], [106.6350, 10.9000], [106.6680, 10.8920], [106.6750, 10.8700],
      [106.6700, 10.8450], [106.6500, 10.8350], [106.6250, 10.8400], [106.6100, 10.8550],
      [106.6050, 10.8750], [106.6100, 10.8950],
    ]]}},
    // Bình Thạnh
    { type: 'Feature', properties: { districtId: 'dist_bth', name: 'Q. Bình Thạnh' }, geometry: { type: 'Polygon', coordinates: [[
      [106.6900, 10.8250], [106.7100, 10.8250], [106.7200, 10.8130], [106.7200, 10.7950],
      [106.7100, 10.7870], [106.6950, 10.7870], [106.6850, 10.7930], [106.6820, 10.8060],
      [106.6850, 10.8180], [106.6900, 10.8250],
    ]]}},
    // Gò Vấp
    { type: 'Feature', properties: { districtId: 'dist_gv', name: 'Q. Gò Vấp' }, geometry: { type: 'Polygon', coordinates: [[
      [106.6550, 10.8450], [106.6750, 10.8460], [106.6900, 10.8380], [106.6920, 10.8250],
      [106.6900, 10.8100], [106.6800, 10.8020], [106.6650, 10.8030], [106.6530, 10.8120],
      [106.6500, 10.8280], [106.6550, 10.8450],
    ]]}},
    // Tân Bình
    { type: 'Feature', properties: { districtId: 'dist_tb', name: 'Q. Tân Bình' }, geometry: { type: 'Polygon', coordinates: [[
      [106.6300, 10.8240], [106.6550, 10.8250], [106.6680, 10.8130], [106.6700, 10.7980],
      [106.6680, 10.7870], [106.6530, 10.7830], [106.6400, 10.7870], [106.6300, 10.7980],
      [106.6250, 10.8100], [106.6300, 10.8240],
    ]]}},
    // TP. Thủ Đức
    { type: 'Feature', properties: { districtId: 'dist_td', name: 'TP. Thủ Đức' }, geometry: { type: 'Polygon', coordinates: [[
      [106.7100, 10.8850], [106.7400, 10.8900], [106.7700, 10.8800], [106.7900, 10.8600],
      [106.7950, 10.8300], [106.7850, 10.8000], [106.7600, 10.7800], [106.7350, 10.7750],
      [106.7200, 10.7850], [106.7100, 10.8050], [106.7050, 10.8350], [106.7050, 10.8600],
      [106.7100, 10.8850],
    ]]}},
  ],
};

// ============================================================================
// HELPERS
// ============================================================================
export const getAllSensorIds = (): string[] => {
  const ids: string[] = [];
  for (const d of HCMC_DISTRICTS) {
    for (const w of d.wards) {
      for (const s of w.sensors) {
        ids.push(s.id);
      }
    }
  }
  return ids;
};

/** Build a mapping: sensorId → wardId (locationId) for the simulator */
export const getSensorLocationMap = (): Record<string, string> => {
  const map: Record<string, string> = {};
  for (const d of HCMC_DISTRICTS) {
    for (const w of d.wards) {
      for (const s of w.sensors) {
        map[s.id] = w.id;
      }
    }
  }
  return map;
};

// ============================================================================
// DISTRICT STATUS HELPERS
// ============================================================================
export type DistrictStatus = 'green' | 'yellow' | 'red' | 'gray';

export interface DistrictMetrics {
  avgCO2: number | null;
  avgNoise: number | null;
  avgTemperature: number | null;
  avgPM25: number | null;
  avgHumidity: number | null;
  aqi: number | null;
  status: DistrictStatus;
  alerts: string[]; // metric labels that are in danger
}

export const getDistrictFillColor = (status: DistrictStatus): string => {
  switch (status) {
    case 'green':  return 'rgba(34, 197, 94, 0.30)';
    case 'yellow': return 'rgba(234, 179, 8, 0.40)';
    case 'red':    return 'rgba(239, 68, 68, 0.45)';
    case 'gray':   return 'rgba(100, 116, 139, 0.15)';
  }
};

export const getDistrictBorderColor = (status: DistrictStatus): string => {
  switch (status) {
    case 'green':  return '#22c55e';
    case 'yellow': return '#eab308';
    case 'red':    return '#ef4444';
    case 'gray':   return '#64748b';
  }
};
