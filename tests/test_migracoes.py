from importlib import import_module
from types import SimpleNamespace
from unittest.mock import MagicMock

migration_0002 = import_module("apps.avaliacoes.migrations.0002_resumovinculo")
migration_0003 = import_module(
    "apps.avaliacoes.migrations.0003_alter_resumovinculo_vinculo"
)


def test_migracao_resumo_nao_recria_tabela_existente():
    connection = SimpleNamespace(
        vendor="postgresql",
        introspection=SimpleNamespace(
            table_names=lambda: ["avaliacoes_resumovinculo"]
        ),
    )
    schema_editor = MagicMock(connection=connection)

    migration_0002.ensure_resumo_table(None, schema_editor)

    schema_editor.execute.assert_not_called()


def test_migracao_fk_nao_recria_constraint_existente():
    cursor = MagicMock()
    cursor.fetchone.return_value = (1,)
    connection = MagicMock(vendor="postgresql")
    connection.cursor.return_value.__enter__.return_value = cursor
    schema_editor = SimpleNamespace(connection=connection)

    migration_0003.ensure_vinculo_fk(None, schema_editor)

    cursor.execute.assert_called_once()
    assert "ALTER TABLE" not in cursor.execute.call_args.args[0]
