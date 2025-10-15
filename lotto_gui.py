#!/usr/bin/env python3
"""
Multi-Lottery System - GUI Version
Modern desktop application for Lotto Max, Lotto 6/49, and Daily Grand
"""

import sys
import os
from typing import Optional, List, Tuple

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QPushButton, QLabel, QComboBox, QSpinBox, QGroupBox,
    QScrollArea, QGridLayout, QMessageBox, QDialog, QProgressBar,
    QRadioButton, QButtonGroup, QSizePolicy, QFrame, QCheckBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve, QTimer
from PyQt6.QtGui import QFont, QPalette, QColor, QAction
from PyQt6.QtCharts import QChart, QChartView, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from lottos.lotto_max import LottoMax
from lottos.lotto_649 import Lotto649
from lottos.daily_grand import DailyGrand
from lottos.strategies.base_strategy import StrategyManager


class NumberBallWidget(QLabel):
    """Custom widget to display a lottery number as a colored ball"""

    def __init__(self, number: int, is_bonus: bool = False, parent=None):
        super().__init__(str(number), parent)
        self.number = number
        self.is_bonus = is_bonus
        self.setup_style()

    def setup_style(self):
        """Setup the visual style of the ball"""
        if self.is_bonus:
            bg_color = "#FFD700"  # Gold for bonus
            text_color = "#000000"
        else:
            # Color gradient based on number value
            if self.number <= 10:
                bg_color = "#FF6B6B"  # Red
            elif self.number <= 20:
                bg_color = "#4ECDC4"  # Teal
            elif self.number <= 30:
                bg_color = "#45B7D1"  # Blue
            elif self.number <= 40:
                bg_color = "#96CEB4"  # Green
            else:
                bg_color = "#DDA15E"  # Orange
            text_color = "#FFFFFF"

        self.setStyleSheet(f"""
            QLabel {{
                background-color: {bg_color};
                color: {text_color};
                border-radius: 30px;
                font-size: 24px;
                font-weight: bold;
                min-width: 60px;
                max-width: 60px;
                min-height: 60px;
                max-height: 60px;
                qproperty-alignment: AlignCenter;
            }}
        """)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)


