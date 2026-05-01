# Spec - Haiku API Atlas

## 0. Idea

Haiku API Atlas es una app nativa para explorar la API de Haiku como una estructura navegable, no solo como documentación textual.

La unidad principal no es una pagina, sino un nodo:

- Kit
- Class
- Struct
- Enum
- Method
- Constant
- Header
- Subsystem
- Example

La app combina dos funciones:

- 70% explorador estructural
- 30% lector de documentacion

Objetivo: ayudar a alguien a entender la API, la arquitectura y la ubicacion del codigo fuente de Haiku sin tener que saltar manualmente entre headers, docs online, repo y busquedas sueltas.

## 1. Principio de diseno

### 1.1 Frase guia

> Un simbolo es un lugar.  
> La documentacion es lo que ves cuando llegas ahi.

### 1.2 No es

No es solo:

- un navegador HTML
- un clon de Zeal/Dash
- un visor estatico de documentacion
- un parser C++ perfecto
- un IDE completo

### 1.3 Si es

Es:

- un atlas de la API
- un browser jerarquico de kits/clases/miembros
- un lector de nodos
- una herramienta de orientacion para contributors
- un mapa entre docs, headers e implementacion

## 2. Usuarios objetivo

### 2.1 Nuevo contributor

Quiere responder:

- Que clase uso
- Donde esta definida
- De que hereda
- Que metodos tiene
- Donde esta implementada
- Que ejemplos existen

### 2.2 Developer de apps Haiku

Quiere navegar rapidamente la API publica:

- Application Kit
- Interface Kit
- Storage Kit
- Media Kit
- Support Kit
- Locale Kit
- Network Kit

### 2.3 Contributor avanzado

Quiere saltar entre:

- header publico
- source implementation
- docs existentes
- relaciones entre clases
- cambios recientes

## 3. UI principal

### 3.1 Layout base

Dos paneles:

```text
+------------------------------+---------------------------------------------+
| Browser                      | Node Reader                                 |
|                              |                                             |
| Kits                         | BView                                       |
|  > Application Kit           |                                             |
|  > Interface Kit             | Kit: Interface Kit                          |
|      BView                   | Kind: Class                                 |
|      BWindow                 | Inherits: BHandler                          |
|      BBitmap                 | Header: headers/os/interface/View.h         |
|  > Storage Kit               | Source: src/kits/interface/View.cpp         |
|  > Media Kit                 |                                             |
|                              | Methods                                     |
| Search: [ BView________ ]    |   Draw(BRect update)                        |
|                              |   MouseDown(BPoint where)                   |
|                              |   AttachedToWindow()                        |
|                              |                                             |
|                              | Related                                     |
|                              |   BWindow, BRegion, BBitmap, app_server     |
+------------------------------+---------------------------------------------+
```

### 3.2 Browser panel

El browser puede cambiar de vista:

- By Kit
- By Class
- By Inheritance
- By Header Path
- By Subsystem
- Search Results
- Recently Viewed
- Bookmarks

Vista inicial recomendada:

- Application Kit
- Interface Kit
- Storage Kit
- Support Kit
- Media Kit
- Translation Kit
- Locale Kit
- Network Kit
- Game Kit
- Kernel / Drivers

### 3.3 Node Reader

El panel derecho cambia segun tipo de nodo.

#### Class node

Muestra:

- Name
- Kind
- Kit
- Header path
- Source path
- Inheritance
- Public methods
- Protected methods
- Constants/enums related
- Related classes
- Docs/comment block
- Examples

#### Method node

Muestra:

- Signature
- Owning class
- Declared in
- Implemented in
- Return type
- Parameters
- Overrides / overridden by
- Docs/comment block
- Examples

#### Kit node

Muestra:

- Kit name
- Summary
- Main classes
- Common patterns
- Headers
- Subsystem relation

#### Header node

Muestra:

- Path
- Kit
- Symbols declared
- Includes
- Last indexed
- Open file action

## 4. Data model

### 4.1 Nodos

