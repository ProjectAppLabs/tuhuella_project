# Tuhuella — ronda de mejora r6 (2026-10-10)

## Alcance y decisión

Base de diagnóstico: `master@d6fdbf59659915bd0fd954d8cb33fe56666d3f38`.
Seis agentes independientes, sin historial, revisaron seguridad, mantenibilidad,
observabilidad, rendimiento, responsividad y QA. La aplicación se delegó;
el orquestador posee decisiones, registros e integración.

Se evaluó el beneficio frente al esfuerzo y riesgo. El motor canónico
`improvement-ledger.sh --select` eligió tres causas globales, sin llenar otros
frentes con trabajo adicional. Las siete causas elegibles restantes siguen
pendientes por cupo; no son descartes por bajo retorno. Las revisiones fueron
localizadas: no se certifica madurez global ni ausencia de vulnerabilidades.

| Frente | Estado del diagnóstico | Trabajo seleccionado |
|---|---|---|
| Seguridad | VALE LA PENA | Ninguno; revocación JWT pendiente |
| Mantenibilidad | VALE LA PENA | Ninguno; tres causas pendientes |
| Observabilidad | VALE LA PENA | Errores de refresh y publicación después del commit |
| Rendimiento | VALE LA PENA | Carga anticipada del refugio en actualizaciones |
| Responsividad | VALE LA PENA | Ninguno; recorte de tableta pendiente |
| QA | VALE LA PENA | QA obligatoria de la combinación; dos mejoras E2E electivas pendientes |

## Seguridad

`I-S-2be8e9550579` — ALTO / MEDIO / MEDIO. Dos escenarios actuales de cambio y
restablecimiento de contraseña: operación 200, access anterior 200, refresh
anterior 200 y access renovado 200; la contraseña anterior ya daba 401 y una
cuenta ajena seguía dando 200. Diagnóstico mediante DiscoverRunner, SQLite en
memoria y transporte local: exit 0; este verde acredita la presencia del fallo.

La futura solución necesita generación de sesión por cuenta con compatibilidad
para JWT legados, comprobación tanto de access como de refresh y login con un
Bearer revocado. Debe definirse la respuesta del cambio autenticado y coordinar
esquema/emisores. Activar una bandera nativa sin transición invalidaría sesiones
legadas; cerrar todas las cuentas queda fuera del alcance. Los controles r5
no se reabrieron como regresiones. Scanners de dependencias no se ejecutaron;
no se adjudica una auditoría completa de dependencias o secretos.

## Mantenibilidad

Dos comandos de diagnóstico aislado, once escenarios, ambos exit 0:

- `I-M-dba8662e66f9` — ALTO / MEDIO / MEDIO. El POST real de borrado individual
  del admin dejó cuatro registros relacionados en cero; el archivo masivo los
  conservó. Un evento PROTECT bloqueó las confirmaciones actuales de un usuario,
  aunque inactivarlo preservando el evento era viable. La acción masiva de archivo
  se auditó como DELETION. La corrección debe ser coherente en confirmación,
  permisos por objeto, CSRF, relaciones protegidas y auditoría transaccional;
  incluye dieciséis tipos con política de archivo.
- `I-M-8d85ad31d0aa` — ALTO / MEDIO / MEDIO. Tres serializers reales de UpdatePost
  lanzaron AttributeError al tratar Library como archivo. Subir PNG válido al
  endpoint de portada lanzó ValueError al asignarlo a la FK Library. Debe usarse
  el helper existente de URL y persistir la portada adjunta transaccionalmente.
- `I-M-addad843f628` — MEDIO / BAJO / BAJO. Duplicación real devolvió 201, cambió
  autor y vació los dos créditos y los dos campos de keywords. La futura copia
  explícita debe conservar el borrador y los reinicios de publicación actuales.

## Observabilidad

- `I-O-cab1b7d335f3` — ALTO / BAJO / BAJO. OperationalError inyectado en la
  renovación produjo 401 token_not_valid; el cliente borra credenciales ante
  ese estado. Seleccionado: conservar los errores nativos de validación y
  autenticación, manejar únicamente usuario eliminado y propagar fallo interno
  como error de servidor, sin detalle sensible en producción.