class APIWorker(QThread):
    """Background worker for API operations"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, operation, lottery, *args):
        super().__init__()
        self.operation = operation
        self.lottery = lottery
        self.args = args

    def run(self):
        try:
            if self.operation == "check_new":
                count = self.lottery.check_for_new_draws()
                self.finished.emit(True, str(count))
            elif self.operation == "update":
                added = self.lottery.update_from_api()
                self.finished.emit(True, f"Added {added} new draw(s)")
            elif self.operation == "check_missing":
                quick_check = self.args[0] if self.args else False
                def progress_callback(year, idx, total):
                    self.progress.emit(f"Checking {year} ({idx}/{total})")

                missing = self.lottery.check_for_missing_years(
                    quick_check=quick_check,
                    progress_callback=progress_callback
                )
                self.finished.emit(True, f"Found {len(missing)} year(s) with issues")
            elif self.operation == "fetch_missing":
                years_dict = self.args[0]
                added = self.lottery.fetch_missing_years(years_dict)
                self.finished.emit(True, f"Fetched {added} draws")
        except Exception as e:
            self.finished.emit(False, str(e))


class LotteryTabWidget(QWidget):
    """Widget for a single lottery tab containing all lottery-specific UI"""

    def __init__(self, lottery, strategy_manager, parent=None):
        super().__init__(parent)
        self.lottery = lottery
        self.strategy_manager = strategy_manager
        self.current_strategy = "frequency"
        self.generated_numbers = []
        self.setup_ui()
        self.load_latest_draw()

    def setup_ui(self):
        """Setup the main layout for this lottery tab"""
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(20)

        # Left Panel - Dashboard
        left_panel = self.create_dashboard_panel()
        main_layout.addWidget(left_panel, stretch=1)

        # Center Panel - Number Generation
        center_panel = self.create_generation_panel()
        main_layout.addWidget(center_panel, stretch=2)

        # Right Panel - Statistics
        right_panel = self.create_statistics_panel()
        main_layout.addWidget(right_panel, stretch=1)

    def create_dashboard_panel(self) -> QWidget:
        """Create the dashboard panel showing latest draw info"""
        panel = QGroupBox("Latest Draw")
        layout = QVBoxLayout(panel)
        layout.setSpacing(15)

        # Title
        title = QLabel(f"🎰 {self.lottery.name}")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Draw date
        self.date_label = QLabel("Loading...")
        self.date_label.setFont(QFont("Arial", 12))
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.date_label)

        # Numbers display
        self.latest_numbers_container = QWidget()
        self.latest_numbers_layout = QHBoxLayout(self.latest_numbers_container)
        self.latest_numbers_layout.setSpacing(10)
        layout.addWidget(self.latest_numbers_container)

        # Jackpot
        jackpot_label = QLabel("Jackpot")
        jackpot_label.setFont(QFont("Arial", 11))
        jackpot_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        jackpot_label.setStyleSheet("color: #666;")
        layout.addWidget(jackpot_label)

        self.jackpot_label = QLabel("$0")
        self.jackpot_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        self.jackpot_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.jackpot_label.setStyleSheet("color: #2ECC71;")
        layout.addWidget(self.jackpot_label)

        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.load_latest_draw)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498DB;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2980B9;
            }
        """)
        layout.addWidget(refresh_btn)

        layout.addStretch()

        return panel

    def create_generation_panel(self) -> QWidget:
        """Create the number generation panel"""
        panel = QGroupBox("Generate Numbers")
        layout = QVBoxLayout(panel)
        layout.setSpacing(20)

        # Strategy selection
        strategy_group = QWidget()
        strategy_layout = QHBoxLayout(strategy_group)
        strategy_layout.addWidget(QLabel("Strategy:"))

        self.strategy_combo = QComboBox()
        self.strategy_combo.addItems([
            "Frequency (Hot/Cold Numbers)",
            "Random",
            "Balanced (Mixed Approach)"
        ])
        self.strategy_combo.currentIndexChanged.connect(self.on_strategy_changed)
        strategy_layout.addWidget(self.strategy_combo, stretch=1)
        layout.addWidget(strategy_group)

        # Generate single button
        generate_btn = QPushButton("🎲 Generate Numbers")
        generate_btn.clicked.connect(self.generate_single)
        generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #9B59B6;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 20px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8E44AD;
            }
            QPushButton:pressed {
                background-color: #7D3C98;
            }
        """)
        layout.addWidget(generate_btn)

        # Generated numbers display
        self.generated_container = QWidget()
        self.generated_layout = QGridLayout(self.generated_container)
        self.generated_layout.setSpacing(15)
        layout.addWidget(self.generated_container)

        # Multiple generation section
        multi_group = QWidget()
        multi_layout = QHBoxLayout(multi_group)
        multi_layout.addWidget(QLabel("Generate:"))

        self.count_spin = QSpinBox()
        self.count_spin.setRange(2, 10)
        self.count_spin.setValue(5)
        self.count_spin.setSuffix(" sets")
        multi_layout.addWidget(self.count_spin)

        multi_btn = QPushButton("Generate Multiple")
        multi_btn.clicked.connect(self.generate_multiple)
        multi_btn.setStyleSheet("""
            QPushButton {
                background-color: #E74C3C;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #C0392B;
            }
        """)
        multi_layout.addWidget(multi_btn)
        layout.addWidget(multi_group)

        # Multiple results display (scrollable)
        self.multi_scroll = QScrollArea()
        self.multi_scroll.setWidgetResizable(True)
        self.multi_scroll.setMaximumHeight(200)
        self.multi_results = QLabel()
        self.multi_results.setWordWrap(True)
        self.multi_results.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.multi_scroll.setWidget(self.multi_results)
        layout.addWidget(self.multi_scroll)

        layout.addStretch()

        return panel

    def create_statistics_panel(self) -> QWidget:
        """Create the statistics panel with charts"""
        panel = QGroupBox("Statistics")
        layout = QVBoxLayout(panel)

        # View stats button
        view_stats_btn = QPushButton("📊 View Detailed Statistics")
        view_stats_btn.clicked.connect(self.show_statistics)
        view_stats_btn.setStyleSheet("""
            QPushButton {
                background-color: #16A085;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #138D75;
            }
        """)
        layout.addWidget(view_stats_btn)

        # Quick stats preview
        self.stats_preview = QLabel("Loading statistics...")
        self.stats_preview.setWordWrap(True)
        self.stats_preview.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.stats_preview.setStyleSheet("""
            QLabel {
                background-color: #F8F9FA;
                border-radius: 5px;
                padding: 15px;
                font-family: monospace;
                font-size: 11px;
            }
        """)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.stats_preview)
        layout.addWidget(scroll)

        # Load stats preview
        self.load_stats_preview()

        return panel

    def on_strategy_changed(self, index: int):
        """Handle strategy selection change"""
        strategies = ["frequency", "random", "balanced"]
        self.current_strategy = strategies[index]

    def load_latest_draw(self):
        """Load and display the latest draw information"""
        try:
            data = self.lottery.load_from_files()
            latest = data.get('latest_draw', {})

            if latest:
                # Update date
                self.date_label.setText(f"Draw Date: {latest.get('date', 'Unknown')}")

                # Update numbers display
                # Clear existing balls
                while self.latest_numbers_layout.count():
                    child = self.latest_numbers_layout.takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()

                # Add main numbers
                numbers = latest.get('numbers', [])
                for num in numbers:
                    ball = NumberBallWidget(num, is_bonus=False)
                    self.latest_numbers_layout.addWidget(ball)

                # Add bonus if exists
                if 'bonus' in latest:
                    # Add separator
                    sep = QLabel("|")
                    sep.setFont(QFont("Arial", 24))
                    sep.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.latest_numbers_layout.addWidget(sep)

                    ball = NumberBallWidget(latest['bonus'], is_bonus=True)
                    self.latest_numbers_layout.addWidget(ball)

                self.latest_numbers_layout.addStretch()

                # Update jackpot
                jackpot = latest.get('jackpot', '$0')
                self.jackpot_label.setText(jackpot)
        except Exception as e:
            self.date_label.setText(f"Error loading: {str(e)}")

    def load_stats_preview(self):
        """Load and display statistics preview"""
        try:
            data = self.lottery.load_from_files()

            # Get hot numbers
            if data.get('main_freq'):
                hot = sorted(data['main_freq'].items(), key=lambda x: x[1], reverse=True)[:10]
                hot_nums = [str(num) for num, _ in hot]

                cold = sorted(data['main_freq'].items(), key=lambda x: x[1])[:10]
                cold_nums = [str(num) for num, _ in cold]

                preview_text = f"""🔥 Hot Numbers:
{', '.join(hot_nums)}

