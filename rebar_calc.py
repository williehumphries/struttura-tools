#!/usr/bin/env python3
"""Structural engineering TUI helper."""

import csv
import math
import os

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import DataTable, Footer, Header, Input, Label, Select, Static, TabbedContent, TabPane

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
DEFAULT_ROW = next(i for i, (n, _) in enumerate(REBAR) if n == DEFAULT_BAR)

# ── Data loading ───────────────────────────────────────────────────────────

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def _fmt(val: str, unit: str = "mm") -> str:
    """Format a CSV value with unit; show '—' for zero/empty."""
    return f"{val} {unit}" if val and val != "0" else "—"


OVM_ANCHORS: dict[str, dict] = {}
OVM_SPACING: dict[str, dict] = {}

try:
    with open(os.path.join(_DATA_DIR, "ovm_anchors.csv"), newline="", encoding="utf-8-sig") as _f:
        for _row in csv.DictReader(_f):
            OVM_ANCHORS[_row["Anchor_Name"]] = _row
except FileNotFoundError:
    pass

try:
    with open(os.path.join(_DATA_DIR, "ovm_anchor_spacing.csv"), newline="", encoding="utf-8-sig") as _f:
        for _row in csv.DictReader(_f):
            OVM_SPACING[_row["Anchor_Name"]] = _row
except FileNotFoundError:
    pass

# ── Macalloy stress bar data ────────────────────────────────────────────────

MACALLOY_BARS: dict[str, dict] = {}

try:
    with open(os.path.join(_DATA_DIR, "macalloy_bars.csv"), newline="", encoding="utf-8-sig") as _f:
        for _row in csv.DictReader(_f):
            MACALLOY_BARS[_row["bar_dia"]] = _row
except FileNotFoundError:
    pass

MACALLOY_BAR_DIAS    = list(MACALLOY_BARS.keys())
DEFAULT_MACALLOY_DIA = MACALLOY_BAR_DIAS[0] if MACALLOY_BAR_DIAS else "20"

# ── OVM post-tensioning constants ────────────────────────────────────────────

DEFAULT_STRANDS = 7
STRAND_ULT_KN   = 279.0   # characteristic breaking load per 15.7 mm strand

PT_SPACING_FIGURE = (
    " ─── concrete edge ─────────────────\n"
    " │\n"
    " │    ◉                   ◉\n"
    " │    │←──────── a ──────→│\n"
    " │←b─→│\n"
    " │\n"
    "\n"
    " a   min. centre-to-centre spacing\n"
    " b   min. edge distance (ctr to face)"
)

# ── Rebar helpers ───────────────────────────────────────────────────────────

def bar_area(d: float) -> float:
    """Cross-sectional area of a circular bar in mm²."""
    return math.pi * d ** 2 / 4.0


def bar_weight(d: float) -> float:
    """Unit weight of a steel bar in kg/m (density = 7850 kg/m³)."""
    return bar_area(d) * 7850e-6


