"""
main.py — punto de entrada de Fase 03 (Etapa 1 + Etapa 2).
Ejecuta el pipeline con muestreo estratificado por target y luego prepara
TRAIN/TEST. NO entrena modelos (eso es Fase 4).
"""
from fase03.config import ConfiguracionPipeline
from fase03.muestreo import MuestreoEstratificadoPorTarget
from fase03.pipeline import PipelineFase03


def main():
    config = ConfiguracionPipeline()
    estrategia = MuestreoEstratificadoPorTarget(config)
    pipeline = PipelineFase03(config, estrategia)
    df_final = pipeline.ejecutar()
    return pipeline.preparar_datasets_modelado(df_final)


if __name__ == "__main__":
    main()