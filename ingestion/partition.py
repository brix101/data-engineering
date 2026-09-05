from datetime import datetime
from pathlib import Path
from typing import NamedTuple

import pyarrow as pa
import pyarrow.parquet as pq


class WriterHandle(NamedTuple):
    """
    Bundle of everything a caller needs to write to a partition.

    Kept as a ``NamedTuple`` so it stays a tuple (cheap, immutable, unpackable)
    while allowing future fields such as a dedicated ``write_parquet`` callable
    to be added without breaking positional call sites.
    """

    writer: pq.ParquetWriter

    def write_parquet(
        self, data: list[tuple], schema: pa.Schema, ingested_at: datetime
    ):
        """
        Write a batch of rows to the underlying ParquetWriter.

        Args:
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
        self.writer.write_table(table)


class PartitionWriterManager:
    """
    Manages one ``pyarrow.parquet.ParquetWriter`` per ``(year, month)`` partition.

    Writers are created lazily on first use via :meth:`get_writer` and cached so
    subsequent rows for the same partition reuse the same file handle. Call
    :meth:`close_all` when ingestion is done to flush and close every writer.
    """

    def __init__(self):
        self.writers: dict[tuple[int, int], pq.ParquetWriter] = {}

    def partition(
        self,
        rows: list[tuple],
        ingested_at: datetime,
        partition_index: int | None = None,
    ) -> dict[tuple[int, int], list[tuple]]:
        """
        Group a batch of rows into ``(year, month)`` partitions.

        When ``partition_index`` is provided, each row is bucketed by the
        ``datetime`` value at that tuple index (its natural event time). When
        it is ``None``, the whole batch is bucketed by ``ingested_at``, which
        is useful for tables that have no meaningful event-time column.

        Args:
            rows (list[tuple]): The rows to partition. Each row must be a
                tuple positionally aligned with the table's schema.
            ingested_at (datetime): Fallback timestamp used when
                ``partition_index`` is ``None``.
            partition_index (int | None): Position of the timestamp column
                within each row. If ``None``, all rows are grouped under the
                partition derived from ``ingested_at``.

        Returns:
            dict[tuple[int, int], list[tuple]]: A mapping from ``(year, month)``
            partition keys to the rows that belong to that partition.

        Raises:
            TypeError: If ``partition_index`` is set and any row does not
                contain a ``datetime`` at that index.
        """

        partitions: dict[tuple[int, int], list[tuple]] = {}

        if partition_index is not None:
            for row in rows:
                timestamp = row[partition_index]

                if not isinstance(timestamp, datetime):
                    raise TypeError(
                        f"Expected datetime at index {partition_index}, got {type(timestamp)}"
                    )

                partition_key = self._get_partition(timestamp)
                partitions.setdefault(partition_key, []).append(row)
        else:
            # No natural event time -> bucket the whole batch by ingested_at.
            partition_key = self._get_partition(ingested_at)
            partitions[partition_key] = rows

        return partitions

    def get_writer(
        self, partition_key: tuple[int, int], table_name: str, schema: pa.Schema
    ) -> WriterHandle:
        """
        Get an existing ParquetWriter for a given partition or create a new one if it doesn't exist.

        Args:
            partition_key (tuple): The (year, month) tuple representing the partition.
            table_name (str): The name of the table being written.
            schema (pa.Schema): The PyArrow schema for the data.

        Returns:
            WriterHandle: A NamedTuple wrapping the ParquetWriter for this partition.
        """

        if partition_key not in self.writers:
            year, month = partition_key
            output_path = Path(f"data/parquet/{table_name}/{year}/{month:02d}")
            output_path.mkdir(parents=True, exist_ok=True)
            output_file = output_path / f"{table_name}.parquet"
            self.writers[partition_key] = pq.ParquetWriter(output_file, schema=schema)

        return WriterHandle(writer=self.writers[partition_key])

    def close_all(self):
        """Close all open ParquetWriter instances."""
        for writer in self.writers.values():
            writer.close()

    def _get_partition(self, timestamp: datetime) -> tuple[int, int]:
        year = timestamp.year
        month = timestamp.month

        return year, month
