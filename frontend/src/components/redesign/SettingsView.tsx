import React from 'react';

const SettingsView: React.FC = () => {
  return (
    <div className="settings-view">
      <div className="view-header">
        <div>
          <h1 className="view-title">Cài Đặt</h1>
          <p className="view-subtitle">Cấu hình hệ thống và tùy chọn</p>
        </div>
      </div>

      <div className="settings-content">
        <div className="settings-section">
          <h2 className="settings-section-title">Hiển Thị</h2>
          <div className="settings-item">
            <div className="settings-item-info">
              <span className="settings-item-label">Chế Độ Tối</span>
              <span className="settings-item-description">Sử dụng giao diện tối</span>
            </div>
            <label className="toggle-switch">
              <input type="checkbox" defaultChecked />
              <span className="toggle-slider"></span>
            </label>
          </div>
          <div className="settings-item">
            <div className="settings-item-info">
              <span className="settings-item-label">Ngôn Ngữ</span>
              <span className="settings-item-description">Chọn ngôn ngữ hiển thị</span>
            </div>
            <select className="settings-select">
              <option value="vi">Tiếng Việt</option>
              <option value="en">English</option>
            </select>
          </div>
        </div>

        <div className="settings-section">
          <h2 className="settings-section-title">Cảnh Báo</h2>
          <div className="settings-item">
            <div className="settings-item-info">
              <span className="settings-item-label">Thông Báo Âm Thanh</span>
              <span className="settings-item-description">Phát âm thanh khi có cảnh báo mới</span>
            </div>
            <label className="toggle-switch">
              <input type="checkbox" defaultChecked />
              <span className="toggle-slider"></span>
            </label>
          </div>
          <div className="settings-item">
            <div className="settings-item-info">
              <span className="settings-item-label">Ngưỡng PM2.5</span>
              <span className="settings-item-description">Giá trị ngưỡng cảnh báo PM2.5 (µg/m³)</span>
            </div>
            <input type="number" className="settings-input" defaultValue={50} />
          </div>
        </div>

        <div className="settings-section">
          <h2 className="settings-section-title">Bản Đồ</h2>
          <div className="settings-item">
            <div className="settings-item-info">
              <span className="settings-item-label">Tự Động Cập Nhật</span>
              <span className="settings-item-description">Cập nhật dữ liệu bản đồ tự động</span>
            </div>
            <label className="toggle-switch">
              <input type="checkbox" defaultChecked />
              <span className="toggle-slider"></span>
            </label>
          </div>
          <div className="settings-item">
            <div className="settings-item-info">
              <span className="settings-item-label">Tần Suất Cập Nhật</span>
              <span className="settings-item-description">Khoảng thời gian cập nhật (giây)</span>
            </div>
            <input type="number" className="settings-input" defaultValue={5} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsView;
