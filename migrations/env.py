"""Online, transactional DDL restricted to the disposable case database."""

from alembic import context
from alembic.util.exc import CommandError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from scripts.migration_config import TEST_DATABASE, test_engine


def run():
    if context.is_offline_mode():
        raise CommandError("Offline execution is not enabled for this exercise")
    target = context.get_x_argument(as_dictionary=True).get("database")
    if target != TEST_DATABASE:
        raise CommandError("Use -x database=ilc_f2p02b_test explicitly")
    engine = test_engine(target)
    try:
        with engine.connect() as connection:
            identity = connection.execute(
                text("SELECT current_user, current_database()")
            ).one()
            if tuple(identity) != ("ilc_app", TEST_DATABASE):
                raise CommandError("Unexpected database identity")
            connection.rollback()
            context.configure(
                connection=connection,
                target_metadata=None,
                transactional_ddl=True,
                version_table_schema="public",
            )
            with context.begin_transaction():
                context.run_migrations()
    except (SQLAlchemyError, OSError, ValueError) as error:
        raise CommandError(f"Migration failed ({type(error).__name__})") from None
    finally:
        engine.dispose()


run()
