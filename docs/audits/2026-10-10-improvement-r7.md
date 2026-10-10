# Tuhuella — ronda de mejora r7 (2026-10-10)

## Decisión y alcance

Base de diagnóstico: `master@88c39702a61a94c56388c8bd97c14e3e88990478`.
Seis agentes independientes, sin historial, completaron diagnóstico de solo
lectura antes de autorizar cambios. El orquestador decide, conserva registros
e integra; los agentes implementan únicamente sus archivos asignados.

El umbral es impacto ALTO, o MEDIO con esfuerzo BAJO y riesgo BAJO. El motor
canónico seleccionó tres causas globales. No llenar cada frente con cambios
es deliberado: ocho causas elegibles conservan evidencia y quedan pendientes
por cupo. Los estados de la tabla corresponden al alcance inspeccionado,
sin certificar madurez global ni ausencia de otras vulnerabilidades.

| Frente | Estado | Aplicación de esta ronda |
|---|---|---|
| Seguridad | VALE LA PENA | Revocación por cuenta y saneamiento del log OAuth |
| Mantenibilidad | VALE LA PENA | Archivo individual y masivo coherente en el admin |
| Observabilidad | VALE LA PENA | Fallos de reCAPTCHA pendientes por cupo |
| Rendimiento | VALE LA PENA | Dos causas medidas pendientes por cupo |
| Responsividad | VALE LA PENA | Desborde de cabecera en tableta pendiente por cupo |
| QA | VALE LA PENA | Validación obligatoria conjunta; dos reparaciones E2E pendientes |

## Tres causas aprobadas

### Archivo del admin sin pérdida de historial

`I-M-dba8662e66f9` — impacto ALTO, esfuerzo MEDIO, riesgo MEDIO.
Nueva evidencia: un POST real, con permiso y CSRF, eliminó en cascada
refugio, animal, solicitud, seguimiento e historial clínico. Conteos antes:
`[1,1,1,1,1]`; después: `[0,0,0,0,0]`; respuesta 302. La pérdida irreversible
justifica severidad bloqueante y prioridad sobre los otros candidatos.

El archivo masivo conservaba filas, pero registraba DELETION. Relaciones
PROTECT bloqueaban confirmaciones aunque archivar preservando el evento era
viable. Sin CSRF y sin permiso, los controles devolvieron 403. Once escenarios
del diagnóstico terminaron con exit 0; ese resultado reproduce el defecto.

Contrato aprobado: archivo coherente individual y masivo para los quince
admins existentes y PostAdoptionFollowUp, preservando relaciones y permisos
por objeto. Confirmación explícita sin Collector ni permisos de borrado sobre
hijos; PROTECT no impide archivar. Conservar las políticas de inactivación,
estado archivado y despublicación actuales. Estado y auditoría CHANGE deben
confirmarse en una misma transacción. Otros admins mantienen su comportamiento.

Dueño: agente de mantenibilidad. Archivos de aplicación: `admin.py` y tres
templates de archivo. Pruebas conductuales en `tests/utils/test_admin_archive.py`.
No se asignaron imágenes ni duplicación editorial a este implementador.

Entrega delegada: `66cc81cc4c2da9ed2477ec8c43be0ea5f8667fcb`, cinco paths y
árbol limpio. Ochenta casos distintos en verde: 74 nuevos y seis históricos,
en lotes de 14/16/16/16/18; ambos modos pasan para los dieciséis tipos. Gate
estricto con Ruff: 100/100, sin errores ni advertencias. El error de traducción
del primer lote quedó corregido; su ejecución inicial se conserva aparte.

### Credenciales fuera del diagnóstico OAuth

`I-S-19307e764661` — impacto ALTO, esfuerzo BAJO, riesgo BAJO.
`views/auth.py:260-263` pasa el credential a Google mediante `id_token` en
querystring; el manejador de error en línea 270 registra la excepción completa.
Una ConnectionError real hacia un socket reservado, sin listener, incluyó el
token sintético en la URL. Inyectada en la frontera HTTP del endpoint, produjo
401 y filtró el mismo token al logger. La configuración StreamHandler envía
esa señal a stdout. No se usaron tokens reales ni se afirmó acceso a journals.

