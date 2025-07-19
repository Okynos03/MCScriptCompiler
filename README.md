# 🎮 MCScript Compiler

> **Construye tu código, bloque a bloque**
> *Un lenguaje de programación inspirado en Minecraft para aprender programación mientras te diviertes.*

---

## Tabla de contenido

1. [¿Qué es MCScript?](#qué-es-mcscript)
2. [Características clave](#características-clave)
3. [Capturas y demo](#capturas-y-demo)
4. [Instalación rápida](#instalación-rápida)
5. [Uso básico](#uso-básico)
6. [Referencia rápida de sintaxis](#referencia-rápida-de-sintaxis)
7. [Arquitectura del compilador](#arquitectura-del-compilador)
8. [Licencia](#licencia)
9. [Contacto y agradecimientos](#contacto-y-agradecimientos)

---

## ¿Qué es MCScript?

MCScript es un **lenguaje de programación educativo** y un **compilador** completo (léxico → sintaxis → semántica → código intermedio → optimización → traducción a Python) que emplea la estética y terminología de **Minecraft** para introducir conceptos fundamentales de programación de forma amigable, permitiendo transicionar hacia otros lenguajes de una forma más sencilla.

El objetivo principal es que cualquier persona, especialmente estudiantes jóvenes y principiantes, puedan **aprender conceptos básicos de programación como variables, condicionales, ciclos y funciones** sin sentirse abrumados por la sintaxis de los lenguajes tradicionales.

---

## Características clave

* **Sintaxis temática**: `spawnear … morir`, `craftear`, `apilar`, `portal`, etc.
* **Tipado fuerte + tipo débil opcional** (`bloque`, `losa`, `libro`, `cofre`, `item`…).
* **Entorno web interactivo** (FastAPI + Jinja2 + Quill) con:

  * Workbench con coloreado y numeración de línea.
  * Consola con pestañas para cada fase: Tokens, AST, Código intermedio, Optimización, Ejecución.
  * Ejecución asíncrona vía WebSockets.
* **Compilación a Python** con optimizaciones (mirilla, propagación de constantes, dead‑code elimination).
* **100 % Open Source** ‑ ¡hackea, extiende y comparte!

---

## Capturas y demo

<!--
Inserta aquí GIF o imágenes.
Ejemplo:
![Demo en vivo](docs/demo.gif)
-->
1. Esto es lo primero que ve el usuario al acceder por primera vez a MCScript
<img width="1919" height="964" alt="image" src="https://github.com/user-attachments/assets/44e52740-c9d5-4f85-8011-2286d356444e" />

2. Puedes ocultar la consola para tener un mayor espacio para programar comodamente
<img width="1898" height="970" alt="image" src="https://github.com/user-attachments/assets/1d073090-1f6f-41cd-8d37-67aa0955d649" />

3. Podemos utilizar los ejemplo propocionados directamente desde la ayuda para dar los primeros pasos
<img width="1895" height="969" alt="image" src="https://github.com/user-attachments/assets/73d4a256-746c-48c4-ac04-11cae3ca7620" />

4. También tenemos un modo oscuro
<img width="1896" height="968" alt="image" src="https://github.com/user-attachments/assets/9564256d-431a-478f-8335-8f67bd79b901" />

---

## Instalación rápida

```bash
# 1 ‑ Clona el repositorio
git clone https://github.com/Okynos03/MCScriptCompiler.git

# 2 - Muevete a la carpeta donde clones el proyecto
cd MCScript

# 3 ‑ Crea un entorno virtual (opcional pero recomendado)
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate.bat  (desde cmd)

# 4 ‑ Instala dependencias
pip install -r requirements.txt

# 5 ‑ Arranca el servidor
uvicorn main:app

# 6 ‑ Abre http://localhost:8000 en tu navegador favorito 🎉
```

> **Requisitos mínimos**: Python 3.8+, 2 núcleos CPU, 1 GB RAM.

---

## Uso básico

1. Escribe tu código en el **Workbench**.
2. Pulsa **⚡ Compilar Bloques ⚡** para generar el IR.
3. Pulsa **🚀 Ejecutar 🚀** para ver la salida en la pestaña *Ejecución*.
4. Modifica → recompila → ejecuta tantas veces como quieras.

### “Hola Mundo”

```mcscript
spawnear {
    chat("Hola MCScript!!");
}
morir;
```

---

## Referencia rápida de sintaxis

| Concepto                    | MCScript                                                         | Ejemplo                                 |
| --------------------------- | ---------------------------------------------------------------- | --------------------------------------- |
| **Operaciones aritméticas** | `craftear`, `romper`, `apilar`, `repartir`, `sobrar`, `encantar` | `bloque r = craftear(a,b);`             |
| **Variables**               | `bloque`, `losa`, `hoja`, `libro`, `palanca`, `cofre`, `item`    | `cofre inventario = ["diamond", 64];`   |
| **Condicionales**           | `si … sino`                                                      | `si(a > 5){ … }`                        |
| **Bucles**                  | `para`, `mientras`                                               | `para(i=0;i<10;i=i+1;){…}`              |
| **Funciones**               | `portal` / `tp`                                                  | `portal suma(a,b){ tp craftear(a,b); }` |

> Consulta `docs/help.html` o pulsa **💡 Ayuda** dentro de la app para la documentación completa.

---

## Arquitectura del compilador

```
          +-------------+
          |   Fuentes   |
          +------+------+           WebSocket
                 |                    ↑
     [Análisis léxico]  →  [Análisis sintáctico]  →  [Análisis semántico]
                 ↓                     ↓
        Tokens (tab)          AST (tab)
                 ↓
       [Código intermedio]
                 ↓
         Optimización
                 ↓
         Traducción → Python
                 ↓
            Ejecución
```

*Más detalles en* [`4.6 Proyecto Final MCScript v5.pdf`](/MCScriptCompiler).

## Licencia

Este proyecto se distribuye bajo la **MIT License** — ver el archivo [`LICENSE`](LICENSE) para más información.

---

## Contacto y agradecimientos

| Rol             | Nombre                                                                  | Contacto                                        |
| --------------- | ----------------------------------------------------------------------- | ----------------------------------------------- |
| Autor           | Ulises Andrade González                                                 | [ulises.ag03@gmail.com](mailto:ulises.ag03@gmail.com) |
| Autor           | Emilio Sebastián Chávez Vega                                            | []                                                |
| Autor           | Luis Ángel Quijano Guerrero                                             |                                                  |
| Autor           | Jesús Adrian Pacheco Garcia                                             |                                                  |
| Autor           | Emiliano Rebolledo Navarrete                                            | [rebolledonavarreteemiliano@gmail.com](mailto:rebolledonavarreteemiliano@gmail.com) |

> MCScript nació como proyecto final de la asignatura **Lenguajes y Autómatas II** del Instituto Tecnológico de Celaya (Julio 2025).

---

*¡Disfruta construyendo tu código bloque a bloque!*
