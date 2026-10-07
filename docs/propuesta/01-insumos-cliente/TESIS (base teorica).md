![Imagen: Logo Universidad Externado de Colombia - Facultad de Ciencias de la Educación 50 Años](source: 1)

PLATAFORMA DE VISUALIZACIÓN DE DATOS PARA CONTROL FISCAL DE COMPRAS PÚBLICAS

JUAN CAMILO SIERRA NOSSA

Universidad Externado de Colombia  
Facultad de Administración de Empresas  
Bogotá, Colombia  
2025

---

PLATAFORMA DE VISUALIZACIÓN DE DATOS PARA CONTROL FISCAL DE COMPRAS PÚBLICAS

JUAN CAMILO SIERRA NOSSA

Tesis o trabajo de investigación presentada(o) como requisito parcial para optar al título de:  
Maestría en Gerencia de Transformación Digital y Analítica de Negocios

Director (a):  
Jenny Carolina Saldaña Cortes

Universidad Externado de Colombia  
Facultad de Administración de Empresas  
Bogotá, Colombia  
2025

---

### Dedicatoria

A mis padres, hermanos, familiares y amigos por respaldarme durante el desarrollo de este proyecto. Igualmente, para mi directora, maestros, y a la universidad por brindar todas las herramientas necesarias para desarrollar esta iniciativa. Que el propósito final sea contribuir a un mejorar la gestión de compras públicas, por ende un mejor país.

---

### Agradecimientos

Agradezco enormemente a la Universidad Externado de Colombia, a la facultad, a la directora Jenny Saldaña y a todos los maestros por brindar todo el conocimiento, herramientas, sugerencias y recomendaciones durante la maestría para la consecución de los objetivos de este proyecto. Este trabajo es fruto del esfuerzo de todos, por lo cual siempre estaré agradecido.

---

### Resumen

La contratación pública en Colombia es uno de los sectores en los cuales se manifiestan altos índices de corrupción estatal. A pesar de que el estado colombiano cuenta con herramientas digitales para gestionar el proceso de adquisición de bienes y servicios a través del SECOP de forma transparente, y que los ciudadanos pueden acceder, vigilar, consultar y fiscalizar dichos procesos, la cantidad de contratos por adquisición que se publica diariamente es enorme. Esta situación genera una incapacidad de abordar un fiscalización amplia y efectiva que permita detectar hallazgos fiscales para combatir el problema de corrupción por sobreprecios en compras de bienes para organismos estatales.

Por lo mencionado anteriormente, se formula el diseño del prototipo de una plataforma de visualización de datos para el análisis de compras públicas, el cual surge de la necesidad de abordar la mayor cantidad de procesos públicos posible, gracias a la implementación de herramientas digitales que facilita el proceso de extracción, transformación y carga de datos ETL (por sus siglas en ingles Extraction, Transformation, Load).

Regularmente para realizar la vigilancia y veeduría de los procesos de compras públicas, es necesario revisar un proceso a la vez, lo cual es completamente ineficiente. Gracias a esta plataforma de visualización, se pueden identificar hallazgos fiscales de manera más eficiente, con mayor amplitud y de forma continua. Es decir que el sistema se encarga de detectar los casos de sobre precios en la adquisiciones de bienes para uso público de forma automática, masiva y autónoma. Esto le permite al veedor o ciudadano, explorar los hallazgos identificados por el sistema, contrastar la información, profundizar más a fondo cada uno de ellos y reportar a los respectivos entes de control.

---

### Abstract

Public procurement in Colombia is one of the sectors with the highest levels of state corruption. Although the Colombian government provides digital tools, such as SECOP, to manage the procurement of goods and services transparently and allow citizens to access, monitor, and oversee these processes, the vast number of procurement contracts published daily makes comprehensive and effective auditing difficult. This limitation hinders the detection of fiscal irregularities, particularly cases of overpricing in state agency purchases, which contribute to corruption.

Given these challenges, this study proposes the design of a prototype for a data visualization platform for public procurement analysis. The platform aims to maximize the oversight of public procurement processes by leveraging digital tools that facilitate ETL (Extraction, Transformation, and Load) data processing.

Currently, monitoring and auditing public procurement require reviewing contracts individually, a process that is highly inefficient. With the implementation of this visualization platform, fiscal irregularities can be identified more efficiently, at a larger scale, and continuously. In essence, the system is designed to automatically, massively, and autonomously detect cases of overpricing in public procurement. This enables auditors and citizens to explore the system's findings, compare data, conduct in-depth analyses, and report irregularities to the relevant oversight authorities.

---

### Contenido

* Dedicatoria 3
* Agradecimientos 4
* Resumen 5
* Abstract 6
* Contenido 7
* Lista de figuras 9
* Lista de Ecuaciones 10
* Introducción 11
* 1.Planteamiento del Problema 13
  * 1.1 Planteamiento del problema 13
  * 1.2 Antecedentes 14
  * 1.3 Preguntas de Investigación 15
  * 1.4 Objetivos 15
  * 1.5 Justificación 16
  * 1.6 Supuestos 17
  * 1.7 Alcance y Limitaciones 18
* 2. Marco Conceptual y Revisión Bibliográfica 19
  * 2.1 Antecedentes Referenciales 19
  * 2.2 Visualización de Datos 20
    * 2.2.1 Dash 21
    * 2.2.2 Python 21
    * 2.2.3 ETL (Extracción, Transformación y Carga de Datos) 22
    * 2.2.4. Selenium 22
    * 2.2.5 Auditoría Digital 22
  * 2.3 Análisis de Datos 23
  * 2.4 Big Data y Machine Learning en el estado 24
* 3. Marco Contextual 25
* 4. Metodología de Investigación 28
  * 4.1 Diseño de la Investigación 29
  * 4.2 Fuentes de Datos. 31
    * i) SECOP II. 31
    * ii) Contraloría 31
    * iii) Informes de Transparencia. 32
    * iv) Precios del mercado privado 33
    * v) Transparencia por Colombia 33
    * vi) Monitor ciudadano. 34
    * vii) Reportes de prensa y periodismo 34
    * viii) Datos fiscales 34
  * 4.3 Herramientas de Análisis 36
* 5. Plataforma de Visualización de datos y análisis de compras públicas 37
  * 5.1. Descripción del sistema de compras públicas SECOP 38
    * 5.1.1 Generalidades de la plataforma 38
  * 5.2. Prototipo de desarrollo de una plataforma web de visualización de grandes volúmenes de datos relacionados con compras públicas. 45
    * 5.2.1. Propuesta de Diseño 45
    * 5.2.2. Propuesta de Arquitectura 47
      * Componentes Principales de la Arquitectura 47
  * 5.3. Metodologías y herramientas de analítica e inteligencia artificial para establecer la evaluación de la gestión de compras del Estado 49
    * 5.3.1. Recopilación de Datos 49
    * 5.3.2. Extracción de datos 51
    * 5.3.3. Limpieza y Preparación de Datos 52
    * 5.3.4. Visualización de datos 52
    * 5.3.5. Pruebas Funcionales 52
    * 5.3.6. Análisis descriptivo 53
    * 5.3.7. Análisis de Contenido 54
    * 5.3.8. Informe de Resultados 56
  * 5.4. Plan de capacitación de apropiación 56
    * 5.4.1. Diseño y Planeación de la Capacitación 57
    * 5.4.2. Desarrollo de la capacitación 57
    * 5.4.3. Implementación 58
    * 5.4.4. Evaluación 58
* Conclusiones y Recomendaciones 59
  * Conclusiones 59
  * Recomendaciones 59
* Bibliografía 61

---

### Lista de figuras

* Figura 1 Distribución Porcentaje de Corrupción en Colombia 32
* Figura 2 Visualizaciones Contratación Colombia Compra Eficiente 34
* Figura 3 Interfaz de búsqueda SECOP II 38
* Figura 4 Diagrama de Flujo Proceso de Adquisición Pública en SECOP II 39
* Figura 5 Selección de Entidad Comprador SECOP II 40
* Figura 6 Resultados de búsqueda SECOP II 42
* Figura 7 Detalle Formulario Información 43
* Figura 8 Documentos Detalle convocatoria 43
* Figura 9. Arquitectura Propuesta 47
* Figura 10 Ciclo Crisp-DM 49
* Figura 11 Six Stage Training Model 56

---

### Lista de Ecuaciones

* Ecuación 1. Análisis Comparativo Porcentual 53
* Ecuación 2. Promedio Total de Variación de precios por entidad 53

---

### Introducción

La era digital ha involucrado todos los sectores sociales, económicos y políticos de nuestra sociedad. Dentro del contexto de la constitución del Estado, surge la necesidad de hacer un control social y fiscal de parte de la ciudadanía sobre la ejecución de recursos públicos por parte del gobierno.

Los procesos de compra publica evolved hacia la digitalización. De la misma forma los ciudadanos pueden ejercer su derecho y deber de vigilancia fiscal a través de medios electrónicos.

Si bien la ley establece que todos los procesos de contratación pública deben ser publicados y de acceso para toda la población, la capacidad de ejercer control de todos se reduce debido a la gran cantidad de información, procesos y volumen que debe procesarse.

Es allí donde surge la necesidad de establecer un proceso que permita extraer, transformar, cargar y analizar la información de compras públicas a través de un único sistema que, de forma amigable con el ciudadano , permita generar insights, reportes, e información que agregue valor en la actividad de vigilancia fiscal.

Aunque por normatividad, Estado Colombiano cuenta con el portal de contratación estatal SECOP II, diariamente se publican miles de procesos en todo el territorio nacional, lo que dificulta la capacidad de acceder a todos los procesos, procesar toda la información y ejercer el proceso de control social y fiscal.

Este proyecto busca formular el prototipo de un sistema de información que realice ese proceso de ETL (Extraction Load Transformation) permitiendo al ciudadano ampliar su capacidad de vigilar y controlar las compras públicas, y obtener insights, reportes y estadísticas, así como consultas sobre la gestión fiscal.

