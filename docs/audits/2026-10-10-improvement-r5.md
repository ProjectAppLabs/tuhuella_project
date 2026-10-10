# Tuhuella — ronda de mejora r5 (2026-10-10)

Base auditada: `d3bb7b02e5244c6bb1e70f7a6e5797d7d327e935` (`origin/master`). Seis diagnósticos de solo lectura, sin adoptar trabajo ajeno. El conductor coordina, registra y modifica únicamente configuración global; los implementadores poseen sus archivos. El límite de la ronda es tres causas, con QA combinada obligatoria fuera del cupo.

## Diagnóstico y decisión

| Frente | Estado del alcance revisado | Decisión |
|---|---|---|
| Seguridad | VALE LA PENA | Privacidad del correo del dueño y controles del endpoint alternativo JWT |
| Mantenibilidad | VALE LA PENA | Pendiente por cupo |
| Observabilidad | VALE LA PENA | Timeout SMTP; configuración del conductor y pruebas del implementador |
| Rendimiento | VALE LA PENA | Pendiente por cupo |
| Responsividad | VALE LA PENA | Pendiente por cupo; reproducir el defecto de tableta sobre la versión actual antes de corregirlo |
| QA | VALE LA PENA | Validación de la ronda; deuda electiva del corpus pendiente por cupo |

Los estados no certifican madurez global. No se ejecutó un escaneo de dependencias, medición de bundles, inspección de producción ni matriz visual nueva. Las métricas citadas de r4 son históricas. Los otros hallazgos elegibles no se descartan por bajo retorno.

## Tres causas seleccionadas

El motor canónico confirmó la misma selección sobre un worktree del SHA auditado. El registro utiliza `IMPROVEMENT_LEDGER_DIR` fuera del toolkit; no se modifican ni se pushean sus archivos.

| ID | Evidencia de la causa en la base | Impacto / esfuerzo / riesgo | Cambio y propietario |
|---|---|---|---|
| `I-S-2687a68e118c` | `serializers/shelter_list.py:7` y `shelter_detail.py:8` incluyen el correo de la cuenta en respuestas públicas | ALTO / BAJO / BAJO | Seguridad omite `owner_email` por objeto para visitantes y usuarios ajenos; dueño, equipo y operadores de plataforma lo conservan. El contacto institucional no cambia. Los IDs autorizados se calculan una vez por petición. |
| `I-S-78d772935c1e` | `base_feature_project/urls.py:33` usa la vista JWT genérica, evitando los controles existentes de `views/auth.py` | ALTO / BAJO / BAJO | Seguridad conserva `/api/token/`, su nombre y el serializer nativo; incorpora throttle compartido, reCAPTCHA y rechazo de archivados. Mantiene body `access`/`refresh`, validación de entrada, respuesta 401 con challenge y comportamiento previo de email/último acceso. |
| `I-O-082a62e80b13` | `base_feature_project/settings.py:245` no define límite SMTP; r4 documentó API y worker ocupados por esperas de correo | ALTO / BAJO / BAJO | Compartido define `DJANGO_EMAIL_TIMEOUT`, entero positivo, default 5 segundos por espera de socket; observabilidad prueba configuración y manejo de fallos reales. Sin reintentos ni cambio de backend. |

Las rutas de aplicación abreviadas son relativas a `backend/base_feature_app/`, salvo las de `base_feature_project`. La lista exacta de archivos se declara en cada PR. Seguridad posee diez archivos; compartido solo `settings.py`, `.env.example` y este reporte; observabilidad solo `tests/utils/test_email_timeout.py`.

## Contrato de validación

- Privacidad: lista y detalle para anónimo, adoptante, administrador de refugio externo, dueño, equipo, administrador de plataforma, web manager y superusuario; serializers sin request, `owner=me`, consumidores administrativos y contacto público distinto del email privado. Consultas constantes al pasar de un refugio a veinte, con presupuesto de hasta seis.
- JWT: tokens utilizables y respuesta exacta; campos ausentes/tipos inválidos/cuerpos no objeto; credenciales incorrectas e inactivos/archivados; captcha ausente/fallido/válido; cuotas compartidas en ambos sentidos; Bearer inválido ignorado como antes; email y `last_login` conservados. Regresiones existentes de sign-in y refresh.
- SMTP: diez casos para default, valor válido, cinco inválidos, propagación al transporte y fallos de contacto/worker. Importar settings reales en proceso aislado, sin `.env` de servicio. Mock únicamente del transporte; comprobar 503, FAILED, ausencia de fecha de envío y un solo intento.
- QA: un SHA combinado limpio con aplicación y tests; JUnit por lote y gate backend con `--external-lint run --semantic-rules strict --junk-severity=error` sobre los seis archivos de tests afectados. Máximo veinte casos por comando y tres comandos por ciclo. No suite local completa, baseline debilitado ni deuda electiva.

