# Tuhuella — ronda de mejora r4 (2026-10-08/09)

Base revisada: `7746c0a5ac718f594378cc2e3868f57c1a7193fe` (`master`). Orquestación sin implementación de frentes por el conductor; las dependencias y los registros compartidos son del conductor. Seis diagnósticos de solo lectura sobre un worktree separado y una app local con datos falsos (SQLite de `settings_dev`, sin `.env`). Cada hallazgo propuesto se volvió a verificar contra el código o la medición antes de decidir.

| Frente | Diagnóstico | Decisión |
|---|---|---|
| Seguridad | VALE LA PENA | Next 16.3.8 + sharp 0.35.5 aplicado en compartido (dependencias); el resto, pendiente por cupo |
| Mantenibilidad | VALE LA PENA | Causa de `owner=me` registrada aquí e implementada en la rama de rendimiento (mismo archivo); el resto, pendiente por cupo |
| Observabilidad | VALE LA PENA | Todo pendiente por cupo (ver prioridad) |
| Rendimiento | VALE LA PENA | N+1 del listado de refugios + filtro `owner=me` del panel, en la misma función |
| Responsividad | VALE LA PENA | Menú móvil autenticado: «Salir» alcanzable en 412×915; la fila de tableta queda pendiente por decisión de producto |
| QA | VALE LA PENA | Validación combinada obligatoria de esta ronda; sus tres arreglos de tests quedan pendientes por cupo |

## Cambios seleccionados y propietarios

El motor canónico seleccionó tres causas no diferibles (ronda `r4-08102026`). Una cuarta, también no diferible, quedaba fuera solo por el desempate fijo entre frentes; el operador autorizó incluirla y se registra aparte (ronda `r4b-08102026`) para respetar el límite de tres por registro.

- `I-S-7751d475b4d8` — Next 16.3.3 afectado por avisos corregidos en 16.3.8: SSRF en Image Optimization (GHSA-cjq9-62q9-8jv4) y cache poisoning SSG/ISR self-hosted (GHSA-4jqv-mc3x-m676, GHSA-mcj8-r9mp-w47p). Impacto ALTO, esfuerzo BAJO, riesgo BAJO. Compartido: `next` y `eslint-config-next` a 16.3.8 y `sharp` transitivo a 0.35.5 dentro del rango de `next` (GHSA-wq5f-xc86-pv6w). El lockfile solo cambia esos paquetes, sus binarios de plataforma y un parche transitivo de `fastq`. `next build` con Node 20 verde.
- `I-M-3608e4e81ca6` — las 5 páginas del panel del refugio piden `GET /shelters/?owner=me` y toman el primero, pero el backend ignoraba `owner`: cada administrador veía y editaba otro refugio. Impacto ALTO, esfuerzo BAJO, riesgo BAJO. `owner=me` devuelve solo los refugios que el usuario gestiona (dueño o equipo), no archivados y en cualquier estado de verificación; anónimo → 401; sin el parámetro, el listado público no cambia.
- `I-P-c653d85ebbe9` — el listado de refugios hacía 3–5 consultas por refugio (6→101 de 1 a 20 refugios; presupuesto del host real: 6). Impacto ALTO, esfuerzo BAJO, riesgo BAJO. `select_related` compartido en la lista pública, la de gestión web y la rama `owner=me`: consultas constantes (1, 2 y 1) con salida idéntica.
- `I-R-e14d2f4b66ad` (r4b) — en 412×915 el menú móvil autenticado crecía más que la pantalla dentro del header sticky: «Salir» (único control para cerrar sesión en el teléfono) y hasta 10 opciones quedaban inalcanzables. Impacto ALTO, esfuerzo BAJO, riesgo BAJO. El panel tiene alto máximo y scroll propio; nada cambia desde 768 px.

## Validación y aceptación

Cada rama se verificó por separado: el diff contiene solo los archivos aprobados y solo la mejora aprobada; las pruebas nuevas fallan sin el arreglo y pasan con él; gate de calidad y sincronía de flujos en verde. La QA combinada se ejecuta sobre un commit de integración limpio con las tres ramas: backend, unitarios, E2E en navegador a 412 px y escritorio contra una app que sirve ese contenido, gate y flujos. Máximo 20 casos por lote y tres comandos por ciclo; no se ejecutó la suite completa local.

Este documento registra alcance, decisiones y aceptación; no certifica un SHA. La evidencia de ejecución y CI se publica en los PR de la ronda, y los artefactos tipados y el ledger de la ronda se archivan fuera de los worktrees antes de retirarlos.

## Pendientes por cupo (en el orden del motor)

No son descartes por bajo retorno: todos tienen evidencia verificada y beneficio material o de bajo costo.

