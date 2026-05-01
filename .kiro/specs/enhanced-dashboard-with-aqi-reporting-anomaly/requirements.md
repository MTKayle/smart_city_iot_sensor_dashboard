# Requirements Document

## Introduction

This document specifies requirements for enhancing the Smart City IoT Dashboard with three major features: Air Quality Index (AQI) System, Automated Reporting & Statistics, and Intelligent Anomaly Detection & Alerting. These enhancements transform the dashboard from a technical demo into a practical solution serving citizens and government officials.

The system currently provides real-time monitoring of CO2, Noise, and Temperature metrics across Ho Chi Minh City districts. This enhancement adds standardized air quality assessment, automated reporting capabilities, and intelligent incident management to deliver actionable insights and proactive environmental monitoring.

## Glossary

- **AQI_System**: Air Quality Index calculation and visualization system following US EPA standards
- **Dashboard**: Web-based user interface displaying real-time environmental data and analytics
- **Telemetry_Processor**: Backend service that processes incoming sensor data
- **Report_Generator**: Service that creates automated daily, weekly, and monthly reports
- **Anomaly_Detector**: Service that identifies unusual patterns in sensor data using statistical methods
- **Incident_Manager**: System for tracking and resolving environmental incidents
- **Notification_Service**: Multi-channel alert delivery system (Dashboard, Email, SMS)
- **WebSocket_Broadcaster**: Real-time data push mechanism to connected clients
- **Oracle_Database**: Relational database storing location hierarchy, sensors, alerts, and summaries
- **MongoDB_Database**: Time-series database storing telemetry readings
- **Breakpoint**: Threshold value defining AQI category boundaries
- **Z-Score**: Statistical measure of how many standard deviations a value is from the mean
- **Spike**: Sudden abnormal increase in sensor readings
- **Deduplication_Window**: Time period (5 minutes) during which duplicate alerts are suppressed
- **Clean_Score**: Existing composite metric ranking location environmental quality (0-100)
- **SLA**: Service Level Agreement defining expected incident resolution time

---

## Requirements

### Requirement 1: Air Quality Index (AQI) Calculation System

**User Story:** As a citizen, I want to see air quality expressed as a standardized AQI value with color coding and health recommendations, so that I can easily understand environmental conditions and make informed decisions about outdoor activities.

#### Acceptance Criteria

1. WHEN telemetry data is received, THE AQI_System SHALL calculate AQI values for CO2 and Noise metrics using US EPA breakpoint formula
2. THE AQI_System SHALL use the highest AQI value among all pollutants as the overall location AQI
3. THE AQI_System SHALL assign one of six categories (Good, Moderate, Unhealthy for Sensitive Groups, Unhealthy, Very Unhealthy, Hazardous) based on AQI value
4. THE AQI_System SHALL store AQI readings in Oracle_Database with timestamp and location reference
5. THE AQI_System SHALL update AQI calculations every 5 seconds synchronized with telemetry frequency
6. WHEN sensor data is missing or out-of-range, THE AQI_System SHALL handle gracefully by using last known valid value or marking as unavailable
7. THE AQI_System SHALL provide health recommendations in Vietnamese for general public and sensitive groups based on AQI category

### Requirement 2: AQI Visualization on Dashboard

**User Story:** As a dashboard user, I want to see AQI displayed prominently with intuitive color coding and visual indicators, so that I can quickly assess air quality across different districts.

#### Acceptance Criteria

1. THE Dashboard SHALL display current AQI value as a large number with category-specific color coding
2. THE Dashboard SHALL show AQI category name in Vietnamese with corresponding icon
3. THE Dashboard SHALL display health recommendations for current AQI level
4. THE Dashboard SHALL color-code district polygons on the map based on AQI category (not just alert status)
5. THE Dashboard SHALL render an AQI trend chart showing last 24 hours of data
6. THE Dashboard SHALL display an AQI gauge visualization showing current value on 0-500 scale
7. WHEN user hovers over a district, THE Dashboard SHALL show AQI value in tooltip alongside existing metrics

### Requirement 3: AQI REST API Endpoints

**User Story:** As a developer or external system, I want to access AQI data through REST API endpoints, so that I can integrate air quality information into other applications.

#### Acceptance Criteria

