import pandas as pd

class CleaningData:
    """This class is used to clean the data following the steps:
    1. Deleting redundant columns
    2. Cleaning individual columns
    3. Removing rows that contains NaN values in any column
    4. Removing rows that are duplicates when every column is the same
    5. Removing the NaN values."""

    def __init__(self, data):
        self.data = data

    def clean_data(self, percent):
        """This method is used to clean the data."""
        self.data = self.drop_columns_above_null_percent(percent)
        self.data = self.remove_duplicates()
        self.data = self.remove_nan_values()
        return self.data

    def remove_duplicates(self):
        """This method is used to remove the duplicate rows when every column is the same."""
        self.data = self.data.drop_duplicates()
        return self.data

    def remove_nan_values(self):
        """This method is used to remove rows that contains NaN values in any column."""
        self.data = self.data.dropna()
        return self.data

    def show_data(self):
        """This method is used to print the data."""
        return self.data

    def save_data(self, file_name):
        """This method is used to save the data."""
        self.data.to_csv(file_name, index=False)
        return self.data

    def print_columns(self):
        """This method is used to print the columns."""
        return self.data.columns

    def print_data_types(self):
        """This method is used to print the data types."""
        return self.data.dtypes

    def get_columns_above_null_percent(self, percent):
        """Get columns whose null share is at least `percent` (0–100)."""
        if not 0 <= percent <= 100:
            raise ValueError("percent must be between 0 and 100")

        null_percent = self.data.isna().mean() * 100
        columns_to_drop = null_percent[null_percent >= percent].index
        return columns_to_drop.tolist()        

    def drop_columns_above_null_percent(self, percent):
        """Drop columns whose null share is at least `percent` (0–100)."""
        columns_to_drop = self.get_columns_above_null_percent(percent)
        self.data = self.data.drop(columns=columns_to_drop)
        return self.data
   
    def drop_columns(self, columns):
        """Drop columns."""
        self.data = self.data.drop(columns=columns)
        return self.data

    def convert_to_boolean_values(self, columns):
        """Convert columns to boolean values, 1 for true else 0."""
        self.data[columns] = self.data[columns].astype(bool).astype(int)
        return self.data

    def trim(self, columns=None):
      """Remove leading and trailing spaces from text values.

      With no columns, every text column is trimmed. Numbers and missing
      values are left as they are.
      """
      if columns is None:
        columns = self.data.select_dtypes(include=["object", "string"]).columns
      else:
        missing = [column for column in columns if column not in self.data.columns]
        if missing:
            raise KeyError(f"columns not found: {missing}")

      for column in columns:
        values = self.data[column]
        text = values.map(lambda value: isinstance(value, str))
        self.data.loc[text, column] = values.loc[text].str.strip()
      return self.data    


    def validate_email_addresses(self, columns):
      """Validate email addresses."""
      self.data[columns] = self.data[columns].apply(lambda x: x.str.match(r"[^@]+@[^@]+\.[^@]+"))
      return self.data

