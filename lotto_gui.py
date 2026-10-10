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
    QTabWidget, QPushButton, QLabel, QComboBox, QSpinBox, QFrame,
    QScrollArea, QGridLayout, QMessageBox, QDialog, QProgressBar,
    QSizePolicy, QStackedWidget, QToolButton
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QAction, QFontDatabase

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from lottos.lotto_max import LottoMax
from lottos.lotto_649 import Lotto649
from lottos.daily_grand import DailyGrand
from lottos.strategies.base_strategy import StrategyManager


# ────────────────────────────────────────────────────────────────────
# Design tokens
# ────────────────────────────────────────────────────────────────────
class Theme:
    BG = "#0d1117"
    SURFACE = "#161b22"
    SURFACE_2 = "#1c2128"
    BORDER = "#30363d"
    BORDER_SOFT = "#21262d"
    TEXT = "#e6edf3"
    TEXT_DIM = "#8b949e"
    TEXT_MUTED = "#6e7681"
    ACCENT = "#6366f1"
    ACCENT_HOVER = "#7c7ff2"
    ACCENT_PRESSED = "#4f52d8"
    SUCCESS = "#3fb950"
    BONUS = "#f0b429"
    DANGER = "#f85149"

    # Number ball palette — single subtle hue, accent border on bonus
    BALL_BG = "#1f242c"
    BALL_BORDER = "#3a4150"
    BALL_TEXT = "#e6edf3"