1. `I-M-dba8662e66f9` — «Eliminar» desde la ficha del admin borra con CASCADE lo que la acción masiva archiva (15 admins con `delete_queryset` y sin `delete_model`), contra el contrato de `models/mixins.py`. Decisión de producto: borrar desde la ficha pasa a archivar.
2. `I-S-2687a68e118c` — el listado público de refugios expone el email de la cuenta del dueño; el frontend solo lo usa en vistas de administración.
3. `I-S-2be8e9550579` — cambiar o restablecer la contraseña no revoca tokens (refresh de 7 días; sin `CHECK_REVOKE_TOKEN` ni blacklist). Decisión de producto: cierre de sesión único en el deploy. Ojo: `http.ts` descarta el refresh rotado; habilitar la blacklist sin corregirlo dejaría fuera a todos los usuarios.
4. `I-M-8d85ad31d0aa` — migración a `SingleImageField` incompleta: la subida de portada del blog responde 500 siempre y los serializers de actualizaciones leen `.url` de una `Library` (500 en páginas públicas si una actualización tiene imagen).
5. `I-O-082a62e80b13` — sin `EMAIL_TIMEOUT`, un SMTP colgado detiene la API (500 a los 30 s, health 34 s con dos envíos) y el único worker de Huey.
6. `I-O-e2e1a77b3178` — las notificaciones se encolan antes del commit: dentro del admin se perdió el 55 % de los correos (44/80) y el admin es el único camino que marca donaciones pagadas.
7. `I-P-8270ddbe6348` — N+1 en el listado de actualizaciones (2→21).
8. `I-R-fdc12518ad0c` — a 835 px sin sesión la fila de tableta desborda 16 px y recorta «Registrarse». Decisión de producto: mover «Campañas» al menú «Más» en tableta, o header de tableta en dos filas.
9. `I-S-c60a11a36315` — el dueño puede poner su apadrinamiento en cualquier estado (incluido `active`) sin pago; dispara `sponsorship_paid`.
10. `I-S-67a175cd9308` — el log de fallo de Google OAuth incluye el `id_token` en la URL de la excepción.
11. `I-S-fef867c1fda0` — el registro no aplica los validadores de contraseña que usan recuperación y cambio.
12. `I-M-addad843f628` — «Duplicar» artículo pierde autor, keywords y créditos.
13. `I-O-bc8918c4d18b` — el aviso de voluntariado va a `team@proyectapps.co` (NXDOMAIN).
14. `I-O-cab1b7d335f3` — `SafeTokenRefreshView` convierte cualquier excepción en 401 sin log.
15. QA (fuera del ledger): E2E de mensajes de campaña con aserción no acotada (falla ~15 % por intento en CI); E2E de detalle y CTA de campaña muertos en CI; E2E de comparar favoritos muertos, que ocultan defectos visibles del modal (clave cruda `animals.breed`, etiqueta «Shelter», enums sin traducir).

## Descartados por bajo retorno

- Seguridad: `sqlparse` (solo DEBUG/silk, sin entrada de atacante); `swiper` crítico (exige major 11→14: paso de modernización aparte); transitivos de npm de toolchain; blacklist completa de JWT (más de lo necesario).
- Rendimiento: intenciones públicas e invitaciones (ninguna pantalla las consume); miniaturas de galería (sin galerías medibles; esfuerzo M); fan-out a donantes (raro; M con riesgo medio); `pending_shelters`, aliados, FAQ y métricas (acotados); catálogo next-intl completo por documento (M); framer-motion global (sin medición, como en r3); polling de no leídas, payloads del blog e índices (dentro del presupuesto).
- Mantenibilidad: paginación malformada (sin camino desde la UI; unificarla cambia contratos); importación JSON del blog (solo staff); listas de autores, mapas de estados y armado del usuario repetidos (sin divergencia); rastreo `pre_save` repetido (cosmético); acoplamientos entre vistas y archivos grandes (sin efecto demostrado); correos siempre en español (producto).
- Observabilidad: reintentos de correo (prohibidos); logs solo en journald, health superficial y telemetría de cliente (sin consumidor ni alertas; ProjectApp como integración pendiente); reCAPTCHA silencioso (inactivo en lo desplegado); Redis sin `socket_timeout`; carreras sin UI.
- Responsividad: objetivos táctiles de la fila de tableta, cierre del menú móvil con Escape, ajustes cosméticos a 1195/2560 px, footer compacto y truncado del email (menores); `Sidebar.tsx` sin uso.
- QA: créditos falsos ya cubiertos por otras capas (`adoption.spec.ts:64`, `adopter.spec.ts:511`, `shelter.spec.ts:219`); carruseles de home (como en r3); flaky del blog mitigado por orden; lint de backend en CI (estilo).

## Evidencia pendiente

- Producción (srv571894): que `DJANGO_GOOGLE_CLIENT_ID` esté definido (si falta, el backend no valida la audiencia del token de Google); configuración SMTP real; `DJANGO_ENV=production`; dataset real (refugios, galerías, donantes por campaña) y uso real del admin.
- Pruebas en dispositivos reales (Safari iOS, Chrome Android) del menú móvil; navegadores sin `dvh` conservan el comportamiento anterior.
- Bundle de producción por ruta y señales del host (silk, slow log, reporte semanal).

## Registros

- Pruebas nuevas: `@flow:navigation-header` con `@outcome:display` además de `success`; el flujo declara solo `success` (reconciliar en la próxima ronda junto con su descripción, que no menciona la variante de tableta). Etiqueta informativa `@viewport:compact` según el estándar responsive §5.3.
- El ledger de la ronda vive fuera del repo (`IMPROVEMENT_LEDGER_DIR`); el ledger central del toolkit sigue sin versionar junto a cambios ajenos y no se modificó.

## Entrega

Un PR por rama `improve/09102026-r4-*` (compartido, rendimiento, responsividad) contra `master`, con tren de integración de `merge-queue` y cierre con `all-in-base --check-only`. Ningún trabajo de rondas anteriores se adopta ni se retira. El checkout desplegado permanece intacto.