Todo elemento navegable es un nodo.

```text
SymbolNode
  id
  kind
  name
  qualified_name
  display_name
  file_id
  line_start
  line_end
  parent_id
  kit_id
```

Tipos iniciales:

- kit
- header
- class
- struct
- enum
- method
- constructor
- destructor
- field
- constant
- typedef
- namespace
- subsystem

### 4.2 Relaciones

Las relaciones son tan importantes como los nodos.

```text
Relation
  id
  from_symbol_id
  relation_type
  to_symbol_id
```

Tipos:

- declares
- contains
- inherits
- implements
- returns
- takes_parameter
- uses
- related_to
- defined_in
- implemented_in
- belongs_to_kit

### 4.3 Archivos

```text
FileRecord
  id
  path
  role
  mtime
  size
  sha256_optional
  last_indexed_at
```

Roles:

- public_header
- private_header
- source
- example
- doc

## 5. Indexer

### 5.1 Objetivo

El indexer convierte headers/source/docs en un indice navegable.

```text
headers publicos
  -> indexer
  -> api-index.sqlite
  -> browser + node reader
```

### 5.2 No reparsear todo siempre

La API no cambia constantemente, asi que el indice puede ser persistente.

En startup:

- scan files
- compare mtime + size
- reindex changed files
- reuse cache for unchanged files

### 5.3 Estrategia de deteccion de cambios

Para cada archivo:

- path
- mtime
- size
- sha256 opcional

Reglas:

- si archivo nuevo: indexar
- si mtime/size cambio: reindexar
- si archivo desaparece: remover simbolos
- si nada cambio: usar cache

sha256 queda como opcion para modo estricto.

### 5.4 Indice descartable

Regla fundamental:

> El indice es cache, no fuente de verdad.

Si se rompe:

- delete api-index.sqlite
- rebuild

## 6. Parser

### 6.1 Fase 1 - parser heuristico

Para v0, evitar libclang.

El parser inicial detecta:

- class BView : public BHandler
- struct rgb_color
- enum orientation
- public/protected/private sections
- method signatures simples
- constructors/destructors
- typedefs
- constants
- comments cercanos

Ventajas:

- simple
- rapido
- sin dependencias pesadas
- suficiente para navegar

Desventajas aceptadas:

- no entiende todo C++
- puede fallar con macros
- puede perder casos raros

### 6.2 Fase 2 - parser mejorado

Mas adelante:

- ClangProvider
- Doxygen/XML provider
- prebuilt docs provider

La app debe disenarse con interfaz de proveedor:

```text
ISymbolProvider
  HeaderHeuristicProvider
  ClangProvider
  CachedJsonProvider
  DoxygenProvider
```

Asi el parser inicial se puede reemplazar sin destruir la app.

## 7. Storage

### 7.1 SQLite recomendado

Base:

- api-index.sqlite

Tablas minimas:

```sql
files(
  id INTEGER PRIMARY KEY,
  path TEXT UNIQUE,
  role TEXT,
  mtime INTEGER,
  size INTEGER,
  sha256 TEXT,
  last_indexed_at INTEGER
);

symbols(
  id INTEGER PRIMARY KEY,
  kind TEXT,
  name TEXT,
  qualified_name TEXT,
  display_name TEXT,
  file_id INTEGER,
  line_start INTEGER,
  line_end INTEGER,
  parent_id INTEGER,
  kit_id INTEGER
);

relations(
  id INTEGER PRIMARY KEY,
  from_symbol_id INTEGER,
  relation_type TEXT,
  to_symbol_id INTEGER
);

docs(
  id INTEGER PRIMARY KEY,
  symbol_id INTEGER,
  source TEXT,
  body TEXT
);
```

### 7.2 Indices

```sql
CREATE INDEX idx_symbols_name ON symbols(name);
CREATE INDEX idx_symbols_qualified ON symbols(qualified_name);
CREATE INDEX idx_symbols_kind ON symbols(kind);
CREATE INDEX idx_rel_from ON relations(from_symbol_id);
CREATE INDEX idx_rel_to ON relations(to_symbol_id);
```