Contrato aprobado: registrar operación y tipo de excepción; excluir mensaje,
URL, cuerpo y traceback que puedan contener la credencial. Conservar el 401,
sin crear una cuenta ante fallo del proveedor. Dueño: seguridad; prueba nueva
`tests/views/test_google_login_diagnostics.py`. La mejora de reCAPTCHA no se
incluye silenciosamente aunque comparta el archivo de autenticación.

### Revocación por cuenta al cambiar o recuperar contraseña

`I-S-2be8e9550579` — impacto ALTO, esfuerzo MEDIO, riesgo MEDIO.
Dos experimentos con SQLite aislado devolvieron 200 al cambiar/restablecer
contraseña, y luego 200 para access anterior, refresh anterior y access
renovado. La contraseña anterior ya daba 401; la nueva y otra cuenta seguían
funcionando. El cambio de contraseña no retiraba las sesiones comprometidas.

Contrato aprobado: generación de autenticación por cuenta en `User.auth_version`,
entero positivo con default 0 y no editable. Emisores añaden ese claim; access
y refresh comprueban su igualdad con la cuenta. Un JWT legado sin claim sólo
es válido mientras la generación de la cuenta siga en 0. Actualizar contraseña
y generación de forma atómica, exclusivamente en la cuenta afectada.

Conservar respuestas HTTP; después del cambio se exige un nuevo login. Un
Bearer revocado no debe bloquear el endpoint público de acceso con la nueva
contraseña. Refresh nunca promueve un token antiguo a la generación nueva.
La emisión conserva la generación de la instancia autenticada para impedir
que un login concurrente con contraseña antigua gane una sesión vigente.

Seguridad posee modelo, helper de emisión, vista, autenticador, serializer de
refresh, dos archivos de pruebas backend y `e2e/app/session-revocation.spec.ts`.
El orquestador posee `migrations/0026_user_auth_version.py` y `settings.py`:
soporte independiente en `ae54027525de44abf92bd346e093e79b30d38b5c`, integrado
en seguridad para probar una rama coherente. No se aplican migraciones ni se
despliegan servicios en esta ronda.

La rama de seguridad pasó 37 casos backend nuevos y dieciséis regresiones de
r5/r6 sobre `a32fb81552cbecdb5c2f7741d17b6197da5ff8bf`. La ruta de recuperación
equivocada en el primer lote se corrigió y se repitieron los lotes afectados.
La comprobación de migraciones no detecta diferencias pendientes. La cobertura
de revocación aprobada corresponde a esos dos endpoints públicos; no certifica
cambios de contraseña realizados por herramientas de mantenimiento.

El E2E inicial confirmó ambos 401, pero esperaba un redirect automático que la
pantalla de perfil existente no realiza al quedar sin usuario. Una segunda
ejecución detectó que el cambio de URL precede a la carga del perfil. El spec
final en `9b346618d2f979550622cb096a83a5231facf946` espera login y validación 200
con la identidad concreta, ambos 401 al revocar, cierre observable de sesión,
rechazo de una nueva navegación protegida y perfil con la contraseña nueva.
Pasó un caso real en 52,094 s, sin mocks, unexpected ni flaky. No se modifica
esa pantalla; los runs rojos anteriores se conservan sin contarlos como
aprobación. Su aceptación conjunta corresponde al manifest de la combinación
final, servido por procesos nuevos en su SHA exacto.

## Ocho causas elegibles pendientes por cupo