class StructCalcApp(App):
    """Structural engineering calculator."""

    TITLE = "STRUTTURA"
    SUB_TITLE = "Design aids"

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "reset", "Reset"),
    ]

    CSS = """
    Screen {
        background: $surface;
    }

    TabbedContent {
        height: 1fr;
    }

    TabbedContent ContentSwitcher {
        height: 1fr;
    }

    TabPane {
        height: 1fr;
        padding: 0;
    }

    /* ── Rebar tab ── */

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

    /* ── OVM PT Anchors tab ── */

    #pt-body {
        height: 1fr;
    }

    #pt-selector-row {
        height: auto;
        padding: 1 2 0 2;
        align: left middle;
    }

    #pt-selector-row Label {
        width: auto;
        padding: 1 1 0 0;
        margin: 0;
        color: $text-muted;
    }

    #pt-selector-row Select {
        width: 28;
        margin: 0;
    }

    .force-box {
        width: auto;
        min-width: 22;
        height: 3;
        padding: 0 1;
        margin: 0 0 0 2;
        border: solid $success;
        color: $success;
        text-style: bold;
        content-align: left middle;
    }

    #pt-content {
        height: 1fr;
    }

    #pt-dims-panel {
        width: 1fr;
        border: solid $primary;
        margin: 1 0 1 1;
        padding: 0 1;
    }

    #pt-dims-panel DataTable {
        height: 1fr;
    }

    #pt-spacing-panel {
        width: 54;
        border: solid $primary;
        margin: 1 1 1 1;
        padding: 0 1;
    }

    #pt-spacing-panel DataTable {
        height: auto;
    }

    #pt-spacing-figure {
        padding: 1 1 0 1;
        color: $text-muted;
    }

    /* ── Macalloy Bars tab ── */

    #mac-body {
        height: 1fr;
    }

    #mac-selector-row {
        height: auto;
        padding: 1 2 0 2;
        align: left middle;
    }

    #mac-selector-row Label {
        width: auto;
        padding: 1 1 0 0;
        margin: 0;
        color: $text-muted;
    }

    #mac-selector-row Select {
        width: 28;
        margin: 0;
    }

    #mac-content {
        height: 1fr;
    }

    #mac-bar-panel {
        width: 1fr;
        border: solid $primary;
        margin: 1 0 1 1;
        padding: 0 1;
    }

    #mac-bar-panel DataTable {
        height: 1fr;
    }

    #mac-acc-panel {
        width: 1fr;
        border: solid $primary;
        margin: 1 1 1 1;
        padding: 0 1;
    }

    #mac-acc-panel DataTable {
        height: 1fr;
    }
    """

    selected_bar: reactive[str] = reactive(DEFAULT_BAR)

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent():

            # ── Tab 1: Rebar ───────────────────────────────────
            with TabPane("Rebar", id="tab-rebar"):
                with Horizontal(id="body"):

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

            # ── Tab 2: PT Anchors ──────────────────────────────
            with TabPane("OVM PT Anchors", id="tab-pt"):
                with Vertical(id="pt-body"):

                    with Horizontal(id="pt-selector-row"):
                        yield Label("Number of strands")
                        yield Select(
                            [(str(n), n) for n in range(1, 38)],
                            value=DEFAULT_STRANDS,
                            id="strand-select",
                        )
                        yield Static("", id="pt-max-force", classes="force-box")
                        yield Static("", id="pt-75-force",  classes="force-box")

                    with Horizontal(id="pt-content"):

                        with Vertical(id="pt-dims-panel"):
                            yield Static("ANCHOR DIMENSIONS", classes="panel-title")
                            dims_table = DataTable(cursor_type="none", id="pt-dims-table")
                            dims_table.add_columns("Property", "Value")
                            yield dims_table

                        with Vertical(id="pt-spacing-panel"):
                            yield Static("MINIMUM SPACING", classes="panel-title")
                            spacing_table = DataTable(cursor_type="none", id="pt-spacing-table")
                            spacing_table.add_columns("f'c (MPa)", "Min c/c  a (mm)", "Min edge  b (mm)")
                            yield spacing_table
                            yield Static(PT_SPACING_FIGURE, id="pt-spacing-figure")

            # ── Tab 3: Macalloy Bars ───────────────────────────
            with TabPane("Macalloy Bars", id="tab-mac"):
                with Vertical(id="mac-body"):

                    with Horizontal(id="mac-selector-row"):
                        yield Label("Bar diameter")
                        yield Select(
                            [(f"Ø{d} mm", d) for d in MACALLOY_BAR_DIAS],
                            value=DEFAULT_MACALLOY_DIA,
                            id="macalloy-bar-select",
                        )
                        yield Static("", id="mac-ult-force", classes="force-box")
                        yield Static("", id="mac-75-force",  classes="force-box")

                    with Horizontal(id="mac-content"):

                        with Vertical(id="mac-bar-panel"):
                            yield Static("BAR & NUT", classes="panel-title")
                            mac_bar_table = DataTable(cursor_type="none", id="mac-bar-table")
                            mac_bar_table.add_columns("Property", "Value")
                            yield mac_bar_table

                        with Vertical(id="mac-acc-panel"):
                            yield Static("COUPLER, END PLATE & SPIRAL", classes="panel-title")
                            mac_acc_table = DataTable(cursor_type="none", id="mac-acc-table")
                            mac_acc_table.add_columns("Property", "Value")
                            yield mac_acc_table

        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#ref-table", DataTable).move_cursor(row=DEFAULT_ROW)
        self._update_pt_display(DEFAULT_STRANDS)
        self._update_macalloy_display(DEFAULT_MACALLOY_DIA)

    # ── Event handlers ─────────────────────────────────────────

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Clicking a row in the reference table updates the calculator."""
        bar_name = str(event.row_key.value)
        self.query_one("#bar-select", Select).value = bar_name

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "bar-select":
            if event.value is Select.BLANK:
                return
            self.selected_bar = str(event.value)
            names = [n for n, _ in REBAR]
            if self.selected_bar in names:
                self.query_one("#ref-table", DataTable).move_cursor(
                    row=names.index(self.selected_bar)
                )
            self._recalculate()
        elif event.select.id == "strand-select":
            if isinstance(event.value, int):
                self._update_pt_display(event.value)
        elif event.select.id == "macalloy-bar-select":
            if isinstance(event.value, str):
                self._update_macalloy_display(event.value)

    def on_input_changed(self, _: Input.Changed) -> None:
        self._recalculate()

    # ── Rebar calculation ──────────────────────────────────────

    def _recalculate(self) -> None:
        d = BAR_DICT.get(self.selected_bar, 12)
        a = bar_area(d)

        count_input  = self.query_one("#count-input",   Input)
        count_result = self.query_one("#count-result",  Static)
        try:
            n = int(count_input.value)
            if n <= 0:
                raise ValueError
            count_result.update(f"{n} × {self.selected_bar}  =  {a * n:.1f} mm²")
            count_result.remove_class("empty")
        except ValueError:
            count_result.update("—")
            count_result.add_class("empty")

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

    # ── PT display ─────────────────────────────────────────────

    def _update_pt_display(self, n: int) -> None:
        anchor_name   = f"OVM.M15A-{n}"
        dims_table    = self.query_one("#pt-dims-table",    DataTable)
        spacing_table = self.query_one("#pt-spacing-table", DataTable)

        dims_table.clear()
        spacing_table.clear()

        max_force = n * STRAND_ULT_KN
        self.query_one("#pt-max-force", Static).update(f"P_ult  {max_force:.0f} kN")
        self.query_one("#pt-75-force",  Static).update(f"P_75%  {max_force * 0.75:.0f} kN")

        anchor = OVM_ANCHORS.get(anchor_name)
        if anchor:
            dims_table.add_row("Anchor",         anchor_name)
            dims_table.add_row("Casting Ø",      _fmt(anchor["Casting_Dia"]))
            dims_table.add_row("Casting length", _fmt(anchor["Casting_Len"]))
            dims_table.add_row("Duct ID",        _fmt(anchor["Duct_ID"]))
            dims_table.add_row("Head Ø",         _fmt(anchor["Head_Dia"]))
            dims_table.add_row("Head thickness", _fmt(anchor["Head_T"]))
            dims_table.add_row("Spiral Ø",       _fmt(anchor["Spiral_Dia"]))
            dims_table.add_row("Spiral bar",     f"Y{anchor['Bar_size']}")
            dims_table.add_row("Spiral pitch",   _fmt(anchor["Spiral_pitch"]))
            dims_table.add_row("Spiral turns",   anchor["Spiral_turns"])

        spacing = OVM_SPACING.get(anchor_name)
        if spacing:
            for fck in ("40", "50", "60"):
                a_val = spacing[f"{fck}_a"]
                b_val = spacing[f"{fck}_b"]
                spacing_table.add_row(f"{fck} MPa", _fmt(a_val), _fmt(b_val))

    # ── Macalloy display ───────────────────────────────────────

    def _update_macalloy_display(self, dia: str) -> None:
        bar_table = self.query_one("#mac-bar-table", DataTable)
        acc_table = self.query_one("#mac-acc-table", DataTable)
        bar_table.clear()
        acc_table.clear()

        bar = MACALLOY_BARS.get(dia)
        if not bar:
            return

        f_load = float(bar["f_load"])
        self.query_one("#mac-ult-force", Static).update(f"P_ult  {f_load:.0f} kN")
        self.query_one("#mac-75-force",  Static).update(f"P_75%  {f_load * 0.75:.0f} kN")

        bar_table.add_row("Bar Ø",        _fmt(bar["bar_dia"]))
        bar_table.add_row("Weight",       f"{bar['kg_per_m']} kg/m")
        bar_table.add_row("Ult. load",    f"{bar['f_load']} kN")
        bar_table.add_row("Nut thick.",   _fmt(bar["nut_t"]))
        bar_table.add_row("Nut A/F",      _fmt(bar["nut_across_flat"]))

        acc_table.add_row("Coupler Ø",      _fmt(bar["coupler_dia"]))
        acc_table.add_row("Coupler length", _fmt(bar["coupler_len"]))
        acc_table.add_row("End plate L",    _fmt(bar["end_plate_len"]))
        acc_table.add_row("End plate W",    _fmt(bar["end_plate_widt"]))
        acc_table.add_row("End plate t",    _fmt(bar["end_plate_t"]))
        acc_table.add_row("Spiral Ø",       _fmt(bar["spiral_d"]))
        acc_table.add_row("Spiral pitch",   _fmt(bar["spiral_pitch"]))
        acc_table.add_row("Spiral turns",   bar["spiral_turns"])
        acc_table.add_row("Spiral bar",     bar["spiral_bar"])

    # ── Actions ────────────────────────────────────────────────

    def action_reset(self) -> None:
        self.query_one("#count-input",   Input).value = ""
        self.query_one("#spacing-input", Input).value = ""


if __name__ == "__main__":
    StructCalcApp().run()