El sistema logra la optimización de la vigilancia y el control en la identificación de hallazgos fiscales en compras publicas gracias al uso de procesamiento de datos a partir de herramientas digitales como librerías de Python, SQL Server y demás técnicas de desarrollo. Esto potencia el margen de acción y vigilancia, permitiendo abarcar muchos más procesos a la vez, en un ciclo de ingesta de datos continuo y actualización constante de la información.

---

### 1. Planteamiento del Problema

#### 1.1 Planteamiento del problema

La transformación digital es un proceso que ha abordado distintos sectores de la economía, optimizando la productividad de muchas empresas, y el sector público no ha sido rezagado a este fenómeno. Y aunque hoy en día hay el reto de transformación en el sector gobierno es muy grande, este ha tenido surtido mejoras sustanciales que no podemos ignorar. Sin embargo, el estado se constituye por el gobierno, los ciudadanos, y el territorio. Los ciudadanos juegan un papel importante en la construcción y mejoramiento del estado, y una de sus actividades primordiales es la veeduría ciudadana de la gestión política y vigilancia fiscal del gobierno en todos sectores y niveles.

Por lo anterior, surge la necesidad de observar y analizar a mayor profundidad cómo el gobierno ejecuta los recursos públicos, siendo esta actividad parte del derecho de veeduría que tienen los ciudadanos para prevenir casos de corrupción, despilfarro, y gastos innecesarios en el Estado. Aunque esta actividad la realizan veedurías o ciudadanos del común que verifican estos procesos de compras públicas a través de plataformas como SECOP, Bolsa Mercantil y portales públicos gubernamentales (medios digitales), esta sigue siendo una tarea manual y dispendiosa, y que no abarca la gran cantidad de procesos de compra pública que se ejecutan diariamente en Colombia. Se puede plantear que existen miles de procesos que no se vigilan o controlan, simplemente por la falta de capacidad de abordar los mismos, y que, aunque la mayoría de estas compras se publican en los portales estatales, desde el gobierno no existen herramientas que permitan analizar a detalle el tipo de información que las veedurías y los ciudadanos deben contemplar en su vigilancia.

#### 1.2 Antecedentes

El control fiscal a través de herramientas analíticas e informáticas ha evolucionado en los últimos años. Por ejemplo, en Kenia existe una plataforma llamada Ushahidi. Esta es una plataforma tecnológica que permite a los ciudadanos reportar y mapear incidentes de corrupción en tiempo real. Dicha plataforma permite monitorear y denunciar casos de corrupción en diversos sectores, incluyendo contratos públicos (Ushahidi, s.f.). Aunque Ushahidi abarca muchas aristas relacionadas con el control gubernamental y la corrupción, uno de sus enfoques es vigilar la gestión relacionada a contratos públicos en ese país.

Un caso similar a nivel internacional de control en contratos públicos es el Estándar de Datos Abiertos Gratuito y de Acceso Público (o por sus siglas en inglés, OCDS, Open Contracting Data Standard) (Open Contracting Data Standard, s.f.). El OCDS es una iniciativa global que promueve la divulgación y el uso de datos abiertos en los procesos de contratación pública. Proporciona un estándar común para la publicación de información sobre contratos, lo que facilita el análisis y la detección de posibles casos de corrupción.

Aunque iniciativas como las de OCDS o Datos Abiertos en Colombia facilitan el acceso a información relacionada con contratos públicos, y por ende su revisión por parte de la ciudadanía, demandan esfuerzos relacionados a la búsqueda y examen de los documentos en casos específicos, y sin el uso de herramientas tecnológicas que no solo habiliten la gestión de auditoría, sino también la capacidad de ampliar el rango de control e identificación de hallazgos, reduce el margen de acción hacia una vigilancia eficiente.

#### 1.3 Preguntas de Investigación

Las preguntas que surgen de acuerdo al planteamiento del problema son:
i) ¿Cómo vincular al ciudadano para hacerlo participativo en procesos de veeduría apoyado en la tecnología?;
ii) ¿Las veedurías estarían interesadas en estas soluciones tecnológicas que puedan facilitar sus procesos de vigilancia fiscal?;
iii) ¿Cuál es la complejidad técnica de extraer, transformar y cargar todo el volumen de información requerido para que al ser procesado pueda generar insights de valor a los interesados?;
iii) ¿Las entidades públicas y el sector gobierno en general estaría dispuesto a permitir que se comparta toda la información de gestión fiscal teniendo en cuenta el impacto político que esto pueda generar?.

#### 1.4 Objetivos

El objetivo general es el de proponer un prototipo de una plataforma de visualización de grandes volúmenes de datos y análisis de compras públicas que permita comparar precios de compra del estado con los precios del mercado, a partir de los siguientes objetivos específicos:
i) Describir las características funcionales de la herramientas de compras públicas SECOP para el seguimiento y control fiscal del Estado colombiano.
ii) Formular un prototipo de desarrollo de una plataforma web de visualización de grandes volúmenes de datos relacionados con compras públicas.
iii) Establecer metodologías y herramientas de analítica e inteligencia artificial para determinar patrones, posibles sobreprecios para establecer la evaluación de la gestión de compras del Estado.
iv) Formular un plan de capacitación a los ciudadanos, veedores ciudadanos y periodistas, para que se apropien del conocimiento sobre el uso de la tecnología y que participen activamente en el control y análisis de la información.

#### 1.5 Justificación

Este trabajo de grado se enfoca en proponer un prototipo de plataforma que recopile, extraiga, transforme y analice múltiples procesos de compras públicas, para visualizar la información que los ciudadanos interesados y veedores puedan consultar a través de un portal unificado. El propósito de la plataforma de tipo unificado y amigable es que los ciudadanos puedan consultar un proceso en particular y explorar insights acerca del mismo, validando si existen anomalías en la contratación relacionadas con el precio. Por otro lado, también se pueden consultar reportes de gestión a alto nivel, para hacer un control más general y posteriormente hacer un análisis especifico de cada sector. La formulación del prototipo se haría con base en las necesidades de los veedores para que se atiendan sus requerimientos específicos, y basado en las necesidades de usuario, concebir la base para desarrollar mejoras e implementación en el futuro.

El acceso a la información pública, portales estatales y estrategia de gobierno en línea han llevado a la necesidad de conocer y aprovechar al máximo el uso y explotación de herramientas digitales para ejercer una veeduría exitosa. Entidades gubernamentales como la Alcaldía de Cali han identificado estas necesidades por lo que han dispuesto cursos de acceso a veedores ciudadanos para que usen herramientas digitales facilitando la labor de auditoría (Muñoz, 2012). Según Transparencia Colombia, una de las necesidades más relevante de los veedores es el acceso a recursos técnicos y financieros (Transparencia por Colombia, 2024).

No solamente se puede cerrar la brecha digital de los veedores con el acceso a herramientas tecnológicas, sino que esta debe ir de la mano con capacitaciones y vinculación de los procesos de adopción para aprovechar al máximo la información pública.

Debido a que la mayoría de las transacciones hoy en día se realizan de manera digital, y un proceso de veeduría se asemeja a una auditoría, se resalta la necesidad de usar herramientas informáticas para fortalecer dicha labor. Hoy día incluso existen muchas herramientas que automatizan diversas tareas de auditoría (Ahmi & Simon, 2013).

#### 1.6 Supuestos

Esta investigación se realiza bajo el supuesto que las Entidades Estatales publicarán información relevante y actualizada sobre las compras públicas en los portales establecidos, como SECOP.

Se asume que los ciudadanos y las veedurías tienen un interés activo en la vigilancia y control de las compras públicas, y están dispuestos a utilizar la plataforma para mejorar su labor. Se da por sentado que las herramientas de visualización y análisis de datos serán efectivas para detectar posibles sobreprecios y patrones de compras en el sector público.

Se presupone que los datos publicados por las entidades estatales son precisos y están libres de errores significativos que puedan afectar el análisis. Se supone que las tecnologías de analítica e inteligencia artificial implementadas en la plataforma podrán manejar y procesar grandes volúmenes de datos de manera eficiente. Esto de la mano con el acceso a internet y herramientas informáticas por parte de veedores y ciudadanía en general.

#### 1.7 Alcance y Limitaciones

Este trabajo de grado se enfoca en formular el prototipo que atienda los requerimientos de gran escala y de análisis de volumen de información necesarios para el control fiscal. El desarrollo de la plataforma no corresponde a este proyecto, sin embargo, se establecen todos los requisitos tecnológicos, y se plantean las herramientas, arquitectura, técnicas y metodologías para el desarrollo de esta. La formulación de la plataforma debe contemplar los requerimientos y necesidades de los ciudadanos para que su derecho a participación y fiscalización estatal sea más eficiente.

---

### 2. Marco Conceptual y Revisión Bibliográfica

#### 2.1 Antecedentes Referenciales

La base teórica del proyecto se sustenta principalmente en la legislación colombiana que permite, avala y promueve la participación ciudadana para el control fiscal. Esto se evidencia en la ley 1712 de 2014, la cual “Regula el derecho de acceso a la información pública”.

Según el “Título II de la publicidad y del contenido de la información, Artículo 7. Disponibilidad de la Información.” En dicho título se define que “deberá estar a disposición del público la información a la que hace referencia la presente ley, a través de medios físicos, remotos o locales de comunicación electrónica”. Siendo el medio electrónico una forma de difusión para la transparencia de información, la tecnología y los sistemas de información jugando un papel importante para el cumplimiento de la estrategia.

El desarrollo de sistemas de información para visualización de datos surge como una herramienta que agiliza y automatiza el proceso de control fiscal. La evolución de la inclusión digital en las auditorias, por ejemplo, ha llevado a considerar la evidencia digital como un insumo fundamental de la auditoría moderna. (Valencia Duque, Tamayo Arias, & Osorio López, 2015). A partir de aquí se consideran sustentos teóricos no solo de la concepción del derecho del ciudadano para el acceso a la información y la transparencia, sino del uso y apropiación de los sistemas de información, los cuales son la base tecnológica y herramienta para el cumplimiento del objetivo inicial.

