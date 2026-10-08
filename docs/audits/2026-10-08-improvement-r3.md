# Tuhuella — ronda de mejora r3 (2026-10-08)

Base revisada: `db157af2973b99ef85c357128f5b815528598d7a` (`master`). Orquestación sin implementación de frentes por el conductor. Se seleccionaron tres causas con el motor canónico de improvement-pass; los demás candidatos no rellenan el cupo.

| Frente | Diagnóstico | Decisión |
|---|---|---|
| Seguridad | VALE LA PENA | HTML seguro del blog y validación de contraseña autenticada |
| Mantenibilidad | VALE LA PENA | Copia de artículos y paginación: pendientes por cupo |
| Observabilidad | VALE LA PENA | Conservar sesión ante fallos transitorios |
| Rendimiento | VALE LA PENA | Refugios/intenciones: medir consultas antes de aplicar |
| Responsividad | NO VALE LA PENA con la evidencia disponible | Sin navegador operativo en diagnóstico; no equivale a madurez |
| QA | VALE LA PENA | Validación obligatoria de esta combinación; comparación de favoritos pendiente por cupo |

## Cambios seleccionados y propietarios

- `I-S-56f0a8ab3aca` — ejecución de eventos en HTML editorial. Impacto ALTO, esfuerzo MEDIO, riesgo MEDIO. Seguridad modifica únicamente renderer, test unitario y E2E del blog. Saneamiento en navegador con DOMPurify; primera hidratación vacía, cancelación de resultados obsoletos y fallo cerrado. Conserva texto, títulos, énfasis, listas, enlaces/imágenes seguros y tablas; retira contenido activo y atributos libres.
- `I-S-f0ce0691a6d4` — cambio autenticado omite validadores existentes. Impacto MEDIO, esfuerzo BAJO, riesgo BAJO. Seguridad modifica la vista y sus pruebas. Rechaza contraseñas cortas/comunes/numéricas/similares sin cambiar la original; conserva el éxito con una contraseña válida.
- `I-O-55d444b43af6` — un fallo transitorio destruye la sesión. Impacto ALTO, esfuerzo BAJO, riesgo BAJO. Observabilidad modifica HTTP, store de autenticación, sus unitarios y E2E de autenticación. Conserva credenciales ante 503/red/timeout, propaga el fallo de refresh y libera la promesa compartida; conserva invalidación definitiva y concurrencia.

Compartido: `dompurify` fijado a `3.4.16`, su lockfile generado por npm y registros de flujos/documentación. La regeneración incorpora metadatos de paquetes opcionales ya incluidos por Tailwind; no actualiza versiones de dependencias existentes. Se declara `failure` en persistencia de sesión y `error` en redirección por credenciales definitivamente rechazadas. El mapa elimina el formulario de cambio de contraseña que la UI no implementa; se conserva su exención E2E.

## Validación y aceptación

Pruebas individuales ya ejecutadas con Node 20.20.2 y Python 3.12/settings_dev: contraseña 7 casos; renderer HTML 14 casos; HTTP 16 casos; autenticación seleccionada 8 casos. No se ejecutó la suite completa local. Máximo 20 casos por lote y tres comandos por ciclo.

QA debe acreditar sobre un commit combinado limpio: backend, unitarios frontend, tres E2E en navegador y quality gate. El blog se abre desde una tarjeta del listado antes de comprobar HTML y disparar el evento inocuo; la sesión prueba 401 inicial seguido de refresh503, recuperación posterior y rechazo401 definitivo. Las APIs de estos E2E se interceptan para no tocar datos reales. Un tag o una captura no reemplaza ejecución real.

Los artefactos tipados y el ledger de la ronda se conservan en `test-results/improvement/r3/` durante validación; se archivan fuera de los worktrees antes de retirarlos. El motor canónico usa su directorio alternativo de ledger para aislar registros de esta ronda: el ledger central del toolkit estaba sin versionar junto a cambios ajenos y no se modificó ni incorporó. La evidencia final de ejecución y CI se publica en los PR de la ronda y el PR draft de integración; este documento registra alcance, decisiones y aceptación, no certifica un SHA antes de probarlo.

## Pendientes y descartes

Pendientes por cupo: duplicación del blog que pierde seis atributos; fallback de paginación malformada; N+1 de listados de refugios/intenciones; tres E2E de comparación que pueden quedar verdes sin interactuar. No son descartes por bajo retorno.

Descartados: ampliar preferencias de notificaciones exige cambios de producto y esfuerzo/riesgo medios; dividir archivos por tamaño o reorganizar por estilo no demuestra beneficio; caches/índices/bundles no cuentan con mediciones que los justifiquen; carruseles cosméticos y checkout de plataforma placeholder tienen menor retorno.

Evidencia pendiente: Google OAuth/configuración desplegada, revocación de JWT tras cambio/reset, bloqueo SMTP por ausencia de timeout y controles responsive no medidos. No se afirman explotaciones ni madurez global. Las correcciones anteriores de pagos, filtros de animales, correo y tabla de solicitudes ya están en la base y no se repiten.

## Entrega

Un PR por rama nueva `improve/08102026-*`; ningún trabajo de rondas anteriores se adopta o retira. La dependencia compartida requiere tren de integración para validar la combinación, aunque los archivos sean disjuntos. Cierre con `merge-queue` y `all-in-base --check-only`, comprobando SHA remoto, estado de PR y contenido en `master`. El checkout desplegado permanece intacto.