| ID | Evidencia vigente | Impacto / esfuerzo / riesgo |
|---|---|---|
| I-M-8d85ad31d0aa | Tres serializers tratan Library como archivo; portada PNG válida produce ValueError en FK y 500 | ALTO / MEDIO / MEDIO |
| I-M-addad843f628 | Duplicación de blog 201 pierde autor y cuatro campos de créditos/keywords ES/EN | MEDIO / BAJO / BAJO |
| I-O-a711cd0f01ee | Timeout, conexión y JSON inválido de reCAPTCHA devuelven False sin diagnóstico, indistinguibles de rechazo normal | MEDIO / BAJO / BAJO |
| I-P-a1c7fcaaff10 | Favoritos, solicitudes y apadrinamientos: Q(1)=3, Q(20)=41; prototipo 2/2 conserva respuesta | ALTO / MEDIO / BAJO |
| I-P-4c272fe82bb6 | FAQ: Q(1)=2, Q(20)=21; prototipo 2/2 conserva filtros, orden e idioma | MEDIO / BAJO / BAJO |
| I-R-fdc12518ad0c | Cabecera ES, 835×1194: scrollWidth 851, botón recortado 15,5 px; registro sigue funcionando | MEDIO / BAJO / BAJO |
| I-M-e9774f378b7b | Tres E2E buscan checkboxes inexistentes; terminan con cero interacciones de comparación | MEDIO / BAJO / BAJO |
| I-M-b73932da8755 | Dos E2E de campañas terminan con cero clicks y cero aserciones cuando no hay fixtures | MEDIO / BAJO / BAJO |

Mediciones de queries: GET decorados, Django 6.0.8, CaptureQueriesContext y
SQLite en memoria; fixtures fuera del conteo. Presupuesto: seis consultas,
constantes al crecer resultados. Miniaturas deben conservar menor rank;
`primary_attachment` puede designar otra imagen. Se precargó un solo adjunto
por galería en el prototipo. No se extrapolaron latencias al VPS.

Responsividad: Node 20.20.2, Chromium 151 e Inter cargada; diez combinaciones
ES/EN de 412×915, 835×1194, 1195×835, 1440×900 y 2560×1440. Sólo tableta ES
desbordó. Las diez navegaciones llegaron al registro correcto; Más/More y
Escape funcionaron. `locator.click()` puede desplazar 16 px; un click de
puntero sobre la parte visible funciona sin scroll. No hay registro bloqueado.

Reproducción de E2E defectuosos: cuerpos originales ejecutados en memoria con
condiciones problemáticas; no acredita navegador. En favoritos las aserciones
globales pueden coincidir con tarjetas sin comprobar el modal. En campañas el
CI prepara DB vacía sin campaña y acepta destinos incompatibles con el estado
conocido. Raza ausente y “Shelter” literal siguen como defectos independientes.

## QA y evidencia de aceptación

La QA formal se ejecuta una sola vez sobre la combinación limpia, con roles
dedicados Architect, Auditor y Verifier. Se requieren backend, E2E real y gate
estricto con Ruff/ESLint reales sobre los nuevos tests. Los lotes locales tienen
máximo veinte casos; nunca se ejecuta la suite local completa. La matriz CI
normal corresponde a cada PR y al tren de integración.

La aceptación se vincula al SHA exacto de la combinación en el manifest
`test-results/improvement/r7-20261010/qa/verification.json`, con JUnit,
Playwright JSON, gate JSON y resultado explícito para los tres candidatos.
Los artefactos son archivos regulares ignorados en el worktree validado y
se archivan fuera de éste antes de retirarlo. Los recibos finales de merge y
all-in-base se conservan junto a esa evidencia. El diagnóstico no reemplaza QA.

El preflight del helper rechazó `--projdir` por host/git_repo. El helper de
sesión tampoco resuelve worktrees anidados. El registro antiguo
`carlos18bp/tuhuella_project` y `ProjectAppLabs/tuhuella_project` resuelven ambos
al repo ID `1188194147`, default `master`. Se conserva el rechazo, se verifica
la coordenada explícitamente y se utilizan roles dedicados, gate del proyecto,
comandos aislados y record-qa sobre el tree real. No se altera el guard del
toolkit ni se afirma que su preflight pasó.

