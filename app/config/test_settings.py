from .settings import Settings


class TestSettings(Settings):
    DB_NAME: str = "test_db"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    DB_HOST: str = "pgdb"
    DB_PORT: int = 5432

    TEST_DB_URL: str = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