#### 2.2 Visualización de Datos

La visualización de datos es una necesidad humana, para entender contextos o situaciones particulares, ya que los humanos tendemos a ser visuales (Aparicio & Costa, 2015). La visualización a través de distintos gráficos es una forma de representar los datos de forma entendible, resumida y didáctica para el usuario. Representa el resultado de un procesamiento a través de ordenador de distintas conexiones y relaciones que representan cierta información (Sadiku, Adebowale, & Musa, 2016). Existen diferentes tipos de visualización de datos, dentro los que se destacan: Gráfico de líneas (usado para relaciones de período de tiempo), gráfico de barras, gráfico de dispersión y gráfico circular. El uso de herramientas de visualización de datos es útil dentro de los procesos de adquisición publica al fortalecer el rendimiento en los procesos de contratación, favoreciendo la integración de los actores involucrados y la identificación de buenas prácticas (Amit & Srivastava , 2019).

Las visualizaciones de datos constituyen una herramienta de utilidad no solo a nivel empresarial o estadístico. Recientemente se ha demostrado su usabilidad para otro tipo de conocimientos y ramas de la ciencia. Por ejemplo, en Colombia recientemente se han apropiado prácticas y conocimientos para visualizar datos relacionados con el postconflicto después del proceso de paz. La explotación de este tipo de herramientas ha acercado al público en general a la divulgación de todos los procesos y contextos asociados al postconflicto. (Marín Ochoa, 2018)

La visualización de datos también ha sido una herramienta poderosa para el control fiscal y territorial. Gracias a la visualización de datos se ha transformado el seguimiento y análisis de la contratación de vías rurales en Colombia. Con esta se pretende identificar entidades y contratistas con mayores volúmenes de contratación en todos los niveles territoriales. (Gomez Cabrera, Cortes Rey, Sanchez Rivera, Felizzola, & Gomez, 2024)

##### 2.2.1 Dash

Dash es una de las herramientas de visualización más comunes caracterizada por replicar datos de forma sencilla y relevante en su interacción con el usuario final mediante paneles de control, los cuales son implementados usualmente como páginas web para ejecutar en cualquier navegador web o dispositivo móvil (Burch & Schmid, 2023). Este es un framework de código abierto para crear interfaces de visualización de datos. Desde su creación en el 2017 como biblioteca de Python ha crecido para incluir implementaciones para otros lenguajes. Se integran con lenguajes de programación como HTML, CSS y Javascript (Pérez Bellido, 2024).

##### 2.2.2 Python

Python es uno de los lenguajes de programación más versátiles que han surgido en los últimos años. Se caracteriza porque admite estilos de programación orientados a objetos, funcionales e imperativos (Sloan, 2019). Python junto con R son los lenguajes más comunes para la representación visual de datos. Es útil en todo el ciclo de análisis de datos para la toma de decisiones empresariales críticas (Embarak, 2018).

Una de las virtudes de este lenguaje es que puede procesar cadenas de texto caracterizadas por tener reglas lingüísticas y aspectos característicos de los idiomas. A través del uso de librería para el procesamiento de lenguaje natural (NLP), con python se pueden extraer insights, visualizar datos y generar reportes para la toma de decisiones basadas en datos. (Bird, Klein, & Loper, 2009)

##### 2.2.3 ETL (Extracción, Transformación y Carga de Datos)

ETL (Extraction, Transformation, Load) es la sigla para simplificar y representar el proceso de extracción, transformación y carga de datos, el cual como su nombre lo indica lleva a cabo la identificación y extracción de datos de diversas fuentes, las transformaciones necesarias para limpiar y personalizar y la carga en un almacén de datos (Vassiliadis, Spiros, & Alkis, 2023). Los modelos predictivos y de análisis aprovechan los procesos de ETL para generar visualizaciones que permitan tomar decisiones basadas en datos. Una integración efectiva entre el proceso de ETL y técnicas de visualización pueden potenciar de manera eficiente la generación de modelos predictivos y tomas de decisiones de manera asertiva (Teja Gurram, 2024).

##### 2.2.4. Selenium

Selenium es una herramienta que fue diseñada para la automatización de pruebas de aplicaciones web. (Yuan, 2023). Sin embargo, su integración con lenguajes de programación como Python o JavaScript facilitaron su uso en la extracción de información de portales y aplicativos web. El data scrapping se realiza usando la herramienta Selenium integrada con bibliotecas de Python, para el procesamiento de datos extraídos. Dicha herramienta tiene la capacidad de acceder a la información del contenido web ya sea por JavaScript o explorando los selectores requeridos para la extracción.

##### 2.2.5 Auditoría Digital

La auditoría digital es la transformación de la auditoría tradicional mediante la digitalización y el uso de tecnologías avanzadas. Este proceso implica la automatización y la capacidad de analizar grandes volúmenes de datos, asignándole al auditor o fiscalizador un papel estratégico en el control de riesgos y la eficiencia de las administraciones públicas.

La auditoría digital permite una mayor transparencia y facilita la identificación de problemas con mayor eficiencia, ayudando a los gobiernos a tomar decisiones basadas en evidencias. (Cordero Valdavida, 2018).

Así mismo, el control fiscal digital ha evolucionado no solo por la necesidad de ampliar la capacidad de control, sino porque la mayoría de los medios hoy día son electrónicos. Aunque en Colombia el crecimiento de la implementación de las TIC en el control fiscal y auditorías ha sido paulatino, ya se han creado organismos exclusivamente destinados para esta labor. Sistemas de información como SINACOF (Sistema Nacional de Control Fiscal) han evolucionado e involucrado herramientas tecnológicas necesarias para optimizar esta función. (Valencia Duque, Tamayo Arias, & Osorio López, 2015)

#### 2.3 Análisis de Datos

El análisis de datos es proceso llevado a cabo para explorar y examinar datos brutos con el propósito de tomar de decisiones soportadas en los mismos. Hoy día existe la capacidad técnica y tecnológica de procesar analizar grandes volúmenes de datos (Big Data). Este proceso lleva a cabo etapas de captura, limpieza, transformación, modelamiento y análisis. (Cordero Valdavida, 2018).

En Colombia la analítica de datos surge de la necesidad de hacer el estado más eficiente con el gasto público. Por ejemplo, desde entidades como el SISBEN, ha sido útil para caracterizar y atender a las personas más vulnerables. La explotación de los datos no había sido aprovechada de una perspectiva analítica sino de forma consultiva y archivo. Sin embargo, entidades como el DNP (Departamento de Planeación Nacional) entidad encarga de administrar los datos del SISBEN, decide construir y mejor un algoritmo para predecir la capacidad de generación de ingresos a través de la analítica de datos. (López, 2020).

#### 2.4 Big Data y Machine Learning en el estado

El aprendizaje automático (Machine Learning) potenciado para el análisis de big data está siendo uno de los impulsadores de la nueva generación de Gobierno 3.0. Este nuevo enfoque se caracteriza por la captura masiva de muchos datos históricos que requieren un nivel de procesamiento mayor. Aunque el abordaje de estas tecnologías implica nuevos desafíos, el aprendizaje automático constituye una nueva oportunidad para abordar grandes proyectos asociados al análisis de datos para la toma de decisiones estratégicas (Alexopoulos, y otros, 2019).

A pesar del potencial que presenta el Big Data para la gestión gubernamental, aún existe una capacidad limitada de la digitalización, sobre todo en los territorios. No obstante, Colombia ha generado importantes iniciativas para asegurar su uso en diferentes entidades y regiones. Entidades como Colciencias, ha destinado recursos a la exploración y apropiación de este conocimiento. El uso y formación en herramientas de este tipo ha contribuido por ejemplo a identificar afiliados duplicados en el SISBEN, evitando el pago repetido de algún subsidio, o entidades como el DNP desde un análisis estadístico a partir del big data ha generado una previsión actualizada de las variaciones del PIB nacional. (Balestreri, 2018).

Un buen ejemplo de ello es la gestión que ha hecho Colombia junto con MINTIC para el aprovechamiento de datos abiertos y su estrategia de Open Goverment Data. El mismo gobierno ha definido 16 criterios para asegurar la calidad de los datos. Estos criterios son: confidencialidad, relevancia, actualización, trazabilidad, cumplimiento, precisión, completitud, consistencia, exactitud, portabilidad, credibilidad, comprensibilidad, accesibilidad, eficiencia, recuperabilidad y disponibilidad. Esto demuestra no solo el interés del gobierno colombiano por aprovechar estos activos, sino avances importantes en la definición de métricas, criterios de calidad y herramientas para su explotación. (Rangel Carrillo & Osorio Sanabria, 2023).

---

### 3. Marco Contextual

El control y vigilancia ciudadano apoyado en herramientas tecnológicas se sustenta en la constitución de los derechos que tienen las personas a la información y el derecho al acceso a la tecnología. Así lo plantea el Estudio sobre la figura de la veeduría ciudadana de Transparencia Internacional Colombia (Transparencia Colombia, 2000).

El artículo 60 de la Ley 1757 de 2015 de Colombia establece no solo el derecho, sino el deber que tienen los ciudadanos de “participar de manera individual o a través de sus organizaciones, redes sociales e instituciones, en la vigilancia de la gestión pública y sus resultados”. Dicho artículo también insta a la participación ciudadana para intercambiar experiencias y sistemas de información. (Congreso de Colombia, 2015).

Uno de los objetivos establecidos en el artículo 64 de la mencionada ley define el fortalecimiento de la participación ciudadana para que las autoridades hagan un manejo transparente y eficiente de los asuntos públicos. Lo anterior destaca la importancia de la participación ciudadana para hacer un control social que asegure un uso adecuado de los recursos públicos. La ejecución fiscal es llevada a cabo a través diferentes mecanismos de contratación los cuales pueden ser consultados por la ciudadanía en general. La Ley 80 en Colombia tiene como objeto “disponer las reglas y principios que rigen los contratos de las entidades estatales.” (Congreso de Colombia, 1993). En dicha ley se establecen todas las definiciones, normativa, actores y demás consideraciones pertinentes que rigen la contratación pública en Colombia.