La auditoría independiente rechazó las aserciones OAuth que miraban sólo la
primera entrada del log: una segunda entrada insegura podía quedar verde.
Seguridad corrigió exclusivamente ese test en `723e39fcc8dfa50dc635fa0bb5e5d94da52f4ab8`;
los cinco casos niegan credencial, URL y cuerpo en toda la captura, además de
traceback y stack en todas las entradas. Pasaron 5/5, Ruff y gate 100/100.
Los registros globales de flujos fueron revalidados por el Analyst; un cambio
posterior sólo de aserciones no altera su semántica aunque la heurística de
fechas incluya archivos de tests bajo `backend/**/views/*.py`.

Entorno aislado propio: Python 3.12.3 y requisitos del lock de la base; Django
6.0.8, DRF 3.18 y SimpleJWT 5.5.1. Next 16.3.8, React 19.2.8 y Node 20.20.2.
Sin archivos `.env` de producción, DB del servicio, migraciones del despliegue
ni cambios en el clon principal. Su HEAD inicial `19a41cc3` estaba limpio y
dieciocho commits detrás; moverlo corresponde al despliegue.

## Descartes y límites de evidencia

- Capas, división de archivos y limpieza cosmética sin fallo demostrable.
- APM, logs generales y retries SMTP sin consumidor o con riesgo de duplicado.
- Timeout global de Axios sin bloqueo reproducido ni presupuesto compatible con uploads.
- Cachés, índices y bundles sin medición de exceso; no incluye los N+1 medidos.
- Objetivos táctiles entre variantes autenticadas: MEDIO / MEDIO / MEDIO.
- Clonar portada al duplicar blog sin contrato de independencia y limpieza.
- Activar Ruff global con deuda extensa: MEDIO / ALTO / MEDIO; no se debilita baseline.
- Cobertura porcentual y complejidad de tests sin defecto conductual concreto.

Invitaciones: N+1 medido 4/61, sin consumidor activo corroborado; requiere
evidencia de uso antes de priorizar. Perfil propio limita miniaturas a cuatro.
CPUQuota versionado 30% frente a 40% del contexto: discrepancia registrada,
sin tuning. El riesgo de redirect mediante backslash se refutó con next-intl
4.13.7 y localePrefix always; no justifica un cambio cosmético.

Se consultaron advisories npm actuales. Swiper 11.2.10, GHSA-hmx5-qpq5-p643,
requiere salto mayor para parche; no se encontró un camino para que un atacante
controle sus opciones. source-map-js 1.2.1, GHSA-68fv-2mgg-jv7q, tampoco tiene
ingestión externa corroborada. Siguen pendientes de evidencia de aplicabilidad,
sin afirmar explotación ni una auditoría limpia. pip-audit no está instalado
en el entorno aislado; la revisión backend de dependencias queda incompleta.

Controles r5/r6 revisados conservan resultados en slices seleccionados. SMTP
tiene timeout positivo; notificaciones se publican después del commit y
conservan FAILED ante rechazo de cola; backups registran y relanzan fallos.
Contrato ProjectApp v1 corroborado en `122bf1fc`; Tuhuella no tiene emisor
confirmado y no se afirmó recepción ni se activó integración.

## Propiedad e integración

Cada archivo tiene un solo autor. Seguridad dispone de ocho paths de escritura;
su diff admite además los dos prerequisites escritos por el orquestador.
Mantenibilidad dispone de cinco paths. Compartido contiene settings, migración,
este reporte y los dos documentos globales del registro E2E. El Analyst
revalidó cuatro descripciones de autenticación contra la aplicación,
manteniendo IDs, outcomes y exenciones; no incorporó flujos ni cambios de UI.
La matriz exacta y los registros del motor están en
el archivo privado de la ronda. No se modificó ni se pusheó el toolkit.

La cola valida el árbol combinado antes de drenar los PR de los frentes y el
de soporte. El draft del tren nunca se mergea. All-in-base se ejecuta en modo
check-only; el retiro posterior, sin force, está autorizado por esta ronda y
ocurre sólo tras comprobar el merge y archivar evidencias. No implica deploy.