# ────────────────────────────────────────────────────────────────────
# Reusable widgets
# ────────────────────────────────────────────────────────────────────
class NumberBall(QLabel):
    """Flat number ball — dark surface, accent border for bonus."""

    def __init__(self, number: int, is_bonus: bool = False, size: int = 44, parent=None):
        super().__init__(str(number), parent)
        self.number = number
        self.is_bonus = is_bonus
        self._size = size
        self._apply_style()

    def _apply_style(self):
        radius = self._size // 2
        font_size = max(13, int(self._size * 0.38))
        if self.is_bonus:
            border = Theme.BONUS
            text = Theme.BONUS
            bg = Theme.SURFACE_2
            border_width = 2
        else:
            border = Theme.BALL_BORDER
            text = Theme.BALL_TEXT
            bg = Theme.BALL_BG
            border_width = 1

        self.setFixedSize(self._size, self._size)
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {bg};
                color: {text};
                border: {border_width}px solid {border};
                border-radius: {radius}px;
                font-size: {font_size}px;
                font-weight: 600;
            }}
        """)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)


class Card(QFrame):
    """Surface card with title + content."""

    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        self.setStyleSheet(f"""
            QFrame#Card {{
                background-color: {Theme.SURFACE};
                border: 1px solid {Theme.BORDER};
                border-radius: 12px;
            }}
        """)

        self._outer = QVBoxLayout(self)
        self._outer.setContentsMargins(20, 18, 20, 18)
        self._outer.setSpacing(14)

        if title:
            self._header_row = QHBoxLayout()
            self._header_row.setSpacing(12)
            self._title = QLabel(title)
            self._title.setStyleSheet(
                f"color: {Theme.TEXT_DIM}; font-size: 12px; font-weight: 600; "
                f"letter-spacing: 1.2px; text-transform: uppercase;"
            )
            self._header_row.addWidget(self._title)
            self._header_row.addStretch()
            self._outer.addLayout(self._header_row)

        self.body = QVBoxLayout()
        self.body.setSpacing(12)
        self._outer.addLayout(self.body)

    def add_header_widget(self, w: QWidget):
        """Add a widget to the right side of the card header."""
        if hasattr(self, "_header_row"):
            self._header_row.addWidget(w)


def primary_button(text: str) -> QPushButton:
    btn = QPushButton(text)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setStyleSheet(f"""
        QPushButton {{
            background-color: {Theme.ACCENT};
            color: white;
            border: none;
            border-radius: 8px;
            padding: 12px 24px;
            font-size: 14px;
            font-weight: 600;
        }}
        QPushButton:hover {{ background-color: {Theme.ACCENT_HOVER}; }}
        QPushButton:pressed {{ background-color: {Theme.ACCENT_PRESSED}; }}
        QPushButton:disabled {{ background-color: {Theme.BORDER}; color: {Theme.TEXT_MUTED}; }}
    """)
    return btn


def ghost_button(text: str) -> QPushButton:
    btn = QPushButton(text)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setStyleSheet(f"""
        QPushButton {{
            background-color: transparent;
            color: {Theme.TEXT_DIM};
            border: 1px solid {Theme.BORDER};
            border-radius: 8px;
            padding: 8px 16px;
            font-size: 13px;
            font-weight: 500;
        }}
        QPushButton:hover {{ color: {Theme.TEXT}; border-color: {Theme.TEXT_MUTED}; }}
        QPushButton:pressed {{ background-color: {Theme.SURFACE_2}; }}
    """)
    return btn


# ────────────────────────────────────────────────────────────────────
# Lottery view
# ────────────────────────────────────────────────────────────────────
class LotteryView(QWidget):
    """Single-view stack: Latest draw → Generator → Quick stats."""

    def __init__(self, lottery, strategy_manager, parent=None):
        super().__init__(parent)
        self.lottery = lottery
        self.strategy_manager = strategy_manager
        self.current_strategy = "frequency"
        self._build()
        self.refresh()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(16)

        root.addWidget(self._build_latest_card())
        root.addWidget(self._build_generate_card())
        root.addWidget(self._build_stats_card())
        root.addStretch()

    # — Latest draw card —
    def _build_latest_card(self) -> Card:
        card = Card("Latest Draw")

        self.date_label = QLabel("—")
        self.date_label.setStyleSheet(f"color: {Theme.TEXT}; font-size: 14px;")
        card.add_header_widget(self.date_label)

        # Numbers row
        self.latest_row = QHBoxLayout()
        self.latest_row.setSpacing(8)
        self.latest_row.setAlignment(Qt.AlignmentFlag.AlignLeft)
        wrap = QWidget()
        wrap.setLayout(self.latest_row)
        card.body.addWidget(wrap)

        # Footer: bonus label + jackpot
        footer = QHBoxLayout()
        footer.setSpacing(24)

        self.bonus_label = QLabel("")
        self.bonus_label.setStyleSheet(f"color: {Theme.TEXT_DIM}; font-size: 12px;")
        footer.addWidget(self.bonus_label)

        footer.addStretch()

        jackpot_caption = QLabel("Jackpot")
        jackpot_caption.setStyleSheet(
            f"color: {Theme.TEXT_MUTED}; font-size: 11px; "
            f"letter-spacing: 1px; text-transform: uppercase;"
        )
        footer.addWidget(jackpot_caption)

        self.jackpot_label = QLabel("—")
        self.jackpot_label.setStyleSheet(
            f"color: {Theme.SUCCESS}; font-size: 18px; font-weight: 700;"
        )
        footer.addWidget(self.jackpot_label)

        card.body.addLayout(footer)
        return card

    # — Generator card —
    def _build_generate_card(self) -> Card:
        card = Card("Generate")

        # Controls row
        controls = QHBoxLayout()
        controls.setSpacing(12)

        strat_label = QLabel("Strategy")
        strat_label.setStyleSheet(f"color: {Theme.TEXT_DIM}; font-size: 12px;")
        controls.addWidget(strat_label)

        self.strategy_combo = QComboBox()
        self.strategy_combo.addItems(["Frequency", "Random", "Balanced"])
        self.strategy_combo.currentIndexChanged.connect(self._on_strategy_changed)
        self.strategy_combo.setMinimumWidth(160)
        controls.addWidget(self.strategy_combo)

        controls.addSpacing(20)

        sets_label = QLabel("Sets")
        sets_label.setStyleSheet(f"color: {Theme.TEXT_DIM}; font-size: 12px;")
        controls.addWidget(sets_label)

        self.count_spin = QSpinBox()
        self.count_spin.setRange(1, 10)
        self.count_spin.setValue(1)
        self.count_spin.setFixedWidth(70)
        controls.addWidget(self.count_spin)

        controls.addStretch()

        gen_btn = primary_button("Generate")
        gen_btn.clicked.connect(self._on_generate)
        controls.addWidget(gen_btn)

        card.body.addLayout(controls)

        # Results container
        self.results_container = QVBoxLayout()
        self.results_container.setSpacing(10)
        results_wrap = QWidget()
        results_wrap.setLayout(self.results_container)
        card.body.addWidget(results_wrap)

        self._set_results_placeholder()
        return card

    def _set_results_placeholder(self):
        self._clear_layout(self.results_container)
        hint = QLabel("Press Generate to see your numbers.")
        hint.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 13px; padding: 20px 0;")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.results_container.addWidget(hint)

    # — Stats card —
    def _build_stats_card(self) -> Card:
        card = Card("Quick Stats")

        full_btn = ghost_button("Full Statistics")
        full_btn.clicked.connect(self._show_statistics)
        card.add_header_widget(full_btn)

        self.hot_row = self._stat_row("Hot")
        self.cold_row = self._stat_row("Cold")
        card.body.addLayout(self.hot_row["layout"])
        card.body.addLayout(self.cold_row["layout"])

        return card

    def _stat_row(self, label_text: str) -> dict:
        layout = QHBoxLayout()
        layout.setSpacing(12)
        label = QLabel(label_text)
        label.setStyleSheet(
            f"color: {Theme.TEXT_DIM}; font-size: 11px; font-weight: 600; "
            f"letter-spacing: 1px; text-transform: uppercase;"
        )
        label.setFixedWidth(48)
        layout.addWidget(label)

        values = QLabel("—")
        values.setStyleSheet(f"color: {Theme.TEXT}; font-size: 14px; font-weight: 500;")
        layout.addWidget(values)
        layout.addStretch()
        return {"layout": layout, "values": values}

    # — Helpers —
    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

    def _on_strategy_changed(self, index: int):
        self.current_strategy = ["frequency", "random", "balanced"][index]

    # — Data load —
    def refresh(self):
        self._load_latest()
        self._load_quick_stats()

    def _load_latest(self):
        try:
            data = self.lottery.load_from_files()
            latest = data.get("latest_draw") or {}

            self._clear_layout(self.latest_row)

            if not latest:
                self.date_label.setText("No data")
                self.bonus_label.setText("")
                self.jackpot_label.setText("—")
                placeholder = QLabel("Run an API update from Settings to load data.")
                placeholder.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 13px;")
                self.latest_row.addWidget(placeholder)
                return

            self.date_label.setText(latest.get("date", "Unknown"))

            for n in latest.get("numbers", []):
                self.latest_row.addWidget(NumberBall(n))

            if "bonus" in latest:
                spacer = QLabel("·")
                spacer.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 18px; padding: 0 4px;")
                self.latest_row.addWidget(spacer)
                self.latest_row.addWidget(NumberBall(latest["bonus"], is_bonus=True))
                self.bonus_label.setText("● Bonus")
                self.bonus_label.setStyleSheet(
                    f"color: {Theme.BONUS}; font-size: 12px; font-weight: 500;"
                )
            else:
                self.bonus_label.setText("")

            self.latest_row.addStretch()
            self.jackpot_label.setText(latest.get("jackpot", "—"))
        except Exception as e:
            self.date_label.setText(f"Error: {e}")

    def _load_quick_stats(self):
        try:
            data = self.lottery.load_from_files()
            freq = data.get("main_freq")
            if not freq:
                self.hot_row["values"].setText("—")
                self.cold_row["values"].setText("—")
                return

            hot = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:8]
            cold = sorted(freq.items(), key=lambda x: x[1])[:8]

            self.hot_row["values"].setText("  ".join(str(n) for n, _ in hot))
            self.cold_row["values"].setText("  ".join(str(n) for n, _ in cold))
        except Exception as e:
            self.hot_row["values"].setText(f"Error: {e}")

    # — Generate —
    def _on_generate(self):
        try:
            data = self.lottery.load_from_files()
            strategy = self.strategy_manager.get_strategy(self.current_strategy)
            config = self.lottery.get_game_config()
            count = self.count_spin.value()

            self._clear_layout(self.results_container)

            seen = set()
            attempts = 0
            sets_made = 0
            while sets_made < count and attempts < count * 20:
                attempts += 1
                main, bonus = strategy.generate_numbers(data, config)
                key = tuple(sorted(main))
                if key in seen:
                    continue
                seen.add(key)
                sets_made += 1
                self.results_container.addLayout(self._build_set_row(sets_made, sorted(main), bonus, count))

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate: {e}")

    def _build_set_row(self, idx: int, numbers: List[int], bonus: Optional[int], total: int) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(8)

        if total > 1:
            tag = QLabel(f"#{idx}")
            tag.setStyleSheet(
                f"color: {Theme.TEXT_MUTED}; font-size: 11px; font-weight: 600; "
                f"letter-spacing: 1px;"
            )
            tag.setFixedWidth(28)
            row.addWidget(tag)

        for n in numbers:
            row.addWidget(NumberBall(n, size=40))

        if bonus is not None:
            sep = QLabel("·")
            sep.setStyleSheet(f"color: {Theme.TEXT_MUTED}; font-size: 16px; padding: 0 2px;")
            row.addWidget(sep)
            row.addWidget(NumberBall(bonus, is_bonus=True, size=40))

        row.addStretch()
        return row

    # — Statistics modal —
    def _show_statistics(self):
        try:
            stats = self.lottery.get_statistics_summary()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load statistics: {e}")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(f"{self.lottery.name} — Statistics")
        dialog.resize(720, 640)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)

        body = QLabel(stats)
        body.setFont(QFont("Menlo", 11))
        body.setWordWrap(True)
        body.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        body.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        body.setStyleSheet(f"color: {Theme.TEXT}; padding: 8px;")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(body)
        scroll.setStyleSheet(f"QScrollArea {{ border: 1px solid {Theme.BORDER}; border-radius: 8px; }}")
        layout.addWidget(scroll)

        close_btn = ghost_button("Close")
        close_btn.clicked.connect(dialog.close)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

        dialog.exec()


# ────────────────────────────────────────────────────────────────────
# Settings dialog
# ────────────────────────────────────────────────────────────────────
class SettingsDialog(QDialog):
    def __init__(self, lotteries: dict, parent=None):
        super().__init__(parent)
        self.lotteries = lotteries
        self.setWindowTitle("Settings")
        self.resize(560, 480)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QLabel("Data Management")
        header.setStyleSheet(f"color: {Theme.TEXT}; font-size: 18px; font-weight: 600;")
        layout.addWidget(header)

        sub = QLabel("Update or verify the local cache against the API.")
        sub.setStyleSheet(f"color: {Theme.TEXT_DIM}; font-size: 13px;")
        layout.addWidget(sub)

        layout.addSpacing(8)

        update = primary_button("Update from API")
        update.clicked.connect(self._update_from_api)
        layout.addWidget(update)

        quick = ghost_button("Quick check (last 3 years)")
        quick.clicked.connect(lambda: self._check_data(quick=True))
        layout.addWidget(quick)

        full = ghost_button("Full check (all years — slow)")
        full.clicked.connect(lambda: self._check_data(quick=False))
        layout.addWidget(full)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(6)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet(f"color: {Theme.TEXT_DIM}; font-size: 12px;")
        layout.addWidget(self.status_label)

        layout.addStretch()

        close = ghost_button("Close")
        close.clicked.connect(self.close)
        bottom = QHBoxLayout()
        bottom.addStretch()
        bottom.addWidget(close)
        layout.addLayout(bottom)

    def _update_from_api(self):
        self.status_label.setText("Checking for new draws…")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        QApplication.processEvents()

        updates = {}
        for lottery in self.lotteries.values():
            try:
                count = lottery.check_for_new_draws()
                if count == -1:
                    updates[lottery.name] = "initial"
                elif count > 0:
                    updates[lottery.name] = count
            except Exception as e:
                QMessageBox.warning(self, "Error", f"{lottery.name}: {e}")

        self.progress_bar.setVisible(False)

        if not updates:
            QMessageBox.information(self, "Up to date", "All lotteries are current.")
            self.status_label.setText("✓ All lotteries up to date")
            return

        msg = "Updates available:\n\n"
        for name, info in updates.items():
            msg += f"• {name}: {'initial fetch' if info == 'initial' else f'{info} new draw(s)'}\n"
        msg += "\nProceed?"

        if QMessageBox.question(self, "Updates available", msg) == QMessageBox.StandardButton.Yes:
            self._perform_updates(updates)

    def _perform_updates(self, updates: dict):
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, len(updates))
        self.progress_bar.setValue(0)

        for idx, (name, info) in enumerate(updates.items()):
            self.status_label.setText(f"Updating {name}…")
            QApplication.processEvents()

            lottery = next((l for l in self.lotteries.values() if l.name == name), None)
            if lottery:
                try:
                    if info == "initial":
                        lottery.fetch_from_api()
                    else:
                        lottery.update_from_api()
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"{name}: {e}")

            self.progress_bar.setValue(idx + 1)
            QApplication.processEvents()

        self.progress_bar.setVisible(False)
        self.status_label.setText("✓ Updates complete")
        QMessageBox.information(self, "Complete", "All updates finished.")

    def _check_data(self, quick: bool = True):
        self.status_label.setText(f"{'Quick' if quick else 'Full'} check in progress…")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        QApplication.processEvents()

        missing = {}
        for lottery in self.lotteries.values():
            try:
                def cb(year, i, total, _name=lottery.name):
                    self.status_label.setText(f"Checking {_name}: {year} ({i}/{total})")
                    QApplication.processEvents()

                issues = lottery.check_for_missing_years(quick_check=quick, progress_callback=cb)
                if issues:
                    missing[lottery.name] = issues
            except Exception as e:
                QMessageBox.warning(self, "Error", f"{lottery.name}: {e}")

        self.progress_bar.setVisible(False)

        if not missing:
            self.status_label.setText("✓ Data integrity verified")
            QMessageBox.information(self, "Clean", "All lotteries have complete data.")
            return

        msg = "Issues found:\n\n"
        for name, years in missing.items():
            msg += f"{name}:\n"
            for year, info in sorted(years.items()):
                msg += f"  • {year}: {info['missing']} missing\n"
        msg += "\nRefetch missing data?"

        if QMessageBox.question(self, "Issues found", msg) == QMessageBox.StandardButton.Yes:
            self._fix_missing(missing)

    def _fix_missing(self, missing: dict):
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, len(missing))
        self.progress_bar.setValue(0)

        for idx, (name, years) in enumerate(missing.items()):
            self.status_label.setText(f"Refetching {name}…")
            QApplication.processEvents()

            lottery = next((l for l in self.lotteries.values() if l.name == name), None)
            if lottery:
                try:
                    lottery.fetch_missing_years(years)
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"{name}: {e}")

            self.progress_bar.setValue(idx + 1)
            QApplication.processEvents()

        self.progress_bar.setVisible(False)
        self.status_label.setText("✓ Refetch complete")
        QMessageBox.information(self, "Done", "Missing data refreshed.")


# ────────────────────────────────────────────────────────────────────
# Main window
# ────────────────────────────────────────────────────────────────────
class LottoGUIApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Multi-Lottery System")
        self.setGeometry(120, 100, 980, 820)
        self.setMinimumSize(720, 640)

        self.lotteries = {
            "1": LottoMax(),
            "2": Lotto649(),
            "3": DailyGrand(),
        }
        self.strategy_manager = StrategyManager()

        self._build()
        self._build_menu()
        self._apply_theme()

    def _build(self):
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(20)

        # Header
        header = QHBoxLayout()
        header.setSpacing(16)

        title = QLabel("Multi-Lottery")
        title.setStyleSheet(
            f"color: {Theme.TEXT}; font-size: 20px; font-weight: 700; letter-spacing: -0.3px;"
        )
        header.addWidget(title)

        header.addStretch()

        # Lottery switcher (segmented control)
        self.switcher = self._build_switcher()
        header.addWidget(self.switcher)

        settings_btn = ghost_button("⚙  Settings")
        settings_btn.clicked.connect(self._show_settings)
        header.addWidget(settings_btn)

        layout.addLayout(header)

        # Stacked content area
        self.stack = QStackedWidget()
        self.views = []
        for key in ("1", "2", "3"):
            view = LotteryView(self.lotteries[key], self.strategy_manager)
            self.views.append(view)

            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            scroll.setWidget(view)
            self.stack.addWidget(scroll)

        layout.addWidget(self.stack, stretch=1)

        # Status bar
        self.statusBar().showMessage("Ready")
        self.statusBar().setStyleSheet(
            f"QStatusBar {{ background-color: {Theme.BG}; color: {Theme.TEXT_MUTED}; "
            f"font-size: 11px; border-top: 1px solid {Theme.BORDER_SOFT}; }}"
        )

    def _build_switcher(self) -> QWidget:
        wrap = QFrame()
        wrap.setObjectName("Switcher")
        wrap.setStyleSheet(f"""
            QFrame#Switcher {{
                background-color: {Theme.SURFACE};
                border: 1px solid {Theme.BORDER};
                border-radius: 8px;
            }}
        """)
        row = QHBoxLayout(wrap)
        row.setContentsMargins(4, 4, 4, 4)
        row.setSpacing(2)

        labels = ["Lotto Max", "6/49", "Daily Grand"]
        self.switcher_buttons = []
        for i, label in enumerate(labels):
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {Theme.TEXT_DIM};
                    border: none;
                    border-radius: 6px;
                    padding: 6px 16px;
                    font-size: 13px;
                    font-weight: 500;
                }}
                QPushButton:hover {{ color: {Theme.TEXT}; }}
                QPushButton:checked {{
                    background-color: {Theme.ACCENT};
                    color: white;
                    font-weight: 600;
                }}
            """)
            btn.clicked.connect(lambda _checked, idx=i: self._switch_to(idx))
            row.addWidget(btn)
            self.switcher_buttons.append(btn)

        self.switcher_buttons[0].setChecked(True)
        return wrap

    def _switch_to(self, index: int):
        for i, btn in enumerate(self.switcher_buttons):
            btn.setChecked(i == index)
        self.stack.setCurrentIndex(index)

    def _build_menu(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("File")
        refresh = QAction("Refresh All", self)
        refresh.setShortcut("Ctrl+R")
        refresh.triggered.connect(self._refresh_all)
        file_menu.addAction(refresh)
        file_menu.addSeparator()
        quit_action = QAction("Quit", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        settings_menu = menubar.addMenu("Settings")
        api_action = QAction("Data Management", self)
        api_action.triggered.connect(self._show_settings)
        settings_menu.addAction(api_action)

        help_menu = menubar.addMenu("Help")
        about = QAction("About", self)
        about.triggered.connect(self._show_about)
        help_menu.addAction(about)

    def _refresh_all(self):
        for view in self.views:
            view.refresh()
        self.statusBar().showMessage("Refreshed", 2000)

    def _show_settings(self):
        dialog = SettingsDialog(self.lotteries, self)
        dialog.exec()
        self._refresh_all()

    def _show_about(self):
        QMessageBox.about(
            self,
            "About",
            "<h3>Multi-Lottery System</h3>"
            "<p>Number generator and analysis for Canadian lotteries.</p>"
            "<p style='color:#8b949e;'>Built with PyQt6.</p>",
        )

    def _apply_theme(self):
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{
                background-color: {Theme.BG};
                color: {Theme.TEXT};
                font-family: -apple-system, "SF Pro Text", "Segoe UI", system-ui, sans-serif;
                font-size: 13px;
            }}
            QScrollArea {{ background-color: transparent; border: none; }}
            QScrollBar:vertical {{
                background: transparent; width: 10px; margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: {Theme.BORDER}; border-radius: 5px; min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{ background: {Theme.TEXT_MUTED}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}

            QComboBox {{
                background-color: {Theme.SURFACE_2};
                color: {Theme.TEXT};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 13px;
                min-height: 24px;
            }}
            QComboBox:hover {{ border-color: {Theme.TEXT_MUTED}; }}
            QComboBox::drop-down {{ border: none; width: 22px; }}
            QComboBox::down-arrow {{ image: none; }}
            QComboBox QAbstractItemView {{
                background-color: {Theme.SURFACE_2};
                color: {Theme.TEXT};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
                selection-background-color: {Theme.ACCENT};
                selection-color: white;
                padding: 4px;
                outline: none;
            }}

            QSpinBox {{
                background-color: {Theme.SURFACE_2};
                color: {Theme.TEXT};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
                padding: 4px 6px;
                font-size: 13px;
            }}
            QSpinBox:hover {{ border-color: {Theme.TEXT_MUTED}; }}
            QSpinBox::up-button, QSpinBox::down-button {{
                background-color: transparent; border: none; width: 16px;
            }}

            QProgressBar {{
                background-color: {Theme.SURFACE_2};
                border: none;
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background-color: {Theme.ACCENT};
                border-radius: 3px;
            }}

            QMenuBar {{
                background-color: {Theme.BG};
                color: {Theme.TEXT_DIM};
                border-bottom: 1px solid {Theme.BORDER_SOFT};
                padding: 2px;
            }}
            QMenuBar::item {{ background: transparent; padding: 6px 12px; border-radius: 4px; }}
            QMenuBar::item:selected {{ background: {Theme.SURFACE_2}; color: {Theme.TEXT}; }}
            QMenu {{
                background-color: {Theme.SURFACE_2};
                color: {Theme.TEXT};
                border: 1px solid {Theme.BORDER};
                border-radius: 6px;
                padding: 4px;
            }}
            QMenu::item {{ padding: 6px 24px; border-radius: 4px; }}
            QMenu::item:selected {{ background-color: {Theme.ACCENT}; color: white; }}

            QDialog {{ background-color: {Theme.BG}; }}
            QMessageBox {{ background-color: {Theme.SURFACE}; }}
            QMessageBox QLabel {{ color: {Theme.TEXT}; }}
        """)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Multi-Lottery System")
    app.setOrganizationName("LottoMax")
    app.setStyle("Fusion")

    window = LottoGUIApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
