# Đặc Tả Tính Năng Thực Tiễn - Smart City IoT Dashboard

## 📋 Tổng Quan

Tài liệu này mô tả 3 tính năng thiết thực nhất để nâng cấp hệ thống Smart City IoT Dashboard từ "demo kỹ thuật" thành "giải pháp thực tiễn" phục vụ người dân và chính quyền.

### Mục Tiêu
- ✅ Giải quyết vấn đề thực tế của thành phố thông minh
- ✅ Dễ triển khai với công nghệ hiện có
- ✅ Tạo giá trị ngay lập tức cho người dùng
- ✅ Phù hợp với phạm vi đồ án

### Các Tính Năng Được Chọn
1. **Hệ Thống Chỉ Số Chất Lượng Không Khí (AQI System)**
2. **Hệ Thống Báo Cáo Tự Động & Thống Kê**
3. **Hệ Thống Phát Hiện Bất Thường & Cảnh Báo Thông Minh**

---

## 🌟 Tính Năng 1: Hệ Thống Chỉ Số Chất Lượng Không Khí (AQI System)

### Vấn Đề Hiện Tại
- Dữ liệu thô (CO2 ppm, Noise dB) khó hiểu với người dân
- Không có chuẩn quốc tế để so sánh
- Thiếu khuyến nghị sức khỏe cụ thể

### Giải Pháp
Tính toán **Air Quality Index (AQI)** theo chuẩn US EPA và Việt Nam, chuyển đổi dữ liệu thô thành chỉ số dễ hiểu (0-500) với phân loại màu sắc và khuyến nghị sức khỏe.


### Yêu Cầu Chức Năng

#### FR1.1: Tính Toán AQI Theo Chuẩn US EPA
**Mô tả:** Hệ thống phải tính toán AQI dựa trên công thức US EPA cho các chỉ số:
- PM2.5 (từ CO2 - ước lượng)
- Noise Level (chuyển đổi sang dB scale)

**Công thức AQI:**
```
AQI = ((I_high - I_low) / (C_high - C_low)) * (C - C_low) + I_low

Trong đó:
- C: Nồng độ đo được
- C_low, C_high: Ngưỡng breakpoint
- I_low, I_high: Chỉ số AQI tương ứng
```

**Bảng Breakpoint (US EPA):**
| AQI Range | Category | CO2 (ppm) | Noise (dB) | Color |
|-----------|----------|-----------|------------|-------|
| 0-50 | Good (Tốt) | 0-400 | 0-50 | Green |
| 51-100 | Moderate (Trung bình) | 401-600 | 51-60 | Yellow |
| 101-150 | Unhealthy for Sensitive Groups | 601-800 | 61-70 | Orange |
| 151-200 | Unhealthy (Kém) | 801-1000 | 71-80 | Red |
| 201-300 | Very Unhealthy (Xấu) | 1001-1500 | 81-90 | Purple |
| 301-500 | Hazardous (Nguy hại) | >1500 | >90 | Maroon |

**Acceptance Criteria:**
1. WHEN telemetry data is received, THE System SHALL calculate AQI for CO2 and Noise
2. THE System SHALL use the HIGHEST AQI value among all pollutants as the overall AQI
3. THE System SHALL store AQI values in Oracle database with timestamp
4. THE System SHALL update AQI every 5 seconds (same as telemetry frequency)
5. THE System SHALL handle edge cases (missing data, out-of-range values)


#### FR1.2: Phân Loại Chất Lượng Không Khí
**Mô tả:** Hệ thống phải phân loại chất lượng không khí thành 6 cấp độ với màu sắc và mô tả tiếng Việt.