1. THE AQI_System SHALL provide GET /api/aqi/current endpoint returning current AQI for all locations
2. THE AQI_System SHALL provide GET /api/aqi/current/{locationId} endpoint returning current AQI for specific location
3. THE AQI_System SHALL provide GET /api/aqi/history/{locationId} endpoint with start_time and end_time query parameters
4. THE API SHALL return AQI data in JSON format including aqi value, category, color, dominant pollutant, and health recommendations
5. THE API SHALL return HTTP 400 for invalid parameters with descriptive error message
6. THE API SHALL return HTTP 404 when location is not found
7. THE API SHALL include CORS headers to allow cross-origin requests

### Requirement 4: Automated Daily Report Generation

**User Story:** As a government official, I want to receive automated daily air quality reports, so that I can review environmental conditions without manually checking the dashboard.

#### Acceptance Criteria

1. THE Report_Generator SHALL create daily reports automatically at 00:00 every day
2. THE Report SHALL include data from previous 24 hours with city-wide average AQI
3. THE Report SHALL calculate hours spent in each AQI category
4. THE Report SHALL identify best and worst performing districts by AQI
5. THE Report SHALL list notable events including AQI spikes and threshold violations
6. THE Report SHALL include AQI trend chart for 24-hour period
7. THE Report SHALL include comparison chart showing AQI across all districts
8. THE Report_Generator SHALL store report metadata in Oracle_Database with generation timestamp and status
9. WHEN data is missing for a time period, THE Report_Generator SHALL note the gap and continue with available data

### Requirement 5: Weekly and Monthly Report Generation

**User Story:** As a city manager, I want to receive weekly and monthly summary reports with trend analysis, so that I can identify long-term patterns and make strategic decisions.

#### Acceptance Criteria

1. THE Report_Generator SHALL create weekly reports every Monday at 00:00
2. THE Report_Generator SHALL create monthly reports on the 1st day of each month at 00:00
3. THE Weekly_Report SHALL include 7-day average AQI with comparison to previous week showing percentage change
4. THE Weekly_Report SHALL identify best and worst days by AQI
5. THE Monthly_Report SHALL include 30-day average AQI with comparison to previous month
6. THE Monthly_Report SHALL provide week-by-week breakdown showing AQI trends
7. THE Report SHALL highlight significant changes defined as greater than 20 percent increase or decrease
8. THE Report SHALL include recommendations for improvement based on identified patterns

### Requirement 6: Report Export to PDF and Excel

**User Story:** As a report consumer, I want to download reports in PDF and Excel formats, so that I can share them in meetings or perform custom analysis.

#### Acceptance Criteria

1. THE Report_Generator SHALL provide API endpoint GET /api/reports/{reportId}/pdf to export reports as PDF
2. THE Report_Generator SHALL provide API endpoint GET /api/reports/{reportId}/excel to export reports as Excel
3. THE PDF SHALL include header with logo, title, and date
4. THE PDF SHALL include summary section, data tables, and charts with proper formatting
5. THE PDF SHALL include footer with signature line and notes section
6. THE Excel SHALL include three sheets: Summary, Detailed Data, and Charts
7. THE Excel SHALL format tables with color coding and include pivot table capabilities
8. THE Export SHALL complete within 10 seconds for monthly reports
9. THE Export SHALL return HTTP 500 with error message if generation fails

### Requirement 7: Automated Email Report Delivery

**User Story:** As a stakeholder, I want to receive reports automatically via email, so that I am notified of air quality conditions without needing to access the dashboard.

#### Acceptance Criteria

1. THE Notification_Service SHALL send email reports automatically based on configured schedule
2. THE Notification_Service SHALL support multiple recipients configured in Oracle_Database
3. THE Email SHALL include executive summary with key metrics in email body
4. THE Email SHALL attach PDF report as file attachment
5. THE Email SHALL use Vietnamese language template with professional formatting
6. THE Notification_Service SHALL retry failed email sends with maximum 3 attempts
7. THE Notification_Service SHALL log email delivery status in Oracle_Database
8. WHEN email delivery fails after all retries, THE Notification_Service SHALL log error and continue with next recipient

### Requirement 8: Report Management Dashboard

**User Story:** As an administrator, I want a dashboard to view and manage generated reports, so that I can access historical reports and configure report settings.

#### Acceptance Criteria

1. THE Dashboard SHALL display list of generated reports with columns for date, type, average AQI, status, and download links
2. THE Dashboard SHALL allow filtering by date range and report type (Daily, Weekly, Monthly)
3. THE Dashboard SHALL provide preview functionality to view report content without downloading
4. THE Dashboard SHALL allow download in both PDF and Excel formats
5. THE Dashboard SHALL show report generation status (Pending, Completed, Failed)
6. THE Dashboard SHALL display list of email recipients with their configured report types
7. THE Dashboard SHALL allow adding new recipients with email address, name, and report type preferences