🥶 Cold Numbers:
{', '.join(cold_nums)}

Click 'View Detailed Statistics'
for complete analysis."""

                self.stats_preview.setText(preview_text)
        except Exception as e:
            self.stats_preview.setText(f"Error loading stats: {str(e)}")

    def generate_single(self):
        """Generate a single set of numbers"""
        try:
            # Clear previous results
            while self.generated_layout.count():
                child = self.generated_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

            # Generate numbers
            data = self.lottery.load_from_files()
            strategy = self.strategy_manager.get_strategy(self.current_strategy)
            main_numbers, bonus_number = strategy.generate_numbers(
                data,
                self.lottery.get_game_config()
            )

            # Display main numbers
            main_label = QLabel("Your Lucky Numbers:")
            main_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
            self.generated_layout.addWidget(main_label, 0, 0, 1, -1)

            sorted_nums = sorted(main_numbers)
            for i, num in enumerate(sorted_nums):
                ball = NumberBallWidget(num, is_bonus=False)
                row = 1 + (i // 4)
                col = i % 4
                self.generated_layout.addWidget(ball, row, col)

            # Display bonus number if applicable
            if bonus_number is not None:
                bonus_label = QLabel("Bonus:")
                bonus_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
                bonus_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

                next_row = ((len(sorted_nums) - 1) // 4) + 2
                self.generated_layout.addWidget(bonus_label, next_row, 0)

                bonus_ball = NumberBallWidget(bonus_number, is_bonus=True)
                self.generated_layout.addWidget(bonus_ball, next_row, 1)

            # Good luck message
            luck_label = QLabel("🍀 Good luck! 🍀")
            luck_label.setFont(QFont("Arial", 16))
            luck_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            luck_label.setStyleSheet("color: #27AE60; margin-top: 20px;")
            final_row = ((len(sorted_nums) - 1) // 4) + 3
            self.generated_layout.addWidget(luck_label, final_row, 0, 1, -1)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate numbers: {str(e)}")

    def generate_multiple(self):
        """Generate multiple sets of numbers"""
        try:
            count = self.count_spin.value()
            data = self.lottery.load_from_files()
            strategy = self.strategy_manager.get_strategy(self.current_strategy)
            config = self.lottery.get_game_config()

            results = []
            used_sets = set()
            sets_generated = 0
            attempts = 0
            max_attempts = count * 10

            while sets_generated < count and attempts < max_attempts:
                attempts += 1
                main_numbers, bonus_number = strategy.generate_numbers(data, config)
                main_tuple = tuple(sorted(main_numbers))

                if main_tuple not in used_sets:
                    used_sets.add(main_tuple)
                    sets_generated += 1

                    nums_str = ", ".join([str(n) for n in sorted(main_numbers)])
                    if bonus_number is not None:
                        results.append(f"Set {sets_generated}: [{nums_str}] + Bonus: {bonus_number}")
                    else:
                        results.append(f"Set {sets_generated}: [{nums_str}]")

            # Display results
            result_text = "\n".join(results)
            self.multi_results.setText(result_text)
            self.multi_results.setStyleSheet("""
                QLabel {
                    font-family: monospace;
                    font-size: 13px;
                    line-height: 1.6;
                    padding: 10px;
                }
            """)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate multiple sets: {str(e)}")

    def show_statistics(self):
        """Show detailed statistics in a dialog"""
        try:
            stats = self.lottery.get_statistics_summary()

            dialog = QDialog(self)
            dialog.setWindowTitle(f"{self.lottery.name} - Detailed Statistics")
            dialog.resize(700, 600)

            layout = QVBoxLayout(dialog)

            stats_text = QLabel(stats)
            stats_text.setFont(QFont("Courier", 11))
            stats_text.setWordWrap(True)
            stats_text.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setWidget(stats_text)
            layout.addWidget(scroll)

            close_btn = QPushButton("Close")
            close_btn.clicked.connect(dialog.close)
            layout.addWidget(close_btn)

            dialog.exec()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load statistics: {str(e)}")


class SettingsDialog(QDialog):
    """Settings dialog for API management and configuration"""

    def __init__(self, lotteries: dict, parent=None):
        super().__init__(parent)
        self.lotteries = lotteries
        self.setWindowTitle("Settings")
        self.resize(600, 400)
        self.setup_ui()

    def setup_ui(self):
        """Setup settings dialog UI"""
        layout = QVBoxLayout(self)

        # API Management section
        api_group = QGroupBox("API Data Management")
        api_layout = QVBoxLayout(api_group)

        update_btn = QPushButton("🌐 Update Lottery Data from API")
        update_btn.clicked.connect(self.update_from_api)
        update_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498DB;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 12px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2980B9;
            }
        """)
        api_layout.addWidget(update_btn)

        quick_check_btn = QPushButton("🔍 Quick Data Check (last 3 years)")
        quick_check_btn.clicked.connect(lambda: self.check_data(quick=True))
        quick_check_btn.setStyleSheet("""
            QPushButton {
                background-color: #16A085;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 12px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #138D75;
            }
        """)
        api_layout.addWidget(quick_check_btn)

        full_check_btn = QPushButton("🔍 Full Data Check (all years - slower)")
        full_check_btn.clicked.connect(lambda: self.check_data(quick=False))
        full_check_btn.setStyleSheet("""
            QPushButton {
                background-color: #E67E22;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 12px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #D35400;
            }
        """)
        api_layout.addWidget(full_check_btn)

        layout.addWidget(api_group)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        layout.addStretch()

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

    def update_from_api(self):
        """Update lottery data from API"""
        self.status_label.setText("Checking for new draws...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate

        # Check all lotteries for updates
        updates_available = {}
        for key, lottery in self.lotteries.items():
            try:
                new_count = lottery.check_for_new_draws()
                if new_count == -1:
                    updates_available[lottery.name] = "initial"
                elif new_count > 0:
                    updates_available[lottery.name] = new_count
            except Exception as e:
                QMessageBox.warning(self, "Error", f"{lottery.name}: {str(e)}")

        self.progress_bar.setVisible(False)

        if not updates_available:
            QMessageBox.information(self, "Up to Date", "All lotteries are up to date!")
            self.status_label.setText("✅ All lotteries are up to date")
            return

        # Show updates and prompt user
        message = "Updates available:\n\n"
        for name, info in updates_available.items():
            if info == "initial":
                message += f"• {name}: Initial fetch needed\n"
            else:
                message += f"• {name}: {info} new draw(s)\n"

        message += "\nWould you like to update now?"

        reply = QMessageBox.question(
            self, "Updates Available", message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.perform_updates(updates_available)

    def perform_updates(self, updates_available: dict):
        """Perform the actual updates"""
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, len(updates_available))
        self.progress_bar.setValue(0)

        for idx, (lottery_name, info) in enumerate(updates_available.items()):
            self.status_label.setText(f"Updating {lottery_name}...")
            QApplication.processEvents()

            lottery = None
            for key, lott in self.lotteries.items():
                if lott.name == lottery_name:
                    lottery = lott
                    break

            if lottery:
                try:
                    if info == "initial":
                        lottery.fetch_from_api()
                    else:
                        lottery.update_from_api()
                    self.status_label.setText(f"✅ {lottery_name} updated successfully")
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"{lottery_name}: {str(e)}")

            self.progress_bar.setValue(idx + 1)
            QApplication.processEvents()

        self.progress_bar.setVisible(False)
        QMessageBox.information(self, "Complete", "All updates completed!")

    def check_data(self, quick: bool = True):
        """Check for missing data"""
        check_type = "Quick" if quick else "Full"
        self.status_label.setText(f"{check_type} data check in progress...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)

        missing_data = {}
        for key, lottery in self.lotteries.items():
            try:
                def progress_callback(year, idx, total):
                    self.status_label.setText(f"Checking {lottery.name}: {year} ({idx}/{total})")
                    QApplication.processEvents()

                years_with_issues = lottery.check_for_missing_years(
                    quick_check=quick,
                    progress_callback=progress_callback
                )

                if years_with_issues:
                    missing_data[lottery.name] = years_with_issues
            except Exception as e:
                QMessageBox.warning(self, "Error", f"{lottery.name}: {str(e)}")

        self.progress_bar.setVisible(False)

        if not missing_data:
            QMessageBox.information(
                self, "Complete",
                "✨ All lotteries have complete and accurate data!"
            )
            self.status_label.setText("✅ Data integrity check passed")
        else:
            message = "Issues found:\n\n"
            for name, years_dict in missing_data.items():
                message += f"{name}:\n"
                for year, info in sorted(years_dict.items()):
                    message += f"  • {year}: {info['missing']} missing draw(s)\n"

            message += "\nWould you like to refetch the missing data?"

            reply = QMessageBox.question(
                self, "Issues Found", message,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.fix_missing_data(missing_data)

    def fix_missing_data(self, missing_data: dict):
        """Fix missing data by refetching"""
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, len(missing_data))
        self.progress_bar.setValue(0)

        for idx, (lottery_name, years_dict) in enumerate(missing_data.items()):
            self.status_label.setText(f"Refetching data for {lottery_name}...")
            QApplication.processEvents()

            lottery = None
            for key, lott in self.lotteries.items():
                if lott.name == lottery_name:
                    lottery = lott
                    break

            if lottery:
                try:
                    lottery.fetch_missing_years(years_dict)
                    self.status_label.setText(f"✅ {lottery_name} data refreshed")
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"{lottery_name}: {str(e)}")

            self.progress_bar.setValue(idx + 1)
            QApplication.processEvents()

        self.progress_bar.setVisible(False)
        QMessageBox.information(self, "Complete", "Data refresh completed!")