Es en el año 2007 cuando el Congreso de la República de Colombia decreta la Ley 1150 “Por medio de la cual se introducen medidas para la eficiencia y la transparencia en la Ley 80 de 1993 y se dictan otras disposiciones generales sobre la contratación con Recursos Públicos.” (Congreso de Colombia, Ley 1150 de 2007). Con el fin de “expedir los actos administrativos, los documentos, contratos y en general los actos derivados de la actividad precontractual y contractual” (Congreso de Colombia, Ley 1150 de 2007)., surgió la necesidad de desarrollar el sistema de información SECOP.

Es allí donde en el 2015 se evolucionó al sistema de información SECOP II, dejando de ser un sistema de publicación de información (SECOP I) a un sistema transaccional de tal forma que se hiciese proceso de contratación en línea (Colombia Compra, 2015). En secuencia con la sistematización del proceso de contratación en línea, el control social por parte de la ciudadanía también empezó a digitalizarse consiguiendo fomentar la participación activa a través de medios electrónicos.

El uso de medios electrónicos proporciona amplios beneficios para el cumplimiento de los objetivos del estado, especialmente en la implementación de los principios de eficiencia, eficacia, transparencia y rapidez que deben guiar el gasto público.

Gracias a los equipos digitales, se facilita la adquisición de obras, bienes y servicios. El uso de medios electrónicos responde a la necesidad de estar en sintonía con las demandas actuales de la informática, convirtiéndose en un derecho. La Ley 1712 de 2014, (Ley de Transparencia y del Derecho de Acceso a la Información Pública Nacional) respalda la capacidad y derecho que tiene la ciudadanía en informarse de los procesos de adquisición en todas y cada una de las etapas durante la etapa precontractual, contractual y pos. (Congreso de la Republica de Colombia, 2014).

---

### 4. Metodología de Investigación

La metodología adoptada para llevar a cabo esta investigación tiene un enfoque explicativo mixto, en donde a través de un análisis cualitativo y cuantitativo de la problemática, se pretende explicar el cómo una plataforma de visualización de datos puede mejorar el control fiscal y detectar irregularidades en las compras públicas. El enfoque mixto definido utilizando análisis de datos secundarios pretende dar respuestas a las preguntas de investigación planteadas previamente. Tal como lo defined Creswell (Creswell, 2015), este tipo de enfoque mixto permite proporcionar una comprensión más completa de un problema de investigación que si fuese a partir de datos cualitativos o cuantitativos por sí solos.

Dicha combinación de métodos cuantitativos y cualitativos, utilizando exclusivamente datos secundarios explica cómo y por qué una plataforma de visualización de datos puede mejorar el control fiscal de las compras públicas. Análisis cuantitativo como datos fiscales provenientes de fuentes oficiales junto con el análisis cualitativo de informes y estudios de casos, facilita la comprensión más completa del problema a resolver.

Un enfoque mixto puede ser bastante útil a la hora de comprender escenarios complejos caracterizados por el componentes numéricos y características sociales. (Tashakkori & Teddlie, 2010). En este caso, el problema abordado radica en componentes sociales los cuales podemos caracterizar desde el punto de vista cualitativo (corrupción, falta de gestión, gobierno) pero a la vez se sustenta en elementos cuantitativos que resaltan y evidencian el fenómeno mencionado. Dichos datos numéricos se observan en el volumen de contratos publicados, categorías de gasto o indicadores de sobreprecio o irregularidades.

A través del enfoque explicativo justificamos cómo una plataforma de visualización adaptada las necesidades del usuario, puede cerrar las brechas de acceso a información y genera insights representativos en el control ciudadano en la fiscalización de los recursos públicos.

Para ello abordamos aspectos relacionados a componentes cuantitativos que proceden y complementan con aspectos cualitativos relacionados con comportamientos personales. Y es que, según Bowen, un estudio que sigue dicha secuencia adopta una fase cuantitativa (cifras) que va seguida de la fase cualitativa (personal) (Bowen, Rose, & Pilkington, 2017).

Con la propuesta de una plataforma para visualización de compras públicas se pretende demostrar que gracias a herramientas digitales se optimiza el proceso de fiscalización de compras públicas, no solo identificando hallazgos de impacto, sino amplificando la capacidad de control gracias al procesamiento de datos a través de analítica y machine learning.

#### 4.1 Diseño de la Investigación

Las etapas de este trabajo de grado son:
i) Descripción del sistema de compras actual SECOP.
ii) Formulación del prototipo de una plataforma de visualización de grandes volúmenes de datos relacionados con compras públicas.
iii) Metodologías y herramientas de analítica e inteligencia artificial para establecer la evaluación de la gestión de compras del Estado.
iv) Plan de capacitación de apropiación del conocimiento sobre el uso de la tecnología.

**Etapa 1. Descripción del sistema de gestión de compras públicas actual SECOP.** Se describe a detalle cómo funciona el sistema de gestión de compras públicas en Colombia SECOP. Este tiene sistemas tiene componentes de carácter informativo como transaccional. Es necesario hacer una caracterización de sus funcionalidades para una comparación eficiente con sus ventajas y desventajas. SECOP es el sistema oficial establecido por el gobierno colombiano para gestionar las compras estatales; su carácter público (de acceso a todos) y transparente, promueve y permite la consulta continua y consumo de información.

**Etapa 2. Formulación del prototipo de una plataforma de visualización de grandes volúmenes de datos relacionados con compras públicas.** Se formula un prototipo piloto que visualice datos asociados a compras públicas, comparado con el mercado regular. Esta visualización es útil para la identificación de hallazgos fiscales que puedan ser explorados a detalle. La plataforma debe ser amigable con el usuario, cumplir características asociadas a una interacción accesible y fácil de usar para el público general.

**Etapa 3. Establecer metodologías y herramientas de analítica e inteligencia artificial para establecer la evaluación de la gestión de compras del Estado.** La analítica de datos se soporta en diferentes metodologías de implementación para definir la mejor toma de decisiones basada en datos. Es necesario identificar una metodología que abarque la mayor cantidad de etapas del ciclo de vida del dato, y que se alinee directamente a los objetivos de la investigación. Este tipo de proyecto contempla variables de carácter cuantitativo y cualitativo, por lo cual se deben procesar estructuras de datos complejas, así como datos estructurados y no estructurados. Para ello existen herramientas tecnológicas como librerías, lenguajes de programación, interfaces y ambientes de desarrollo que son útiles para abordar procesos de recolección, extracción, visualización, análisis y modelamiento de datos.

**Etapa 4. Plan de capacitación de apropiación del conocimiento sobre el uso de la tecnología.** La construcción de una solución tecnológica o un sistema de información, sin abordar un plan de capacitación apropiación no constituye el cumplimiento del objeto de negocio o problema a resolver. Por lo anterior, es imperativo que dentro de esta fórmula se involucre al usuario y a través de un plan de capacitación, este adopte la tecnología propuesta para que él mismo, identifique y visualice la información, y genere hallazgos fiscales relacionados a compras públicas.

#### 4.2 Fuentes de Datos.

**i) SECOP II.** De las principales fuentes de información para identificar hallazgos fiscales en compras públicas, la más importantes es SECOP II. Esta es la principal fuente de datos para la presente investigación, ya que allí reposan y se publican todos los contratos públicos y compras realizadas por el estado en todas sus dependencias. Según el portal de Datos Abiertos (Ministerio de las Tecnologias y las Comunicaciones de Colombia, 2024)., desde el año 2019 a diciembre de 2024 se han realizado más de 61.000 descargas en las plataformas de compras SECOP II. Los contratos publicados allí pueden oscilar entre 100 y 300 documentos diarios y nuevos procesos de contratación alrededor de 50 a 150 procesos, aunque este número puede aumentar durante los primeros meses del año y hacia finales, debido al cierre fiscal. La plataforma SECOP II es de acceso público, y la cantidad de datos para analizar, documentos e información es bastante robusta.

**ii) Contraloría.** En un contexto global las contralorías velan por conseguir el mejor valor posible dentro de la adquisiciones y ejecución de contratos gubernamentales. El gobierno es ineficiente en conseguir la supervisión adecuada, lo que disminuye sus capacidades de control. (Berrios, 2006). La Contraloría General de la República de Colombia dentro de sus funciones y misión publica tiene como objeto fiscalizar al estado. (Senado de la Republica de Colombia, 1993).

Para el informe de gestión del 2020-2021 de la contraloría entregada a la presidente de la cámara de Representantes (Contraloría General de la Republica, 2021)., se identificaron 766 hallazgos con incidencia fiscal, es decir, hechos o situaciones administrativas que se identifican como resultado de una evaluación de la gestión fiscal en donde que evidencia que se ha producido un daño patrimonial al Estado. (Congreso de Colombia, 2000)., de acuerdo con el Artículo 6°. Daño patrimonial al Estado.

Dichos hallazgos son fuentes e insumos relevantes para esta investigación, siendo que la contraloría es el ente encargo de vigilar y ejercer control fiscal sobre los recursos públicos. Una de sus actividad de vigilancia corresponde el identificar sobre precios en la adquisición de bienes públicos. Estas identificaciones también constituyen un hallazgo fiscal

**iii) Informes de Transparencia.** Informes extraoficiales como Monitor Ciudadano, entidad respaldada por organismos internacionales como Transparency International, ha recopilado y generado algunos informes relacionados a hechos de corrupción en las entidades públicas de Colombia. (Monitor Ciudadano de Colombia, 2021). En dicho informe, por ejemplo, se evidencia que el acto de corrupción que representa el más alto impacto y detrimento patrimonial es el asociado a Contratación Estatal.

![Figura 1 Distribución Porcentaje de Corrupción en Colombia](source: 1)  
*Figura 1 Distribución Porcentaje de Corrupción en Colombia*

