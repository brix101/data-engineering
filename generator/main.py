import time
from datetime import timedelta

from generator.categories import seed_categories
from generator.coupon_assignment import seed_coupon_assignment
from generator.coupons import seed_coupons
from generator.customers import seed_customers
from generator.order_items import seed_order_items
from generator.orders import seed_orders
from generator.payments import seed_payments
from generator.products import seed_products
from generator.returns import seed_returns
from generator.sellers import seed_sellers
from generator.shipments import seed_shipments


def main():
    start_time = time.perf_counter()

    print("Generating customers...")
    seed_customers(1_000_000)

    print("Generating categories...")
    seed_categories()

    print("Generating sellers...")
    seed_sellers(10_000)

    print("Generating products...")
    seed_products()

    print("Generating coupons...")
    seed_coupons()

    print("Generating orders...")
    seed_orders()

    print("Generating order items...")
    seed_order_items()

    print("Assigning coupons to eligible orders...")
    seed_coupon_assignment()

    print("Generating payments...")
    seed_payments()

    print("Generating shipments...")
    seed_shipments()

    print("Generating returns...")
    seed_returns()

    elapsed = time.perf_counter() - start_time
    print(f"Done! Total runtime: {timedelta(seconds=int(elapsed))} ({elapsed:.2f}s)")


if __name__ == "__main__":
    main()
