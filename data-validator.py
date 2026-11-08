import pandas as pd

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
        self.check_missing()
        self.check_duplicates()
        self.check_whitespace()
        return self

    def report(self):
        if not self.findings:
            return pd.DataFrame(columns=["column", "rule", "severity", "count", "message"])
        return pd.DataFrame(self.findings).sort_values(
            ["severity", "count"], ascending=[True, False]
        )

    def check_missing(self, warn_at=5, error_at=50):
      null_percent = self.data.isna().mean() * 100
      for column, percent in null_percent.items():
        if percent == 0:
            continue
        severity = "error" if percent >= error_at else "warning" if percent >= warn_at else "info"
        self._add(
            column, "missing", severity,
            self.data[column].isna(),
            #f"{percent:.1f}% of values are missing.",
            f"{percent}% of values are missing.",
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

#Testing the validator class
data = pd.read_csv("resources/Airbnb_Open_Data.csv")
validator = DataValidator(data)
validator.run()
summary = validator.run().report()
print(summary.to_string(index=False))
summary.to_csv("validation_report.csv", index=False)