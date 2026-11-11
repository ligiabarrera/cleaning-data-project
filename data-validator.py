import pandas as pd
import re

class DataValidator:
    def __init__(self, data: pd.DataFrame):
        self.data = data
        self.findings = []

    def _add(self, column, rule, severity, mask, message):
        """Add a finding to the findings list."""
        count = int(mask.sum())
        if count == 0:
            return
        self.findings.append({
            "column": column,
            "rule": rule,
            "severity": severity,
            "count": count,
            "message": message,
            "sample_rows": self.data.index[mask][:5].tolist(),
        })

    def run(self):
        self.findings = []
        self.check_missing_percent_values()
        self.check_duplicates()
        self.check_whitespace()
        self.check_invalid_email_addresses()
        self.check_valid_price_values()
        self.check_valid_quantity_values()
        self.check_valid_age_values()
        self.check_valid_age_ranges()
        return self

    def report(self):
        if not self.findings:
            return pd.DataFrame(columns=["column", "rule", "severity", "count", "message"])
        return pd.DataFrame(self.findings).sort_values(
            ["severity", "count"], ascending=[True, False]
        )

    def check_missing_percent_values(self, warn_at=5, error_at=50):
      null_percent = self.data.isna().mean() * 100
      for column, percent in null_percent.items():
        if percent == 0:
            continue
        severity = "error" if percent >= error_at else "warning" if percent >= warn_at else "info"
        self._add(
            column, "missing", severity,
            self.data[column].isna(),
            f"{percent:.2f}% of values are missing.",
        )        

    def check_duplicates(self):
        mask = self.data.duplicated(keep=False)
        self._add("all columns", "duplicate_row", "warning", mask,
                  "Rows are exact copies of another row.")
        return self

    def check_whitespace(self):
        text_columns = self.data.select_dtypes(include=["object", "string"]).columns
        for column in text_columns:
            values = self.data[column]
            is_text = values.map(lambda value: isinstance(value, str))
            stripped = values.map(lambda value: value.strip() if isinstance(value, str) else value)
            has_space = is_text & (values != stripped)
            self._add(column, "whitespace", "warning", has_space,
                      "Text has leading or trailing spaces.")
        return self

    def check_invalid_email_addresses(self):
        email_columns = self.data.filter(like="email").columns
        for column in email_columns:
            values = self.data[column]
            # Missing cells are reported by the missing-value check.
            # Flag only text that is present and does not match an email.
            is_invalid = values.map(
                lambda value: isinstance(value, str)
                and re.fullmatch(r"[^@]+@[^@]+\.[^@]+", value.strip()) is None
            )
            self._add(column, "invalid_email", "warning", is_invalid,
                      "Email addresses are invalid.")
        return self

    def check_valid_phone_numbers(self):
        phone_columns = self.data.filter(like="phone").columns
        for column in phone_columns:
            values = self.data[column]
            is_valid = values.map(lambda value: isinstance(value, str) and re.fullmatch(r"^\d{10}$", value.strip()) is not None)
            self._add(column, "valid_phone", "warning", is_valid,
                      "Phone numbers are invalid.")
        return self

    def check_valid_age_values(self):
        age_columns = self.data.filter(like="age").columns
        for column in age_columns:
            values = self.data[column]
            in_invalid_values = values.map(lambda value: isinstance(value, str) and re.fullmatch(r"^\d{1,3}$", value.strip()) is not None)
            self._add(column, "valid_age", "warning", in_invalid_values,
                      "Ages are invalid.")
        return self

    def check_valid_age_ranges(self):
        age_columns = self.data.filter(like="age").columns
        for column in age_columns:
            values = self.data[column]
            #check if value is between 0 and 100
            in_invalid_ranges = values.map(self._is_invalid_age_range)
            self._add(column, "invalid_age_range", "warning", in_invalid_ranges,
                      "Ages are invalid.")
        return self

    def check_valid_price_values(self):
        price_columns = self.data.filter(
            regex=r"price|cost|total|amount|fee"
        ).columns
        for column in price_columns:
            values = self.data[column]
            # Valid: a number that is 0 or greater, or text made only of
            # digits with one optional decimal point ("800.00").
            # A minus sign, comma, currency symbol, letter, or space is invalid.
            # Blank cells stay on the missing-value check.
            is_invalid = values.map(self._is_invalid_amount)
            self._add(column, "invalid_amount", "warning", is_invalid,
                      "Value is not a non-negative number.")
        return self

    @staticmethod
    def _is_invalid_amount(value):
        if pd.isna(value):
            return False
        if isinstance(value, str):
            return re.fullmatch(r"\d+(\.\d+)?", value) is None
        if isinstance(value, bool) or not pd.api.types.is_number(value):
            return True
        return float(value) < 0

    @staticmethod
    def _is_invalid_quantity(value):
        if pd.isna(value):
            return False
        if isinstance(value, str):
            if re.fullmatch(r"\d+", value) is None:
                return True
            number = int(value)
        elif isinstance(value, bool) or not pd.api.types.is_number(value):
            return True
        elif float(value) != int(value):
            return True
        else:
            number = int(value)
        return number < 0 or number > 100

    @staticmethod
    def _is_invalid_age_range(value):
        if pd.isna(value):
            return False
        if isinstance(value, str):
            text = value.strip()
            if re.fullmatch(r"^\d{1,3}$", text) is not None:
                return False
            number = int(text)    
        elif isinstance(value, bool) or not pd.api.types.is_number(value):
            return False
        else:
            number = int(value)
        return number < 0 or number > 100

    def check_valid_quantity_values(self):
        quantity_columns = self.data.filter(like="quantity").columns
        for column in quantity_columns:
            values = self.data[column]
            # -1 is stored as a number, so a string-only check never sees it.
            # Valid values are whole numbers from 0 through 100.
            is_invalid = values.map(self._is_invalid_quantity)
            self._add(column, "invalid_quantity", "warning", is_invalid,
                      "Quantities are negative.")
        return self

#Testing the validator class
data = pd.read_csv("resources/orders_qa_exercise.csv")
validator = DataValidator(data)
validator.run()
summary = validator.run().report()
print(summary.to_string(index=False))
summary.to_csv("validation_report.csv", index=False)