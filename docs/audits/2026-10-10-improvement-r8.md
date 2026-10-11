# Ronda de mejora r8 — Tuhuella

## Decisión y alcance

Base de diagnóstico: master `5f429379879c90078965624c221b5ec724086a9d`. Seis agentes nuevos, sin historial, revisaron alcances concretos y distinguieron observaciones actuales de evidencia histórica. El censo previo de merge-queue no encontró PRs abiertos; los cambios de r5–r7 ya estaban integrados. El clon de deploy se conserva intacto.

El objetivo es decidir qué compensa corregir. Se seleccionaron tres causas por la política canónica de beneficio y prioridad; la validación obligatoria no agrega causas al cupo. Los demás candidatos elegibles siguen pendientes, sin declararlos de bajo valor o declarar suficiencia global.

| Frente | Estado del alcance revisado | Selección |
|---|---|---|
| Seguridad | VALE LA PENA | I-S-6888824d9319: API de video omite allowlist del modelo |
| Mantenibilidad | VALE LA PENA | I-M-8d85ad31d0aa: Library/Attachment; I-M-addad843f628: metadatos de duplicación |
| Observabilidad | VALE LA PENA | Pendiente por cupo: reCAPTCHA sin diagnóstico saneado |
| Rendimiento | VALE LA PENA | Pendientes por cupo: miniaturas y FAQ |
| Responsividad | VALE LA PENA | Pendiente por cupo: cabecera ES en tableta vertical |
| QA | VALE LA PENA | Validación obligatoria; deuda discrecional pendiente |

## Cambios aprobados y contratos

- I-S-6888824d9319: MEDIO/BAJO/BAJO. Restaurar la validación existente mp4/webm/mov/ogg; conservar omisión, null y permisos. El bypass fue observado en el serializer exacto en memoria. No se acreditó ejecución XSS ni se agrega validación MIME/tamaño.
- I-M-8d85ad31d0aa: ALTO/MEDIO/MEDIO. Representar URLs desde Library.primary_attachment y reparar upload multipart de portada. Mantener endpoints, FK de entrada y null sin imagen. Crear Library/Attachment nuevos, filas atómicas y compensar exclusivamente el archivo nuevo ante un fallo; no borrar bibliotecas anteriores compartidas. Evidencia actual: tres métodos exactos reproducen AttributeError en memoria; los 500 HTTP reales proceden de r7 sobre código idéntico.
- I-M-addad843f628: MEDIO/BAJO/BAJO. Copiar author, crédito/URL y keywords ES/EN. Conservar copia borrador, slug independiente, fecha nula, destacado desactivado y JSON independiente. Omisiones reconfirmadas mediante la función exacta y constructor en memoria.

## Aislamiento y propiedad

Clon de coordinación privado con el origin registrado que corresponde al mismo repositorio GitHub. Worktrees planos propios; create/status y QA preflight reales pasaron, sin alterar guards, registry ni origin del deploy. Cada archivo tiene un solo autor. Seguridad posee su serializer y dos archivos de tests. Mantenibilidad posee tres serializers de updates, blog.py, tres archivos de tests y el spec editorial real. Un QA Engineer posee únicamente la fixture editorial; el conductor posee mapa/registro y este reporte.

La fixture editorial es una solicitud necesaria de aceptación, de impacto ALTO y riesgo BAJO: CI no tenía staff/datos editoriales reales. El spec la prepara exclusivamente en CI efímero con SQLite, MemoryHuey y email local; el target privado recibe datos previamente sembrados. No cambia contratos de aplicación ni agrega una mejora discrecional. Se descartó un hook global de workflow: añadiría una dependencia entre PRs y sería redundante con ese bootstrap acotado.

Pruebas locales en SQLite y medios privados, sin cargar .env ni conectar SMTP/Redis reales. Máximo veinte casos por comando y tres comandos por ciclo; no suite local completa. E2E debe servir el SHA limpio probado con Node20 y APIs reales. Un servidor público detectado por preflight no constituye evidencia de ese SHA.

## Validación

Este documento fija la decisión y los contratos previos al cierre. Seguridad entregó 37/37 casos sobre `ead635077cc38b5251621003ae81a5d65c8012cb`; mantenibilidad entregó 39/39 sobre `d11cd12fc1b3f0c6c321a1bc62d58a9119f16677`, ambos limpios y con artefactos originales. El Architect definió B1–B8 y E1–E3: validación/permisos de video, Library/Attachment reales, endpoints con imágenes, upload/reemplazo/fallo de almacenamiento, metadatos e independencia de duplicación, y editor/feed públicos con imágenes realmente cargadas.

