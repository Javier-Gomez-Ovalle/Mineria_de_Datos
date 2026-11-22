from tools.verificar_publicacion import verificar

def test_integridad_referencia_y_ausencia_test():
    resultado = verificar()
    assert resultado['columnas'] == 62
    assert resultado['datasets_leidos'] is False