- `I-O-e2e1a77b3178` — ALTO / BAJO / BAJO. DonationAdmin.changeform_view real
  publicó durante atomic; su guardado interno se sustituyó por el despachador.
  Un worker con conexión SQLite independiente terminó sin fila ni envío; tras
  commit el log quedó queued. Control autocommit: sent y un envío simulado.
  Es prueba de la frontera transacción/worker, no un POST completo de donación.
  Seleccionado: transaction.on_commit, captura individual de ID y manejo del
  rechazo de cola en el callback, preservando la operación confirmada.

Tres escenarios actuales, exit 0. Los porcentajes de pérdida de r4 son
históricos y no se usan como medición de esta ronda. La integración con
ProjectApp sigue pendiente: no se emitieron eventos ni se afirmó recepción.

Aplicación delegada: `65dc470670a64df8085905f53d75cf86faa6d5fd` conserva
errores nativos y `1bef92d01b8b0d90509c1661e6bfac206f47ceea` difiere el correo
al commit. Doce casos de refresh y dieciséis de notificaciones pasaron en lotes
independientes; cuatro regresiones seleccionadas fallaron antes del arreglo.
El gate estricto final, con Ruff real, terminó con exit 0 y sin errores,
advertencias ni fallos de infraestructura. Esto valida la rama del frente;
la aceptación de la combinación sigue vinculada al manifest final de QA.

## Rendimiento

`I-P-8270ddbe6348` — MEDIO / BAJO / BAJO. GET real de /api/updates/ en el SHA
actual, con refugios distintos e imágenes nulas válidas:

| Filas | HTTP | Consultas totales | SELECT individuales de refugio |
|---:|---:|---:|---:|
| 1 | 200 | 2 | 1 |
| 20 | 200 | 21 | 20 |

Perfil resuelto del host que sirve el proyecto: vps-projectapp-staging,
calibración 2026-09-14, 1 vCPU, 3.8 GB, CPUQuota 30%, MemoryMax 300M,
dos workers de un thread. Presupuesto del listado: seis consultas.
Seleccionado: select_related('shelter'); preservar datos, filtros y respuesta
plana. El guard conductual debe verificar constancia y presupuesto, con
fixtures fuera del conteo. No se midió la DB del servicio.

Aplicación delegada: `92ca0c8d594d0293ff2921558d9c76be7cc185c3` añade
select_related('shelter') sin alterar el contrato. El guard nuevo falló en dos
casos sobre la vista anterior. Después del arreglo, Q(1)=Q(20)=1 con veinte
refugios distintos; tres guards nuevos y tres pruebas existentes de listado
pasaron. Ruff y el gate estricto del guard terminaron con exit 0.

Solicitud aprobada al orquestador: incorporar la copia canónica de
`docs/PERFORMANCE_STANDARDS.md`, versión 1.0.0, requerida para aplicar perf-pass.
Es soporte de esta causa, sin otra optimización ni cambio de presupuesto.
La copia es idéntica al toolkit: SHA256
`8de5cc41e796837ef4c240ecfd1a5f78b88d60b63419896fb8608a25c8b4c4dc`.

## Responsividad

`I-R-fdc12518ad0c` — MEDIO / BAJO / BAJO. App local del SHA auditado, Node
20.20.2 y Chromium 151. Tableta vertical primero; diez combinaciones ES/EN:

| Viewport | scrollWidth ES / EN | Registro por click real |
|---|---|---|
| 835x1194 | 851 / 835 | Alcanzable; ES recorta 15.5 px del botón |
| 412x915 | 412 / 412 | Alcanzable tras abrir menú |
| 1195x835 | 1195 / 1195 | Alcanzable |
| 1440x900 | 1440 / 1440 | Alcanzable |
| 2560x1440 | 2560 / 2560 | Alcanzable |

