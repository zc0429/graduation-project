"""Independently compare running MySQL columns, keys and constraints with DDL."""
import csv
import json
import re
from pathlib import Path
import pymysql

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / 'docs/validation/thesis-system-consistency-20261113'


def main():
    password = dict(line.split('=', 1) for line in (ROOT / '.local/mysql.env').read_text().splitlines())['MYSQL_ROOT_PASSWORD']
    db = pymysql.connect(host='127.0.0.1', port=3307, user='root', password=password,
                         database='wrongbook_browser', cursorclass=pymysql.cursors.DictCursor)
    def query(sql):
        with db.cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchall()
    columns = query("SELECT TABLE_NAME,COLUMN_NAME,COLUMN_TYPE,IS_NULLABLE,COLUMN_DEFAULT,COLUMN_KEY,EXTRA,ORDINAL_POSITION FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() ORDER BY TABLE_NAME,ORDINAL_POSITION")
    indexes = query("SELECT TABLE_NAME,INDEX_NAME,NON_UNIQUE,SEQ_IN_INDEX,COLUMN_NAME FROM information_schema.STATISTICS WHERE TABLE_SCHEMA=DATABASE() ORDER BY TABLE_NAME,INDEX_NAME,SEQ_IN_INDEX")
    constraints = query("SELECT TABLE_NAME,CONSTRAINT_NAME,CONSTRAINT_TYPE FROM information_schema.TABLE_CONSTRAINTS WHERE TABLE_SCHEMA=DATABASE() ORDER BY TABLE_NAME,CONSTRAINT_NAME")
    tables = query("SELECT TABLE_NAME,ENGINE,TABLE_COLLATION FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() ORDER BY TABLE_NAME")
    actual = {(c['TABLE_NAME'], c['COLUMN_NAME']): c for c in columns}
    expected_keys = set()
    expected_columns = set()
    sql = (ROOT / 'server/src/main/resources/db/schema.sql').read_text()
    for match in re.finditer(r'CREATE TABLE IF NOT EXISTS `(\w+)` \((.*?)\) ENGINE[^;]+;', sql, re.S):
        table, body = match.groups()
        for line in body.splitlines():
            col = re.match(r'\s*`?(\w+)`?\s+(BIGINT|VARCHAR\(\d+\)|CHAR\(\d+\)|TINYINT|INT|TEXT|DATETIME|DATE)\s+(.+)', line)
            if not col:
                continue
            name, typ, rest = col.groups()
            key = table, name
            expected_columns.add(key)
            row = actual[key]
            assert row['COLUMN_TYPE'] == typ.lower(), (key, typ, row)
            assert row['IS_NULLABLE'] == ('NO' if 'NOT NULL' in rest else 'YES'), key
            default = re.search(r'DEFAULT (CURRENT_TIMESTAMP|NULL|\d+|\x27[^\x27]*\x27)', rest)
            value = default[1].strip("'").lower().removesuffix('()') if default else None
            if value == 'null':
                value = None
            current = None if row['COLUMN_DEFAULT'] is None else str(row['COLUMN_DEFAULT']).lower().removesuffix('()')
            assert current == value, (key, current, value)
            assert ('auto_increment' in row['EXTRA']) == ('AUTO_INCREMENT' in rest), key
            assert ('on update' in row['EXTRA'].lower()) == ('ON UPDATE CURRENT_TIMESTAMP' in rest), key
        for key in re.finditer(r'(PRIMARY KEY|UNIQUE KEY (\w+)|KEY (\w+))\s*\(([^)]+)\)', body):
            label, unique, ordinary, fields = key.groups()
            name = 'PRIMARY' if label == 'PRIMARY KEY' else unique or ordinary
            for position, field in enumerate(fields.split(','), 1):
                expected_keys.add((table, name, 1 if ordinary else 0, position, field.strip(' `')))
    assert expected_columns == set(actual)
    assert expected_keys == {(r['TABLE_NAME'], r['INDEX_NAME'], r['NON_UNIQUE'], r['SEQ_IN_INDEX'], r['COLUMN_NAME']) for r in indexes}
    assert all(t['ENGINE'] == 'InnoDB' and t['TABLE_COLLATION'] == 'utf8mb4_unicode_ci' for t in tables)
    assert not any(c['CONSTRAINT_TYPE'] in ['FOREIGN KEY', 'CHECK'] for c in constraints)
    result = {'database': 'wrongbook_browser', 'server_version': query('SELECT VERSION() version')[0]['version'],
              'tables': tables, 'columns': columns, 'indexes': indexes, 'constraints': constraints,
              'table_count': len(tables), 'column_count': len(columns), 'named_index_count': len({(r['TABLE_NAME'], r['INDEX_NAME']) for r in indexes}),
              'foreign_key_count': 0, 'check_count': 0, 'ddl_exact_metadata_match': True}
    (RUN / 'runtime-schema.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    for filename, rows in [('schema-columns.tsv', columns), ('schema-indexes.tsv', indexes), ('schema-constraints.tsv', constraints)]:
        with (RUN / filename).open('w') as file:
            writer = csv.DictWriter(file, fieldnames=rows[0].keys(), delimiter='\t', lineterminator='\n')
            writer.writeheader(); writer.writerows(rows)
    print(json.dumps({k: result[k] for k in ['server_version', 'table_count', 'column_count', 'named_index_count', 'foreign_key_count', 'check_count', 'ddl_exact_metadata_match']}))
    db.close()


if __name__ == '__main__':
    main()
