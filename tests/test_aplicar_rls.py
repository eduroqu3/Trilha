from io import StringIO
from unittest.mock import MagicMock, patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from config.management.commands.aplicar_rls import ENABLE_RLS_SQL


def test_aplicar_rls_executes_rls_ddl_without_policies():
    cursor = MagicMock()
    connection = MagicMock(vendor="postgresql")
    connection.cursor.return_value.__enter__.return_value = cursor
    output = StringIO()

    with patch("config.management.commands.aplicar_rls.connection", connection):
        call_command("aplicar_rls", stdout=output)

    cursor.execute.assert_called_once_with(ENABLE_RLS_SQL)
    assert "ENABLE ROW LEVEL SECURITY" in ENABLE_RLS_SQL
    assert "CREATE POLICY" not in ENABLE_RLS_SQL.upper()
    assert "RLS habilitado" in output.getvalue()


def test_aplicar_rls_requires_postgresql():
    connection = MagicMock(vendor="sqlite")

    with (
        patch("config.management.commands.aplicar_rls.connection", connection),
        pytest.raises(CommandError, match="requer PostgreSQL"),
    ):
        call_command("aplicar_rls", stdout=StringIO())
