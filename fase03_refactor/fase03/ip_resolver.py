"""
ip_resolver.py
==============
Resolución de rangos IP mediante IPinfo + pd.merge_asof (solo
enriquecimiento — NUNCA sustituye 'Country'/'Region'/'City' originales
del RBA).

POR QUÉ ES UNA CLASE (justificación real, no nominal)
------------------------------------------------------
ResolutorIPinfo agrupa la ruta del catálogo IPinfo (config) con una
secuencia de pasos que comparten variables intermedias (clasificación
de IPs, construcción de rangos, merge_asof, validación de rango). Es
un único método público (resolver()), pero con lógica interna multi-
paso no trivial que se beneficia de quedar autocontenida en su propio
módulo/clase en vez de vivir como función de 150 líneas en el
orquestador.

CONTIENE EL FIX DE DTYPE YA VALIDADO
-------------------------------------
'ip_int' (lado RBA) puede nacer float64 si en algún punto del archivo
completo existen IPs IPv6/inválidas (fuerzan NaN a nivel de columna).
'start_ip_int'/'end_ip_int' (lado IPinfo) pueden nacer int64 si el
catálogo no contiene ninguna entrada inválida. pd.merge_asof() exige
que ambas claves compartan dtype. La corrección castea EXPLÍCITAMENTE
a int64 ambos lados, SOLO después de garantizar la ausencia de NaN en
el subconjunto que participa del merge (ver comentarios inline). Esta
corrección NO se elimina ni se modifica en este refactor.
"""
import pandas as pd
import numpy as np

from .ip_utils import clasificar_ip


