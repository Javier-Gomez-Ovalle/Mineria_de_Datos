"""
ip_utils.py
===========
Utilidades PURAS de clasificación de direcciones IP. No tienen estado
compartido entre llamadas, por eso permanecen como funciones de módulo
y NO como métodos de una clase (ver docs/FASE_03_INFORME_TECNICO.md,
sección "Qué NO se convirtió en clase y por qué").
"""
import numpy as np
import pandas as pd
import ipaddress


def clasificar_ip(ip_str):
    """Clasifica una IP y, si es IPv4 válida, la convierte a entero.
    version=4 -> IPv4 (ip_int válido). version=6 -> IPv6 (no se resuelve
    en Fase 03). version=None -> inválida/nula. Nunca lanza excepción."""
    if pd.isna(ip_str):
        return (np.nan, None)
    try:
        ip_obj = ipaddress.ip_address(str(ip_str).strip())
        if isinstance(ip_obj, ipaddress.IPv4Address):
            return (int(ip_obj), 4)
        else:
            return (np.nan, 6)
    except ValueError:
        return (np.nan, None)


def diagnosticar_ipv4_ipv6(serie_ips, etiqueta_poblacion):
    """Diagnóstico IPv4/IPv6/inválidas para CUALQUIER población de IPs,
    etiquetado explícitamente para que el checklist nunca mezcle
    poblaciones distintas sin identificarlas."""
    versiones = serie_ips.apply(lambda x: clasificar_ip(x)[1])
    total = len(versiones)
    total_ipv4 = int((versiones == 4).sum())
    total_ipv6 = int((versiones == 6).sum())
    total_invalidas = int(versiones.isna().sum())

    return {
        "poblacion": etiqueta_poblacion,
        "total_ips": total,
        "total_ipv4": total_ipv4,
        "total_ipv6": total_ipv6,
        "total_invalidas": total_invalidas,
        "pct_ipv4": 100 * total_ipv4 / total if total else 0.0,
        "pct_ipv6": 100 * total_ipv6 / total if total else 0.0,
        "pct_invalidas": 100 * total_invalidas / total if total else 0.0,
    }