El primer combinado limpio `992aab6c433168bdd7fbc0424f6a1a55f380d697` fue REJECTED: 76 casos backend pasaron, dos de tres E2E pasaron y E1 falló en la aserción de título inglés. La repetición aislada y CI del tren reprodujeron el mismo fallo. El frontend público ya solicita `fetchPost(slug, 'es')` desde `/en/` en la base `5f4293`; es una causa independiente pendiente. El guion corregido exige ruta EN, GET real 200 del artículo exacto y publicado, URL de la portada subida y carga de la imagen de su figura. Conserva subida/editor/recarga y comprobación ES, pero no acredita traducción ni el flujo blog-detail. El defecto queda anotado como known-gap, sin skips, mocks ni modificación del producto. El gate estricto también rechazó nueve docstrings ausentes en tests de seguridad; su autor las añadió sin cambiar el AST funcional y repitió los 37 casos. Se conserva toda la evidencia del rechazo antes de repetir QA sobre el nuevo combinado.

La revisión independiente corrigió dos créditos E2E indebidos, exigió recarga de la imagen de campaña, retiró un caso duplicado y comprobó compensación del seed si falla después de escribir el archivo. La versión 5.11.2 del mapa documenta cuatro contratos afectados sin ampliar outcomes ni cambiar exenciones. La aceptación definitiva exige ejecución backend y E2E viva del Verifier sobre un SHA combinado limpio, gate, CI verde del tren y comprobación de contenido en master; sus resultados y manifiesto se archivan en el cierre privado de esta ronda. Los pases del autor no reemplazan esa aceptación; no se certifica QA global ni se cuentan mocks como persistencia comprobada.

## Pendientes por cupo

- I-O-a711cd0f01ee: fallos reCAPTCHA indistinguibles de rechazo válido. MEDIO/BAJO/BAJO.
- I-P-4c272fe82bb6: miniaturas de favoritos/solicitudes/apadrinamientos; evidencia histórica de consultas creciente, código idéntico. ALTO/MEDIO/BAJO.
- I-P-a1c7fcaaff10: FAQ con consulta adicional por tema. MEDIO/BAJO/BAJO.
- I-R-fdc12518ad0c: desborde de cabecera ES a835×1194; registro sigue operable. MEDIO/BAJO/BAJO, reconfirmar navegador antes de aplicar.
- I-M-e9774f378b7b: favoritos omite acciones al buscar controles inexistentes. MEDIO/BAJO/BAJO.
- I-M-b73932da8755: campañas vacías omiten interacción/aserciones. MEDIO/BAJO/BAJO.
- Selector de mensajería: coincidencia transitoria div/textarea, fallo histórico que pasó al reintentar; no reproducido en r8. MEDIO/BAJO/BAJO.
- I-M-e36fa294537b: la ruta inglesa del artículo solicita contenido español aunque hay título/contenido inglés; reproducido en navegador y CI, con hardcode idéntico a la base. MEDIO/BAJO/BAJO. Causa independiente, sin cuarto cambio en esta ronda.

Corrección documental: el resumen sellado de r7 intercambió los dos IDs de rendimiento. La asociación correcta del ledger es miniaturas I-P-4c272fe82bb6 y FAQ I-P-a1c7fcaaff10. El archivo sellado anterior no se modificó.

## Descartes por retorno

- Separar capas/archivos por tamaño: sin error o beneficio demostrable.
- Clonar portadas y limpiar medios globalmente: propiedad/referencias no resueltas; complejidad y riesgo exceden el arreglo.
- APM, logs generales y retries SMTP nuevos: sin consumidor/camino fallido observado; riesgo de duplicación.
- Timeout Axios global, cachés, índices y bundles: falta medición/reproducción que justifique el cambio.
- Ampliar objetivos táctiles adicionales: MEDIO/MEDIO/MEDIO, fuera del umbral.
- Subir porcentajes, tests gemelos, reformateo y barrido global Ruff: no compensan sin bug concreto.

## Límites y riesgos abiertos

La ruta inglesa del artículo sigue mostrando contenido español; las pruebas de imagen no certifican su traducción.

Las bibliotecas/medios anteriores se retienen para proteger referencias compartidas y rollback; no hay limpieza automática de huérfanos. Validar extensiones no equivale a validar MIME ni demostrar/excluir XSS. pip-audit sigue ausente. El npm audit actual detectó 12 paquetes afectados (3 moderados, 8 altos y 1 crítico), correspondientes a nueve avisos distintos; no son doce explotaciones demostradas. Manifiestos y lock no cambiaron. Seguridad reconfirmó opciones literales de Swiper y ausencia de ingesta de source maps externos; sigue pendiente la aplicabilidad de esos avisos, sin declarar dependencias limpias. Rendimiento se contrastó con perfil declarado, no units/latencia desplegadas; listados sin paginación no quedan certificados en memoria. Sin deploy, migración de producción ni push del toolkit.

La evidencia final y los diagnósticos se conservarán en el archivo privado r8-20261010; el ledger canónico privado registra decisiones/punteros y la QA exacta, sin métricas ni porcentajes de avance.
