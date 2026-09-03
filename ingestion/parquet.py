from datetime import datetime

import pyarrow as pa
import pyarrow.parquet as pq


def write_parquet_batch(
    writer: pq.ParquetWriter,
    data: list[tuple],
    schema: pa.Schema,
    ingested_at: datetime,
) -> None:
    """
    Write a single batch of rows to an already-open ParquetWriter as one row group.

    The caller owns the writer's lifecycle (open/close), so many batches can be
    appended to the same Parquet file across the extraction loop.

    Args:
        writer (pq.ParquetWriter): An open ParquetWriter to write the batch to.
        data (list[tuple]): The batch to write, where each tuple represents a row.
        schema (pa.Schema): The PyArrow schema for the data.
        ingested_at (datetime): The timestamp to add to the 'ingested_at' column.
    """
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