**Acceptance Criteria:**
1. THE System SHALL assign a category based on AQI value:
   - 0-50: "Tốt" (Good) - Green (#00e400)
   - 51-100: "Trung bình" (Moderate) - Yellow (#ffff00)
   - 101-150: "Không tốt cho nhóm nhạy cảm" - Orange (#ff7e00)
   - 151-200: "Kém" (Unhealthy) - Red (#ff0000)
   - 201-300: "Rất kém" (Very Unhealthy) - Purple (#8f3f97)
   - 301-500: "Nguy hại" (Hazardous) - Maroon (#7e0023)
2. THE System SHALL display category name in Vietnamese on dashboard
3. THE System SHALL use color coding consistently across all UI components

#### FR1.3: Khuyến Nghị Sức Khỏe
**Mô tả:** Hệ thống phải cung cấp khuyến nghị sức khỏe cụ thể cho từng cấp độ AQI.

**Khuyến Nghị Theo Cấp Độ:**

**Good (0-50):**
- Chung: "Chất lượng không khí tốt. An toàn cho mọi hoạt động ngoài trời."
- Nhóm nhạy cảm: "Không có hạn chế."

**Moderate (51-100):**
- Chung: "Chất lượng không khí chấp nhận được. Có thể hoạt động bình thường."
- Nhóm nhạy cảm: "Người nhạy cảm nên hạn chế hoạt động ngoài trời kéo dài."

**Unhealthy for Sensitive Groups (101-150):**
- Chung: "Người bình thường có thể hoạt động bình thường."
- Nhóm nhạy cảm: "Trẻ em, người già, người bệnh hô hấp nên hạn chế ra ngoài."

**Unhealthy (151-200):**
- Chung: "Mọi người nên hạn chế hoạt động ngoài trời kéo dài."
- Nhóm nhạy cảm: "Nên ở trong nhà, đóng cửa sổ."

**Very Unhealthy (201-300):**
- Chung: "Tránh hoạt động ngoài trời. Đeo khẩu trang khi ra ngoài."
- Nhóm nhạy cảm: "Ở trong nhà, sử dụng máy lọc không khí."

**Hazardous (301-500):**
- Chung: "KHẨN CẤP: Ở trong nhà, đóng kín cửa. Không ra ngoài trừ trường hợp cần thiết."
- Nhóm nhạy cảm: "Sơ tán khỏi khu vực nếu có thể."

**Acceptance Criteria:**
1. THE System SHALL provide health recommendations in Vietnamese
2. THE System SHALL differentiate recommendations for general public and sensitive groups
3. THE System SHALL display recommendations on dashboard and in reports
4. THE System SHALL update recommendations when AQI category changes


#### FR1.4: Hiển Thị AQI Trên Dashboard
**Mô tả:** Dashboard phải hiển thị AQI một cách trực quan và dễ hiểu.

**Acceptance Criteria:**
1. THE Dashboard SHALL display current AQI value as a large number with color coding
2. THE Dashboard SHALL show AQI category name and icon
3. THE Dashboard SHALL display health recommendations
4. THE Map SHALL color-code districts by AQI level (not just alert status)
5. THE System SHALL show AQI trend chart (last 24 hours)
6. THE System SHALL display AQI gauge/meter visualization

#### FR1.5: API Endpoint cho AQI
**Mô tả:** Cung cấp REST API để truy vấn dữ liệu AQI.

**Endpoints:**
```
GET /api/aqi/current
Response: {
  "locationId": "district_001",
  "aqi": 85,
  "category": "Moderate",
  "categoryVi": "Trung bình",
  "color": "#ffff00",
  "dominantPollutant": "CO2",
  "healthRecommendation": {
    "general": "...",
    "sensitive": "..."
  },
  "timestamp": "2024-01-15T10:30:00Z"
}

GET /api/aqi/history/{locationId}?start_time=&end_time=
Response: [
  {
    "aqi": 85,
    "category": "Moderate",
    "timestamp": "2024-01-15T10:30:00Z"
  },
  ...
]

GET /api/aqi/forecast/{locationId}
Response: {
  "current": 85,
  "forecast": [
    {"hour": 11, "aqi": 90},
    {"hour": 12, "aqi": 95},
    ...
  ]
}
```

**Acceptance Criteria:**
1. THE API SHALL return AQI data in JSON format
2. THE API SHALL support time range filtering
3. THE API SHALL return 400 for invalid parameters
4. THE API SHALL return 404 if location not found
5. THE API SHALL include CORS headers


### Thiết Kế Kỹ Thuật

#### Database Schema
```sql
-- AQI_READINGS table (Oracle)
CREATE TABLE AQI_READINGS (
    ReadingID VARCHAR2(50) PRIMARY KEY,
    LocationID VARCHAR2(50) NOT NULL,
    AQI NUMBER NOT NULL,
    Category VARCHAR2(50) NOT NULL,
    DominantPollutant VARCHAR2(20),
    CO2_AQI NUMBER,
    Noise_AQI NUMBER,
    Timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (LocationID) REFERENCES LOCATIONS(LocationID)
);

CREATE INDEX idx_aqi_location_time ON AQI_READINGS(LocationID, Timestamp);
CREATE INDEX idx_aqi_category ON AQI_READINGS(Category);
```

#### Backend Implementation
```python
# backend/app/services/aqi_service.py

class AQIService:
    """Service for calculating and managing AQI data."""
    
    # US EPA Breakpoints
    AQI_BREAKPOINTS = {
        'CO2': [
            (0, 400, 0, 50),      # Good
            (401, 600, 51, 100),  # Moderate
            (601, 800, 101, 150), # USG
            (801, 1000, 151, 200),# Unhealthy
            (1001, 1500, 201, 300),# Very Unhealthy
            (1501, 2000, 301, 500) # Hazardous
        ],
        'Noise': [
            (0, 50, 0, 50),
            (51, 60, 51, 100),
            (61, 70, 101, 150),
            (71, 80, 151, 200),
            (81, 90, 201, 300),
            (91, 120, 301, 500)
        ]
    }
    
    def calculate_aqi(self, pollutant: str, concentration: float) -> int:
        """Calculate AQI for a specific pollutant."""
        breakpoints = self.AQI_BREAKPOINTS[pollutant]
        
        for c_low, c_high, i_low, i_high in breakpoints:
            if c_low <= concentration <= c_high:
                aqi = ((i_high - i_low) / (c_high - c_low)) * (concentration - c_low) + i_low
                return round(aqi)
        
        # Out of range - return max
        return 500
    
    def get_category(self, aqi: int) -> dict:
        """Get AQI category and color."""
        if aqi <= 50:
            return {"name": "Good", "nameVi": "Tốt", "color": "#00e400"}
        elif aqi <= 100:
            return {"name": "Moderate", "nameVi": "Trung bình", "color": "#ffff00"}
        elif aqi <= 150:
            return {"name": "Unhealthy for Sensitive Groups", "nameVi": "Không tốt cho nhóm nhạy cảm", "color": "#ff7e00"}
        elif aqi <= 200:
            return {"name": "Unhealthy", "nameVi": "Kém", "color": "#ff0000"}
        elif aqi <= 300:
            return {"name": "Very Unhealthy", "nameVi": "Rất kém", "color": "#8f3f97"}
        else:
            return {"name": "Hazardous", "nameVi": "Nguy hại", "color": "#7e0023"}
```


---

## 📊 Tính Năng 2: Hệ Thống Báo Cáo Tự Động & Thống Kê

### Vấn Đề Hiện Tại
- Lãnh đạo không có thời gian xem dashboard real-time
- Thiếu báo cáo định kỳ để ra quyết định
- Không có so sánh xu hướng theo thời gian
- Không có cách export dữ liệu cho họp báo

### Giải Pháp
Tạo hệ thống báo cáo tự động với:
- Báo cáo hàng ngày/tuần/tháng
- So sánh xu hướng
- Export PDF/Excel
- Gửi email tự động

### Yêu Cầu Chức Năng

#### FR2.1: Báo Cáo Hàng Ngày Tự Động
**Mô tả:** Hệ thống tự động tạo báo cáo tổng hợp chất lượng không khí hàng ngày.

**Nội dung báo cáo:**
1. **Tóm tắt tổng quan:**
   - AQI trung bình toàn thành phố
   - Số giờ ở mỗi cấp độ AQI
   - Khu vực tốt nhất / kém nhất
   
2. **Chi tiết theo quận:**
   - AQI trung bình mỗi quận
   - Số cảnh báo phát sinh
   - Xu hướng so với ngày hôm trước
   
3. **Sự kiện đáng chú ý:**
   - Các spike bất thường
   - Thời điểm AQI cao nhất
   - Khu vực cần can thiệp

4. **Biểu đồ:**
   - AQI theo giờ (24h)
   - So sánh giữa các quận
   - Xu hướng 7 ngày

**Acceptance Criteria:**
1. THE System SHALL generate daily report at 00:00 every day
2. THE Report SHALL include data from previous 24 hours
3. THE Report SHALL be stored in Oracle database
4. THE Report SHALL be available via API endpoint
5. THE System SHALL handle missing data gracefully


#### FR2.2: Báo Cáo Tuần & Tháng
**Mô tả:** Tạo báo cáo tổng hợp theo tuần và tháng với phân tích xu hướng.

**Nội dung báo cáo tuần:**
- AQI trung bình 7 ngày
- So sánh với tuần trước (% thay đổi)
- Ngày tốt nhất / kém nhất
- Xu hướng tăng/giảm

**Nội dung báo cáo tháng:**
- AQI trung bình 30 ngày
- So sánh với tháng trước
- Phân tích theo tuần
- Đề xuất cải thiện

**Acceptance Criteria:**
1. THE System SHALL generate weekly report every Monday at 00:00
2. THE System SHALL generate monthly report on 1st day of month at 00:00
3. THE Reports SHALL include trend analysis and comparisons
4. THE Reports SHALL highlight significant changes (>20% increase/decrease)

#### FR2.3: Export PDF/Excel
**Mô tả:** Cho phép export báo cáo sang định dạng PDF và Excel.

**PDF Format:**
- Header: Logo, tiêu đề, ngày tháng
- Nội dung: Tóm tắt, bảng, biểu đồ
- Footer: Chữ ký, ghi chú

**Excel Format:**
- Sheet 1: Tóm tắt
- Sheet 2: Dữ liệu chi tiết
- Sheet 3: Biểu đồ
- Formatted tables với màu sắc

**Acceptance Criteria:**
1. THE System SHALL provide API endpoint to export reports as PDF
2. THE System SHALL provide API endpoint to export reports as Excel
3. THE PDF SHALL include charts and tables with proper formatting
4. THE Excel SHALL include raw data and pivot tables
5. THE Export SHALL complete within 10 seconds for monthly reports


#### FR2.4: Email Tự Động
**Mô tả:** Gửi báo cáo tự động qua email cho danh sách người nhận.

**Email Template:**
```
Subject: [Smart City] Báo Cáo Chất Lượng Không Khí - [Ngày/Tuần/Tháng]

Kính gửi [Tên],

Đây là báo cáo tự động về chất lượng không khí thành phố.

📊 TÓM TẮT:
- AQI trung bình: 85 (Trung bình)
- Khu vực tốt nhất: Quận 7 (AQI: 45)
- Khu vực kém nhất: Quận 1 (AQI: 120)
- Số cảnh báo: 15

📈 XU HƯỚNG:
- So với hôm qua: Tăng 5%
- So với tuần trước: Giảm 10%

⚠️ CẢNH BÁO:
- 3 khu vực vượt ngưỡng an toàn
- 2 sự kiện bất thường được phát hiện

📎 File đính kèm: Báo cáo chi tiết (PDF)

Xem chi tiết tại: http://dashboard.smartcity.vn

Trân trọng,
Hệ thống Smart City IoT Dashboard
```

**Acceptance Criteria:**
1. THE System SHALL send email reports automatically based on schedule
2. THE System SHALL support multiple recipients (configurable)
3. THE Email SHALL include summary and PDF attachment
4. THE System SHALL retry failed email sends (max 3 attempts)
5. THE System SHALL log email delivery status

#### FR2.5: Dashboard Báo Cáo
**Mô tả:** Trang dashboard để xem và quản lý báo cáo.

**Chức năng:**
- Danh sách báo cáo (ngày, tuần, tháng)
- Xem trước báo cáo
- Download PDF/Excel
- Lọc theo thời gian
- Tìm kiếm báo cáo

**Acceptance Criteria:**
1. THE Dashboard SHALL display list of generated reports
2. THE Dashboard SHALL allow filtering by date range and type
3. THE Dashboard SHALL provide preview functionality
4. THE Dashboard SHALL allow download in multiple formats
5. THE Dashboard SHALL show report generation status


### Thiết Kế Kỹ Thuật

#### Database Schema
```sql
-- REPORTS table (Oracle)
CREATE TABLE REPORTS (
    ReportID VARCHAR2(50) PRIMARY KEY,
    ReportType VARCHAR2(20) CHECK (ReportType IN ('DAILY', 'WEEKLY', 'MONTHLY')),
    StartDate DATE NOT NULL,
    EndDate DATE NOT NULL,
    GeneratedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Status VARCHAR2(20) CHECK (Status IN ('PENDING', 'COMPLETED', 'FAILED')),
    FilePath VARCHAR2(500),
    Summary CLOB,
    UNIQUE (ReportType, StartDate)
);

-- REPORT_RECIPIENTS table (Oracle)
CREATE TABLE REPORT_RECIPIENTS (
    RecipientID VARCHAR2(50) PRIMARY KEY,
    Email VARCHAR2(100) NOT NULL,
    Name VARCHAR2(100),
    ReportTypes VARCHAR2(100), -- Comma-separated: DAILY,WEEKLY,MONTHLY
    Active NUMBER(1) DEFAULT 1,
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- EMAIL_LOGS table (Oracle)
CREATE TABLE EMAIL_LOGS (
    LogID VARCHAR2(50) PRIMARY KEY,
    ReportID VARCHAR2(50),
    RecipientEmail VARCHAR2(100),
    Status VARCHAR2(20) CHECK (Status IN ('SENT', 'FAILED', 'PENDING')),
    ErrorMessage VARCHAR2(500),
    SentAt TIMESTAMP,
    FOREIGN KEY (ReportID) REFERENCES REPORTS(ReportID)
);
```

#### Backend Implementation
```python
# backend/app/services/report_service.py

from datetime import datetime, timedelta
from typing import List, Dict
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

class ReportService:
    """Service for generating and managing reports."""
    
    def generate_daily_report(self, date: datetime.date) -> Dict:
        """Generate daily air quality report."""
        # Query data from last 24 hours
        start_time = datetime.combine(date, datetime.min.time())
        end_time = start_time + timedelta(days=1)
        
        # Get AQI data
        aqi_data = self.get_aqi_data(start_time, end_time)
        
        # Calculate statistics
        summary = {
            'avg_aqi': self.calculate_average_aqi(aqi_data),
            'best_location': self.find_best_location(aqi_data),
            'worst_location': self.find_worst_location(aqi_data),
            'alert_count': self.count_alerts(start_time, end_time),
            'hours_by_category': self.calculate_hours_by_category(aqi_data)
        }
        
        # Generate charts
        charts = self.generate_charts(aqi_data)
        
        # Store report
        report_id = self.store_report('DAILY', date, summary, charts)
        
        return {
            'report_id': report_id,
            'summary': summary,
            'charts': charts
        }
    
    def export_to_pdf(self, report_id: str) -> bytes:
        """Export report to PDF format."""
        report = self.get_report(report_id)
        
        # Create PDF
        pdf_buffer = io.BytesIO()
        c = canvas.Canvas(pdf_buffer, pagesize=A4)
        
        # Add content
        self.add_pdf_header(c, report)
        self.add_pdf_summary(c, report['summary'])
        self.add_pdf_charts(c, report['charts'])
        self.add_pdf_footer(c)
        
        c.save()
        return pdf_buffer.getvalue()
```


---

## 🚨 Tính Năng 3: Hệ Thống Phát Hiện Bất Thường & Cảnh Báo Thông Minh

### Vấn Đề Hiện Tại
- Cảnh báo hiện tại chỉ dựa trên ngưỡng cố định
- Không phát hiện được spike đột ngột (có thể là sự cố)
- Không có cảnh báo đa kênh (chỉ có WebSocket)
- Thiếu lịch sử sự cố để phân tích

### Giải Pháp
Xây dựng hệ thống phát hiện bất thường thông minh với:
- Phát hiện spike đột ngột (statistical anomaly detection)
- Cảnh báo đa cấp (Dashboard, Email, SMS)
- Quản lý sự cố (incident management)
- Phân tích nguyên nhân

### Yêu Cầu Chức Năng

#### FR3.1: Phát Hiện Spike Đột Ngột
**Mô tả:** Phát hiện các thay đổi bất thường trong dữ liệu cảm biến.

**Thuật toán:**
1. **Z-Score Method:**
   - Tính mean và standard deviation của 100 readings gần nhất
   - Nếu |value - mean| > 3 * std_dev → Bất thường
   
2. **Rate of Change:**
   - Nếu thay đổi > 50% trong 1 phút → Bất thường
   - Ví dụ: CO2 tăng từ 400 → 700 ppm trong 1 phút

3. **Pattern Deviation:**
   - So sánh với pattern thông thường cùng giờ
   - Ví dụ: CO2 thường 400 ppm lúc 3 AM, nay 1000 ppm → Bất thường

**Acceptance Criteria:**
1. THE System SHALL detect anomalies using Z-score method (threshold: 3 sigma)
2. THE System SHALL detect rapid changes (>50% in 1 minute)
3. THE System SHALL compare with historical patterns (same hour, same day of week)
4. THE System SHALL create anomaly record in database
5. THE System SHALL trigger alert when anomaly detected


#### FR3.2: Cảnh Báo Đa Cấp
**Mô tả:** Gửi cảnh báo qua nhiều kênh dựa trên mức độ nghiêm trọng.

**Cấp độ cảnh báo:**
1. **INFO (Thông tin):**
   - Kênh: Dashboard only
   - Ví dụ: AQI tăng nhẹ
   
2. **WARNING (Cảnh báo):**
   - Kênh: Dashboard + Email
   - Ví dụ: AQI vượt ngưỡng, spike nhỏ
   
3. **CRITICAL (Nghiêm trọng):**
   - Kênh: Dashboard + Email + SMS
   - Ví dụ: Spike lớn, có thể là sự cố
   
4. **EMERGENCY (Khẩn cấp):**
   - Kênh: Dashboard + Email + SMS + Phone Call
   - Ví dụ: Spike cực lớn, nguy hiểm tức thì

**Acceptance Criteria:**
1. THE System SHALL classify alerts into 4 severity levels
2. THE System SHALL send notifications via appropriate channels based on severity
3. THE System SHALL include location, value, and recommended action in alerts
4. THE System SHALL prevent alert spam (max 1 alert per sensor per 5 minutes)
5. THE System SHALL log all alert deliveries

#### FR3.3: Quản Lý Sự Cố (Incident Management)
**Mô tả:** Tạo và theo dõi sự cố từ cảnh báo bất thường.

**Workflow:**
1. **Tạo sự cố tự động:**
   - Khi phát hiện anomaly CRITICAL/EMERGENCY
   - Tạo incident ticket với ID duy nhất
   
2. **Phân công xử lý:**
   - Gán cho team/người phụ trách khu vực
   - Gửi thông báo cho người được gán
   
3. **Theo dõi tiến độ:**
   - Status: NEW → ASSIGNED → IN_PROGRESS → RESOLVED → CLOSED
   - Ghi nhận thời gian mỗi bước
   
4. **Ghi chú và cập nhật:**
   - Cho phép thêm ghi chú
   - Upload ảnh/tài liệu
   - Cập nhật tiến độ

**Acceptance Criteria:**
1. THE System SHALL create incident automatically for CRITICAL/EMERGENCY anomalies
2. THE System SHALL assign incident to responsible team based on location
3. THE System SHALL track incident status through workflow
4. THE System SHALL allow adding notes and attachments
5. THE System SHALL calculate resolution time (SLA tracking)


#### FR3.4: Dashboard Quản Lý Sự Cố
**Mô tả:** Giao diện để xem và quản lý các sự cố.

**Chức năng:**
- Danh sách sự cố (bảng, bộ lọc)
- Chi tiết sự cố (timeline, notes, attachments)
- Cập nhật trạng thái
- Gán người xử lý
- Thống kê sự cố (số lượng, thời gian xử lý trung bình)

**Acceptance Criteria:**
1. THE Dashboard SHALL display list of incidents with filters (status, severity, location)
2. THE Dashboard SHALL show incident details with timeline
3. THE Dashboard SHALL allow status updates and note additions
4. THE Dashboard SHALL display incident statistics (count, avg resolution time)
5. THE Dashboard SHALL highlight overdue incidents (>24h unresolved)

#### FR3.5: Phân Tích Nguyên Nhân
**Mô tả:** Phân tích và gợi ý nguyên nhân có thể của bất thường.

**Phân tích:**
1. **Thời gian:**
   - Giờ cao điểm? Cuối tuần? Lễ hội?
   
2. **Vị trí:**
   - Gần nhà máy? Đường lớn? Công trình xây dựng?
   
3. **Thời tiết:**
   - Gió yếu? Nhiệt độ cao? Mưa?
   
4. **Lịch sử:**
   - Đã xảy ra tương tự trước đây?
   - Nguyên nhân lần trước là gì?

**Gợi ý nguyên nhân:**
```
Ví dụ:
- "Spike CO2 lúc 8 AM tại Quận 1 → Có thể do tắc đường giờ cao điểm"
- "Noise tăng đột ngột lúc 2 AM → Có thể do công trình xây dựng trái phép"
- "CO2 cao khi gió yếu → Ô nhiễm tích tụ do điều kiện thời tiết"
```

**Acceptance Criteria:**
1. THE System SHALL analyze time, location, weather, and history
2. THE System SHALL provide possible root causes with confidence score
3. THE System SHALL suggest similar past incidents
4. THE System SHALL recommend actions based on root cause
5. THE System SHALL learn from resolved incidents (update knowledge base)


### Thiết Kế Kỹ Thuật

#### Database Schema
```sql
-- ANOMALIES table (Oracle)
CREATE TABLE ANOMALIES (
    AnomalyID VARCHAR2(50) PRIMARY KEY,
    SensorID VARCHAR2(50) NOT NULL,
    MetricType VARCHAR2(20) NOT NULL,
    Value NUMBER NOT NULL,
    ExpectedValue NUMBER,
    Deviation NUMBER,
    DetectionMethod VARCHAR2(50), -- ZSCORE, RATE_OF_CHANGE, PATTERN
    Severity VARCHAR2(20) CHECK (Severity IN ('INFO', 'WARNING', 'CRITICAL', 'EMERGENCY')),
    DetectedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (SensorID) REFERENCES SENSOR_REGISTRY(SensorID)
);

-- INCIDENTS table (Oracle)
CREATE TABLE INCIDENTS (
    IncidentID VARCHAR2(50) PRIMARY KEY,
    AnomalyID VARCHAR2(50),
    Title VARCHAR2(200) NOT NULL,
    Description CLOB,
    Status VARCHAR2(20) CHECK (Status IN ('NEW', 'ASSIGNED', 'IN_PROGRESS', 'RESOLVED', 'CLOSED')),
    Severity VARCHAR2(20),
    AssignedTo VARCHAR2(100),
    LocationID VARCHAR2(50),
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ResolvedAt TIMESTAMP,
    ResolutionTime NUMBER, -- Minutes
    RootCause VARCHAR2(500),
    FOREIGN KEY (AnomalyID) REFERENCES ANOMALIES(AnomalyID),
    FOREIGN KEY (LocationID) REFERENCES LOCATIONS(LocationID)
);

-- INCIDENT_NOTES table (Oracle)
CREATE TABLE INCIDENT_NOTES (
    NoteID VARCHAR2(50) PRIMARY KEY,
    IncidentID VARCHAR2(50) NOT NULL,
    Author VARCHAR2(100) NOT NULL,
    Content CLOB NOT NULL,
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (IncidentID) REFERENCES INCIDENTS(IncidentID)
);

-- NOTIFICATION_CHANNELS table (Oracle)
CREATE TABLE NOTIFICATION_CHANNELS (
    ChannelID VARCHAR2(50) PRIMARY KEY,
    UserID VARCHAR2(50) NOT NULL,
    ChannelType VARCHAR2(20) CHECK (ChannelType IN ('EMAIL', 'SMS', 'PHONE')),
    Address VARCHAR2(200) NOT NULL, -- Email or phone number
    Enabled NUMBER(1) DEFAULT 1,
    MinSeverity VARCHAR2(20) DEFAULT 'WARNING'
);
```


#### Backend Implementation
```python
# backend/app/services/anomaly_detection_service.py

import numpy as np
from scipy import stats
from datetime import datetime, timedelta
from typing import Optional, Dict, List

class AnomalyDetectionService:
    """Service for detecting anomalies in sensor data."""
    
    def __init__(self):
        self.zscore_threshold = 3.0
        self.rate_change_threshold = 0.5  # 50%
        self.window_size = 100  # Last 100 readings
    
    def detect_zscore_anomaly(self, sensor_id: str, current_value: float) -> Optional[Dict]:
        """Detect anomaly using Z-score method."""
        # Get historical data
        historical_data = self.get_historical_data(sensor_id, limit=self.window_size)
        
        if len(historical_data) < 30:  # Need minimum data
            return None
        
        # Calculate statistics
        values = [d['value'] for d in historical_data]
        mean = np.mean(values)
        std = np.std(values)
        
        if std == 0:  # Avoid division by zero
            return None
        
        # Calculate Z-score
        zscore = abs((current_value - mean) / std)
        
        if zscore > self.zscore_threshold:
            return {
                'method': 'ZSCORE',
                'value': current_value,
                'expected': mean,
                'deviation': zscore,
                'severity': self.calculate_severity(zscore)
            }
        
        return None
    
    def detect_rate_change_anomaly(self, sensor_id: str, current_value: float) -> Optional[Dict]:
        """Detect anomaly based on rate of change."""
        # Get last reading (1 minute ago)
        last_reading = self.get_last_reading(sensor_id, minutes_ago=1)
        
        if not last_reading:
            return None
        
        # Calculate rate of change
        rate = abs(current_value - last_reading['value']) / last_reading['value']
        
        if rate > self.rate_change_threshold:
            return {
                'method': 'RATE_OF_CHANGE',
                'value': current_value,
                'expected': last_reading['value'],
                'deviation': rate,
                'severity': 'CRITICAL' if rate > 1.0 else 'WARNING'
            }
        
        return None
    
    def calculate_severity(self, zscore: float) -> str:
        """Calculate severity based on Z-score."""
        if zscore > 5:
            return 'EMERGENCY'
        elif zscore > 4:
            return 'CRITICAL'
        elif zscore > 3:
            return 'WARNING'
        else:
            return 'INFO'
    
    def create_incident(self, anomaly: Dict) -> str:
        """Create incident from anomaly."""
        incident_id = str(uuid.uuid4())
        
        # Determine title and description
        title = f"Bất thường {anomaly['metric_type']} tại {anomaly['location_name']}"
        description = f"""
        Phát hiện bất thường:
        - Giá trị đo được: {anomaly['value']}
        - Giá trị dự kiến: {anomaly['expected']}
        - Độ lệch: {anomaly['deviation']:.2f}
        - Phương pháp phát hiện: {anomaly['method']}
        """
        
        # Store incident
        self.oracle_client.insert_incident({
            'incident_id': incident_id,
            'anomaly_id': anomaly['anomaly_id'],
            'title': title,
            'description': description,
            'severity': anomaly['severity'],
            'status': 'NEW',
            'location_id': anomaly['location_id']
        })
        
        # Assign to team
        self.assign_incident(incident_id, anomaly['location_id'])
        
        # Send notifications
        self.send_notifications(incident_id, anomaly['severity'])
        
        return incident_id
```


---

## 🎯 Kế Hoạch Triển Khai

### Phase 1: AQI System (Tuần 1-2)
**Mục tiêu:** Tính toán và hiển thị AQI cơ bản

**Tasks:**
1. ✅ Tạo AQI Service với công thức US EPA
2. ✅ Tạo database schema (AQI_READINGS table)
3. ✅ Tích hợp vào telemetry processing pipeline
4. ✅ Tạo API endpoints cho AQI
5. ✅ Cập nhật frontend để hiển thị AQI
6. ✅ Thêm color coding theo AQI category
7. ✅ Hiển thị health recommendations
8. ✅ Viết unit tests

**Deliverables:**
- AQI được tính toán real-time
- Dashboard hiển thị AQI với màu sắc
- API endpoints hoạt động
- Tests pass

### Phase 2: Reporting System (Tuần 3-4)
**Mục tiêu:** Báo cáo tự động và export

**Tasks:**
1. ✅ Tạo Report Service
2. ✅ Tạo database schema (REPORTS, REPORT_RECIPIENTS tables)
3. ✅ Implement daily report generation
4. ✅ Implement weekly/monthly reports
5. ✅ Tạo PDF export functionality (ReportLab)
6. ✅ Tạo Excel export functionality (openpyxl)
7. ✅ Setup email service (SMTP)
8. ✅ Tạo scheduler cho báo cáo tự động
9. ✅ Tạo dashboard quản lý báo cáo
10. ✅ Viết unit tests

**Deliverables:**
- Báo cáo tự động hàng ngày
- Export PDF/Excel hoạt động
- Email gửi tự động
- Dashboard quản lý báo cáo


### Phase 3: Anomaly Detection (Tuần 5-6)
**Mục tiêu:** Phát hiện bất thường và quản lý sự cố

**Tasks:**
1. ✅ Tạo Anomaly Detection Service
2. ✅ Tạo database schema (ANOMALIES, INCIDENTS tables)
3. ✅ Implement Z-score detection
4. ✅ Implement rate-of-change detection
5. ✅ Tạo Incident Management Service
6. ✅ Implement notification system (Email, SMS)
7. ✅ Tạo dashboard quản lý sự cố
8. ✅ Implement root cause analysis
9. ✅ Tạo incident workflow
10. ✅ Viết unit tests

**Deliverables:**
- Anomaly detection hoạt động
- Incident management system
- Multi-channel notifications
- Dashboard quản lý sự cố

### Phase 4: Integration & Testing (Tuần 7)
**Mục tiêu:** Tích hợp và kiểm thử toàn bộ

**Tasks:**
1. ✅ Integration testing
2. ✅ Performance testing
3. ✅ User acceptance testing
4. ✅ Bug fixes
5. ✅ Documentation
6. ✅ Deployment

**Deliverables:**
- Hệ thống hoạt động ổn định
- Documentation đầy đủ
- Ready for production

---

## 📊 Metrics & KPIs

### Metrics Đo Lường Thành Công

**AQI System:**
- ✅ AQI được tính toán cho 100% telemetry data
- ✅ Độ chính xác: So sánh với chuẩn US EPA
- ✅ Latency: < 1 second từ telemetry đến AQI
- ✅ User satisfaction: Survey feedback

**Reporting System:**
- ✅ Báo cáo được tạo đúng giờ (100% on-time)
- ✅ Email delivery rate: > 95%
- ✅ Report generation time: < 10 seconds
- ✅ Download success rate: > 98%

**Anomaly Detection:**
- ✅ False positive rate: < 10%
- ✅ Detection latency: < 30 seconds
- ✅ Incident resolution time: < 24 hours (average)
- ✅ Notification delivery: > 99%


---

## 🛠️ Công Nghệ & Thư Viện

### Backend (Python)
```python
# requirements.txt additions

# AQI Calculation
numpy==1.24.0
scipy==1.10.0

# PDF Generation
reportlab==4.0.0
matplotlib==3.7.0  # For charts in PDF

# Excel Generation
openpyxl==3.1.0
xlsxwriter==3.1.0

# Email
python-dotenv==1.0.0
jinja2==3.1.2  # Email templates

# SMS (Optional)
twilio==8.5.0

# Anomaly Detection
scikit-learn==1.3.0  # For advanced ML models (future)
```

### Frontend (React)
```json
// package.json additions
{
  "dependencies": {
    "recharts": "^2.5.0",  // Better charts for AQI
    "react-gauge-chart": "^0.4.0",  // AQI gauge
    "react-pdf": "^7.0.0",  // PDF preview
    "file-saver": "^2.0.5"  // File download
  }
}
```

### Infrastructure
- **Email Server:** SMTP (Gmail, SendGrid, AWS SES)
- **SMS Gateway:** Twilio, AWS SNS
- **Scheduler:** APScheduler (Python) hoặc Celery
- **Storage:** Local filesystem hoặc S3 cho PDF/Excel files

---

## 📝 API Endpoints Summary

### AQI Endpoints
```
GET  /api/aqi/current                    # Current AQI for all locations
GET  /api/aqi/current/{locationId}       # Current AQI for specific location
GET  /api/aqi/history/{locationId}       # Historical AQI data
GET  /api/aqi/forecast/{locationId}      # AQI forecast (future)
```

### Report Endpoints
```
GET  /api/reports                        # List all reports
GET  /api/reports/{reportId}             # Get report details
GET  /api/reports/{reportId}/pdf         # Download PDF
GET  /api/reports/{reportId}/excel       # Download Excel
POST /api/reports/generate               # Manually trigger report generation
GET  /api/reports/recipients             # List email recipients
POST /api/reports/recipients             # Add recipient
```

### Anomaly & Incident Endpoints
```
GET  /api/anomalies                      # List anomalies
GET  /api/anomalies/{anomalyId}          # Get anomaly details
GET  /api/incidents                      # List incidents
GET  /api/incidents/{incidentId}         # Get incident details
PUT  /api/incidents/{incidentId}/status  # Update incident status
POST /api/incidents/{incidentId}/notes   # Add note to incident
GET  /api/incidents/statistics           # Incident statistics
```


---

## 🎨 UI/UX Mockups

### AQI Display on Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│  SMART CITY OPERATION CENTER                                │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  CHẤT LƯỢNG KHÔNG KHÍ HIỆN TẠI                      │    │
│  │                                                      │    │
│  │      ┌──────────────┐                               │    │
│  │      │              │                               │    │
│  │      │      85      │  ← AQI Number (Large, Yellow)│    │
│  │      │              │                               │    │
│  │      └──────────────┘                               │    │
│  │                                                      │    │
│  │      TRUNG BÌNH (Moderate)  ← Category              │    │
│  │      🟡 Chất lượng không khí chấp nhận được         │    │
│  │                                                      │    │
│  │  📋 KHUYẾN NGHỊ:                                    │    │
│  │  • Người bình thường: Có thể hoạt động bình thường │    │
│  │  • Nhóm nhạy cảm: Hạn chế hoạt động ngoài trời     │    │
│  │                                                      │    │
│  │  📊 XU HƯỚNG 24H:                                   │    │
│  │  [Chart showing AQI over last 24 hours]            │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Report Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│  BÁO CÁO CHẤT LƯỢNG KHÔNG KHÍ                               │
│                                                              │
│  [Hàng ngày ▼] [Tuần này ▼] [Tháng này ▼]  [Tạo báo cáo]  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Ngày        │ Loại    │ AQI TB │ Trạng thái │ Tải   │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │ 15/01/2024  │ Ngày    │ 85     │ ✅ Hoàn tất│ 📄 📊 │   │
│  │ 14/01/2024  │ Ngày    │ 92     │ ✅ Hoàn tất│ 📄 📊 │   │
│  │ 08-14/01    │ Tuần    │ 88     │ ✅ Hoàn tất│ 📄 📊 │   │
│  │ 01/2024     │ Tháng   │ 90     │ 🔄 Đang tạo│       │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  📧 NGƯỜI NHẬN EMAIL:                                       │
│  • admin@smartcity.vn (Hàng ngày, Tuần, Tháng)            │
│  • director@smartcity.vn (Tuần, Tháng)                     │
│  [+ Thêm người nhận]                                        │
└─────────────────────────────────────────────────────────────┘
```

### Incident Management Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│  QUẢN LÝ SỰ CỐ                                              │
│                                                              │
│  [Tất cả ▼] [Mới] [Đang xử lý] [Đã giải quyết]            │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 🔴 #INC-001 | Spike CO2 bất thường tại Quận 1       │   │
│  │    Mức độ: CRITICAL | Trạng thái: Đang xử lý        │   │
│  │    Phát hiện: 15/01 10:30 | Gán cho: Team A         │   │
│  │    Giá trị: 1500 ppm (dự kiến: 400 ppm)             │   │
│  │    [Xem chi tiết] [Cập nhật]                         │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │ 🟡 #INC-002 | Tiếng ồn cao tại Quận 3               │   │
│  │    Mức độ: WARNING | Trạng thái: Mới                │   │
│  │    Phát hiện: 15/01 11:00 | Chưa gán                │   │
│  │    [Xem chi tiết] [Gán người xử lý]                 │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  📊 THỐNG KÊ:                                               │
│  • Tổng sự cố: 45                                          │
│  • Đang xử lý: 8                                           │
│  • Thời gian xử lý TB: 4.5 giờ                             │
│  • Quá hạn (>24h): 2 ⚠️                                    │
└─────────────────────────────────────────────────────────────┘
```


---

## 🧪 Testing Strategy

### Unit Tests

**AQI Service Tests:**
```python
def test_calculate_aqi_good_range():
    """Test AQI calculation for Good range (0-50)."""
    service = AQIService()
    aqi = service.calculate_aqi('CO2', 350)
    assert 0 <= aqi <= 50
    
def test_calculate_aqi_hazardous_range():
    """Test AQI calculation for Hazardous range (301-500)."""
    service = AQIService()
    aqi = service.calculate_aqi('CO2', 1800)
    assert 301 <= aqi <= 500

def test_get_category_moderate():
    """Test category assignment for Moderate AQI."""
    service = AQIService()
    category = service.get_category(85)
    assert category['name'] == 'Moderate'
    assert category['color'] == '#ffff00'
```

**Report Service Tests:**
```python
def test_generate_daily_report():
    """Test daily report generation."""
    service = ReportService()
    report = service.generate_daily_report(date.today())
    assert report['summary']['avg_aqi'] is not None
    assert len(report['charts']) > 0

def test_export_to_pdf():
    """Test PDF export functionality."""
    service = ReportService()
    pdf_bytes = service.export_to_pdf('report_001')
    assert len(pdf_bytes) > 0
    assert pdf_bytes[:4] == b'%PDF'  # PDF magic number
```

**Anomaly Detection Tests:**
```python
def test_detect_zscore_anomaly():
    """Test Z-score anomaly detection."""
    service = AnomalyDetectionService()
    anomaly = service.detect_zscore_anomaly('sensor_001', 1500)
    assert anomaly is not None
    assert anomaly['severity'] in ['WARNING', 'CRITICAL', 'EMERGENCY']

def test_no_anomaly_for_normal_value():
    """Test that normal values don't trigger anomaly."""
    service = AnomalyDetectionService()
    anomaly = service.detect_zscore_anomaly('sensor_001', 420)
    assert anomaly is None
```

### Integration Tests

**End-to-End AQI Flow:**
```python
def test_aqi_calculation_flow():
    """Test complete AQI calculation flow from telemetry to API."""
    # 1. Publish telemetry
    telemetry = {"sensorId": "sensor_001", "co2": 850, "noise": 75}
    mqtt_client.publish("sensors/sensor_001/telemetry", json.dumps(telemetry))
    
    # 2. Wait for processing
    time.sleep(2)
    
    # 3. Query AQI via API
    response = requests.get("http://localhost:8000/api/aqi/current/district_001")
    assert response.status_code == 200
    data = response.json()
    assert data['aqi'] > 0
    assert data['category'] in ['Good', 'Moderate', 'Unhealthy', ...]
```

### Performance Tests

**AQI Calculation Performance:**
```python
def test_aqi_calculation_performance():
    """Test AQI calculation performance under load."""
    service = AQIService()
    
    start_time = time.time()
    for i in range(1000):
        service.calculate_aqi('CO2', 400 + i)
    end_time = time.time()
    
    avg_time = (end_time - start_time) / 1000
    assert avg_time < 0.001  # < 1ms per calculation
```


---

## 🚀 Deployment Guide

### Environment Variables

```bash
# .env additions

# AQI Configuration
AQI_CALCULATION_ENABLED=true
AQI_UPDATE_INTERVAL=5  # seconds

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=smartcity@example.com
SMTP_PASSWORD=your_password
SMTP_FROM_EMAIL=smartcity@example.com
SMTP_FROM_NAME=Smart City IoT Dashboard

# SMS Configuration (Optional)
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890

# Report Configuration
REPORT_STORAGE_PATH=/app/reports
REPORT_GENERATION_TIME=00:00  # Daily at midnight
REPORT_RETENTION_DAYS=90

# Anomaly Detection Configuration
ANOMALY_DETECTION_ENABLED=true
ANOMALY_ZSCORE_THRESHOLD=3.0
ANOMALY_RATE_CHANGE_THRESHOLD=0.5
ANOMALY_MIN_DATA_POINTS=30

# Notification Configuration
NOTIFICATION_EMAIL_ENABLED=true
NOTIFICATION_SMS_ENABLED=false
NOTIFICATION_MAX_RETRIES=3
```

### Docker Compose Updates

```yaml
# docker-compose.yml additions

services:
  backend:
    environment:
      # ... existing env vars ...
      - AQI_CALCULATION_ENABLED=${AQI_CALCULATION_ENABLED}
      - SMTP_HOST=${SMTP_HOST}
      - SMTP_PORT=${SMTP_PORT}
      - SMTP_USERNAME=${SMTP_USERNAME}
      - SMTP_PASSWORD=${SMTP_PASSWORD}
    volumes:
      - ./reports:/app/reports  # Mount for report storage
```

### Database Migration

```sql
-- Run these SQL scripts in order:

-- 1. Create AQI tables
\i backend/app/db/sql/create_aqi_tables.sql

-- 2. Create Report tables
\i backend/app/db/sql/create_report_tables.sql

-- 3. Create Anomaly tables
\i backend/app/db/sql/create_anomaly_tables.sql

-- 4. Seed initial data (optional)
\i backend/app/db/sql/seed_notification_channels.sql
```

### Startup Checklist

1. ✅ Update environment variables in `.env`
2. ✅ Run database migrations
3. ✅ Configure SMTP server credentials
4. ✅ Test email sending
5. ✅ Verify report storage directory exists
6. ✅ Restart backend service
7. ✅ Verify AQI calculation in logs
8. ✅ Check first daily report generation
9. ✅ Test anomaly detection with spike data
10. ✅ Verify all API endpoints


---

## 📚 User Documentation

### Hướng Dẫn Sử Dụng Cho Người Dùng Cuối

#### Xem Chỉ Số AQI

1. Truy cập dashboard tại `http://localhost:3000`
2. Xem chỉ số AQI hiện tại ở góc trên bên phải
3. Màu sắc cho biết mức độ:
   - 🟢 Xanh: Tốt (0-50)
   - 🟡 Vàng: Trung bình (51-100)
   - 🟠 Cam: Không tốt cho nhóm nhạy cảm (101-150)
   - 🔴 Đỏ: Kém (151-200)
   - 🟣 Tím: Rất kém (201-300)
   - 🟤 Nâu: Nguy hại (301-500)

#### Đọc Báo Cáo

1. Vào menu "Báo cáo"
2. Chọn loại báo cáo (Ngày/Tuần/Tháng)
3. Click vào báo cáo để xem chi tiết
4. Download PDF hoặc Excel nếu cần

#### Quản Lý Sự Cố (Dành cho Admin)

1. Vào menu "Sự cố"
2. Xem danh sách sự cố đang xử lý
3. Click vào sự cố để xem chi tiết
4. Cập nhật trạng thái và thêm ghi chú
5. Đánh dấu "Đã giải quyết" khi hoàn tất

### Hướng Dẫn Cấu Hình Cho Admin

#### Thêm Người Nhận Email

```bash
# Via API
curl -X POST http://localhost:8000/api/reports/recipients \
  -H "Content-Type: application/json" \
  -d '{
    "email": "director@smartcity.vn",
    "name": "Giám đốc",
    "reportTypes": "DAILY,WEEKLY,MONTHLY"
  }'
```

#### Cấu Hình Ngưỡng Cảnh Báo

```python
# backend/app/core/config.py

class Settings(BaseSettings):
    # ... existing settings ...
    
    # Anomaly detection thresholds
    anomaly_zscore_threshold: float = 3.0
    anomaly_rate_change_threshold: float = 0.5
    
    # Alert severity thresholds
    alert_critical_zscore: float = 4.0
    alert_emergency_zscore: float = 5.0
```


---

## 🎓 Tài Liệu Tham Khảo

### AQI Standards
- [US EPA Air Quality Index](https://www.airnow.gov/aqi/aqi-basics/)
- [Vietnam Air Quality Standards](https://thuvienphapluat.vn/van-ban/Tai-nguyen-Moi-truong/Quyet-dinh-1459-QD-TTg-2019-phe-duyet-Chuong-trinh-quan-trac-moi-truong-quoc-gia-giai-doan-2016-2020-427895.aspx)
- [WHO Air Quality Guidelines](https://www.who.int/news-room/feature-stories/detail/what-are-the-who-air-quality-guidelines)

### Technical References
- [ReportLab Documentation](https://www.reportlab.com/docs/reportlab-userguide.pdf)
- [OpenPyXL Documentation](https://openpyxl.readthedocs.io/)
- [APScheduler Documentation](https://apscheduler.readthedocs.io/)
- [Twilio SMS API](https://www.twilio.com/docs/sms)

### Anomaly Detection
- [Statistical Anomaly Detection](https://en.wikipedia.org/wiki/Anomaly_detection)
- [Z-Score Method](https://en.wikipedia.org/wiki/Standard_score)
- [Time Series Anomaly Detection](https://towardsdatascience.com/time-series-anomaly-detection-with-python-e7d4c5c3c5b5)

---

## 💡 Lợi Ích Thực Tiễn

### Cho Người Dân
✅ **Hiểu rõ chất lượng không khí:** AQI dễ hiểu hơn số liệu thô
✅ **Bảo vệ sức khỏe:** Khuyến nghị cụ thể cho từng nhóm người
✅ **Lập kế hoạch hoạt động:** Biết khi nào nên/không nên ra ngoài

### Cho Chính Quyền
✅ **Ra quyết định dựa trên dữ liệu:** Báo cáo định kỳ với xu hướng
✅ **Phản ứng nhanh với sự cố:** Phát hiện bất thường tự động
✅ **Quản lý hiệu quả:** Theo dõi và xử lý sự cố có hệ thống
✅ **Minh bạch:** Báo cáo công khai cho người dân

### Cho Nhà Nghiên Cứu
✅ **Dữ liệu lịch sử:** Export Excel để phân tích
✅ **Phát hiện pattern:** Anomaly detection giúp tìm ra quy luật
✅ **So sánh xu hướng:** Báo cáo tuần/tháng cho nghiên cứu dài hạn

---

## 🎯 Kết Luận

Đặc tả này mô tả 3 tính năng thiết thực nhất để nâng cấp Smart City IoT Dashboard:

1. **AQI System:** Chuyển đổi dữ liệu thô thành thông tin dễ hiểu
2. **Reporting System:** Tự động hóa báo cáo và phân tích xu hướng
3. **Anomaly Detection:** Phát hiện sự cố sớm và quản lý hiệu quả

Các tính năng này:
- ✅ Giải quyết vấn đề thực tế
- ✅ Dễ triển khai (7 tuần)
- ✅ Tạo giá trị ngay lập tức
- ✅ Phù hợp với đồ án

**Bước tiếp theo:** Bắt đầu triển khai Phase 1 (AQI System) trong tuần tới.

---

**Tác giả:** Kiro AI Assistant  
**Ngày tạo:** 2024-01-15  
**Phiên bản:** 1.0  
**Trạng thái:** Ready for Implementation