class LottoGUIApp(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Multi-Lottery System")
        self.setGeometry(100, 100, 1400, 800)

        # Initialize lottery instances
        self.lotteries = {
            '1': LottoMax(),
            '2': Lotto649(),
            '3': DailyGrand(),
        }
        self.strategy_manager = StrategyManager()

        self.setup_ui()
        self.setup_menu_bar()
        self.apply_theme()

    def setup_ui(self):
        """Setup the main UI"""
        # Central widget with tabs
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # Title
        title = QLabel("🎰 Multi-Lottery System 🎰")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #2C3E50; margin: 20px;")
        layout.addWidget(title)

        # Tab widget for different lotteries
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)
        self.tabs.setMovable(False)

        # Create tabs for each lottery
        self.lotto_max_tab = LotteryTabWidget(
            self.lotteries['1'],
            self.strategy_manager
        )
        self.tabs.addTab(self.lotto_max_tab, "🎯 Lotto Max")

        self.lotto_649_tab = LotteryTabWidget(
            self.lotteries['2'],
            self.strategy_manager
        )
        self.tabs.addTab(self.lotto_649_tab, "🎲 Lotto 6/49")

        self.daily_grand_tab = LotteryTabWidget(
            self.lotteries['3'],
            self.strategy_manager
        )
        self.tabs.addTab(self.daily_grand_tab, "🌟 Daily Grand")

        layout.addWidget(self.tabs)

        # Status bar
        self.statusBar().showMessage("Ready")

    def setup_menu_bar(self):
        """Setup the menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        refresh_action = QAction("Refresh All Data", self)
        refresh_action.triggered.connect(self.refresh_all)
        file_menu.addAction(refresh_action)

        file_menu.addSeparator()

        quit_action = QAction("Quit", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # Settings menu
        settings_menu = menubar.addMenu("Settings")

        api_settings_action = QAction("API & Data Management", self)
        api_settings_action.triggered.connect(self.show_settings)
        settings_menu.addAction(api_settings_action)

        # Help menu
        help_menu = menubar.addMenu("Help")

        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def apply_theme(self):
        """Apply custom theme to the application"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ECF0F1;
            }
            QTabWidget::pane {
                border: 1px solid #BDC3C7;
                border-radius: 5px;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #BDC3C7;
                color: #2C3E50;
                padding: 10px 20px;
                margin: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: white;
                color: #3498DB;
            }
            QTabBar::tab:hover {
                background-color: #D5DBDB;
            }
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #BDC3C7;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)

    def refresh_all(self):
        """Refresh all lottery data"""
        self.statusBar().showMessage("Refreshing all data...")

        # Refresh each tab
        self.lotto_max_tab.load_latest_draw()
        self.lotto_max_tab.load_stats_preview()

        self.lotto_649_tab.load_latest_draw()
        self.lotto_649_tab.load_stats_preview()

        self.daily_grand_tab.load_latest_draw()
        self.daily_grand_tab.load_stats_preview()

        self.statusBar().showMessage("All data refreshed!", 3000)

    def show_settings(self):
        """Show settings dialog"""
        dialog = SettingsDialog(self.lotteries, self)
        dialog.exec()

        # Refresh data after settings close
        self.refresh_all()

    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About Multi-Lottery System",
            """<h2>Multi-Lottery System</h2>
            <p><b>Version:</b> 2.0 (GUI)</p>
            <p><b>Description:</b> A comprehensive lottery prediction system for
            Canadian lotteries including Lotto Max, Lotto 6/49, and Daily Grand.</p>
            <p><b>Features:</b></p>
            <ul>
                <li>Multiple number generation strategies</li>
                <li>Historical data analysis</li>
                <li>Real-time API updates</li>
                <li>Detailed statistics and visualizations</li>
            </ul>
            <p><b>Developed with:</b> Python, PyQt6</p>
            """
        )


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("Multi-Lottery System")
    app.setOrganizationName("LottoMax")

    # Set application-wide font
    app.setFont(QFont("Arial", 11))

    # Create and show main window
    window = LottoGUIApp()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
