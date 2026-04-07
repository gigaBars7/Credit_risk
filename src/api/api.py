from fastapi import FastAPI
import uvicorn
from pydantic import BaseModel, Field
import pandas as pd
import numpy as np


app = FastAPI()


class DataScheme(BaseModel):
    RevolvingUtilizationOfUnsecuredLines: int = Field(ge=0, le=1e6)
    age: int = Field(ge=0, le=120)
    DebtRatio: int = Field(ge=0, le=1e7)
    MonthlyIncome: int = Field(ge=0, le=1e7)
    NumberOfOpenCreditLinesAndLoans: int = Field(ge=0, le=100)
    NumberOfTime30_59DaysPastDueNotWorse: int = Field(ge=0, le=100)
    NumberOfTime60_89DaysPastDueNotWorse: int = Field(ge=0, le=100)
    NumberOfTimes90DaysLate: int = Field(ge=0, le=100)
    NumberRealEstateLoansOrLines: int = Field(ge=0, le=100)
    NumberOfDependents: int = Field(ge=0, le=30)


def calc_data(data: DataScheme):
    d = data.model_dump()

    monthly_income_is_nan = int(d['MonthlyIncome'] is None)
    dependents_is_nan = int(d['NumberOfDependents'] is None)

    total_late = (
            int(d['NumberOfTime30_59DaysPastDueNotWorse']) +
            int(d['NumberOfTime60_89DaysPastDueNotWorse']) * 1.5 +
            int(d['NumberOfTimes90DaysLate']) * 2
    )
    late_severity_log = float(np.log1p(total_late))

    features = {
        'RevolvingUtilizationOfUnsecuredLines': float(d['RevolvingUtilizationOfUnsecuredLines']),
        'age': int(d['age']),
        'DebtRatio': float(d['DebtRatio']),
        'MonthlyIncome': float(d['MonthlyIncome']),
        'NumberOfOpenCreditLinesAndLoans': int(d['NumberOfOpenCreditLinesAndLoans']),
        'NumberOfTimes90DaysLate': int(d['NumberOfTimes90DaysLate']),
        'NumberRealEstateLoansOrLines': int(d['NumberRealEstateLoansOrLines']),
        'NumberOfDependents': int(d['NumberOfDependents']),

        'MonthlyIncome_is_nan': monthly_income_is_nan,
        'NumberOfDependents_is_nan': dependents_is_nan,
        'Revolving_high': int(float(d['RevolvingUtilizationOfUnsecuredLines']) > 0.8),
        'Revolving_excess': int(float(d['RevolvingUtilizationOfUnsecuredLines']) > 1.0),
        'DebtRatio_high': int(float(d['DebtRatio']) > 1.0),
        'Late_severity_log': late_severity_log,
        'Late_per_credit': float(
            late_severity_log / int(d['NumberOfOpenCreditLinesAndLoans']) + 1e-5
        ),
        'Is_old': int(int(d['age']) > 55),
    }

    columns_order = [
        'RevolvingUtilizationOfUnsecuredLines',
        'age',
        'MonthlyIncome',
        'NumberOfOpenCreditLinesAndLoans',
        'NumberOfTimes90DaysLate',
        'NumberRealEstateLoansOrLines',
        'NumberOfDependents',
        'MonthlyIncome_is_nan',
        'NumberOfDependents_is_nan',
        'Revolving_high',
        'Revolving_excess',
        'DebtRatio_high',
        'Late_severity_log',
        'Late_per_credit',
        'Is_old'
    ]

    return pd.DataFrame([features], columns=columns_order)


@app.post('/credit_risk')
def credit_risk(data: DataScheme):
    return data


if __name__ == '__main__':
    uvicorn.run('main:app', host='0.0.0.0', port=8080)