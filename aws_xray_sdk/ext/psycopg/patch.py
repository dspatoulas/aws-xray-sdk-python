import wrapt
from operator import methodcaller

from aws_xray_sdk.ext.dbapi2 import XRayTracedConn


def patch():
    wrapt.wrap_function_wrapper(
        'psycopg',
        'connect',
        _xray_traced_connect
    )

    wrapt.wrap_function_wrapper(
        'psycopg_pool.pool',
        'ConnectionPool._connect',
        _xray_traced_connect
    )


def _xray_traced_connect(wrapped, instance, args, kwargs):
    conn = wrapped(*args, **kwargs)
    parameterized_dsn = {c[0]: c[-1] for c in map(methodcaller('split', '='), conn.info.dsn.split(' '))}
    db_name = parameterized_dsn.get('dbname', 'unknown')
    meta = {
        'database_type': 'PostgreSQL',
        'url': 'postgresql://{}@{}:{}/{}'.format(
            parameterized_dsn.get('user', 'unknown'),
            parameterized_dsn.get('host', 'unknown'),
            parameterized_dsn.get('port', 'unknown'),
            db_name,
        ),
        'user': parameterized_dsn.get('user', 'unknown'),
        'database_version': str(conn.info.server_version),
        'driver_version': 'Psycopg 3',
        'name': db_name,
    }

    return XRayTracedConn(conn, meta)
