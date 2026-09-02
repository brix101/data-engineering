import psycopg


def get_connection():
    return psycopg.connect("postgresql://ecommerce:ecommerce@localhost:5432/ecommerce")
