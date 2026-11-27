# Captura manual del filtro de fechas de Licitaciones.info

Objetivo: comprobar si el feed de Contratos admite un filtro remoto
por fecha de publicación que permita consultar subventanas de forma
verificable. Lo hace el titular a mano, desde la interfaz; Eureka no
consulta el feed.

## Pasos

1. Abre Contratos en el Edge dedicado, con sólo el perfil
   `infoexpress` seleccionado. Si quieres comparar con la búsqueda
   ciega, aplica también las ubicaciones de Boyacá y Huila desde la
   UI.
2. Abre DevTools con F12, ve a la pestaña **Network** y activa
   **Preserve log**. Escribe `get-info` en el filtro y pulsa **Clear**
   para vaciar la lista.
3. En la UI aplica **sólo** un filtro de fecha de publicación con un
   rango corto y cerrado, por ejemplo del 20 al 21 de noviembre. No
   cambies otros filtros.
4. Abre la solicitud `POST /cliente/contratos/get-info/MP?perfiles=…`
   que aparezca justo después de aplicar el filtro.
   - En **Payload**, pulsa **view source** y copia el JSON completo.
   - En **Response** o **Preview**, anota `count`, el número de filas
     y el `FechaPublicacion` de la primera y de la última fila.
5. Repite el paso 3 con un segundo rango contiguo, por ejemplo del 18
   al 19 de noviembre, y anota lo mismo.
6. Opcional: aplica un rango antiguo, de unos 25 días atrás, y pasa a
   la página 2 para ver si la paginación conserva el filtro.

## Qué enviar

- El JSON del payload de cada rango.
- Para cada rango: `count`, número de filas y fechas de la primera y
  de la última fila.

## Qué no enviar

- Encabezados, cookies, tokens ni la pestaña **Headers**.
- El valor de `perfiles` en la URL: sustitúyelo por `<ID>`.
- Respuestas completas: bastan los datos del paso 4.

## Cómo se evaluará

El filtro se considera verificable si se cumplen las tres
condiciones:

- El payload contiene un campo de fecha explícito, por ejemplo dentro
  de `query`.
- Todas las filas devueltas caen dentro del rango pedido.
- Dos rangos contiguos no se solapan, salvo en el límite del día.

Si no se cumplen, se mantiene la alternativa de descubrimiento
paginado con presupuesto propio.