### Requirement 9: Statistical Anomaly Detection Using Z-Score

**User Story:** As a monitoring operator, I want the system to automatically detect unusual sensor readings, so that I can investigate potential equipment failures or environmental incidents.

#### Acceptance Criteria

1. THE Anomaly_Detector SHALL calculate Z-score for each new telemetry reading using mean and standard deviation of last 100 readings
2. WHEN absolute Z-score exceeds 3.0, THE Anomaly_Detector SHALL classify reading as anomalous
3. THE Anomaly_Detector SHALL require minimum 30 historical readings before performing Z-score detection
4. THE Anomaly_Detector SHALL create anomaly record in Oracle_Database with detection method, value, expected value, and deviation
5. THE Anomaly_Detector SHALL assign severity level (INFO, WARNING, CRITICAL, EMERGENCY) based on Z-score magnitude
6. WHEN Z-score exceeds 5.0, THE Anomaly_Detector SHALL assign EMERGENCY severity
7. WHEN Z-score exceeds 4.0, THE Anomaly_Detector SHALL assign CRITICAL severity
8. WHEN Z-score exceeds 3.0, THE Anomaly_Detector SHALL assign WARNING severity

### Requirement 10: Rate-of-Change Anomaly Detection

**User Story:** As a safety officer, I want to be alerted when sensor values change rapidly, so that I can respond quickly to sudden environmental events.

#### Acceptance Criteria

1. THE Anomaly_Detector SHALL calculate rate of change by comparing current reading to reading from 1 minute ago
2. WHEN rate of change exceeds 50 percent within 1 minute, THE Anomaly_Detector SHALL classify as anomalous
3. WHEN rate of change exceeds 100 percent within 1 minute, THE Anomaly_Detector SHALL assign CRITICAL severity
4. WHEN rate of change exceeds 50 percent but less than 100 percent, THE Anomaly_Detector SHALL assign WARNING severity
5. THE Anomaly_Detector SHALL create anomaly record with RATE_OF_CHANGE detection method
6. THE Anomaly_Detector SHALL handle missing previous reading by skipping rate-of-change detection for that reading

### Requirement 11: Multi-Level Alert Notification System

**User Story:** As a stakeholder, I want to receive alerts through appropriate channels based on severity, so that I can respond appropriately to different types of incidents.

#### Acceptance Criteria

1. THE Notification_Service SHALL classify alerts into four severity levels: INFO, WARNING, CRITICAL, EMERGENCY
2. FOR INFO alerts, THE Notification_Service SHALL send notifications via Dashboard only
3. FOR WARNING alerts, THE Notification_Service SHALL send notifications via Dashboard and Email
4. FOR CRITICAL alerts, THE Notification_Service SHALL send notifications via Dashboard, Email, and SMS
5. FOR EMERGENCY alerts, THE Notification_Service SHALL send notifications via Dashboard, Email, SMS, and Phone Call
6. THE Notification SHALL include location, metric type, measured value, and recommended action
7. THE Notification_Service SHALL prevent alert spam by limiting to maximum 1 alert per sensor per 5 minutes
8. THE Notification_Service SHALL log all notification deliveries in Oracle_Database with delivery status

### Requirement 12: Automated Incident Creation and Management

**User Story:** As an incident manager, I want the system to automatically create incident tickets for critical anomalies, so that I can track and resolve environmental issues systematically.

#### Acceptance Criteria

1. WHEN anomaly with CRITICAL or EMERGENCY severity is detected, THE Incident_Manager SHALL create incident automatically
2. THE Incident_Manager SHALL generate unique incident ID using UUID format
3. THE Incident_Manager SHALL assign incident to responsible team based on location mapping
4. THE Incident_Manager SHALL send notification to assigned team members
5. THE Incident SHALL track status through workflow: NEW, ASSIGNED, IN_PROGRESS, RESOLVED, CLOSED
6. THE Incident_Manager SHALL record timestamp for each status transition
7. THE Incident_Manager SHALL calculate resolution time as duration from creation to RESOLVED status
8. THE Incident_Manager SHALL allow adding notes and attachments to incidents
9. WHEN incident remains in NEW or ASSIGNED status for more than 24 hours, THE Incident_Manager SHALL mark as overdue

### Requirement 13: Incident Management Dashboard

