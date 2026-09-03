from datetime import datetime

import pyarrow as pa
import pyarrow.parquet as pq


def write_parquet_file(
    table_name: str,
    data: list[tuple],
    schema: pa.Schema,
    ingested_at: datetime,
    output_path: str = ".",
) -> None:
    """
    Write data to a Parquet file with the given schema.

    Args:
        table_name (str): The name of the table (used for the Parquet file name).
        data (list[tuple]): The data to write, where each tuple represents a row.
        schema (pa.Schema): The PyArrow schema for the data.
        ingested_at (datetime): The timestamp to add to the 'ingested_at' column.
    """
    with pq.ParquetWriter(
        f"{output_path}/{table_name}.parquet", schema=schema
    ) as writer:
        columns = list(zip(*data))
        arrays = [
            pa.array(col, type=schema.field(i).type) for i, col in enumerate(columns)
        ]
        arrays.append(
            pa.array(
                [ingested_at] * len(data),
                type=schema.field(-1).type,
            )
        )
        table = pa.Table.from_arrays(arrays, schema=schema)
        writer.write_table(table)
