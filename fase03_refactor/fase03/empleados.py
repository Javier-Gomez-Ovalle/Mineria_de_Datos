"""
empleados.py
============
Generación del maestro sintético de empleados (empleados.csv).

POR QUÉ ES UNA CLASE (justificación real, no nominal)
------------------------------------------------------
GeneradorEmpleados agrupa: (a) las distribuciones ponderadas de roles/
turnos/países (importadas de config.py), (b) el estado de los
generadores aleatorios (Faker + numpy Generator, ambos sembrados desde
config), y (c) las validaciones de integridad post-generación. Todo
esto se usa en una sola llamada (generar()), pero mantenerlo agrupado
en una clase deja explícito que la reproducibilidad depende del mismo
config en TODO el proceso — no es solo "una función con muchos
parámetros".

Pais_Residencia se genera DIRECTAMENTE como código ISO2 canónico
(ej. 'CO'), no como nombre en español — esta es la corrección aplicada
en la Versión 4 para permitir comparación directa contra
ip_country_code en features.py, sin fricción de idioma.
"""
import random

import numpy as np
import pandas as pd
from faker import Faker

from .config import (
    ROLES_ASISTENCIALES,
    ROLES_NO_ASISTENCIALES,
    TURNOS,
    PAISES_RESIDENCIA_PESOS,
    CIUDADES_POR_PAIS,
)


def _construir_lista_ponderada(pesos_dict):
    """Función pura auxiliar, sin estado — no forma parte del
    contrato público de GeneradorEmpleados."""
    etiquetas = list(pesos_dict.keys())
    pesos = np.array(list(pesos_dict.values()), dtype=float)
    pesos = pesos / pesos.sum()
    return etiquetas, pesos


class GeneradorEmpleados:
    def __init__(self, config):
        self.config = config

    def generar(self, usuarios_seleccionados):
        """Genera empleados.csv con EXACTAMENTE los User ID reales
        pasados en usuarios_seleccionados. Atributos 100% sintéticos
        (Faker, seed reproducible). Ciudad_Base coherente con
        Pais_Residencia (ISO2)."""
        config = self.config
        print("=" * 60)
        print("[5/8] Generando maestro sintético de empleados...")
        print("=" * 60)

        Faker.seed(config.FAKER_SEED)
        fake = Faker()
        rng = np.random.default_rng(config.RANDOM_STATE)
        rng_python = random.Random(config.RANDOM_STATE)

        peso_asistencial = config.PESO_ASISTENCIAL_HOSPITALARIO
        peso_no_asistencial = 1.0 - peso_asistencial

        roles_etiquetas = list(ROLES_ASISTENCIALES.keys()) + list(ROLES_NO_ASISTENCIALES.keys())
        roles_pesos = np.array(
            [w * peso_asistencial for w in ROLES_ASISTENCIALES.values()] +
            [w * peso_no_asistencial for w in ROLES_NO_ASISTENCIALES.values()]
        )
        roles_pesos = roles_pesos / roles_pesos.sum()

        turnos_etiquetas, turnos_pesos = _construir_lista_ponderada(TURNOS)
        paises_etiquetas, paises_pesos = _construir_lista_ponderada(PAISES_RESIDENCIA_PESOS)

        n = len(usuarios_seleccionados)

        roles_asignados = rng.choice(roles_etiquetas, size=n, p=roles_pesos)
        turnos_asignados = rng.choice(turnos_etiquetas, size=n, p=turnos_pesos)
        paises_asignados = rng.choice(paises_etiquetas, size=n, p=paises_pesos)
        estados_cuenta = rng.choice(
            ["Activo", "Inactivo"], size=n,
            p=[config.PROB_CUENTA_ACTIVA, 1 - config.PROB_CUENTA_ACTIVA],
        )

        registros = []
        for i, uid in enumerate(usuarios_seleccionados):
            pais_iso2 = paises_asignados[i]
            ciudades_del_pais = CIUDADES_POR_PAIS.get(pais_iso2, ["Ciudad no catalogada"])
            ciudad = rng_python.choice(ciudades_del_pais)

            registros.append({
                "User ID": uid,
                "Nombre_Completo": fake.name(),
                "Rol_Hospitalario": roles_asignados[i],
                "Pais_Residencia": pais_iso2,
                "Ciudad_Base": ciudad,
                "Turno_Asignado": turnos_asignados[i],
                "Estado_Cuenta": estados_cuenta[i],
                "Fecha_Ingreso": fake.date_between(start_date="-10y", end_date="-1y"),
            })

        df_empleados = pd.DataFrame(registros)

        self._validar_integridad(df_empleados, usuarios_seleccionados)

        iso2_no_reconocidos = set(df_empleados["Pais_Residencia"].unique()) - config.ISO2_RECONOCIDOS
        if iso2_no_reconocidos:
            print(f"  [ATENCIÓN] Códigos ISO2 generados fuera del set reconocido: "
                  f"{iso2_no_reconocidos}. Revisa PAISES_RESIDENCIA_PESOS.")
        else:
            print("  [OK] Todos los códigos ISO2 de 'Pais_Residencia' están dentro "
                  "del set reconocido por el pipeline.")

        df_empleados.to_csv(config.OUT_EMPLEADOS, index=False)

        print(f"  Empleados generados: {len(df_empleados):,}")
        print("  [OK] Integridad referencial (User ID): 100% verificado")
        print("  [OK] Coherencia Pais_Residencia (ISO2) / Ciudad_Base: 100% verificado")
        print("  Distribución de roles (asistencial vs. no asistencial):")
        print(df_empleados["Rol_Hospitalario"].value_counts(normalize=True)
              .mul(100).round(1).to_string())
        print(f"  Archivo generado: {config.OUT_EMPLEADOS}\n")

        return df_empleados

    def _validar_integridad(self, df_empleados, usuarios_seleccionados):
        """Método privado: validaciones bloqueantes post-generación,
        idénticas a las de generar_empleados() en fase03_pipeline_v4.py."""
        config = self.config

        if set(df_empleados["User ID"]) != set(usuarios_seleccionados):
            raise RuntimeError(
                "ERROR CRÍTICO DE INTEGRIDAD REFERENCIAL: los User ID de "
                "empleados.csv no coinciden 100% con los usuarios extraídos "
                "del RBA."
            )
        if len(df_empleados) != config.N_USUARIOS:
            raise RuntimeError(
                f"ERROR CRÍTICO: empleados.csv tiene {len(df_empleados)} filas, "
                f"se esperaban exactamente {config.N_USUARIOS}."
            )
        if not pd.api.types.is_integer_dtype(df_empleados["User ID"]):
            raise RuntimeError(
                "El dtype de 'User ID' en empleados.csv debe ser entero (int64)."
            )

        incoherentes = df_empleados.apply(
            lambda r: r["Ciudad_Base"] not in CIUDADES_POR_PAIS.get(r["Pais_Residencia"], []),
            axis=1,
        ).sum()
        if incoherentes > 0:
            raise RuntimeError(
                f"ERROR CRÍTICO: {incoherentes} empleados tienen Ciudad_Base "
                "incoherente con su Pais_Residencia."
            )
