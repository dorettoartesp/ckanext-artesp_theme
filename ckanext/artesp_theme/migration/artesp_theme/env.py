# -*- coding: utf-8 -*-
from __future__ import with_statement

import os

from alembic import context
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool

from ckan.model.meta import metadata

config = context.config
fileConfig(config.config_file_name)

target_metadata = metadata

name = os.path.basename(os.path.dirname(__file__))


def include_object(object, object_name, type_, reflected, compare_to):
    if type_ == "table":
        # Only touch tables owned by this extension
        return object_name.startswith("dataset_rating") or object_name == "rating_action"
    return True


def run_migrations_offline():
    url = config.get_main_option(u"sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        version_table=u'{}_alembic_version'.format(name),
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix=u'sqlalchemy.',
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table=u'{}_alembic_version'.format(name),
            include_object=include_object,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
