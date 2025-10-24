from .openrouter import (
    complete,
    astream,
    consume_and_drop,
    StreamController,
    content_from,
    content_from_file,
    with_api_key,
    build_or_messages,
)

from .models import (
    get_default_catalog,
    fetch_openrouter_models,
    merge_catalogs,
    validate_catalog,
    select_model,
    export_catalog,
    ensure_models,
    resolve_model_id,
)

from .models_sqlite import (
    create_table_sql,
    ensure_sqlite_schema,
    sqlite_upserter,
    seed_sqlite,
)

__all__ = [
    "complete",
    "astream",
    "consume_and_drop",
    "StreamController",
    "content_from",
    "content_from_file",
    "with_api_key",
    "build_or_messages",
    # models helpers
    "get_default_catalog",
    "fetch_openrouter_models",
    "merge_catalogs",
    "validate_catalog",
    "select_model",
    "export_catalog",
    "ensure_models",
    "resolve_model_id",
    # sqlite helpers
    "create_table_sql",
    "ensure_sqlite_schema",
    "sqlite_upserter",
    "seed_sqlite",
]
