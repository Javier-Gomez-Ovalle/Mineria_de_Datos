"""
pipeline.py
===========
Orquestador de Fase 03.

DIP: recibe la estrategia de muestreo por constructor.
MEMORIA: self solo guarda config y estrategia; los DataFrames/Counters grandes
son variables locales, liberadas con del + gc.collect().
INTEGRIDAD: el target viaja con su evento durante la ingeniería. Se verifica
la asociación por clave estable antes/después; las features no leen el target.

ejecutar()                     -> Fase 03 hasta dataset_final_modelo.csv (evento).
preparar_datasets_modelado()   -> Etapa 2: split por usuario -> X/y ->
                                  preprocesamiento (fit solo TRAIN) ->
                                  remuestreo solo TRAIN. NO entrena modelos.
"""
import gc

import joblib

from .rba_reader import AnalizadorRBA
from .empleados import GeneradorEmpleados
from .ip_resolver import ResolutorIPinfo
from .features import (
    crear_features_temporales,
    crear_feature_impossible_travel,
    crear_feature_turnos,
    crear_features_negocio,
)
from .validacion import validar_calidad_bloqueante
from .diagnostico import generar_metricas_diagnosticas, imprimir_checklist_final
from .exportacion import exportar_dataset_final
from .split import dividir_train_test_por_usuario
from .preprocessing import separar_x_y, preprocesar_train_test, COLUMNA_TARGET
from .resampling import remuestrear_train
from .asociacion_target import capturar_asociacion_target, verificar_asociacion_target


class PipelineFase03:
    def __init__(self, config, estrategia_muestreo):
        self.config = config
        self.estrategia_muestreo = estrategia_muestreo

    def ejecutar(self):
        config = self.config

        # --- [1-2/8] Análisis del RBA por chunks (incluye conteo ATO por usuario) ---
        analizador = AnalizadorRBA(config)
        contador_usuarios, contador_eventos_ato, diagnostico_global = analizador.primera_pasada()

        # --- [3/8] Selección de usuarios (estrategia inyectada) ---
        resultado_muestreo = self.estrategia_muestreo.seleccionar(
            contador_usuarios, contador_eventos_ato
        )
        usuarios_seleccionados = resultado_muestreo.usuarios
        del contador_usuarios, contador_eventos_ato
        gc.collect()

        # --- [4/8] Historial completo de los usuarios seleccionados ---
        df_logs, diagnostico_subconjunto = analizador.segunda_pasada(usuarios_seleccionados)

        # --- [5/8] Maestro sintético de empleados ---
        generador_empleados = GeneradorEmpleados(config)
        df_empleados = generador_empleados.generar(usuarios_seleccionados)

        df_integrado = df_logs.merge(df_empleados, on="User ID", how="inner")
        del df_logs, df_empleados
        gc.collect()

        # --- [6/8] Resolución IP (incluye fix de dtype de merge_asof) ---
        resolutor_ip = ResolutorIPinfo(config)
        df_integrado, diagnostico_resolucion = resolutor_ip.resolver(df_integrado)

        # El target permanece unido al evento; nunca se reasigna por índice.
        referencia_target = capturar_asociacion_target(df_integrado)

        # --- [7/8] Features (no utilizan el target como entrada de cálculo) ---
        df_integrado, n_login_desconocidos = crear_features_temporales(df_integrado, config)
        df_integrado, diagnostico_centroides = crear_feature_impossible_travel(df_integrado, config)
        df_integrado = crear_feature_turnos(df_integrado)
        df_integrado = crear_features_negocio(df_integrado)

        verificar_asociacion_target(df_integrado, referencia_target)
        del referencia_target

        # --- [8/8] Validación bloqueante + exportación + diagnóstico ---
        validar_calidad_bloqueante(df_integrado, usuarios_seleccionados, config)

        df_final = exportar_dataset_final(df_integrado, config)

        metricas = generar_metricas_diagnosticas(
            df_integrado, usuarios_seleccionados, diagnostico_global,
            diagnostico_subconjunto, diagnostico_resolucion,
            diagnostico_centroides, n_login_desconocidos, config,
        )

        imprimir_checklist_final(df_final, metricas, config)

        return df_final

    def preparar_datasets_modelado(self, df_final):
        """Etapa 2. SPLIT -> X/y -> preprocesamiento (fit solo TRAIN) ->
        remuestreo (solo TRAIN). Exporta dataset_train_prepared.csv,
        dataset_test_prepared.csv y preprocessor.joblib. No entrena nada."""
        config = self.config
        print("=" * 60)
        print("[ETAPA 2] split -> X/y -> preprocesamiento -> remuestreo TRAIN")
        print("=" * 60)

        df_train, df_test, info_split = dividir_train_test_por_usuario(df_final, config)
        X_train, y_train = separar_x_y(df_train)
        X_test, y_test = separar_x_y(df_test)
        del df_train, df_test
        gc.collect()

        preprocesador, X_train_t, X_test_t = preprocesar_train_test(X_train, X_test)
        del X_train, X_test
        gc.collect()

        X_train_res, y_train_res, info_remuestreo = remuestrear_train(
            X_train_t, y_train, config
        )
        del X_train_t
        gc.collect()

        train_preparado = X_train_res.copy()
        train_preparado[COLUMNA_TARGET] = y_train_res.to_numpy()
        test_preparado = X_test_t.copy()
        test_preparado[COLUMNA_TARGET] = y_test.to_numpy()
        train_preparado.to_csv(config.OUT_TRAIN_PREPARED, index=False)
        test_preparado.to_csv(config.OUT_TEST_PREPARED, index=False)
        joblib.dump(preprocesador, config.OUT_PREPROCESSOR)
        filas_train, filas_test = len(train_preparado), len(test_preparado)
        del train_preparado, test_preparado
        gc.collect()

        print(f"  Archivos: {config.OUT_TRAIN_PREPARED} ({filas_train:,} filas), "
              f"{config.OUT_TEST_PREPARED} ({filas_test:,} filas), "
              f"{config.OUT_PREPROCESSOR}")
        print("  [OK] No se entrenó ningún modelo, no hay predicciones ni métricas.\n")

        return {
            "X_train": X_train_res, "y_train": y_train_res,
            "X_test": X_test_t, "y_test": y_test,
            "preprocesador": preprocesador,
            "info_split": info_split, "info_remuestreo": info_remuestreo,
        }