Así mismo el tipo de corrupción más presente, es el de corrupción administrativa con un 49.4%. (Monitor Ciudadano de Colombia, 2021).

**iv) Precios del mercado privado.** Es función de los organismos estatales, durante la fase de estudios previos hacer un análisis de los precios del mercado antes de publicar la convocatoria para adquirir bienes o servicios. El Estado no tiene un respaldo jurídico que le permita para pagar más por un bien o servicio que los precios que manejan en el mercado regular. (Montoya, 2021). Es así como la identificación de los precios del mercado regular representa una referencia importante previo a la publicación de una convocatoria de adquisición.

Los precios del mercado se pueden adquirir gracias al acceso a la información digital provista por marketplace e e-commerce públicos como lo son: Mercado Libre, Cadenas de supermercados o herramientas como Google Shopping, la cual permite comparar precios de forma rápida y efectiva.

**v) Transparencia por Colombia.** Transparencia por Colombia es una organización sin ánimo de lucro cuyo propósito es integrar a la ciudadanía y liderar procesos para combatir la corrupción a nivel institucional. (Transparencia por Colombia, s.f.). Dicho organismo se caracteriza por generar artículos e informes que evidencian la corrupción administrativa a través de la contratación estatal. Sus publicaciones de “índices de Transparencia”, evidencia la creciente problemática de corrupción institucional.

**vi) Monitor ciudadano.** Monitor ciudadano publica constantemente informes asociados a casos de sobre precios y corrupción en general. Particularmente en cuanto a contratación estatal existen informes donde a través de análisis de datos, identifican hallazgos asociados y recomendaciones para combatir esta problemática.

**vii) Reportes de prensa y periodismo.** La prensa publica, periodistas independientes y pertenecientes a alguna editorial han fungido como veedores ciudadanos en la identificación y hallazgo de sobre precios en la contratación pública. El periodismo tiene una función social que lo hace participe no solo de la publicación de las noticias consecuencia de actos particulares, sino que este debe sumarse y comprometerse con los procesos sociales, la participación y la prevención. (Llobet, 2006).

**viii) Datos fiscales**
* **Volumen de Contratos y/o Convenios Interadministrativos.** Esta variable nos ayuda a establecer patrones de gasto a nivel regional o por sector. El origen de la variable proveniente directamente desde SECOP a través de las visualizaciones que la misma entidad provee. (Colombia Compra, 2024).

![Figura 2 Visualizaciones Contratación Colombia Compra Eficiente](source: 1)  
*Figura 2 Visualizaciones Contratación Colombia Compra Eficiente*

* **Precios del Mercado.** Los precios del mercado constituyen la principal fuente comparativa para establecer si una entidad está incurriendo en sobreprecios. Dicho precio como se mencionó previamente se extrae de Marketplace e ecommerce permitiendo generar indicadores de sobreprecios que se van a analizar.
* **Precios presupuestos por la entidad dentro del proceso de adquisición.** Corresponde a los precios previstos por las entidades a través de la plataforma SECOP II. Es importante resaltar la diferencia entre los precios unitarios para hacer la respectiva comparación, y el presupuesto total establecido dentro del proceso adquisitorio. Identificar el precio unitario para la respectiva comparación implica un reto tecnológico complejo debido a que en la mayoría de los casos dicha información se extrae de documentos escaneados y cargados en la plataforma SECOP II.
* **Precio contratado por la entidad dentro del proceso de adquisición.** Corresponde al precio definitivo con el cual la entidad ha realizado la contratación de la adquisición del bien. Este es el valor con el que se compara de acuerdo los precios del mercado regular si hubo o no sobreprecios.
* **Cantidad definida de bienes dentro del proceso de adquisición.** Corresponde a la cantidad de bienes a ser adquiridos dentro del proceso adquisitorio y que se publica dentro de la plataforma SECOP. Como se menciona anteriormente en la mayoría de los casos la información debe extraerse de documentos escaneados.
* **Presupuesto establecido dentro del proceso de adquisición.** Corresponde al valor total del presupuesto establecido por la entidad y que se publica a través de los campos de formularios en la plataforma SECOP y dentro de los documentos cargados. El dato sirve como referencia para validar por ejemplo si el bien a comparar hace parte de un grupo de bienes a adquirir adicionales que juntos suman el total del presupuesto, y evitar sesgos en el análisis y posibles hallazgos.

#### 4.3 Herramientas de Análisis

Tanto para el proceso de ETL como el de análisis de datos se usan herramientas tecnológicas como Python, el lenguaje más práctico para este tipo de análisis con su amplia gama de librería. También se utilizan técnicas de extracción como webscrapping, almacenamiento y procesamiento de datos en la nube y SQL para el consumo y requerimiento de variables.

---

### 5. Plataforma de Visualización de datos y análisis de compras públicas

Este trabajo de grado se realiza a través de la recolección de datos provenientes de fuentes oficiales que por ley deben generar informes fiscales publicados en portales como SECOP II, Colombia Compra Eficiente y bases de datos abiertas del gobierno. Todas estas fuentes secundarias facilitan el análisis cuantitativo del problema dentro del abordaje mixto, siendo, por ejemplo, los contratos publicados en SECOP II, la principal fuente de datos para la generación de reportes y tableros de visualización. A través del análisis de volúmenes de contratos publicados mensualmente, categorías de gasto, y otros indicadores se pueden identificar el porcentaje de contratos que presentan sobreprecios, tendencias y patrones de gasto e irregularidades en sectores específicos.

Así mismo, identificar el porcentaje de contratos que presentan sobreprecios facilita la identificación tendencias de gasto en sectores específicos. Por otro lado, se realiza un análisis documental a través de fuentes secundarias de informes de auditoría y estudios de casos de corrupción. Dichos informes son publicados por organismos oficiales como lo son la Contraloría General de la República, Transparencia por Colombia, y organismos internacionales como el Banco Mundial. También existen casos documentados de corrupción o sobreprecio en compras públicas facilitando la identificación de causas comunes de irregularidades y descubriendo ciertos patrones en actos de corrupción. Este enfoque cualitativo nos permite tener acceso a información rica y disponible y suficiente para generar un análisis robusto y abordar un mayor enfoque en el análisis técnico, aprovechando datos reales y análisis previos realizados por expertos y organismos en control fiscal.

#### 5.1. Descripción del sistema de compras públicas SECOP

SECOP es la principal fuente de datos para la presente investigación, ya que allí reposan y se publican todos los contratos públicos y compras realizadas por el estado en todas sus dependencias. Según el portal de Datos Abiertos (Ministerio de las Tecnologias y las Comunicaciones de Colombia, 2024)., desde el año 2019 a Diciembre de 2024 se han realizado más de 61.000 descargas en la plataformas de compras SECOP.

Los contratos publicados allí pueden oscilar entre 100 y 300 documentos diarios y nuevos procesos de contratación alrededor de 50 a 150 procesos.

##### 5.1.1 Generalidades de la plataforma

![Figura 3 Interfaz de búsqueda SECOP II](source: 1)  
*Figura 3 Interfaz de búsqueda SECOP II*

La plataforma cuenta con formulario de campos que facilita la búsqueda y filtra la información requerida por el usuario. Cualquier dependencia, organismo e institución estatal debe publicar el proceso de adquisición y contratación desde la apertura hasta la liquidación del contrato. Las fases definidas en la fase de contratación dentro de la plataforma SECOP se relacionan en la figura 4.

*Figura 4 Diagrama de Flujo Proceso de Adquisición Pública en SECOP II*

La plataforma pasa de ser un sistema publicación informativo a un sistema transaccional, (Colombia Compra, 2015)., ya que abarca muchas fases del proceso de contratación pública. Esta investigación solamente se centra en la característica informativa de la plataforma relacionada a publicaciones, documentación e informes asociados a precios. Por ejemplo, se quiere hacer una veeduría de los precios con los cuales la Secretaria Distrital de Bogotá ha contratado en el último trimestre del 2024. Para ello, se realiza el respectivo filtro, seleccionando la entidad correspondiente y las fechas establecidas.

Estos son algunos parámetros que ayudan filtrar la información en SECOP II (ver figura 5):

* **Datos del proceso:** Numero de proceso, descripción o región
* **Número del Proceso:** Caracteriza cada uno de los procesos de contratación y su codificación se determina por el nombre de la entidad, tipo de proceso de contratación, consecutivo y año de publicación (MJD-LP-001-2023).
* **Descripción:** Si se relaciona el título del proceso, u objeto de contratación, a través de este filtro se facilita y optimiza la búsqueda (Ej. software, agrícola, televisor, etc.)
* **Código UNSPSC:** United Nations Standard Products and Services Code UNSPSC - Código Estándar de Productos y Servicios de Naciones Unidas, es una metodología uniforme de codificación utilizada para clasificar productos y servicios fundamentada en un arreglo jerárquico y en una estructura lógica.

![Figura 5 Selección de Entidad Comprador SECOP II](source: 1)  
*Figura 5 Selección de Entidad Comprador SECOP II*

