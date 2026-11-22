"""
conftest.py
===========
Fixtures compartidos para las 4 capas de prueba de regresión.

Capa A (equivalencia end-to-end) y Capa B (reproducibilidad de
empleados.csv contra el fixture real) requieren archivos que NO
existen en este entorno de desarrollo — viven únicamente en el Google
Colab de Javier: rba_2000_users.csv (54.742 filas, generado en la
corrida real) y el catálogo IPinfo (~230 MB).

Estas pruebas se marcan con skip automático si los archivos no están
presentes, indicando exactamente qué variable de entorno definir para
activarlas. Esto es intencional: no se puede demostrar equivalencia
end-to-end sin los datos reales, pero el resto de la suite (Capas C y
D, más un smoke test sintético) sí corre siempre y no depende de nada
externo.
"""
import os
import pytest


def ruta_fixture_rba_2000():
    """Ruta al rba_2000_users.csv real, si Javier lo copió a
    tests/fixtures/ o definió la variable de entorno FASE03_RBA_2000_PATH."""
    return os.environ.get(
        "FASE03_RBA_2000_PATH",
        os.path.join(os.path.dirname(__file__), "fixtures", "rba_2000_users.csv"),
    )


def ruta_fixture_ipinfo():
    """Ruta al catálogo IPinfo real (~230 MB), si Javier lo copió a
    tests/fixtures/ o definió FASE03_IPINFO_PATH."""
    return os.environ.get(
        "FASE03_IPINFO_PATH",
        os.path.join(os.path.dirname(__file__), "fixtures", "country_asn.csv"),
    )


requiere_fixture_real = pytest.mark.skipif(
    not (os.path.exists(ruta_fixture_rba_2000()) and os.path.exists(ruta_fixture_ipinfo())),
    reason=(
        "Requiere los archivos reales de Colab: copia rba_2000_users.csv y "
        "country_asn.csv a tests/fixtures/, o define las variables de entorno "
        "FASE03_RBA_2000_PATH y FASE03_IPINFO_PATH. Sin estos archivos, la "
        "equivalencia end-to-end contra el pipeline monolítico no puede "
        "demostrarse con datos reales — se omite en vez de fingir que pasó."
    ),
)
