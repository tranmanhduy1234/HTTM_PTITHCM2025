from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QHeaderView, QGroupBox, QComboBox, QFrame)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QFont, QColor, QPainter, QPen, QBrush
import random
from datetime import datetime, timedelta
from services.statistics_service import get_daily_drowsy_frequency, get_hourly_drowsy_frequency, \
    get_daily_detail_statistics


class SimpleChartWidget(QWidget):
    """Widget vẽ chart đơn giản bằng QPainter"""

    def __init__(self, title="Chart", parent=None):
        super().__init__(parent)
        self.title = title
        self.data = []
        self.labels = []
        self.setMinimumHeight(200)
        self.setStyleSheet("background-color: white;")

    def set_data(self, labels, data):
        """Set dữ liệu cho chart"""
        self.labels = labels
        self.data = data
        self.update()

    def paintEvent(self, event):
        """Vẽ chart"""
        if not self.data:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Margins
        margin_left = 40
        margin_right = 20
        margin_top = 30
        margin_bottom = 30

        width = self.width() - margin_left - margin_right
        height = self.height() - margin_top - margin_bottom

        # Draw title
        painter.setFont(QFont('Arial', 10, QFont.Bold))
        painter.drawText(10, 15, self.title)

        # Draw axes
        painter.setPen(QPen(QColor("#34495e"), 2))
        painter.drawLine(margin_left, margin_top, margin_left, margin_top + height)
        painter.drawLine(margin_left, margin_top + height, margin_left + width, margin_top + height)

        if not self.data:
            return

        # Find max value
        max_val = max(self.data) if self.data else 1
        if max_val == 0:
            max_val = 1

        # Draw bars
        bar_width = width / len(self.data) * 0.8
        spacing = width / len(self.data)

        for i, value in enumerate(self.data):
            bar_height = (value / max_val) * height * 0.9
            x = margin_left + i * spacing + spacing * 0.1
            y = margin_top + height - bar_height

            # Color based on value
            if value < max_val * 0.3:
                color = QColor("#27ae60")
            elif value < max_val * 0.6:
                color = QColor("#f39c12")
            else:
                color = QColor("#e74c3c")

            painter.setBrush(QBrush(color))
            painter.setPen(QPen(color.darker(120), 1))
            painter.drawRect(int(x), int(y), int(bar_width), int(bar_height))

            # Draw value on top
            painter.setFont(QFont('Arial', 7))
            painter.setPen(QPen(QColor("#2c3e50")))
            painter.drawText(int(x), int(y - 5), int(bar_width), 15,
                             Qt.AlignCenter, str(value))

        # Draw labels
        painter.setFont(QFont('Arial', 7))
        for i, label in enumerate(self.labels):
            x = margin_left + i * spacing
            painter.drawText(int(x), margin_top + height + 5,
                             int(spacing), 20, Qt.AlignCenter, str(label))