class ResolutorIPinfo:
    def __init__(self, config):
        self.config = config

    def resolver(self, df_logs):
        """Enriquece cada IP con datos de IPinfo. Enriquecimiento
        ADICIONAL, NUNCA sustituye 'Country'/'Region'/'City' originales
        del RBA. Las columnas nuevas llevan prefijo 'ip_'.

        'ip_country_code' es el código ISO2 nativo de 2 letras que
        entrega IPinfo en su columna 'country' — esta es la columna
        que se usa en features.py para 'country_mismatch', NUNCA
        'ip_country_name'.
        """
        config = self.config
        print("=" * 60)
        print("[6/8] Resolviendo rangos IP mediante IPinfo (solo enriquecimiento)...")
        print("=" * 60)

        clasificacion = df_logs["IP Address"].apply(clasificar_ip)
        df_logs["ip_int"] = clasificacion.apply(lambda t: t[0])
        df_logs["ip_version"] = clasificacion.apply(lambda t: t[1])
        del clasificacion

        total_ips = len(df_logs)
        total_ipv4 = int((df_logs["ip_version"] == 4).sum())
        total_ipv6 = int((df_logs["ip_version"] == 6).sum())
        total_invalidas = int(df_logs["ip_version"].isna().sum())

        df_ipinfo = pd.read_csv(config.IPINFO_PATH)

        columnas_ipinfo_esperadas = {"start_ip", "end_ip", "country", "country_name",
                                      "asn", "as_name", "as_domain"}
        faltantes_ipinfo = columnas_ipinfo_esperadas - set(df_ipinfo.columns)
        if faltantes_ipinfo:
            raise ValueError(
                f"ERROR: el archivo IPinfo no contiene las columnas esperadas: "
                f"{faltantes_ipinfo}"
            )

        start_clas = df_ipinfo["start_ip"].apply(clasificar_ip)
        end_clas = df_ipinfo["end_ip"].apply(clasificar_ip)
        df_ipinfo["start_ip_int"] = start_clas.apply(lambda t: t[0])
        df_ipinfo["start_version"] = start_clas.apply(lambda t: t[1])
        df_ipinfo["end_ip_int"] = end_clas.apply(lambda t: t[0])
        del start_clas, end_clas

        df_ipinfo_v4 = df_ipinfo[df_ipinfo["start_version"] == 4].copy()
        del df_ipinfo

        df_ipinfo_v4 = df_ipinfo_v4.dropna(subset=["start_ip_int", "end_ip_int"])
        df_ipinfo_v4 = df_ipinfo_v4.sort_values("start_ip_int").reset_index(drop=True)

        # CORRECCIÓN DE DTYPE (no eliminar): tras el dropna() anterior,
        # start_ip_int/end_ip_int YA NO contienen NaN en este
        # subconjunto. Se fuerza int64 explícitamente, ahora que la
        # ausencia de NaN está garantizada.
        df_ipinfo_v4["start_ip_int"] = df_ipinfo_v4["start_ip_int"].astype("int64")
        df_ipinfo_v4["end_ip_int"] = df_ipinfo_v4["end_ip_int"].astype("int64")

        print(f"  Rangos IPv4 disponibles en IPinfo: {len(df_ipinfo_v4):,}")

        ips_unicas = (
            df_logs.loc[df_logs["ip_version"] == 4, ["ip_int"]]
            .drop_duplicates()
            .sort_values("ip_int")
            .reset_index(drop=True)
        )

        # CORRECCIÓN DE DTYPE (no eliminar): 'ip_int' llega aquí ya
        # filtrado a ip_version==4, lo que garantiza ausencia de NaN en
        # ESTE subconjunto. Se fuerza int64 explícitamente para que
        # coincida con el dtype de start_ip_int en el merge_asof.
        ips_unicas["ip_int"] = ips_unicas["ip_int"].astype("int64")
        print(f"  IPs IPv4 únicas a resolver: {len(ips_unicas):,}")

        columnas_geo_ipinfo = {
            "country": "ip_country_code",
            "country_name": "ip_country_name",
            "asn": "ip_asn",
            "as_name": "ip_as_name",
            "as_domain": "ip_as_domain",
        }
        df_ipinfo_v4 = df_ipinfo_v4.rename(columns=columnas_geo_ipinfo)
        columnas_geo_final = list(columnas_geo_ipinfo.values())

        resuelto = pd.merge_asof(
            ips_unicas,
            df_ipinfo_v4[["start_ip_int", "end_ip_int"] + columnas_geo_final],
            left_on="ip_int",
            right_on="start_ip_int",
            direction="backward",
        )
        del df_ipinfo_v4

        dentro_de_rango = resuelto["ip_int"] <= resuelto["end_ip_int"]
        for col in columnas_geo_final:
            resuelto.loc[~dentro_de_rango, col] = np.nan

        ipv4_unicas_resueltas = int(dentro_de_rango.sum())
        ipv4_unicas_no_resueltas = len(resuelto) - ipv4_unicas_resueltas

        resuelto_final = resuelto[["ip_int"] + columnas_geo_final].drop_duplicates(subset="ip_int")
        del resuelto
        df_logs = df_logs.merge(resuelto_final, on="ip_int", how="left")
        del resuelto_final

        # Normalización de mayúsculas del código ISO2 nativo (por
        # seguridad, sin depender de un supuesto silencioso).
        df_logs["ip_country_code"] = df_logs["ip_country_code"].str.upper()

        pct_resolucion = (
            100 * ipv4_unicas_resueltas / len(ips_unicas) if len(ips_unicas) else 0.0
        )

        diagnostico_resolucion = {
            "total_ips": total_ips,
            "total_ipv4": total_ipv4,
            "total_ipv6": total_ipv6,
            "total_invalidas": total_invalidas,
            "ipv4_unicas_resueltas": ipv4_unicas_resueltas,
            "ipv4_unicas_no_resueltas": ipv4_unicas_no_resueltas,
            "pct_resolucion_ipv4": pct_resolucion,
        }

        print(f"  IPs IPv4 únicas resueltas: {ipv4_unicas_resueltas:,} / "
              f"{len(ips_unicas):,} ({pct_resolucion:.2f}%)")
        print("  (No se asume 100% de resolución; se mide realmente)")
        print("  Columnas de IPinfo agregadas con prefijo 'ip_' (no sustituyen "
              "'Country'/'Region'/'City'/'ASN' originales del RBA)")
        print("  'ip_country_code' (ISO2, normalizado a mayúsculas) es la columna "
              "que se usa en country_mismatch — 'ip_country_name' se conserva "
              "solo para lectura humana.\n")

        return df_logs, diagnostico_resolucion