## 8. Project layout

Repo propio:

```text
haiku-api-atlas/
  README.md
  src/
    app/
      AtlasApp.cpp
      MainWindow.cpp
      BrowserPanel.cpp
      NodeReader.cpp

    index/
      HeaderScanner.cpp
      SymbolGraph.cpp
      IndexStore.cpp
      FileScanner.cpp

    model/
      SymbolNode.h
      Relation.h
      FileRecord.h

    providers/
      ISymbolProvider.h
      HeaderHeuristicProvider.cpp

    ui/
      KitTreeView.cpp
      ClassListView.cpp
      NodeView.cpp
      SearchBox.cpp

  data/
    schema.sql

  docs/
    design.md
    parser-notes.md
    roadmap.md

  tests/
    fixtures/
      simple_class.h
      inheritance.h
      enum_method.h
```

## 9. Modos de uso

### 9.1 Modo User

Para quien solo quiere usar docs:

- abrir app
- usar indice incluido o generado
- buscar clase
- leer nodo

### 9.2 Modo Contributor

Para quien tiene repo local de Haiku:

- seleccionar path del repo Haiku
- indexar headers
- abrir nodos
- saltar a header/source
- detectar cambios tras git pull

### 9.3 Modo SDK Installed

Para app instalada dentro de Haiku:

- usar /boot/system/develop/headers
- usar /boot/system/develop/documentation si existe

### 9.4 Modo Source Tree

Para contributor:

- usar ~/haiku/headers
- usar ~/haiku/src
- usar ~/haiku/docs

## 10. MVP v0

### Objetivo

Una app nativa Haiku que permita navegar clases publicas de la API.

### Incluye

- escaneo de headers publicos
- agrupacion por kit
- deteccion de clases/structs
- deteccion de herencia simple
- deteccion de metodos publicos
- busqueda por nombre
- panel derecho con detalles basicos
- cache SQLite persistente
- reindex incremental por mtime/size

### No incluye

- parser C++ perfecto
- grafico visual de herencia
- Doxygen completo
- busqueda semantica
- integracion con editor externo
- source implementation linking perfecto

### Success criteria

- abrir app
- seleccionar repo/SDK path
- indexar sin crash
- ver Application Kit / Interface Kit
- abrir BApplication, BWindow, BView, BMessage
- ver metodos principales
- buscar por nombre
- cerrar/reabrir instantaneo usando cache

## 11. v1

Mejoras:

- comentarios cercanos extraidos de headers
- source path guessing
- examples finder
- bookmarks
- recent nodes
- mejor search
- members heredados
- modo header path

Examples finder:

Buscar en:

- src/apps
- src/tests
- src/preferences
- src/demos

Relacion:

- example_uses_symbol

## 12. v2

Exploracion avanzada:

- grafo visual de herencia
- related classes
- used by
- method override tree
- diff entre versiones de API
- modo contributor: donde tocar docs
- abrir en editor externo
- exportar indice JSON

## 13. UI behavior

### 13.1 Search

Search global:

- BView
- view
- Draw
- BMessage

Resultados agrupados:

- Classes
- Methods
- Headers
- Enums

### 13.2 Breadcrumb

El Node Reader muestra:

- Interface Kit > BView > Draw(BRect)

### 13.3 Navigation history

- Back
- Forward
- Recently viewed

### 13.4 Bookmarks

Bookmarks locales:

- BApplication
- BWindow
- BView
- BMessage
- BBitmap
- BPath
- BEntry

## 14. Technical risks

### 14.1 C++ parsing

Riesgo:

- headers complejos
- macros
- #ifdef
- signatures multiline
- templates

Mitigacion:

- heuristica suficiente para MVP
- fallar suave
- mostrar raw declaration si no entiende
- disenar provider reemplazable

### 14.2 Source linking

Riesgo:

- declaracion en header no mapea 1:1 con implementation
- overloads
- inline methods
- generated code

Mitigacion:

- v0 solo header
- v1 source guess
- v2 index source

### 14.3 Scope creep

Riesgo:

- terminar haciendo IDE

Mitigacion:

- no editar codigo
- no compilar
- no debugger
- no LSP initially

## 15. Non-goals explicitos

- No es un IDE.
- No es un reemplazo de la documentacion oficial.
- No intenta parsear todo C++ perfectamente en v0.
- No requiere conexion a internet.
- No depende de AI.
- No modifica el repo de Haiku.

## 16. Filosofia de implementacion

### 16.1 Simple primero

Primero:

- headers -> simbolos -> arbol -> nodo

Despues:

- docs
- examples
- source links
- graphs

### 16.2 Native-first

Idealmente app nativa Haiku:

- BApplication
- BWindow
- BView / BColumnListView
- BStringView
- BTextView

Pero el indexer debe poder ser CLI tambien.

### 16.3 Separar indexer y UI

```text
atlas-indexer
  -> genera api-index.sqlite

atlas
  -> consume api-index.sqlite
```

Eso permite debuggear el parser sin abrir UI.

## 17. CLI companion

### atlas-indexer

Uso:

```bash
atlas-indexer --sdk /boot/system/develop/headers --out api-index.sqlite
```

O:

```bash
atlas-indexer --haiku-source /boot/home/haiku --out api-index.sqlite
```

Opciones:

- --full
- --incremental
- --strict-hash
- --dump-symbols
- --dump-kits
- --verbose

### atlas

Uso:

```bash
atlas
atlas --index api-index.sqlite
atlas --source ~/haiku
```

## 18. Primeros nodos canonicos para probar

- BApplication
- BLooper
- BHandler
- BMessage
- BMessenger
- BWindow
- BView
- BBitmap
- BRect
- BPoint
- BRegion
- BFile
- BEntry
- BPath
- BDirectory
- BNode
- BMediaNode
- BBuffer
- BParameterWeb

Si esos funcionan, la app ya empieza a ser util.

## 19. UX ideal para un nodo de clase

Ejemplo BView:

```text
BView
Class - Interface Kit

Declared in:
  headers/os/interface/View.h

Implemented in:
  src/kits/interface/View.cpp

Inherits:
  BHandler

Inherited by:
  BButton
  BControl
  BTextView
  ...

Common lifecycle:
  AttachedToWindow()
  Draw(BRect update)
  MouseDown(BPoint where)
  FrameResized(float width, float height)

Public methods:
  Draw(BRect update)
  Invalidate()
  SetViewColor(rgb_color)
  SetHighColor(rgb_color)
  FillRect(BRect rect)
  StrokeLine(BPoint start, BPoint end)

Related:
  BWindow
  BBitmap
  BRegion
  app_server
```

## 20. Open questions

- El indice debe incluir private headers
- Debe apuntar al source tree completo o solo al SDK instalado
- Conviene app nativa desde el dia uno o primero CLI
- SQLite o JSON para v0
- Se integran docs existentes o solo estructura
- Nombre final: Haiku Atlas, API Atlas, BeMap, ClassTracker

## 21. Roadmap sugerido

### Semana 1 - Indexer minimo

- scan headers
- detect class/struct
- detect kit by path
- write SQLite/JSON
- CLI dump

### Semana 2 - UI minima

- BApplication
- MainWindow
- Browser tree
- Node reader text
- load index
- click class -> show details

### Semana 3 - Methods + search

- parse public methods
- search box
- method list
- header line references

### Semana 4 - Polish

- cache invalidation
- recent nodes
- bookmarks
- basic docs extraction
- package hpkg experimental

## 22. Nombre tentativo

Favoritos:

- Haiku Atlas
- API Atlas
- BeMap
- ClassTracker
- KitExplorer

Mi voto: Haiku Atlas.

Porque no promete documentacion perfecta. Promete algo mas interesante:

> cartografia del sistema.
