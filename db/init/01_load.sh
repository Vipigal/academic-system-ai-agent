#!/usr/bin/env bash
# Carrega data/<sistema>/<tabela>.csv em <sistema>.<tabela>, tudo ou nada.
#
# - Todas as colunas são text: o dado fica idêntico ao CSV, inclusive zeros à
#   esquerda e espaços (`011550`, ` 01233-5 `), que fazem parte do cruzamento de
#   identidades. Tipos e normalização ficam para as camadas seguintes.
# - Nomes de coluna em minúsculas: os nomes do README funcionam sem aspas
#   (`SELECT STUDENT_ID` ou `SELECT contractId`).
# - Os CSVs usam CRLF: o \r do cabeçalho é removido para não entrar no nome da
#   última coluna.
set -euo pipefail

for csv in /data/*/*.csv; do
  schema="$(basename "$(dirname "$csv")")"
  table="$(basename "$csv" .csv)"
  columns="$(head -n 1 "$csv" | tr -d '\r' | tr '[:upper:]' '[:lower:]' | sed -E 's/[^,]+/"&" text/g; s/,/, /g')"

  cat <<SQL
CREATE SCHEMA IF NOT EXISTS ${schema};
CREATE TABLE ${schema}.${table} (${columns});
\\copy ${schema}.${table} FROM '${csv}' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8')
SQL
done | psql -v ON_ERROR_STOP=1 --no-psqlrc --quiet --single-transaction \
  --username "$POSTGRES_USER" --dbname "$POSTGRES_DB"

psql -v ON_ERROR_STOP=1 --no-psqlrc --quiet \
  --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" --command "ANALYZE"