* **Región:** Ayuda a filtrar por departamento o región del país, facilitando la limitación geográfica.
* **Estado:** filtra el proceso en la clasificación actúa en la cual se encuentre el proceso: Publicado, Proceso en evaluación y observaciones, Proceso adjudicado y celebrado, Proceso Cancelado, y Obsoleto.
* **Fecha Publicación Desde:** Indica la fecha en la cual el proceso fue publicado y cargado en la plataforma SECOP.
* **Fecha Publicación Hasta:** Indica la fecha límite más reciente en la cual el proceso ha sido publicado y cargado en la plataforma SECOP.
* **Fecha de presentación de ofertas desde:** Establece la fecha inicial desde la cual un proponente puede presentar una oferta.
* **Tipo de proceso:** Permite filtrar los procesos de contratación clasificados según el régimen jurídico aplicable y la modalidad de contratación. Estos tipos de proceso son:
  * **Contratación Directa:** se utiliza cuando no se requiere un proceso competitivo. incluye: contratación de mínima cuantía, urgencia manifiesta, contratos interadministrativos, contratos de régimen especial.
  * **Licitación Pública.** Es el proceso más común para compras de alto valor, donde se busca la mayor pluralidad de oferentes.
  * **Selección Abreviada.** Un proceso más ágil que aplica a casos específicos como: contratos de menor cuantía, bienes y servicios de características técnicas uniformes.
  * **Concurso de Méritos.** Se utiliza para contratar servicios relacionados con estudios, diseños o proyectos que requieran conocimientos especializados.
  * **Subasta Inversa.** Procedimiento en el que los proponentes compiten ofreciendo el menor precio, aplicable a bienes y servicios de características uniformes.
  * **Acuerdos Marco de Precios (AMP).** Permite a las entidades públicas adquirir bienes o servicios previamente negociados por Colombia Compra Eficiente para obtener mejores condiciones.
  * **Mínima Cuantía.** Aplica para compras cuyo monto no excede el límite de mínima cuantía, según el presupuesto de la entidad.
  * **Contratación en Régimen Especial.** Para entidades que tienen regímenes de contratación particulares, como universidades públicas o empresas industriales y comerciales del Estado.
  * **Proceso de Concesión.** Utilizado para proyectos de infraestructura y otros donde se requiere la participación del sector privado en la financiación, operación o mantenimiento.
  * **Manifestación de Interés.** Invitación a los proveedores a expresar su interés en participar en un proceso futuro.
* **Fecha de apertura desde:** Aquí el sistema mostrará los procesos cuya fecha de apertura sea igual o posterior a esta fecha.
* **Fecha de apertura hasta:** Aquí el sistema incluirá los procesos cuya fecha de apertura sea igual o anterior a esta fecha.

Después de filtrada la información, la tabla de resultados debería verse de acuerdo con la figura 6.

![Figura 6 Resultados de búsqueda SECOP II](source: 1)  
*Figura 6 Resultados de búsqueda SECOP II*

Las columnas identificadas son:
* **País:** Establece el país de contratación.
* **Entidad Estatal:** Establece la entidad gubernamental, organismo o entidad estatal que publica el proceso.
* **Descripción:** Describe el tipo de producto o servicio a adquirir.
* **Fase Actual:** Detalla la fase actual en la cual se encuentra el proceso. (Presentación de Oferta, Fase de Ofertas)
* **Fecha de Publicación:** Indica la fecha en la que el proceso fue publicado.
* **Fecha de Presentación de Ofertas:** Indica la fecha límite en la cual los proponentes pueden presentar una oferta.
* **Cuantía:** Establece el valor o presupuesto del contrato
* **Estado:** Determina el estado en el cual se encuentra el proceso de adquisición (Publicado, Proceso en evaluación y observaciones, Proceso adjudicado y celebrado, Proceso Cancelado, y Obsoleto.)
* **Detalle:** Link de acceso para ver a detalle las oportunidades, identificar fechas importantes y descargar documentos.

Profundizando en el “Detalle” de cada oportunidad se visualiza la siguiente interfaz:

![Figura 7 Detalle Formulario Información](source: 1)  
*Figura 7 Detalle Formulario Información*

![Figura 8 Documentos Detalle convocatoria](source: 1)  
*Figura 8 Documentos Detalle convocatoria*

Es necesario resaltar que la interfaz presentada anteriormente es para el usuario final, ciudadanos y comunidad en general. La interfaz que usan las entidades y los organismos gubernamental es diferente.

#### 5.2. Prototipo de desarrollo de una plataforma web de visualización de grandes volúmenes de datos relacionados con compras públicas.

##### 5.2.1. Propuesta de Diseño

El siguiente es el diseño del mockup de la plataforma de visualización.

![Mockup Vista general de adquisiciones](source: 1)

![Mockup Detalles de proceso](source: 1)

![Mockup Búsqueda DataMonitor](source: 1)

![Mockup Discover Insights](source: 1)

![Mockup Analiza las compras efectivamente](source: 1)

![Mockup Potencia tu viaje de supervisión](source: 1)

![Mockup Casos de Hallazgos](source: 1)

![Mockup Simplifica tu trabajo](source: 1)

![Mockup Explora ahora y Footer](source: 1)

##### 5.2.2. Propuesta de Arquitectura

A continuación, se presenta la arquitectura propuesta para la formulación de la plataforma de visualización de datos.

![Figura 9. Arquitectura Propuesta](source: 1)  
*Figura 9. Arquitectura Propuesta*

###### Componentes Principales de la Arquitectura

**Fuentes de Datos:**
* SECOP y E-commerce
* Scraping con Selenium (Python) para extraer datos de estas fuentes.

**Ingesta y Almacenamiento de Datos:**
* Base de Datos PostgreSQL alojada en AWS para almacenar la información extraída.

**Procesamiento y ETL:**
* Scripts de limpieza y procesamiento ejecutados en Máquinas Virtuales (VMs) en AWS EC2.
* Procesamiento ETL periódico y persistente en estas VMs.

**Visualización y Consumo de Datos:**
* Plataforma de visualización en Dash (Python) alojada en la nube.
* Dash consulta la BD PostgreSQL con SQL queries para mostrar los datos procesados.

**Acceso a la Plataforma:**
* Se puede acceder desde cualquier navegador en PC o celular.

#### 5.3. Metodologías y herramientas de analítica e inteligencia artificial para establecer la evaluación de la gestión de compras del Estado

El proceso para análisis y visualización de datos sigue el ciclo Crisp-DM de IBM el cual abarca todas la fases del ciclo de vida del dato y contempla el problema de negocio. (IBM, 1999).

![Figura 10 Ciclo Crisp-DM](source: 1)  
*Figura 10 Ciclo Crisp-DM*

##### 5.3.1. Recopilación de Datos

###### 5.3.1.1. Recopilación de Datos de SECOP

La recopilación de datos relacionados a información sobre procesos de contratación estatal proviene principalmente de SECOP II. Como se estableció previamente, toda la información por ley debe ser cargada y publicada en dicha plataforma.

La recopilación llevada a cabo se ejecutará de la siguiente manera:
1. Acceso a la plataforma a través del link `https://community.secop.gov.co/STS/Users/Login/Index?SkinName=CCE`
2. Entrar a la sección “Buscar Procesos de Contratación”
3. Filtrar por el criterio de búsqueda de los procesos que se van a analizar (ej. Por región, por entidad, por fecha de publicación, por Estado, etc.)
4. A través de la técnica webscrapping se extraen y se alojan en una tabla todos los procesos del filtro aplicado en la búsqueda. Esta tabla sirve como registro para saber cuáles son los procesos licitatorios que son analizados posteriormente.
5. A través de la herramienta Selenium, se accede a cada uno de los links del selector Detalle encontrados en la búsqueda, se descargan todos los documentos del proceso, así como todos los campos del formulario del proceso y se registran en una tabla en Excel.
6. Toda la información que se ha ido recopilando, tanto los documentos como lo registros se almacenan en un repositorio en la nube para posteriormente acceder a la información para su respectivo análisis.

###### 5.3.1.2. Recopilación de Datos de Ecommerce y Marketplace

Los marketplace más comunes y que proveen la información más confiable para realizar el respectivo análisis del mercado suelen contar con RSS para acceder de forma automatizada a información específica.

Un RSS común es el de Mercado Libre, el cual ofrece a un API para buscar y extraer productos. (`https://developers.mercadolibre.com.co/es_ar/buscador-de-productos`).

El API debe configurase dentro del ambiente de desarrollo para buscar según el parámetro del ítem del cual se quiere extraer información, por ejemplo, televisores, computadores, videobeam, etc.

La información recopilada se alojará en una base de datos relacional en la nube llamada Postgres, para posteriormente ser consumida y hacer los análisis requeridos.

##### 5.3.2. Extracción de datos

La extracción de datos para documentos escaneados se realiza a través de herramientas tecnológicas como Python con sus respectivas librerías como PyPdf2, NumPy, Pandas, Matplotlib, Seaborn, Plotly, Scikit-Learn entre otros.

La mayor parte de la información del mercado regular será extraída directamente de los archivos XML y RSS provisto por los marketplace.

Toda la información se alojará en una base de datos en la base de datos PostgreSQL.

##### 5.3.3. Limpieza y Preparación de Datos

Esta fase del ciclo requiere la limpieza de los datos almacenados. Muchos de los datos contienen errores, valores duplicados o caracteres que puedan afectar las operaciones numéricas. Esta fase de preparación evita sesgos en el análisis y en la evaluación del modelo.

Algunos datos que pueden sesgar un modelo en esta investigación pueden ser, por ejemplo, las puntuaciones numérica que afecten el precio de un ítem. El proceso de limpieza se realiza con herramientas y librerías de procesamiento de datos como pandas de Python.

##### 5.3.4. Visualización de datos

La visualización de datos propuesta tiene la cualidad de ser interactiva con el usuario final. Es por esto por lo que se usa la herramienta Dash de la librería Plotly de Python. Dicha herramienta se integra con los lenguaje de programación HTML y CSS, facilitando al usuario el acceso a la visual desde cualquier navegador web o dispositivo móvil y la interacción con la herramienta.

A través de Dash se visualizan gráficos de diferentes categorías, los cuales evidencian el procesamiento previo para mostrar datos limpios, facilitando el filtrado de la información y tipos de variables.

##### 5.3.5. Pruebas Funcionales

La interfaz debe cumplir características visuales que faciliten su interpretación. Sin embargo, las funciones asignadas a la graficas, así como la interacción entre las tablas y la ejecución de modelos, debe funcionar de manera interrumpida. Por lo anterior, es imperativo realizar pruebas funcionales de código y de carga de datos para evitar afectación e interrupciones del sistema durante la etapa de producción.

##### 5.3.6. Análisis descriptivo

Desde esta fase se establece un análisis preliminar de la información recibida. Para esta investigación, el análisis descriptivo abarca visualizaciones preliminares como distribuciones de rubros, ejecución presupuestal o frecuencias de compra de ciertos bienes.

