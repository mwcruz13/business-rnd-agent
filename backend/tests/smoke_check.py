import psycopg

from backend.app.config import get_settings


def main() -> None:
    settings = get_settings()
    with psycopg.connect(
        host=settings.postgres_host,
        port=settings.postgres_port,
        dbname=settings.postgres_db,
        user=settings.postgres_user,
        password=settings.postgres_password,
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute("select 1")
            result = cursor.fetchone()

    print(
        "smoke-check "
        f"backend={settings.llm_backend} "
        f"db={settings.postgres_host}:{settings.postgres_port} "
        f"query_result={result[0] if result else 'none'}"
    )


if __name__ == "__main__":
    main()
