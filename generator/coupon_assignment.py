import random
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from db import get_connection

BATCH_SIZE = 10_000

COUPON_PROBABILITY = 0.25

# Max rejection-sampling attempts per order. With the date index we only
# reject on minimum_order_amount and the intraday starts_at/expires_at
# boundary, so this succeeds on the first or second try for nearly every
# order that has any active coupons.
MAX_SAMPLE_TRIES = 5


@dataclass(slots=True)
class Coupon:
    id: UUID
    starts_at: datetime
    expires_at: datetime
    minimum_order_amount: Decimal | None


def get_coupons() -> list[Coupon]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, starts_at, expires_at, minimum_order_amount
                FROM coupons
            """)
            return [
                Coupon(
                    id=row[0],
                    starts_at=row[1],
                    expires_at=row[2],
                    minimum_order_amount=row[3],
                )
                for row in cur.fetchall()
            ]


def build_active_index(
    coupons: list[Coupon],
) -> dict[date, list[Coupon]]:
    """
    Index coupons by every calendar day on which they are active.

    Lookup by order date then narrows candidates to O(active-on-that-day),
    which for our volumes is a few thousand instead of ~100k.
    """

    index: dict[date, list[Coupon]] = defaultdict(list)

    for coupon in coupons:
        day = coupon.starts_at.date()
        end = coupon.expires_at.date()

        while day <= end:
            index[day].append(coupon)
            day += timedelta(days=1)

    return index


def iter_orders_with_subtotal(batch_size: int = BATCH_SIZE):
    """
    Stream orders together with their subtotals derived from order_items.

    `coupon_id IS NULL` is a safety net: `seed_orders` writes NULL for
    every row, but this keeps the query correct if the pipeline is
    re-run partway through.
    """

    with get_connection() as conn:
        with conn.cursor(name="coupon_assignment_cursor") as cur:
            cur.execute("""
                SELECT
                    o.id,
                    o.created_at,
                    COALESCE(
                        SUM(
                            (oi.quantity * oi.unit_price) - oi.discount
                        ),
                        0
                    ) AS subtotal
                FROM orders o
                JOIN order_items oi
                    ON oi.order_id = o.id
                WHERE o.coupon_id IS NULL
                GROUP BY o.id, o.created_at
            """)

            while True:
                rows = cur.fetchmany(batch_size)

                if not rows:
                    break

                yield rows


def pick_valid_coupon(
    active_index: dict[date, list[Coupon]],
    created_at: datetime,
    subtotal: Decimal,
) -> UUID | None:
    """
    Sample a random coupon that is valid for this order.

    Candidates are pre-filtered to those active on the order's calendar
    day, so we only need to check the intraday time boundary and the
    minimum_order_amount.
    """

    candidates = active_index.get(created_at.date())

    if not candidates:
        return None

    for _ in range(MAX_SAMPLE_TRIES):
        coupon = random.choice(candidates)

        # Same-day boundary: coupon may not have started yet, or may
        # have already expired earlier that day.
        if coupon.starts_at > created_at:
            continue

        if coupon.expires_at < created_at:
            continue

        if (
            coupon.minimum_order_amount is not None
            and subtotal < coupon.minimum_order_amount
        ):
            continue

        return coupon.id

    return None


def build_assignments(
    order_batch,
    active_index: dict[date, list[Coupon]],
) -> list[tuple[UUID, UUID]]:
    assignments = []

    for order_id, created_at, subtotal in order_batch:
        if random.random() >= COUPON_PROBABILITY:
            continue

        coupon_id = pick_valid_coupon(
            active_index=active_index,
            created_at=created_at,
            subtotal=subtotal,
        )

        if coupon_id is None:
            continue

        assignments.append((order_id, coupon_id))

    return assignments


def apply_assignments(assignments: list[tuple[UUID, UUID]]) -> None:
    if not assignments:
        return

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TEMP TABLE tmp_coupon_assignments (
                    order_id UUID PRIMARY KEY,
                    coupon_id UUID NOT NULL
                ) ON COMMIT DROP
            """)

            with cur.copy(
                "COPY tmp_coupon_assignments (order_id, coupon_id) FROM STDIN"
            ) as copy:
                for row in assignments:
                    copy.write_row(row)

            cur.execute("""
                UPDATE orders o
                SET coupon_id = t.coupon_id
                FROM tmp_coupon_assignments t
                WHERE o.id = t.order_id
            """)

        conn.commit()


def seed_coupon_assignment() -> None:
    coupons = get_coupons()

    if not coupons:
        raise RuntimeError("No coupons found.")

    active_index = build_active_index(coupons)

    print(
        f"Loaded {len(coupons):,} coupons into memory "
        f"(indexed across {len(active_index):,} active days)"
    )

    total_scanned = 0
    total_assigned = 0

    for order_batch in iter_orders_with_subtotal():
        assignments = build_assignments(order_batch, active_index)

        apply_assignments(assignments)

        total_scanned += len(order_batch)
        total_assigned += len(assignments)

        print(
            f"Scanned {total_scanned:,} orders, "
            f"assigned coupons to {total_assigned:,} "
            f"({total_assigned / total_scanned:.1%})"
        )

    print(
        f"Done! Assigned coupons to "
        f"{total_assigned:,} / {total_scanned:,} orders."
    )
