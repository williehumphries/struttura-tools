#!/usr/bin/env python3
"""Rebar Area Calculator — structural engineering TUI helper."""

import math

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import DataTable, Footer, Header, Input, Label, Select, Static

REBAR = [
    ("Y6",   6),
    ("Y8",   8),
    ("Y10", 10),
    ("Y12", 12),
    ("Y16", 16),
    ("Y20", 20),
    ("Y25", 25),
    ("Y32", 32)    
]

BAR_DICT: dict[str, int] = {name: d for name, d in REBAR}

DEFAULT_BAR = "Y12"
DEFAULT_ROW  = next(i for i, (n, _) in enumerate(REBAR) if n == DEFAULT_BAR)


def bar_area(d: float) -> float:
    """Cross-sectional area of a circular bar in mm²."""
    return math.pi * d ** 2 / 4.0


def bar_weight(d: float) -> float:
    """Unit weight of a steel bar in kg/m (density = 7850 kg/m³)."""
    return bar_area(d) * 7850e-6


class RebarApp(App):
    """Rebar area calculator."""

    TITLE = "Rebar Area Calculator"
    SUB_TITLE = "Structural Engineering Helper"

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "reset", "Reset"),
    ]

    CSS = """
    Screen {
        background: $surface;
    }

    #body {
        height: 1fr;
    }

    #ref-panel {
        width: 38;
        border: solid $primary;
        margin: 1 0 1 1;
        padding: 0 1;
    }

    #ref-panel DataTable {
        height: 1fr;
    }

    #calc-panel {
        border: solid $primary;
        margin: 1;
        padding: 0 2 1 2;
    }

    .panel-title {
        background: $primary;
        color: $text;
        text-align: center;
        text-style: bold;
        padding: 0 1;
        margin-bottom: 1;
    }

    .section-label {
        color: $accent;
        text-style: bold;
        margin-top: 1;
        border-bottom: dashed $accent;
        padding-bottom: 0;
    }

    .field-label {
        margin-top: 1;
        color: $text-muted;
    }

    .result-box {
        margin-top: 1;
        padding: 0 1;
        border: solid $success;
        color: $success;
        text-style: bold;
        height: 3;
        content-align: left middle;
    }

    .result-box.empty {
        border: solid $surface-darken-2;
        color: $text-disabled;
    }

    Input {
        margin-top: 0;
        width: 1fr;
    }

    Select {
        margin-top: 0;
        width: 1fr;
    }
    """

    selected_bar: reactive[str] = reactive(DEFAULT_BAR)

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="body"):

            # ── Left: reference table ──────────────────────────
            with Vertical(id="ref-panel"):
                yield Static("REFERENCE", classes="panel-title")
                table = DataTable(cursor_type="row", id="ref-table")
                table.add_columns("Bar", "Ø (mm)", "Area mm²", "kg/m")
                for name, d in REBAR:
                    table.add_row(
                        name, str(d), f"{bar_area(d):.1f}", f"{bar_weight(d):.3f}",
                        key=name,
                    )
                yield table

            # ── Right: calculator ──────────────────────────────
            with Vertical(id="calc-panel"):
                yield Static("CALCULATOR", classes="panel-title")

                yield Label("Bar size", classes="field-label")
                yield Select(
                    [(name, name) for name, _ in REBAR],
                    value=DEFAULT_BAR,
                    id="bar-select",
                )

                yield Label("COUNT", classes="section-label")
                yield Label("Number of bars", classes="field-label")
                yield Input(placeholder="e.g. 5", id="count-input", restrict=r"\d*")
                yield Static("—", id="count-result", classes="result-box empty")

                yield Label("SPACING", classes="section-label")
                yield Label("Centre-to-centre spacing (mm)", classes="field-label")
                yield Input(placeholder="e.g. 150", id="spacing-input", restrict=r"[\d.]*")
                yield Static("—", id="spacing-result", classes="result-box empty")

        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#ref-table", DataTable).move_cursor(row=DEFAULT_ROW)

    # ── Event handlers ─────────────────────────────────────────

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Clicking a row in the reference table updates the calculator."""
        bar_name = str(event.row_key.value)
        select = self.query_one("#bar-select", Select)
        select.value = bar_name

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id != "bar-select" or event.value is Select.BLANK:
            return
        self.selected_bar = str(event.value)
        # Keep table cursor in sync
        names = [n for n, _ in REBAR]
        if self.selected_bar in names:
            self.query_one("#ref-table", DataTable).move_cursor(
                row=names.index(self.selected_bar)
            )
        self._recalculate()

    def on_input_changed(self, _: Input.Changed) -> None:
        self._recalculate()

    # ── Calculation logic ──────────────────────────────────────

    def _recalculate(self) -> None:
        d = BAR_DICT.get(self.selected_bar, 12)
        a = bar_area(d)

        # Count → total area
        count_input   = self.query_one("#count-input",   Input)
        count_result  = self.query_one("#count-result",  Static)
        try:
            n = int(count_input.value)
            if n <= 0:
                raise ValueError
            count_result.update(f"{n} × {self.selected_bar}  =  {a * n:.1f} mm²")
            count_result.remove_class("empty")
        except ValueError:
            count_result.update("—")
            count_result.add_class("empty")

        # Spacing → area per metre
        spacing_input  = self.query_one("#spacing-input",  Input)
        spacing_result = self.query_one("#spacing-result", Static)
        try:
            s = float(spacing_input.value)
            if s <= 0:
                raise ValueError
            area_per_m = a * (1000.0 / s)
            spacing_result.update(
                f"{self.selected_bar} @ {s:.0f} mm c/c  =  {area_per_m:.1f} mm²/m"
            )
            spacing_result.remove_class("empty")
        except ValueError:
            spacing_result.update("—")
            spacing_result.add_class("empty")

    # ── Actions ────────────────────────────────────────────────

    def action_reset(self) -> None:
        self.query_one("#count-input",   Input).value = ""
        self.query_one("#spacing-input", Input).value = ""


if __name__ == "__main__":
    RebarApp().run()
