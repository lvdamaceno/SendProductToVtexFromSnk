import logging
import psycopg2
import os


class PostgresLogHandler(logging.Handler):
    def __init__(self, project: str):
        super().__init__()
        self.project = project
        self.dsn = os.getenv("DATABASE_URL")
        if not self.dsn:
            raise EnvironmentError("❌ Variável de ambiente DATABASE_URL não está definida.")

        self.conn = psycopg2.connect(self.dsn)
        self.conn.autocommit = True

    def emit(self, record):
        try:
            message = self.format(record)
            cursor = self.conn.cursor()
            query = """
                INSERT INTO logs (timestamp, level, logger_name, file_name, line_number, message, project)
                VALUES (CURRENT_TIMESTAMP, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                record.levelname,
                record.name,
                record.pathname,
                record.lineno,
                message,
                self.project
            ))
        except Exception as e:
            print(f"❌ Erro ao salvar log no PostgreSQL: {e}")
