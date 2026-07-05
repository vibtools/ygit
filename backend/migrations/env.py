from logging.config import fileConfig
from alembic import context
from backend.core.config import get_settings
from backend.shared.base.models import Base
import backend.engines.auth_engine.models  # noqa: F401
import backend.engines.auth_engine.connected_accounts_module.models  # noqa: F401
import backend.engines.project_engine.models  # noqa: F401
import backend.engines.repository_engine.models  # noqa: F401
import backend.engines.repository_analysis_engine.models  # noqa: F401
import backend.workers.models  # noqa: F401
import backend.engines.domain_engine.models  # noqa: F401
import backend.engines.audit_engine.models  # noqa: F401
import backend.engines.platform_engine.models  # noqa: F401
import backend.engines.notification_engine.models  # noqa: F401
import backend.engines.deployment_history_engine.models  # noqa: F401
import backend.engines.deploy_engine.models  # noqa: F401
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    settings = get_settings()
    context.configure(url=settings.database_url, target_metadata=target_metadata, literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    from sqlalchemy import create_engine
    settings = get_settings()
    sync_url = settings.database_url.replace("+asyncpg", "")
    connectable = create_engine(sync_url)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
