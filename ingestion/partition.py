from datetime import datetime
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq


def build_object_key(table_name: str, timestamp: datetime) -> str:
    year, month = get_partition(timestamp)

    return f"{table_name}/{year}/{month:02d}/{table_name}.parquet"


def get_partition(timestamp: datetime) -> tuple[int, int]:
    year = timestamp.year
    month = timestamp.month

    return year, month


def group_by_partition(
    rows: list[tuple], timestamp_index: int
) -> dict[tuple[int, int], list[tuple]]:
    """
    Group rows by partition (year, month) using each row's own timestamp.

    Args:
        rows (list[tuple]): The rows to group.
        timestamp_index (int): Position of the timestamp column within each row.

    Returns:
        dict[tuple[int, int], list[tuple]]: A dictionary where keys are (year, month) tuples and values are lists of rows.
    """
    partitions: dict[tuple[int, int], list[tuple]] = {}

    for row in rows:

        timestamp = row[timestamp_index]

        if not isinstance(timestamp, datetime):
            raise TypeError(
                f"Expected datetime at index {timestamp_index}, got {type(timestamp)}"
            )

        partition_key = get_partition(row[timestamp_index])
        partitions.setdefault(partition_key, []).append(row)

    return partitions


def get_or_create_writer(
    writers: dict[tuple[int, int], "pq.ParquetWriter"],
    partition_key: tuple[int, int],
    table_name: str,
    schema: "pa.Schema",
) -> "pq.ParquetWriter":
    """
    Get an existing ParquetWriter for a given partition or create a new one if it doesn't exist.

    Args:
        writers (dict): A dictionary mapping partition keys to ParquetWriters.
        partition_key (tuple): The (year, month) tuple representing the partition.
        table_name (str): The name of the table being written.
        schema (pa.Schema): The PyArrow schema for the data.

    Returns:
        pq.ParquetWriter: The ParquetWriter for the specified partition.
    """
    if partition_key not in writers:
        year, month = partition_key
        output_path = Path(f"data/parquet/{table_name}/{year}/{month:02d}")
        output_path.mkdir(parents=True, exist_ok=True)
        output_file = output_path / f"{table_name}.parquet"
        writers[partition_key] = pq.ParquetWriter(output_file, schema=schema)

    return writers[partition_key]