No se alteran interacciones frontend: `authStore` usa sign-in y la renovación mantiene su endpoint. E2E y Jest no son capas necesarias para estas tres causas; el CI del repo mantiene su matriz habitual.

Este documento registra decisiones y aceptación, no certifica un SHA por sí mismo. Resultados reales, commits, CI y PR se publican en los PR de la ronda; los artefactos tipados y el ledger se archivan fuera de los worktrees antes de retirarlos.

## Pendientes por cupo

1. `I-O-cab1b7d335f3`: excepciones internas de refresh se convierten en 401 y pueden cerrar sesiones durante fallos transitorios.
2. `I-O-e2e1a77b3178`: tarea de correo publicada antes del commit; el worker puede no encontrar el registro. La pérdida documentada por r4 no es una medición nueva.
3. `I-P-8270ddbe6348`: listado de actualizaciones carga el refugio por fila; r4 midió 2 a 21 consultas. Revalidar antes/después en la próxima corrección.
4. `I-S-2be8e9550579`: cambiar o restablecer contraseña no revoca los JWT anteriores; conservar compatibilidad del refresh del frontend al abordarlo.
5. `I-M-8d85ad31d0aa`: consumidores de `SingleImageField` usan la API de archivo sobre una `Library`; portada del blog y actualizaciones con imagen pueden fallar.
6. `I-M-dba8662e66f9`: borrado individual del admin no respeta el archivo masivo. El arreglo coherente también necesita confirmación, permisos, PROTECT y auditoría; esfuerzo y riesgo MEDIO.
7. `I-M-addad843f628`: duplicación del blog omite metadatos editoriales.
8. `I-M-b73932da8755`: E2E de comparación de favoritos busca controles inexistentes y puede omitir la interacción; no arreglar silenciosamente los defectos del modal al reparar las pruebas.
9. `I-M-e9774f378b7b`: E2E de detalle/CTA de campaña puede terminar sin aserciones cuando faltan fixtures.
10. `I-R-fdc12518ad0c`: fila de tableta recorta el registro según evidencia histórica; reproducción actual pendiente. Preferir dos filas conservando enlaces; mover Campañas requiere decisión de producto.

El correo de voluntariado a un dominio inexistente sigue siendo un pendiente histórico de r4, sin verificación DNS nueva aquí. El flaky de mensajes de campaña requiere reproducir el fallo y conservar trace; no se atribuye a esta ronda sin evidencia.

## Descartados por bajo retorno

- Mantenibilidad: dividir archivos, reordenar estilo o centralizar mapas y autores sin divergencia demostrada añade costo sin corregir un fallo. Reabrir solo ante una divergencia o un cambio de regla concreto.
- Observabilidad: más logs, health o APM sin consumidor/alerta real; reintentos SMTP añaden riesgo de duplicados. No agregar instrumentación para justificar la ronda.
- Rendimiento: cachés, índices, miniaturas y optimizaciones de bundle sin dataset o medición que exceda el presupuesto. Reabrir con evidencia del servicio real.
- Responsividad: retoques cosméticos, objetivos táctiles menores, Escape y truncado del email no superan el umbral. No reabrir sin un flujo realmente inaccesible.
- QA: nuevas pruebas duplicadas de conductas ya comprobadas en otra capa y arreglos de estilo que no detectan una regresión. El gate de los cambios sigue siendo obligatorio.

## Aislamiento y entrega

Ramas `improve/seguridad`, `improve/compartido` e `improve/observabilidad`, en `.worktrees/` ignorado por Git, conforme al pedido de esta ronda. Observabilidad parte del commit SMTP de compartido: su autoría se mide contra ese commit, no contra master. Los cambios heredados siguen perteneciendo al conductor.

El clon principal queda intacto. El helper local no reconoce el nombre del clon; además `qa-agent.sh --preflight` rechaza su URL porque `projects.yml` conserva `carlos18bp/tuhuella_project`, que GitHub redirige a `ProjectAppLabs/tuhuella_project`. La identidad y la coordenada se verifican por Git/GitHub y el resolver con el nombre registrado; no se cambian guards ni el toolkit. QA ejecuta directamente el gate del repo con severidad de CI y registra evidencia mediante el motor canónico.

Un PR por rama, validación combinada y drenaje mediante `merge-queue`, sin adoptar PRs ajenos. Conflictos semánticos y fallos se delegan al implementador; tras dos fallos no se absorbe su trabajo. Retiro solo de worktrees propios, limpios y mergeados, sin forzar. Cierre final `all-in-base --check-only`, con verificación que considera squash. Ningún deploy ni migración sobre la base de servicio.
