# CONTEXTO DE INICIATIVA
## MVP – Plataforma Inteligente de Análisis de Compras Públicas

### 1. Propósito de este ejercicio

Se desea transformar un trabajo de grado previamente desarrollado en una solución
de software real, desplegable y utilizable.

El documento académico original se titula:

**“Plataforma de Visualización de Datos para Control Fiscal de Compras Públicas”**

El trabajo fue desarrollado como tesis de la Maestría en Gerencia de Transformación
Digital y Analítica de Negocios de la Universidad Externado de Colombia.

La tesis constituye el DOCUMENTO BASE de la iniciativa, pero NO debe interpretarse
como una especificación funcional o técnica definitiva.

El objetivo de esta nueva etapa es evolucionar el concepto académico hacia un
producto MVP real.

Para ello se utilizará el Método Ceiba comenzando por la elaboración de un Brief
de producto y posteriormente, si procede:

Brief
→ PRD
→ Épicas / Historias de Usuario
→ Arquitectura
→ Mockups
→ Estimación
→ Desarrollo
→ Pruebas
→ Despliegue productivo

En esta primera iteración NO se solicita diseñar toda la solución ni generar
historias de usuario.

Se solicita analizar el contexto y construir/iterar el BRIEF.


# 2. Problema de origen

Colombia dispone de información pública sobre contratación estatal mediante
SECOP y otras fuentes públicas.

El problema identificado no es principalmente la inexistencia de información,
sino la dificultad de analizarla de manera amplia, continua y eficiente debido
al volumen de procesos, contratos, documentos y variables involucradas.

La vigilancia tradicional obliga en muchos casos a consultar y analizar procesos
individualmente.

Esto limita la capacidad de ciudadanos, veedores, periodistas y otros actores
para identificar oportunamente:

- posibles sobreprecios;
- comportamientos atípicos;
- patrones de gasto;
- concentración de contratación;
- diferencias relevantes entre precios contratados y precios de mercado;
- casos que merezcan una investigación humana más profunda.

La oportunidad identificada consiste en utilizar tecnología para pasar de:

**“buscar manualmente contratos para posteriormente analizarlos”**

a:

**“procesar grandes cantidades de contratación y dirigir la atención humana
hacia aquello que merece ser investigado”.**


# 3. Visión original de la tesis

La tesis propuso conceptualmente una plataforma capaz de:

1. Recopilar información de contratación pública.
2. Extraer, transformar y cargar información (ETL).
3. Centralizar información procedente de diferentes fuentes.
4. Visualizar grandes volúmenes de datos.
5. Consultar procesos y contratos particulares.
6. Generar indicadores y reportes agregados.
7. Comparar precios contratados por entidades públicas contra referencias de
   precios del mercado.
8. Identificar posibles sobreprecios, anomalías y patrones.
9. Permitir profundizar desde indicadores agregados hasta casos específicos.
10. Contrastar hallazgos con información documental y antecedentes.
11. Generar resultados trazables que puedan posteriormente ser revisados por
    ciudadanos, veedores, periodistas u organismos de control.

La tesis llegó a la FORMULACIÓN del prototipo, no a la construcción productiva
del sistema.


# 4. Fuentes de información identificadas originalmente

La investigación contempla, entre otras:

- SECOP II como fuente principal.
- Datos abiertos gubernamentales.
- Colombia Compra Eficiente.
- Contraloría General de la República.
- Informes de Transparencia por Colombia.
- Monitor Ciudadano.
- Informes y antecedentes periodísticos.
- Información fiscal pública.
- Precios del mercado privado.
- Marketplaces y e-commerce como posibles referencias de precios.

Estas fuentes deben considerarse candidatos.

NO asumir que todas deben incorporarse al MVP.

El Brief debe ayudar a determinar cuál es el conjunto mínimo de fuentes necesario
para demostrar valor.


# 5. Datos relevantes planteados en la investigación

Entre las variables consideradas originalmente se encuentran:

- entidad contratante;
- proceso/contrato;
- objeto/descripción;
- región;
- modalidad/tipo de proceso;
- fechas;
- códigos/categorías de bienes y servicios;
- presupuesto;
- precio presupuestado;
- precio finalmente contratado;
- cantidades de bienes;
- precios unitarios;
- referencias de precios del mercado;
- variación entre precio contratado y precio de mercado;
- indicadores agregados por entidad/sector;
- documentos asociados al proceso.

Una dificultad identificada por la tesis es que determinada información,
especialmente precios unitarios y cantidades, puede encontrarse dentro de
documentos o documentos escaneados y no necesariamente como campos
estructurados.


# 6. Usuarios inicialmente considerados

La tesis contempla principalmente:

- ciudadanos interesados en control social;
- veedores ciudadanos;
- periodistas;
- organizaciones relacionadas con transparencia;
- potencialmente organismos de vigilancia y control.