**User Story:** As an incident responder, I want a dashboard to view and update incidents, so that I can efficiently manage environmental issues.

#### Acceptance Criteria

1. THE Dashboard SHALL display list of incidents with filters for status, severity, and location
2. THE Dashboard SHALL show incident details including timeline of status changes
3. THE Dashboard SHALL allow updating incident status with dropdown selection
4. THE Dashboard SHALL allow adding notes with author name and timestamp
5. THE Dashboard SHALL display incident statistics including total count, in-progress count, and average resolution time
6. THE Dashboard SHALL highlight overdue incidents with visual indicator
7. THE Dashboard SHALL allow assigning incidents to team members with dropdown selection
8. THE Dashboard SHALL display incident history showing all status changes and notes in chronological order

### Requirement 14: Root Cause Analysis for Anomalies

**User Story:** As an analyst, I want the system to suggest possible root causes for anomalies, so that I can investigate incidents more efficiently.

#### Acceptance Criteria

1. THE Anomaly_Detector SHALL analyze time of day, day of week, and location when anomaly occurs
2. THE Anomaly_Detector SHALL query historical incidents for similar patterns in same location
3. THE Anomaly_Detector SHALL provide list of possible root causes with confidence scores
4. THE Anomaly_Detector SHALL suggest similar past incidents with their documented root causes
5. THE Anomaly_Detector SHALL recommend actions based on identified root cause patterns
6. WHEN incident is resolved, THE Incident_Manager SHALL store documented root cause in knowledge base
7. THE Anomaly_Detector SHALL learn from resolved incidents by updating root cause patterns

### Requirement 15: Enhanced Dashboard UI Redesign

**User Story:** As a dashboard user, I want a modern, intuitive interface with clear visual hierarchy, so that I can quickly understand system status and access key features.

#### Acceptance Criteria

1. THE Dashboard SHALL display system overview panel with key metrics: average AQI, active alerts count, incident count, and sensor online count
2. THE Dashboard SHALL render full-screen map with AQI-based color coding as primary visual element
3. THE Dashboard SHALL display real-time trend charts for selected location in side panel
4. THE Dashboard SHALL show live alerts list with severity indicators and timestamps
5. THE Dashboard SHALL display district ranking by AQI with top 3 highlighted
6. THE Dashboard SHALL provide navigation to Report Management dashboard
7. THE Dashboard SHALL provide navigation to Incident Management dashboard
8. THE Dashboard SHALL use consistent color scheme: green for good, yellow for moderate, orange for unhealthy, red for very unhealthy, purple for hazardous
9. THE Dashboard SHALL update all visualizations in real-time via WebSocket without page refresh
10. THE Dashboard SHALL be responsive and functional on desktop screens with minimum 1280x720 resolution

---

## Parser and Serializer Requirements

### Requirement 16: AQI Data Serialization

**User Story:** As a system integrator, I want AQI data to be serialized consistently in JSON format, so that external systems can reliably parse the data.

#### Acceptance Criteria

1. THE AQI_System SHALL serialize AQI readings to JSON format with fields: locationId, aqi, category, categoryVi, color, dominantPollutant, healthRecommendation, timestamp
2. THE AQI_System SHALL parse incoming telemetry JSON with fields: sensorId, locationId, co2, noise, temperature, timestamp
3. THE JSON_Serializer SHALL format timestamp fields in ISO 8601 format with timezone
4. THE JSON_Serializer SHALL format numeric fields with maximum 2 decimal places
5. FOR ALL valid AQI objects, THE System SHALL satisfy round-trip property: parse(serialize(aqi)) produces equivalent object
6. WHEN JSON parsing fails, THE System SHALL return HTTP 400 with descriptive error message indicating invalid field

### Requirement 17: Report Data Export Serialization

**User Story:** As a data analyst, I want report data exported in standard formats, so that I can import it into analysis tools.

#### Acceptance Criteria

1. THE Report_Generator SHALL serialize report data to PDF format using ReportLab library
2. THE Report_Generator SHALL serialize report data to Excel format using OpenPyXL library
3. THE Excel_Serializer SHALL format date columns with DD/MM/YYYY format
4. THE Excel_Serializer SHALL format numeric columns with appropriate decimal places and thousand separators
5. FOR ALL valid Report objects, THE System SHALL satisfy round-trip property: parsing exported Excel data produces equivalent summary statistics
6. WHEN PDF generation fails, THE System SHALL log error with stack trace and return HTTP 500

---

