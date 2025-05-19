import polars as pl
from pathlib import Path
from datetime import datetime

data_folder = "data/"
data = []
date_format = "%d-%m-%Y_%H-%M-%S"

for file in Path(data_folder).iterdir():
    df = pl.read_csv(file, separator=";").filter(pl.col("Denominació / Denominación").is_not_null())

    date_string = file.name.removeprefix("estat_traf").removesuffix(".csv")
    timestamp = datetime.strptime(date_string, date_format)

    instance = {}
    instance["timestamp"] = timestamp
    for row in df.iter_rows(named=True):
        instance[str(row["gid"])] = row["Estat / Estado"]
    data.append(instance)

df_concat = pl.DataFrame(data)
print(df_concat.head())

df_concat.write_csv("data_concat.csv")