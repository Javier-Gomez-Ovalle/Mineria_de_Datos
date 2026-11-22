"""Selector conjunto sin etiquetas externas; orden histórico ante empate exacto."""
from fractions import Fraction
from fase04_modelado.modelos import NOMBRES

def seleccionar_variante(decisiones):
    valores={n:Fraction(decisiones[n]['f1_numerador'],decisiones[n]['f1_denominador']) for n in NOMBRES}
    mejor=max(valores.values());empates=[n for n in NOMBRES if valores[n]==mejor]
    return dict(modelo=empates[0],variantes_empatadas=empates,f1_interno=float(mejor))