Sin embargo, NO asumir que todos son usuarios objetivo del MVP.

Durante el Brief se debe identificar:

- usuario primario;
- problema principal de ese usuario;
- frecuencia del problema;
- decisiones que necesita tomar;
- valor que recibiría de la plataforma.

Si existen varios segmentos posibles, deben explicitarse como hipótesis y
priorizarse para validación posterior.


# 7. Hipótesis de valor

La hipótesis inicial es:

> Una plataforma capaz de procesar contratación pública de manera masiva y
> presentar señales, comparaciones y evidencia relevante puede aumentar
> significativamente la capacidad de una persona para identificar casos que
> merezcan revisión, frente al análisis manual contrato por contrato.

El sistema NO debe afirmar automáticamente que existe corrupción.

Debe distinguir entre:

- dato;
- indicador;
- anomalía;
- señal o posible hallazgo;
- evidencia;
- conclusión humana o de un organismo competente.

La explicabilidad y trazabilidad del análisis son características importantes.


# 8. Evolución respecto a la tesis original

La tesis fue formulada principalmente desde visualización de datos, ETL,
analítica y técnicas de machine learning disponibles en el momento de su diseño.

La nueva iniciativa quiere explorar tecnologías actuales de IA generativa y
arquitecturas agénticas.

Esto NO significa convertir la plataforma en un chatbot.

La solución debe continuar teniendo capacidades determinísticas tradicionales:

- consultas;
- filtros;
- indicadores;
- visualizaciones;
- estadísticas;
- comparación de información;
- navegación por entidades, proveedores, procesos y contratos.

La IA debe incorporarse únicamente donde genere una capacidad adicional
demostrable.


# 9. Hipótesis de capacidades de IA / agentes

Estas capacidades son HIPÓTESIS y no requisitos cerrados.

Se desea evaluar, entre otras:

### Extracción inteligente

Procesar documentos asociados a contratación y convertir información no
estructurada en datos utilizables:

- bienes;
- cantidades;
- precios unitarios;
- características;
- tablas;
- información contractual relevante.

### Investigación asistida

Permitir que un agente pueda recibir una pregunta o una señal y decidir qué
información necesita consultar para investigarla.

Ejemplo conceptual:

Usuario:
“Analiza la contratación de esta entidad durante los últimos tres años e
identifica comportamientos que merezcan revisión.”

Agente:
1. determina qué análisis realizar;
2. consulta contratos;
3. consulta proveedores;
4. calcula indicadores;
5. compara períodos;
6. recupera documentos/antecedentes cuando corresponda;
7. sintetiza resultados;
8. presenta evidencia y trazabilidad.

### Tool calling

Los agentes podrían utilizar herramientas controladas para:

- consultar contratos;
- ejecutar consultas analíticas;
- recuperar documentos;
- consultar precios;
- calcular indicadores;
- buscar antecedentes;
- recuperar información de una base de conocimiento.

### RAG / Knowledge

Documentos públicos, informes fiscales, antecedentes y documentación contractual
podrían constituir una base de conocimiento que permita fundamentar respuestas
con evidencia.

### Detección y análisis proactivo

A futuro podría evaluarse un proceso que analice nueva contratación
periódicamente, detecte señales relevantes y ejecute análisis adicionales sin
necesidad de que un usuario formule inicialmente una pregunta.

Esto NO debe asumirse automáticamente como alcance del primer MVP.


# 10. Principios de producto para el MVP

### 10.1 El producto debe funcionar sin IA

Debe existir una propuesta de valor base aun si las capacidades generativas son
deshabilitadas.

La IA complementa el producto; no reemplaza su fundamento de datos.

### 10.2 MVP antes que plataforma nacional

No se pretende construir inicialmente un sistema capaz de fiscalizar toda la
contratación colombiana.

Se debe encontrar un subconjunto suficientemente pequeño para:

- construirlo;
- desplegarlo;
- probarlo;
- obtener usuarios;
- aprender;
- medir valor.

Puede limitarse inicialmente por:

- categoría de compra;
- entidad;
- región;
- período;
- tipo de proceso;
- tipo de bien;

o por otra dimensión que resulte técnicamente y funcionalmente más apropiada.

### 10.3 Evidencia antes que acusación

El producto debe ayudar a identificar señales y facilitar investigación.

Una diferencia de precio NO implica automáticamente corrupción.

El sistema debe permitir comprender de dónde provienen los datos y cómo se
obtuvo un resultado.

### 10.4 Arquitectura evolutiva

El MVP debe ser suficientemente simple para construirlo con recursos limitados,
pero permitir incorporar posteriormente nuevas fuentes, análisis y capacidades
de IA.


# 11. Restricciones y decisiones ya tomadas

## Canal

Aplicación WEB.

NO se desarrollará aplicación móvil nativa en el MVP.

Motivos:

