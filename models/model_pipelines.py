import numpy as np

from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, StandardScaler


LOG_FEATURES_LOGREG = [
    'RevolvingUtilizationOfUnsecuredLines',
    'MonthlyIncome',
]

SCALE_FEATURES_LOGREG = [
    'RevolvingUtilizationOfUnsecuredLines',
    'age',
    'DebtRatio',
    'NumberRealEstateLoansOrLines',
]

PASSTHROUGH_FEATURES_LOGREG = [
    'NumberOfOpenCreditLinesAndLoans',
    'NumberOfTimes90DaysLate',
    'NumberOfDependents',
    'MonthlyIncome_is_nan',
    'NumberOfDependents_is_nan',
    'Revolving_high',
    'Revolving_excess',
    'DebtRatio_high',
    'Late_severity_log',
]

LOG_FEATURES_GB = [
    'MonthlyIncome',
]

PASSTHROUGH_FEATURES_GB = [
    'RevolvingUtilizationOfUnsecuredLines',
    'age',
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
    'Is_old',
]


def log_features_logreg(X):
    X = X.copy()
    X[LOG_FEATURES_LOGREG] = np.log1p(X[LOG_FEATURES_LOGREG])
    return X


def log_features_gb(X):
    X = X.copy()
    X[LOG_FEATURES_GB] = np.log1p(X[LOG_FEATURES_GB])
    return X


def make_logreg_pipeline(model):
    scaler_block = ColumnTransformer(
        transformers=[
            ('scale', StandardScaler(), SCALE_FEATURES_LOGREG),
            ('keep', 'passthrough', PASSTHROUGH_FEATURES_LOGREG),
        ],
        remainder='drop',
        verbose_feature_names_out=False
    )

    pipe = Pipeline([
        ('log', FunctionTransformer(log_features_logreg, validate=False)),
        ('scale', scaler_block),
        ('model', model)
    ])

    return pipe


def make_gb_pipeline(model):
    pipe = Pipeline([
        ('log', FunctionTransformer(log_features_gb, validate=False)),
        ('model', model)
    ])
    return pipe


class EnsembleClassifier(BaseEstimator, ClassifierMixin):
    def __init__(
        self,
        logreg_model,
        lgbm_model,
        gbm_model=None,
        logreg_columns=[
            'RevolvingUtilizationOfUnsecuredLines', 'age', 'DebtRatio',
            'MonthlyIncome', 'NumberOfOpenCreditLinesAndLoans',
            'NumberOfTimes90DaysLate', 'NumberRealEstateLoansOrLines',
            'NumberOfDependents', 'MonthlyIncome_is_nan',
            'NumberOfDependents_is_nan', 'Revolving_high', 'Revolving_excess',
            'DebtRatio_high', 'Late_severity_log'
        ],
        boost_columns=[
            'RevolvingUtilizationOfUnsecuredLines', 'age', 'MonthlyIncome',
            'NumberOfOpenCreditLinesAndLoans', 'NumberOfTimes90DaysLate',
            'NumberRealEstateLoansOrLines', 'NumberOfDependents',
            'MonthlyIncome_is_nan', 'NumberOfDependents_is_nan', 'Revolving_high',
            'Revolving_excess', 'DebtRatio_high', 'Late_severity_log',
            'Late_per_credit', 'Is_old'
        ],
        threshold=0.5,
        weights=None
    ):
        self.logreg_model = logreg_model
        self.lgbm_model = lgbm_model
        self.gbm_model = gbm_model
        self.logreg_columns = logreg_columns
        self.boost_columns = boost_columns
        self.threshold = threshold
        self.weights = weights

    def predict_proba(self, X):
        probs = []

        X_logreg = X[self.logreg_columns]
        X_boost = X[self.boost_columns]

        p_logreg = self.logreg_model.predict_proba(X_logreg)[:, 1]
        probs.append(p_logreg)

        p_lgbm = self.lgbm_model.predict_proba(X_boost)[:, 1]
        probs.append(p_lgbm)

        p_gbm = self.gbm_model.predict_proba(X_boost)[:, 1]
        probs.append(p_gbm)

        probs = np.array(probs)

        if self.weights is None:
            final_prob = np.mean(probs, axis=0)
        else:
            final_prob = np.average(probs, axis=0, weights=self.weights)

        return np.column_stack([1 - final_prob, final_prob])

    def predict(self, X):
        probs = self.predict_proba(X)[:, 1]
        return (probs >= self.threshold).astype(int)


class BoostingClassifier(BaseEstimator, ClassifierMixin):
    def __init__(self, lgbm_model, gbm_model, threshold=0.5, w_lgbm=0.85, w_gbm=0.15):
        self.lgbm_model = lgbm_model
        self.gbm_model = gbm_model
        self.threshold = threshold

        self.w_lgbm = w_lgbm
        self.w_gbm = w_gbm

    def predict_proba(self, X):
        p_lgbm = self.lgbm_model.predict_proba(X)[:, 1]
        p_gbm = self.gbm_model.predict_proba(X)[:, 1]

        final_prob = (
            self.w_lgbm * p_lgbm +
            self.w_gbm * p_gbm
        )

        return np.column_stack([1 - final_prob, final_prob])

    def predict(self, X):
        probs = self.predict_proba(X)[:, 1]
        return (probs >= self.threshold).astype(int)