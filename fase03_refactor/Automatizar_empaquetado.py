import os

# Carpeta raíz de tu proyecto refactorizado
CARPETA_PROYECTO = "fase03_refactor"
ARCHIVO_SALIDA = "proyecto_consolidado.md"

# Directorios a omitir para no saturar memoria
EXCLUIR = ["legacy", "fixtures", "__pycache__", ".pytest_cache", ".git"]

with open(ARCHIVO_SALIDA, "w", encoding="utf-8") as outfile:
    outfile.write("# CÓDIGO FUENTE Y PRUEBAS ACTIVAS - FASE 03\n\n")
    archivos_incluidos = 0

    for root, dirs, files in os.walk(CARPETA_PROYECTO):
        # Omitir carpetas no deseadas
        if any(ignorar in root for ignorar in EXCLUIR):
            continue

        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                outfile.write(f"### ARCHIVO: {filepath}\n")
                outfile.write("```python\n")
                with open(filepath, "r", encoding="utf-8") as infile:
                    outfile.write(infile.read())
                outfile.write("\n```\n\n")
                archivos_incluidos += 1
                print(f"Incluido: {filepath}")

print(
    f"\n¡Proceso completado! Se consolidaron {archivos_incluidos} archivos en '{ARCHIVO_SALIDA}'."
)