class StatisticsView(QWidget):
    """View thống kê - Hiển thị biểu đồ và bảng thống kê lịch sử buồn ngủ"""

    back_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.current_user = None
        self.init_ui()

    def init_ui(self):
        """Khởi tạo giao diện"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Header
        header_layout = self.create_header()
        main_layout.addLayout(header_layout)

        # Stats cards
        stats_cards_layout = self.create_stats_cards()
        # main_layout.addLayout(stats_cards_layout)

        # Content
        content_layout = QHBoxLayout()
        content_layout.setSpacing(10)

        # Bên trái: Charts
        charts_widget = self.create_charts()
        content_layout.addWidget(charts_widget, 60)

        # Bên phải: Detail table
        table_widget = self.create_detail_table()
        content_layout.addWidget(table_widget, 40)

        main_layout.addLayout(content_layout, 1)

        self.setLayout(main_layout)

    def create_header(self):
        """Tạo header"""
        layout = QHBoxLayout()

        title_label = QLabel("📊 THỐNG KÊ LỊCH SỬ BUỒN NGỦ")
        title_label.setFont(QFont('Arial', 14, QFont.Bold))
        title_label.setStyleSheet("color: #2c3e50;")

        filter_label = QLabel("Thời gian:")
        filter_label.setFont(QFont('Arial', 9))

        self.time_filter = QComboBox()
        self.time_filter.addItems(['7 ngày qua', '30 ngày qua', '3 tháng qua', 'Tất cả'])
        self.time_filter.setMinimumWidth(120)
        self.time_filter.setMaximumHeight(30)
        self.time_filter.currentIndexChanged.connect(self.load_data)

        back_button = QPushButton("← Quay lại")
        back_button.setMaximumHeight(30)
        back_button.setMinimumWidth(100)
        back_button.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 15px;
                font-weight: bold;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        back_button.clicked.connect(self.back_signal.emit)

        layout.addWidget(title_label)
        layout.addStretch()
        layout.addWidget(filter_label)
        layout.addWidget(self.time_filter)
        layout.addWidget(back_button)

        return layout

    def create_stats_cards(self):
        """Tạo các card thống kê"""
        layout = QHBoxLayout()
        layout.setSpacing(10)

        card1 = self.create_stat_card("Tổng cảnh báo", "0", "lần", "#e74c3c", "⚠️")
        self.total_alerts_label = card1.findChild(QLabel, "value_label")

        card2 = self.create_stat_card("Xác nhận", "0%", "của tổng số", "#e67e22", "✅")
        self.confirm_rate_label = card2.findChild(QLabel, "value_label")

        card3 = self.create_stat_card("Tổng TG", "0h 0m", "lái xe", "#3498db", "⏱️")
        self.total_time_label = card3.findChild(QLabel, "value_label")

        card4 = self.create_stat_card("TB cảnh báo", "0 phút", "từ bắt đầu", "#27ae60", "📈")
        self.avg_time_label = card4.findChild(QLabel, "value_label")

        layout.addWidget(card1)
        layout.addWidget(card2)
        layout.addWidget(card3)
        layout.addWidget(card4)

        return layout

    def create_stat_card(self, title, value, subtitle, color, icon):
        """Tạo một card thống kê"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-left: 4px solid {color};
                border-radius: 5px;
                padding: 8px;
            }}
        """)
        card.setMaximumHeight(100)

        layout = QVBoxLayout(card)
        layout.setSpacing(3)
        layout.setContentsMargins(5, 5, 5, 5)

        header_layout = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setFont(QFont('Arial', 16))

        title_label = QLabel(title)
        title_label.setFont(QFont('Arial', 8))
        title_label.setStyleSheet("color: #7f8c8d;")

        header_layout.addWidget(icon_label)
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        value_label = QLabel(value)
        value_label.setObjectName("value_label")
        value_label.setFont(QFont('Arial', 18, QFont.Bold))
        value_label.setStyleSheet(f"color: {color};")

        subtitle_label = QLabel(subtitle)
        subtitle_label.setFont(QFont('Arial', 7))
        subtitle_label.setStyleSheet("color: #95a5a6;")

        layout.addLayout(header_layout)
        layout.addWidget(value_label)
        layout.addWidget(subtitle_label)

        return card

    def create_charts(self):
        """Tạo khu vực biểu đồ - DÙNG QPainter"""
        group = QGroupBox("📈 Biểu đồ phân tích")
        group.setFont(QFont('Arial', 10, QFont.Bold))
        group.setStyleSheet("""
            QGroupBox {
                background-color: white;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                margin-top: 8px;
                padding-top: 12px;
            }
            QGroupBox::title {
                color: #2c3e50;
            }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(10)

        # Chart 1: Theo ngày
        self.chart1 = SimpleChartWidget("Số lần cảnh báo theo ngày")
        layout.addWidget(self.chart1, 1)

        # Chart 2: Theo giờ
        self.chart2 = SimpleChartWidget("Phân bố theo giờ trong ngày")
        layout.addWidget(self.chart2, 1)

        group.setLayout(layout)
        return group

    def create_detail_table(self):
        """Tạo bảng chi tiết"""
        group = QGroupBox("📋 Chi tiết theo ngày")
        group.setFont(QFont('Arial', 10, QFont.Bold))
        group.setStyleSheet("""
            QGroupBox {
                background-color: white;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                margin-top: 8px;
                padding-top: 12px;
            }
            QGroupBox::title {
                color: #2c3e50;
            }
        """)

        layout = QVBoxLayout()

        self.detail_table = QTableWidget()
        self.detail_table.setColumnCount(4)
        self.detail_table.setHorizontalHeaderLabels(['Ngày', 'Cảnh báo', 'Xác nhận', 'TG lái'])

        self.detail_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 1px solid #bdc3c7;
                gridline-color: #ecf0f1;
                font-size: 9px;
            }
            QTableWidget::item {
                padding: 3px;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 5px;
                border: none;
                font-weight: bold;
                font-size: 9px;
            }
        """)

        self.detail_table.verticalHeader().setDefaultSectionSize(25)
        self.detail_table.verticalHeader().setVisible(False)

        header = self.detail_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)

        layout.addWidget(self.detail_table)

        group.setLayout(layout)
        return group

    def load_data(self):
        """Tải dữ liệu giả lập"""
        try:
            time_filter = self.time_filter.currentText()
            if '7 ngày' in time_filter:
                days = 7
            elif '30 ngày' in time_filter:
                days = 30
            elif '3 tháng' in time_filter:
                days = 90
            else:
                days = 180

            # load data from service (replace with real calls)
            user_id = self.current_user["id"] if self.current_user else 0
            daily_stats = get_daily_drowsy_frequency(user_id, days=days)
            detail = get_daily_detail_statistics(user_id, days=days)
            hourly_stats = get_hourly_drowsy_frequency(user_id)
            print(daily_stats)
            print(hourly_stats)
            # Update charts
            self.update_charts((daily_stats, hourly_stats))

            # Update table
            self.update_detail_table(detail)

        except Exception as e:
            print(f"⚠️ Lỗi load data: {e}")

    def update_charts(self, datas):
        """Cập nhật biểu đồ"""
        data1, data2 = datas

        fomat_date = lambda x: datetime.strptime(x, "%Y-%m-%d").strftime("%d/%m")
        fomat_time = lambda x: datetime.strptime(x, "%Y-%m-%d %H:%M").strftime("%H:%M")
        try:
            # Chart 1: Theo ngày
            dates = [fomat_date(data["date"]) for data in data1]
            alerts = [data["count"] for data in data1]

            self.chart1.set_data(dates, alerts)

            # Chart 2: Theo giờ
            hours = [fomat_time(data["hour"]) for data in data2]
            counts = [data["count"] for data in data2]

            self.chart2.set_data(hours, counts)

        except Exception as e:
            print(f"⚠️ Lỗi update charts: {e}")

    def update_detail_table(self, datas):
        """Cập nhật bảng chi tiết"""
        try:
            self.detail_table.setRowCount(0)
            for data in datas:
                date = data['date']
                alerts = data['alert_count']
                confirmed = data['confirmed_count']
                total_minutes = data['driving_time']
                hours, minutes = 23, 59

                row = self.detail_table.rowCount()
                self.detail_table.insertRow(row)

                date_item = QTableWidgetItem(date)
                date_item.setFont(QFont('Arial', 9))
                self.detail_table.setItem(row, 0, date_item)

                alerts_item = QTableWidgetItem(str(alerts))
                alerts_item.setFont(QFont('Arial', 9, QFont.Bold))
                alerts_item.setForeground(QColor("#e74c3c"))
                alerts_item.setTextAlignment(Qt.AlignCenter)
                self.detail_table.setItem(row, 1, alerts_item)

                confirmed_item = QTableWidgetItem(str(confirmed))
                confirmed_item.setFont(QFont('Arial', 9))
                confirmed_item.setForeground(QColor("#e67e22"))
                confirmed_item.setTextAlignment(Qt.AlignCenter)
                self.detail_table.setItem(row, 2, confirmed_item)

                time_item = QTableWidgetItem(f"{hours}h {minutes}m")
                time_item.setFont(QFont('Arial', 9))
                time_item.setTextAlignment(Qt.AlignCenter)
                self.detail_table.setItem(row, 3, time_item)


        except Exception as e:
            print(f"⚠️ Lỗi update table: {e}")

    def set_user_info(self, user_info):
        """Set user và load data"""
        try:
            self.current_user = user_info
            self.load_data()
        except Exception as e:
            print(f"⚠️ Lỗi set user: {e}")