Así mismo, la visualización de datos para identificar patrones de gasto y sobrecostos. En cuanto al análisis cualitativo, se interpretan los hallazgos y categorización de resultados de los documentos.

###### 5.3.6.1. Análisis Comparativo Porcentual

Habiendo obtenido los datos tanto del precio del bien publicado por la entidad como los precios en el mercado se regular, la siguiente formula calcula el porcentaje de variación entre uno y otro de la siguiente manera:

*Ecuación 1. Análisis Comparativo Porcentual*

$$ID = \frac{PE - PM}{PM}$$

Donde:
* $ID$ = Indicador porcentual que evidencia la diferencia entre los precios.
* $PE$ = Precio contratado por la entidad dentro del proceso de adquisición.
* $PM$ = Precio del mercado.

###### 5.3.6.2. Promedio Total de variación de precios por entidad

Corresponde al promedio total de los porcentajes en la variación de precio por entidad.

*Ecuación 2. Promedio Total de Variación de precios por entidad*

$$\frac{ID_1 + ID_2 + \dots + ID_x}{ID_n}$$

Donde:
* $ID_x$ = cada uno de los indicadores de diferencia por contrato
* $ID_n$ = Cantidad total de indicadores diferencia.

###### 5.3.6.3. Identificación de patrones y anomalías

Después de procesar la información y generar un análisis descriptivo de los datos, se generan estadísticas y gráficas para detectar sobreprecios e irregularidades. Estos hallazgos son el resultado de aplicación de modelos para identificaciones de patrones y tendencias. En este paso se categorizan los resultados encontrados.

##### 5.3.7. Análisis de Contenido

Se realiza un análisis de contenido y análisis de literatura referente a los informes de las fuentes de datos descritas previamente. Dicho análisis permite encontrar hallazgos comunes, patrones y recomendaciones para combatir esta problemática. Se debe hacer una comparativa de los hallazgos identificados y contrastarlo con contenidos documentales asociados a informes y hallazgos fiscales similares.

Casos recurrentes de corrupción según los organismos de vigilancia y control mencionados previamente asociados a sobreprecios evidencian detrimentos patrimoniales, sobre todo en la compra de bienes relacionados con kits y conjuntos de productos de diferentes categorías.

Es así el caso de la investigación preliminar que llevó a cabo la CGR a la Alcaldía de Sincelejo derivado de presuntos sobreprecios y la entrega incompleta de algunos ítems que hacían parte de los 26.666 kits para la población vulnerable durante la pandemia. (Transparencia por Colombia, 2021).

Algunos otros hallazgos han sido producto de la investigación periodística en el territorio nacional. La problemática asociada a sobreprecios en la contratación pública muchas veces es difícil de rastrear debido a la complejidad que implica recopilar, extraer y analizar información relevante para investigar si hubo o no corrupción.

Sin embargo, en los casos en los que el ejercicio periodístico ha llevado una labor social, se han identificado hallazgos fiscales que han despertado la indignación colectiva.

El primer caso por mencionar se vincula a la Cámara de Comercio de Tunja en el año 2024, donde la Contraloría abre una investigación por un posible hallazgo fiscal relacionado con sobre precios asociados a la compra de unas pantallas LED las cuales fueron pagadas a un valor de 242.080.000 pesos colombianos, siendo que la cotización estaba en 76.180.000, lo que tipifica un detrimento fiscal de 169.210.449 pesos colombianos. (Díaz, 2024).

El siguiente caso se sitúa en la Gobernación de Santander en el año 2023, donde gracias a la investigación del diputado Ferley Sierra, se identificó un sobreprecio por la compra de juegos parqués por un valor de 795.000 pesos cada uno. Estos juegos pueden oscilar entre 20.000 y 50.000, sin embargo, el presunto acto de corrupción asociado a dicho sobreprecio generó ese detrimento patrimonial. (Múnera Zambrano, 2023).

Finalmente, un caso reciente en Colombia evidenció actos de corrupción en la compra de 40 carro tanques de agua para la alta Guajira por sobre costos de más de 7.760 millones en pesos para la adquisición de estos vehículos. Este hecho generó un detrimento que afectó no solo el patrimonio del Estado, sino la prestación del servicio para la población vulnerable en la Guajira. (Ortíz Fonnegra, 2024).

Todos los casos expuestos previamente son un referente que permiten al hallazgo identificado como resultado de la visualización de datos fiscales, tener un punto de partida para presentarlo ante una veeduría, prensa o directamente a un organismo de control.

##### 5.3.8. Informe de Resultados

Se realiza un informe con el resultado visual de los hallazgos identificados y antecedentes similares identificados por el análisis de contenido documental.

Dicho informe presenta la trazabilidad del proceso llevado a cabo para garantizar la transparencia y entendimiento claro de los pasos que se siguieron para la identificación del hallazgo.

#### 5.4. Plan de capacitación de apropiación

Se utiliza un marco teórico-práctico aplicado a la apropiación de la tecnología propuesta apoyado en documentación explicativa, tutoriales y manual de uso enfocado en ciudadanos del común o cualquier usuario particular. La metodología toma elementos del modelo Six Stage Training Model de McArdle (McArdle, 2015)., el aborda las fases Entendimiento de negocio, Análisis, Plan/Diseño, Desarrollo, Implementación y Evaluación.

![Figura 11 Six Stage Training Model](source: 1)  
*Figura 11 Six Stage Training Model*

Para la presente investigación se usa del modelo únicamente las fases de diseño y planeación de la capacitación, desarrollo de la capacitación, implementación de la capacitación y evaluación de la capacitación.

##### 5.4.1. Diseño y Planeación de la Capacitación

Se establecen los objetivos de capacitación no solo para la adopción del sistema, sino para la apropiación de la búsqueda de objetivos en la identificación de hallazgos fiscales: mostrar las funcionalidades y ventajas de la herramienta, adoptar el conocimiento asociado a la plataforma y asegurar que el público en general pueda identificar hallazgos con la plataforma.

##### 5.4.2. Desarrollo de la capacitación

Se desarrolla el contenido de la capacitación, se definen los temas y actividades principales, se establecen los mecanismos de enseñanza como sesiones informativas, infografías y tutoriales, y se desarrollan los materiales necesarios para la capacitación, así como un compendio de las instrucciones funcionales del sistema recopiladas durante la fase de desarrollo y prueba.

##### 5.4.3. Implementación

En esta etapa se imparte la ejecución de la capacitación. Cuenta con el constante acompañamiento al usuario final, de tal forma que se asegure una comprensión clara de la herramienta para la consecución de los objetivos del problema a resolver.

##### 5.4.4. Evaluación

En esta fase final se miden los resultados de la capacitación para validar el cumplimiento de los objetivos planteados en la primera fase. Al ser una herramienta de visualización se documentan las pruebas de usuario en el uso de esta, así como las métricas de identificación de hallazgos fiscales.

---

### Conclusiones y Recomendaciones

#### Conclusiones

A partir de la formulación del prototipo diseñado e integrado a una metodología eficiente de analítica de datos, se contempla la viabilidad y factibilidad de un proceso de seguimiento y fiscalización eficiente de compras públicas desde la plataforma SECOP II. Este prototipo contempla las necesidades de fiscalización al tiempo que optimiza la validación de información gracias al procesamiento de datos que ofrecen herramientas de analítica a partir de librerías de Python, SQL y otras técnicas de desarrollo.

Se evidencia la necesidad de abarcar muchos mas procesos de compras que sin herramientas tecnológicas, sería muy difícil contemplar. Así mismo permite a veedores, ciudadanía en general, y demás actores activos de vigilancia, gracias a un plan de capacitación y apropiación tecnológica, identificar hallazgos fiscales en la contratación pública para evitar futuros sobre precios, generando persuasión en los encargados de las compras públicas en entidades estatales.

La implementación de la herramienta en diferentes sectores y niveles del proceso de compras públicas ampliará la capacidad de identificación de hallazgos y permitirá a cualquier ciudadano ejercer su derecho y deber de vigilancia de una manera más eficiente y fácil de ejecutar.

#### Recomendaciones

El prototipo inicial facilita la identificación de las características generales de la solución, sin embargo, se recomienda realizar y ejecutar un desarrollo completo e implementación de la solución a gran escala, involucrando a todos los usuarios que participan en las diferentes fases de la contratación pública, desde la apertura hasta la vigilancia y cierre de los procesos.

El desarrollo de un sistema robusto y completo motivará la participación activa de todos los ciudadanos para identificar hallazgos fiscales a nivel nacional, logrando así la optimización de recursos públicos y disminución de los índices de corrupción y detrimentos patrimoniales.

Para concluir el diseño completo del sistema es necesario contar con los recursos y disponibilidad tecnológica adecuada para que el despliegue y producción involucre a la mayor cantidad de actores activos posibles (veedores, ciudadanos y organismos de control).Debido a la alta demanda de contratos por revisar, se requiere de un sistema robusto, que ejecute todas las funcionalidades de manera solvente, con un flujo de información e ingesta de datos continua y que se mantenga actualizada.

Si bien este estudio ha demostrado la viabilidad técnica del sistema, se recomienda avanzar en pruebas piloto con entidades gubernamentales para evaluar su impacto en procesos reales de contratación pública. La adopción de esta tecnología no solo optimizaría los mecanismos de control fiscal, sino que también fortalecería la confianza ciudadana en la gestión de los recursos públicos.

---

### Bibliografía

