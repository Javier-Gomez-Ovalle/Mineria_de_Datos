# Procedencia, atribución y licencias por componente

## RBA

Fuente: https://www.kaggle.com/datasets/dasgroup/rba-dataset
Documentación de los autores: https://github.com/das-group/rba-dataset
Licencia: Creative Commons Attribution 4.0 International, https://creativecommons.org/licenses/by/4.0/
Atribución: Stephan Wiefling, Paul René Jørgensen, Sigurd Thunem y Luigi Lo Iacono. “Pump Up Password Security! Evaluating and Enhancing Risk-Based Authentication on a Real-World Large-Scale Online Service” (2022), https://doi.org/10.1145/3546069.

Los valores publicados son sintetizados a partir de comportamiento real, no registros identificables de clientes. IP, timestamps e identificadores no deben interpretarse como identidades o accesos reales. El original local `rba_dataset.csv` tiene 9.052.907.531 bytes y queda externo.

## IPinfo

Fuente: https://www.kaggle.com/datasets/ipinfo/ipinfo-country-asn
Proveedor: IPinfo, catálogo IP to Country and ASN. Licencia de la base gratuita: Creative Commons Attribution-ShareAlike 4.0 International, https://creativecommons.org/licenses/by-sa/4.0/
Evidencia del proveedor: https://community.ipinfo.io/t/librespeed-org-has-adopted-ipinfos-free-ip-database/5728
Atribución: IP address data powered by IPinfo, https://ipinfo.io/.

Es un catálogo de redes reales, aplicado aquí a eventos sintéticos. `country_asn.csv` local tiene 204.153.289 bytes. No se acreditó versión/fecha exacta de descarga ni correspondencia byte a byte con Kaggle. No se inventa esa información ni se reemplaza por una edición reciente. El catálogo queda externo; descargar la versión actual puede cambiar el enriquecimiento.

## Derivados incluidos

`dataset_train_fase04.csv` combina una selección RBA, enriquecimiento IPinfo, atributos generados y features temporales; conserva etiquetas reconciliadas y es la partición de usuarios de train con semilla 42. Se conservan las atribuciones RBA e IPinfo. Su redistribución adaptada se ofrece con CC BY-SA 4.0 para el material derivado aplicable, manteniendo los avisos RBA CC BY 4.0; no se atribuye autoría del original al proyecto. La publicación de este derivado se realiza bajo la autorización de los responsables del proyecto, con atribución a ambas fuentes y condición CompartirIgual. La edición local sigue sin acreditarse; no se afirma equivalencia con una descarga actual.

`empleados.csv`: nombres mediante Faker y roles, residencia, ciudad, turnos, estado y fecha simulados, vinculados a identificadores RBA. Se conserva para reproducir exactamente el enriquecimiento histórico. Los atributos propios se publican con autorización de sus responsables, sin declarar una licencia adicional no elegida; los identificadores mantienen su procedencia RBA.

El completo corregido y `rba_2000_users.csv` se omiten de esta entrega porque contienen eventos de usuarios reservados para test; no por contener identificadores sintéticos. Los datos de test y copias históricas tampoco se distribuyen.

## Código, informes y artefactos

No se impone una licencia única a todo el repositorio. No se encontró una declaración general de licencia del código propio: queda pendiente elección por sus titulares. Las dependencias mantienen sus licencias. Informes y figuras conservan atribuciones y contenido histórico; modelo, preprocesador, umbral y manifiestos son copias exactas. Los inventarios históricos incluyen rutas locales y hashes documentales; son procedencia, no configuraciones ejecutables ni credenciales. Publicación temporal no revoca los permisos ya concedidos bajo licencias abiertas.