Las diez navegaciones conservaron idioma y scrollX=0. Es fricción real, no un
registro bloqueado. Más/More conservó sus seis destinos y Escape cerró el menú.
La futura redistribución en dos filas queda pendiente por cupo. Controles de
idioma/tema pequeños requieren coordinar variantes autenticadas: MEDIO /
MEDIO / MEDIO, fuera del umbral de esta ronda. La matriz sólo acredita el
encabezado público revisado, no toda la aplicación.

## QA

- `I-M-e9774f378b7b` — MEDIO / BAJO / BAJO. Tres E2E de favoritos buscan checkboxes
  inexistentes y omiten selección/modal cuando el conteo es cero. Verificar
  atributos en toda la página tampoco distingue el modal de las tarjetas.
  La futura reescritura exige selector estable, interacción obligatoria y
  aserciones dentro de la tabla. Clave de raza ausente y Shelter literal en ES
  son defectos de producto separados; no se repararon silenciosamente.
- `I-M-b73932da8755` — MEDIO / BAJO / BAJO. Dos E2E de campañas aceptan ausencia
  de tarjeta sin aserciones. El CI no prepara esas campañas. La futura
  reescritura necesita fixtures API deterministas y destino exacto de CTA.

Ruff real, selección exacta del gate, sin cache: 111 archivos, exit 1,
372 hallazgos en 96 archivos: 346 docstrings, 14 orden de imports, siete
imports sin uso, dos variables sin uso y tres PT018. No aparecieron nombres
indefinidos, tests sobrescritos o aserciones siempre falsas. Instalar Ruff en
el job global sin reconciliar el corpus produciría CI rojo. Esa activación
se difiere: MEDIO / ALTO / MEDIO; no se debilitan reglas ni baseline.

La aceptación de los cambios seleccionados corresponde al manifest tipado
posterior de esta misma ronda, asociado al SHA limpio de su combinación:
`test-results/improvement/r6-20261010/qa/verification.json`. El manifest y
sus JUnit/gate son evidencias locales ignoradas que se conservan fuera de los
worktrees antes de retirarlos. CI/PR y prueba de contenido en la base se
registran en el recibo final; el diagnóstico no sustituye esa aceptación.

## Propiedad y pendientes

Observabilidad posee cuatro archivos: views de refresh, sus pruebas, servicio
de notificaciones y sus pruebas. Rendimiento posee la vista de actualizaciones
y su guard de queries. El orquestador posee este reporte y las copias de
estándares que resulten necesarias; ningún agente modifica archivos globales.

Se conservan los diez IDs históricos, tres elegidos y siete pendientes. No
se inventan nuevos IDs para la misma causa. Se usó el motor canónico con ledger
privado de la ronda, sembrado desde el archivo de r5, sin editar YAML a mano.
El contexto r6 invalida huellas antiguas por metadatos; eso no demuestra una
regresión de los tres resultados verificados de r5.

El helper de QA rechazó --projdir por el registro/host. GitHub resolvió el
nombre registrado carlos18bp/tuhuella_project y el actual ProjectAppLabs al
mismo repo ID 1188194147, default master. La validación usa gate canónico,
roles dedicados, comandos explícitos y record-qa sobre el worktree real;
no se altera el guard ni el registro del toolkit.

Descartes por bajo retorno en este alcance:

- Dividir archivos o extraer capas sin otra divergencia demostrada.
- Logs/APM sin consumidor y retries SMTP con riesgo de duplicados.
- Cachés, índices, miniaturas y bundles sin exceso medido de su presupuesto.
- Ampliar ahora objetivos táctiles entre tres variantes: MEDIO/MEDIO/MEDIO.
- Clonar la portada al duplicar blog sin contrato de independencia/limpieza.
- Activar Ruff global antes de reconciliar los 96 archivos afectados.
- Cobertura porcentual o limpieza de estilo sin un fallo conductual concreto.

Reabrir descartes si cambia el contexto, aparece una falla reproducible o se
aprueba explícitamente su alcance. No se modificó ni se pusheó el toolkit.