* Ahmi, A., & Simon, K. (2013). The utilisation of generalized audit software (GAS) by external auditors. Managerial Auditing Journal, 1.
* Alexopoulos, C., Lachana, Z., Androutsopoulou, A., Diamantopoulou, V., Charalabidis, Y., & Avgerinos, M. (2019). How Machine Learning is Changing e-Government. Obtenido de `https://dl.acm.org/doi/abs/10.1145/3326365.3326412`
* Amit, A., & Srivastava , S. (2019). A data visualization tool to benchmark government tendering process: Insights from two public enterprises. Benchmarking: An International Journa, 1. Obtenido de `https://www.emerald.com/insight/content/doi/10.1108/bij-06-2017-0148/full/html`
* Aparicio, M., & Costa, C. (2015). Data Visualization. Communication Design Quarterly Review, 1. Obtenido de `https://dl.acm.org/doi/abs/10.1145/2721882.2721883`
* Balestreri, M. (2018). Del Gobierno Electrónico Al Big Data: La Digitalización De La Gestión Pública En Colombia Frente Al Control Territorial (From Electronic Government to Big Data: Digitalizing Public Management in Colombia in the Face of Territorial Control). Obtenido de `https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3114480`
* Berrios, R. (2006). Government Contracts and Contractor Behavior. J Bus Ethics, 123.
* Bird, S., Klein, E., & Loper, E. (2009). Natural Language Processing with Python. oreilly.
* Bowen, P., Rose, R., & Pilkington, A. (2017). MIXED METHODS- THEORY AND PRACTICE. SEQUENTIAL, EXPLANATORY. International Journal of Quantitative and Qualitative Research Methods, 12.
* Burch, M., & Schmid, M. (2023). 3 Python, Dash, Plotly, and More. River Publishers. Obtenido de `https://ieeexplore.ieee.org/abstract/document/10266949`
* Colombia Compra. (2015). SECOP II. Obtenido de `https://www.colombiacompra.gov.co/ciudadanos/preguntas-frecuentes/secop-ii`
* Colombia Compra. (2024). Contratos y/o Convenios Interadministrativos. BOGOTÁ. Obtenido de `https://www.colombiacompra.gov.co/content/contratos-yo-convenios-interadministrativos`
* Congreso de Colombia. (1993). LEY 80 DE 1993 Por la cual se expide el Estatuto General de Contratación de la Administración PÚBLICA. Obtenido de `https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=304`
* Congreso de Colombia. (2000). Ley 610 de 2000. Bogotá: Función Pública. Obtenido de `https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=5725`
* Congreso de Colombia. (2015). LEY ESTATUTARIA 1757 DE 2015. Bogotá. Obtenido de `https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=65335`
* Congreso de Colombia. (Ley 1150 de 2007). 2007. Obtenido de `https://www.mincit.gov.co/ministerio/normograma-sig/procesos-estrategicos/direccionamiento-estrategico/leyes/ley-1150-de-2007-c.aspx`
* Congreso de la Republica de Colombia. (2014). La Ley 1712 de 2014, Ley de Transparencia y del Derecho de Acceso a la Información Pública Nacional y se dictan otras disposiciones. Obtenido de `https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=56882`
* Contraloría General de la Republica. (2021). Informe de Gestión 2020 a 2021. Bogotá. Obtenido de `https://www.camara.gov.co/sites/default/files/2021-08/5.1%20Informe.pdf?utm_source=chatgpt.com`
* Cordero Valdavida, M. (2018). Auditoría digital: el reto del siglo XXI. Presupuesto y Gasto Público. Obtenido de `https://www.ief.es/docs/destacados/publicaciones/revistas/pgp/91_09.pdf`
* Creswell, J. (2015). Research design: Qualitative, quantitative, and mixed methods approaches. Pearson Education.
* Díaz, A. (06 de Marzo de 2024). Denuncian malos manejos en la Camara de Comercio de Tunja. Wradio, pág. 1. Obtenido de `https://www.wradio.com.co/2024/03/06/denuncian-malos-manejos-en-camara-de-comercio-de-tunja/`
* Embarak, D. (2018). Data Analysis and Visualization Using Python. Apress. Obtenido de `https://link.springer.com/book/10.1007/978-1-4842-4109-7`
* Gomez Cabrera, A., Cortes Rey, J., Sanchez Rivera, O., Felizzola, H., & Gomez, C. (2024). Analizando la Calidad de los Datos Abiertos en la Contratación Pública Plataforma Colombiana en medio de la Revolución Digital. Pontificia Universidad Javeriana, 7. Obtenido de `http://dspace.aeipro.com/xmlui/handle/123456789/3697`
* IBM. (Marzo de 1999). Conceptos básicos de ayuda de CRISP-DM. Obtenido de `https://www.ibm.com/docs/es/spss-modeler/saas?topic=dm-crisp-help-overview`
* Llobet, L. (Julio de 2006). La función social del periodismo o periodismo social. Unirevista Vol 1, pág. 3.
* López, J. (2020). Experimentando con la pobreza: El Sisbén y los proyectos de analítica de datos en Colombia. 20. Obtenido de `https://www.researchgate.net/publication/339461530_Experimentando_con_la_pobreza_El_Sisben_y_los_proyectos_de_analitica_de_datos_en_Colombia`
* Marín Ochoa, B. (2018). El tratamiento del postconflicto colombiano por medio de infografías y visualizaciones de datos. Universidad Pontificia Bolivariana. Obtenido de `https://dialnet.unirioja.es/servlet/articulo?codigo=6363535`
* McArdle, G. (2015). Training Design and Delivery A Guide for Every Trainer, Training Manager, and Occasional Trainer. Mattoon: ATD Press Editorial.
* Ministerio de las Tecnologias y las Comunicaciones de Colombia. (04 de December de 2024). Datos Abiertos. Obtenido de `https://www.datos.gov.co/Gastos-Gubernamentales/SECOP-II-Procesos-de-Contrataci-n/p6dx-8zbt/about_data`
* Monitor Ciudadano de Colombia. (2021). Radiografia de los Hechos de Corrupción en Colombia. Obtenido de `https://www.monitorciudadano.co/about/`
* Montoya, M. (2021). Los sobreprecios: identificación y corrupción en la contratación estatal. Bogotá: Universidad de Caldas.
* Múnera Zambrano, M. (24 de Julio de 2023). `https://www.wradio.com.co/2024/03/06/denuncian-malos-manejos-en-camara-de-comercio-de-tunja/`. El Tiempo, pág. 1. Obtenido de `https://www.eltiempo.com/colombia/santander/parques-a-mas-de-700-mil-pesos-nueva-contratacion-en-la-gobernacion-789387`
* Muñoz, E. (15 de Septiembre de 2012). Herramientas Informaticas para Veedores. Obtenido de Alcaldía de Santiago de Cali: `https://www.cali.gov.co/cinterno/publicaciones/47892/herramientas_informticas_para_veedores_ciudadanos/`
* Open Contracting Data Standard. (s.f.). OCDS. Obtenido de `https://standard.open-contracting.org/latest/en/`
* Ortíz Fonnegra, M. (12 de Marzo de 2024). Caso carrotanques: Contraloría declaró impacto nacional y embargará a exjefes de UNGRD. El Tiempo, pág. 1. Obtenido de `https://www.eltiempo.com/justicia/investigacion/caso-carrotanques-contraloria-declaro-impacto-nacional-y-embargara-a-exjefes-de-ungrd-3324081`
* Pérez Bellido, R. (2024). METEOROLÓGICOS USANDO PLOTLY DASH AUTOMATIZACIÓN DE LA GESTIÓN DE DATOS. UNALM, 17.
* Rangel Carrillo, A., & Osorio Sanabria, M. (2023). Exploración sobre datos gubernamentales abiertos y big data desde una perspectiva de calidad. Obtenido de `https://revistas.unab.edu.co/index.php/rcc/article/view/4389`
* Sadiku, M., Adebowale, S., & Musa, S. (2016). Data Visualization. International Journal of Engineering Research And Advanced Technology, 12. Obtenido de `https://www.researchgate.net/profile/Adebowale-Shadare/publication/311597028_DATA_VISUALIZATION/links/5851945608aef7d0309f20a7/DATA-VISUALIZATION.pdf`
* Senado de la Republica de Colombia. (1993). Ley 106 de 1993. En D. A. Pública. Obtenido de `https://www.funcionpublica.gov.co/eva/gestornormativo/norma_pdf.php?i=3425`
* Sloan, K. (2019). Python, PyGame and Raspberry Pi Game Development. Apress. Obtenido de `https://link.springer.com/chapter/10.1007/978-1-4842-2517-2_2`
* Tashakkori, A., & Teddlie, C. (2010). Handbook of Mixed Methods in Social and Behavioral Research - Principles of Mixed Methods.
* Teja Gurram, R. (2024). LEVERAGING ETL AND VISUALIZATION FOR PREDICTIVE ANALYTICS IN RETAIL. International Journal of Computer Engineering and Technology (IJCET, 2.
* Transparencia Colombia. (2000). Estudio sobre la figura de la veeduría ciudadana. CUADERNOS DE TRANSPARENCIA, 58.
* Transparencia por Colombia. (2021). Quinto informe de seguimiento A la contratación pública en la emergencia COVID-19. Bogotá: CORPORACIÓN TRANSPARENCIA POR COLOMBIA.
* Transparencia por Colombia. (2024). Recomendaciones para el fortalecimiento del proyecto de ley de veedurias. Transparencia Colombia, 4.
* Transparencia por Colombia. (s.f.). Transparencia por Colombia. Recuperado el 16 de Diciembre de 2024, de `https://transparenciacolombia.org.co/`
* Ushahidi. (s.f.). Ushahidi empowers people through citizen-generated data to develop solutions that strengthen their communities. Obtenido de USHAIDI: `https://www.ushahidi.com/`
* Valencia Duque, F. J., Tamayo Arias, J. A., & Osorio López, K. (2015). Tecnologías de información y comunicaciones en el Control Fiscal Colombiano. Escuela Superior de Administración Pública, 3.
* Vassiliadis, P., Spiros, S., & Alkis, S. (2023). The History, Present, and Future of ETL Technology. DOLAP. Obtenido de `https://www.cs.uoi.gr/~pvassil/publications/TALKS/2023_03_dolap_tota/23DOLAP_TestOfTimeAward_CEUR-CR.pdf`
* Yuan, S. (2023). Design and Visualization of Python Web Scraping Based on Third-Party Libraries and Selenium Tools. Wuhan: Academic Journal of Computing & Information Science.