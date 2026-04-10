import os

import httpx
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Label, Button, Input

DATA_SCHEME_FIELDS = [
    ("RevolvingUtilizationOfUnsecuredLines", "0-1", float),
    ("age", "0-120", int),
    ("DebtRatio", "0-1", float),
    ("MonthlyIncome", "0-1000000", int),
    ("NumberOfOpenCreditLinesAndLoans", "0-100", int),
    ("NumberOfTime30_59DaysPastDueNotWorse", "0-100", int),
    ("NumberOfTime60_89DaysPastDueNotWorse", "0-100", int),
    ("NumberOfTimes90DaysLate", "0-100", int),
    ("NumberRealEstateLoansOrLines", "0-100", int),
    ("NumberOfDependents", "0-30", int),
]

API_URL = os.getenv("API_URL", "http://localhost:8080").rstrip("/")
RISK_STATUS_THRESHOLDS = [
    (0.10, "минимальный риск", "status-minimal"),
    (0.25, "низкий риск", "status-low"),
    (0.35, "умеренный риск", "status-moderate"),
    (0.45, "повышенный риск", "status-elevated"),
    (0.50, "плохой рейтинг", "status-bad"),
    (0.60, "высокий риск", "status-high"),
]


class CreditRiskApp(App[None]):
    CSS_PATH = "styles.tcss"

    def compose(self) -> ComposeResult:
        with Container(id="app"):
            with Container(id="main_block", classes="content"):
                with Container(id="features_list"):
                    for field_name, field_limits, _ in DATA_SCHEME_FIELDS:
                        with Container(classes="feature"):
                            yield Label(field_name, classes="feature_label")
                            yield Input(
                                placeholder=field_limits,
                                classes="feature_input",
                                id=f"input_{field_name}",
                            )
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
        status_label.remove_class(
            "status-minimal",
            "status-low",
            "status-moderate",
            "status-elevated",
            "status-bad",
            "status-high",
            "status-critical",
        )
        if status_class is not None:
            status_label.add_class(status_class)

    def set_result(self, rating: float, status: str, status_class: str | None = None):
        self.set_rating(rating)
        self.set_status(status, status_class)

    def get_risk_status(self, risk: float) -> tuple[str, str]:
        for threshold, status, status_class in RISK_STATUS_THRESHOLDS:
            if risk < threshold:
                return status, status_class
        return "критический риск", "status-critical"

    def collect_payload(self) -> dict[str, int | float]:
        payload: dict[str, int | float] = {}
        for field_name, _, field_type in DATA_SCHEME_FIELDS:
            input_widget = self.query_one(f"#input_{field_name}", Input)
            raw_value = input_widget.value.strip().replace(",", ".")
            payload[field_name] = field_type(raw_value)
        return payload

    async def send_credit_risk_request(self, payload: dict[str, int | float]) -> float:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(f"{API_URL}/credit_risk", json=payload)
            response.raise_for_status()
        data = response.json()
        return float(data["credit_risk"])

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id != "result_button":
            return

        button = event.button
        button.disabled = True
        try:
            payload = self.collect_payload()
        except ValueError:
            self.notify("Проверьте значения полей", severity="error")
            button.disabled = False
            return

        try:
            risk = await self.send_credit_risk_request(payload)
            status, status_class = self.get_risk_status(risk)
            self.set_result(risk, status, status_class)
        except httpx.HTTPError as exc:
            self.notify(f"Не удалось отправить запрос: {exc}", severity="error")
        except (KeyError, TypeError, ValueError):
            self.notify("API вернул некорректный ответ", severity="error")
        finally:
            button.disabled = False


def run() -> None:
    CreditRiskApp().run()


if __name__ == "__main__":
    run()
