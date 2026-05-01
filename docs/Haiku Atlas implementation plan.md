# Haiku API Atlas - Plan de implementacion

Este documento separa el plan operativo del Spec/Seed.

## 1. Decisiones base

- [x] Confirmar stack v0: Python 3.10+, SQLite, CLI-first, UI desacoplada.
- [ ] Confirmar alcance v0: parser heuristico, index incremental, search por nombre.
- [ ] Definir politica de entrada: SDK instalado, source tree completo o ambos.
- [x] Cerrar nombre del proyecto y nombres de binarios (atlas-indexer, atlas-query).

## 2. Semana 1 - Bootstrap del proyecto

- [x] Crear estructura de carpetas (src/, data/, tests/, docs/).
- [x] Crear pyproject.toml con tooling basico (formatter, linter, test).
- [x] Definir comandos CLI base (index, dump-symbols, dump-kits, search).
- [x] Agregar data/schema.sql con tablas files, symbols, relations, docs.
- [x] Implementar inicializacion de DB y migracion de esquema en arranque.
- [x] Documentar setup rapido en README.

## 3. Semana 2 - Indexer minimo funcional

- [ ] Implementar escaneo de archivos header (.h, .hpp) por path configurado.
- [ ] Persistir metadata de archivos (path, mtime, size, last_indexed_at).
- [ ] Implementar deteccion incremental (nuevo/cambio/borrado/sin cambios).
- [ ] Implementar parser heuristico para class, struct, enum.
- [ ] Guardar simbolos y relaciones minimas (contains, inherits, defined_in).
- [ ] Exponer atlas-indexer --full y atlas-indexer --incremental.
- [ ] Validar con fixtures de prueba y dump legible por consola.

## 4. Semana 3 - Metodos publicos y busqueda

- [ ] Detectar secciones public/protected/private por clase.
- [ ] Extraer firmas simples de metodos publicos y constructores/destructores.
- [ ] Guardar metodos en symbols y relaciones belongs_to_kit/contains.
- [ ] Implementar busqueda por nombre (clase/metodo/header) con ranking simple.
- [ ] Agregar comando atlas-query search "BView".
- [ ] Agregar comando atlas-query show "BView" para detalle de nodo.

## 5. Semana 4 - Calidad y DX

- [ ] Agregar logging configurable (--verbose) para indexer.
- [ ] Agregar manejo de errores y fallos suaves del parser (raw declaration).
- [ ] Cubrir casos borde: macros, multiline signatures, headers incompletos.
- [ ] Agregar pruebas de regresion con fixtures reales de Haiku API.
- [ ] Medir performance base (tiempo full index y incremental).
- [ ] Definir umbrales de aceptacion para performance de v0.

## 6. Semana 5 - UI minima cross-platform

- [ ] Elegir frontend v0 (TUI o web local) consumidor de SQLite.
- [ ] Mostrar browser por kit y panel de detalle de nodo.
- [ ] Implementar search box conectado a atlas-query/consultas SQL.
- [ ] Implementar historial basico (back/forward/recent).
- [ ] Validar en Linux y Windows con el mismo indice.

## 7. Semana 6 - Release v0

- [ ] Congelar formato de indice SQLite v0.
- [ ] Escribir guia de uso para modo SDK y modo source tree.
- [ ] Generar binarios/paquetes para Linux y Windows.
- [ ] Ejecutar smoke test end-to-end en entorno limpio.
- [ ] Publicar changelog y roadmap de v1.

## 8. Definicion de done (v0)

- [ ] Indexa headers sin crash en un arbol real de Haiku.
- [ ] Encuentra nodos canonicos (BApplication, BWindow, BView, BMessage).
- [ ] Muestra metodos publicos principales por clase.
- [ ] Reindex incremental reutiliza cache y reduce tiempo de ejecucion.
- [ ] Funciona en Linux y Windows con el mismo flujo CLI.

## 9. Backlog post-v0

- [ ] Extraccion de comentarios cercanos para docs por nodo.
- [ ] Source path guessing e index de implementaciones.
- [ ] Examples finder (example_uses_symbol).
- [ ] Bookmarks persistentes y recently viewed.
- [ ] Provider alternativo con Clang o Doxygen.
