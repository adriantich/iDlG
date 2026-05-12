from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd
import plotly.graph_objects as go


@dataclass(frozen=True)
class ScanCase:
    key: str
    chromosome: str
    window_size: int
    step_size: int

    @property
    def label(self) -> str:
        return f"{self.chromosome} | window={self.window_size} | step={self.step_size}"


class InteractivePlot:
    _cached_frames: dict[str, pd.DataFrame] = {}

    def __init__(self, scanner: Any):
        self.scanner = scanner
        self.cases = self._build_cases()
        if not self.cases:
            raise ValueError("The provided ScanerByPos instance does not contain scan results.")
        
        self.chromosomes = sorted(set(c.chromosome for c in self.cases))
        self.windows = sorted(set(c.window_size for c in self.cases))
        self.steps = sorted(set(c.step_size for c in self.cases))
        
        self.selected_chromosome = self.chromosomes[0]
        self.selected_window = self.windows[0]
        self.selected_step = self.steps[0]

    def _build_cases(self) -> list[ScanCase]:
        cases = []
        for item in getattr(self.scanner, "result_index", []):
            if isinstance(item, dict):
                cases.append(
                    ScanCase(
                        key=item["key"],
                        chromosome=item["chromosome"],
                        window_size=item["window_size"],
                        step_size=item["step_size"],
                    )
                )
                continue

            if not isinstance(item, (list, tuple)) or len(item) != 4:
                raise ValueError(
                    "Each entry in result_index must be a 4-item tuple/list: "
                    "(key, chromosome, window_size, step_size)."
                )

            key, chromosome, window_size, step_size = item
            cases.append(
                ScanCase(
                    key=key,
                    chromosome=str(chromosome),
                    window_size=int(window_size),
                    step_size=int(step_size),
                )
            )
        return cases
    
    def _find_case(self, chromosome: str, window_size: int, step_size: int) -> ScanCase | None:
        """Find a case matching the given chromosome, window, and step."""
        for case in self.cases:
            if case.chromosome == chromosome and case.window_size == window_size and case.step_size == step_size:
                return case
        return None

    def case_to_dataframe(self, case_key: str) -> pd.DataFrame:
        case_rows = self.scanner.results_mean.get(case_key)
        if case_rows is None:
            raise KeyError(f"Case '{case_key}' is not available in results_mean.")

        table = pd.DataFrame(case_rows)
        if table.empty:
            raise ValueError(f"Case '{case_key}' does not contain rows to plot.")

        required_columns = {"start", "end"}
        missing_columns = required_columns - set(table.columns)
        if missing_columns:
            missing_display = ", ".join(sorted(missing_columns))
            raise ValueError(f"Case '{case_key}' is missing required columns: {missing_display}.")

        table = table.sort_values("start").reset_index(drop=True)
        table["midpoint"] = (table["start"] + table["end"]) / 2
        return table

    def _sample_columns(self, table: pd.DataFrame) -> list[str]:
        return [column for column in table.columns if column not in {"start", "end", "midpoint"}]

    def _frame_traces(self, case: ScanCase) -> list[go.Scatter]:
        table = self.case_to_dataframe(case.key)
        traces = []
        for sample_name in self._sample_columns(table):
            traces.append(
                go.Scatter(
                    x=table["midpoint"],
                    y=table[sample_name],
                    mode="lines+markers",
                    name=sample_name,
                    hovertemplate=(
                        "sample=%{fullData.name}<br>"
                        "position=%{x}<br>"
                        "mean=%{y}<extra></extra>"
                    ),
                )
            )
        return traces

    def build_figure(self) -> go.Figure:
        current_case = self._find_case(self.selected_chromosome, self.selected_window, self.selected_step)
        if current_case is None:
            current_case = self.cases[0]
        
        if current_case.key not in self._cached_frames:
            self._cached_frames[current_case.key] = self._frame_traces(current_case)
        initial_traces = self._cached_frames[current_case.key]

        frames = []
        for case in self.cases:
            frames.append(
                go.Frame(
                    name=case.key,
                    data=self._frame_traces(case),
                    layout=go.Layout(title=self._title(case)),
                )
            )
        y_chr = 1.15
        y_win = 1.1
        y_step = 1.05
        xpos = 0.52
        figure = go.Figure(data=initial_traces, frames=frames)
        figure.update_layout(
            title=self._title(current_case),
            xaxis_title="Mean Window Position",
            yaxis_title="Mean Window value",
            template="plotly_white",
            hovermode="x unified",
            updatemenus=[
                self._build_dimension_menu("chromosome", self.chromosomes, y_chr, xpos=xpos),
                self._build_dimension_menu("window", self.windows, y_win, xpos=xpos),
                self._build_dimension_menu("step", self.steps, y_step, xpos=xpos),
            ],
            annotations=[
                dict(
                    text = "Chromosome:",
                    x=xpos, y=y_chr,
                    xref="paper", yref="paper",
                    showarrow=False, align="left",
                    xanchor="right",
                    yanchor="top"
                    ),
                dict(
                    text = "Window Size:",
                    x=xpos, y=y_win,
                    xref="paper", yref="paper",
                    showarrow=False, align="left",
                    xanchor="right",
                    yanchor="top"
                    ),
                dict(
                    text = "Step Size:",
                    x=xpos, y=y_step,
                    xref="paper", yref="paper",
                    showarrow=False, align="left",
                    xanchor="right",
                    yanchor="top"
                    )
            ]
        )
        return figure

    def show(self) -> None:
        self.build_figure().show()

    def write_html(self, output_path: str) -> None:
        self.build_figure().write_html(output_path)

    def _title(self, case: ScanCase) -> str:
        return (
            "Interactive scan by position"
            f"<br><sup>{case.label}</sup>"
        )

    def _build_dimension_menu(
            self,
            dimension: str,
            values: list[int | str],
            y_position: float,
            xpos: float) -> dict[str, Any]:
        """Build a button menu for selecting a single dimension (chromosome, window, or step)."""
        buttons = []
        for value in values:
            # Determine which case matches this value and current selections
            if dimension == "chromosome":
                target_chr, target_win, target_step = str(value), self.selected_window, self.selected_step
            elif dimension == "window":
                target_chr, target_win, target_step = self.selected_chromosome, int(value), self.selected_step
            else:  # step
                target_chr, target_win, target_step = self.selected_chromosome, self.selected_window, int(value)
            
            target_case = self._find_case(target_chr, target_win, target_step)
            
            buttons.append(
                {
                    "label": str(value),
                    "method": "animate",
                    "args": [
                        [target_case.key] if target_case else [None],
                        {
                            "frame": {"duration": 300, "redraw": True},
                            "mode": "immediate",
                            "transition": {"duration": 150},
                        },
                    ],
                }
            )
        
        # Determine the initial active button
        if dimension == "chromosome":
            active_idx = values.index(self.selected_chromosome)
        elif dimension == "window":
            active_idx = values.index(self.selected_window)
        else:  # step
            active_idx = values.index(self.selected_step)

        return {
            "buttons": buttons,
            "direction": "left",
            "pad": {"r": 10, "t": 0.5},
            "showactive": True,
            "type": "buttons",
            "x": xpos,
            "xanchor": "left",
            "y": y_position,
            "yanchor": "top",
            "active": active_idx,
            "bgcolor": "#f0f0f0",
        }