from django.core.management.base import BaseCommand, CommandError
from django.db import connection

ENABLE_RLS_SQL = """
DO $$
DECLARE
    target RECORD;
BEGIN
    FOR target IN
        SELECT schemaname, tablename
        FROM pg_catalog.pg_tables
        WHERE schemaname = 'public'
    LOOP
        EXECUTE format(
            'ALTER TABLE %I.%I ENABLE ROW LEVEL SECURITY',
            target.schemaname,
            target.tablename
        );
    END LOOP;
END
$$;
"""


class Command(BaseCommand):
    help = "Habilita RLS em todas as tabelas do schema public, sem criar policies."

    def handle(self, *args, **options):
        if connection.vendor != "postgresql":
            raise CommandError("aplicar_rls requer PostgreSQL.")

        with connection.cursor() as cursor:
            cursor.execute(ENABLE_RLS_SQL)

        self.stdout.write(self.style.SUCCESS("RLS habilitado nas tabelas do schema public."))
