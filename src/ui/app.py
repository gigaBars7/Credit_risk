from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Label, Button, Input

DATA_SCHEME_FIELDS = [
    ("RevolvingUtilizationOfUnsecuredLines", "0-1"),
    ("age", "0-120"),
    ("DebtRatio", "0-1"),
    ("MonthlyIncome", "0-1000000"),
    ("NumberOfOpenCreditLinesAndLoans", "0-100"),
    ("NumberOfTime30_59DaysPastDueNotWorse", "0-100"),
    ("NumberOfTime60_89DaysPastDueNotWorse", "0-100"),
    ("NumberOfTimes90DaysLate", "0-100"),
    ("NumberRealEstateLoansOrLines", "0-100"),
    ("NumberOfDependents", "0-30"),
]


class CreditRiskApp(App[None]):
    CSS_PATH = "styles.tcss"

    def compose(self) -> ComposeResult:
        with Container(id="app"):
            with Container(id="main_block", classes="content"):
                with Container(id="features_list"):
                    for field_name, field_limits in DATA_SCHEME_FIELDS:
                        with Container(classes="feature"):
                            yield Label(field_name, classes="feature_label")
                            yield Input(placeholder=field_limits, classes="feature_input")
            with Container(id="result_content", classes="content"):
                with Container(id="result_row"):
                    yield Button("Расчет рейтинга", id="result_button", variant="success", compact=True)
                    with Container(id="result_values"):
                        yield Label("Рейтинг: 0.0", id="rating_value")
                        yield Label("Статус: ", id="status_value")

    def set_rating(self, value: float):
        self.query_one("#rating_value", Label).update(f"Рейтинг: {value:.4f}")

    def set_status(self, text: str, status_class: str | None = None):
        status_label = self.query_one("#status_value", Label)
        status_label.update(f"Статус: {text}")
        status_label.remove_class("status-low", "status-medium", "status-high")
        if status_class is not None:
            status_label.add_class(status_class)

    def set_result(self, rating: float, status: str, status_class: str | None = None):
        self.set_rating(rating)
        self.set_status(status, status_class)


def run() -> None:
    CreditRiskApp().run()


if __name__ == "__main__":
    run()