- reducir complejidad;
- evitar publicación y aprobación en App Store / Google Play;
- facilitar experimentación;
- permitir despliegues rápidos;
- permitir pruebas con usuarios mediante una URL.

## Experiencia

Diseño:

**desktop-first + responsive**

Desktop será la experiencia principal debido a:

- dashboards;
- tablas;
- filtros;
- comparación de información;
- visualizaciones;
- análisis documental;
- interacción con capacidades analíticas/agénticas.

Tablet y móvil deberán permitir una experiencia funcional adaptada, pero no
condicionarán el diseño principal del MVP.


# 12. Contexto de infraestructura

Actualmente existen recursos tecnológicos utilizados por otro producto del
propietario de la iniciativa (Express App), incluyendo:

- Railway;
- PostgreSQL;
- servicios/backend desplegados;
- algunos recursos de Google.

Existe actualmente un gasto aproximado conjunto cercano a COP $100.000/mes.

Se desea evaluar si parte de esa infraestructura o conocimiento operativo puede
aprovecharse, pero:

- Compras Públicas debe mantenerse como producto independiente;
- no debe acoplarse funcionalmente a Express App;
- no debe reutilizar tecnología únicamente porque ya exista;
- cualquier costo adicional de IA, procesamiento, almacenamiento o búsqueda debe
  ser identificado.

Existe preferencia por mantener un costo operativo bajo durante el MVP.


# 13. Tecnología: no cerrada todavía

NO considerar como decisiones obligatorias las tecnologías propuestas en la
tesis original.

La tesis menciona tecnologías como:

- Python;
- Dash;
- PostgreSQL;
- SQL;
- Selenium;
- infraestructura cloud;
- ETL tradicional.

Estas representan el diseño conceptual de aquel momento.

Para el nuevo MVP se permite replantear completamente la arquitectura.

También se desea evaluar, cuando genere valor:

- Microsoft Foundry;
- modelos generativos;
- agentes;
- tool calling;
- MCP;
- RAG / knowledge bases;
- Azure AI Search / Foundry IQ;
- capacidades multimodales;
- extracción inteligente de información;
- otras tecnologías que resulten apropiadas.

NO imponer Azure a componentes que puedan resolverse mejor o más
económicamente con la infraestructura existente.


# 14. Objetivo adicional del proyecto

Además de convertirse potencialmente en un producto útil, este desarrollo
funcionará como proyecto práctico y demostrable de:

- ingeniería de producto;
- arquitectura;
- analítica;
- IA aplicada;
- sistemas agénticos;
- integración de datos;
- desarrollo asistido por agentes.

Se pretende documentar aprendizajes e incrementos técnicos para generar
publicaciones profesionales y demostraciones, sin sacrificar las decisiones de
producto por objetivos de contenido.


# 15. Estrategia de construcción

Se pretende utilizar agentes especializados del Método Ceiba durante el ciclo de
desarrollo.

La intención preliminar es:

1. Agente de producto / discovery
   → Brief
   → PRD
   → alcance

2. Agente funcional
   → épicas
   → historias de usuario
   → criterios de aceptación

3. Agente de arquitectura
   → arquitectura
   → decisiones técnicas
   → integraciones
   → atributos de calidad

4. Agente de diseño
   → UX
   → mockups

5. Estimación
   → esfuerzo
   → costo
   → riesgos
   → priorización

6. Agente(s) de desarrollo
   → implementación incremental
   → pruebas
   → integración
   → despliegue

El propietario del producto actuará como responsable de las decisiones de
producto y revisión técnica. Los agentes no deben asumir decisiones críticas
cuando falte información.


# 16. Lo que se solicita al agente AHORA

Construir una PRIMERA VERSIÓN DEL BRIEF.

Antes de cerrar el Brief:

1. Analiza críticamente la tesis y este contexto.
2. Separa:
   - hechos conocidos;
   - decisiones ya tomadas;
   - hipótesis;
   - supuestos;
   - preguntas abiertas.
3. Identifica contradicciones o elementos de la tesis que ya no deban asumirse.
4. Determina qué información falta para definir correctamente el MVP.
5. Formula preguntas de discovery de alto valor.
6. Evita preguntas cuya respuesta ya se encuentre en este contexto.
7. No conviertas todavía el Brief en PRD ni en arquitectura detallada.
8. No selecciones tecnologías por defecto.
9. No presupongas que todas las funcionalidades planteadas en la tesis deben
   entrar al MVP.
10. Cuestiona el alcance cuando sea demasiado grande.

Posteriormente, con las respuestas del Product Owner, itera el Brief hasta
obtener una versión suficientemente sólida para avanzar al PRD.


# 17. Pregunta fundamental que debe resolver el Brief

Al terminar el proceso de discovery debemos poder responder con precisión:

**¿Quién utilizará el primer MVP, qué problema concreto resolverá para esa
persona, qué información necesita para hacerlo y cuál es el conjunto mínimo de
capacidades que demuestra que la solución genera valor?**