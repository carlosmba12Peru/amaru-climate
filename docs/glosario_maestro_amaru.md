# 📚 GLOSARIO MAESTRO DE TÉRMINOS: GOVTECH, CIBERSEGURIDAD, IA Y MARCO TÉCNICO HIDROCLIMÁTICO

**Documento Doctrinal y Guía Terminológica Homologada**  
**Proyecto:** Sistema AMARU (AMARU-FEN & AMARU-CHIRI)  
**Titular:** MERCADOS PLAZA DEL PERU S.A.C.  
**Arquitecto de Software:** Carlos Baños Díaz, MBA  
**Fecha:** Septiembre 2026  
**Homologación Normativa:** Ley Nº 31814 (IA y Soberanía Humana), Ley Nº 29733 (LPDP), D.S. Nº 124-2026-PCM, D.S. Nº 234-2025-EF (FONDES 1,891 Distritos), D.S. Nº 122-2024-PCM (PMHF), Directivas INDECI / SINPAD, Memoria CGR Cap. 5, ISO/IEC 42001, NIST AI RMF 1.0, FIPS 180-4, FIPS 140-3.

---

## 🏛️ PARTE I: GOVTECH, GOBERNANZA ANTICIPATORIA Y MARCO NORMATIVO PERUANO

### 1. FONDES (Fondo para Intervenciones ante la Ocurrencia de Desastres Naturales)
* **Entidad Administradora:** Ministerio de Economía y Finanzas (MEF) y Secretaría Técnica INDECI.
* **Definición:** Fondo intangible creado por la Ley Nº 30458 para financiar proyectos de inversión pública de mitigación, reconstrucción y rehabilitación de infraestructura dañada por fenómenos naturales de gran magnitud.
* **Articulación con AMARU:** AMARU integra el maestro de **1,891 distritos priorizados bajo el Decreto Supremo Nº 234-2025-EF**, proveyendo el sustento pericial técnico necesario para la priorización y ejecución presupuestal preventiva antes del colapso del cauce.

### 2. Programa Presupuestal PP 0068 (PREVAED / GRD)
* **Definición:** Categoría presupuestaria estratégica del MEF dedicada a la *"Reducción de la Vulnerabilidad y Atención de Emergencias por Desastres"*.
* **Articulación con AMARU:** El sistema formula *Triggers Biofísicos Objetivos* que habilitan a los alcaldes y comités de defensa civil a ejecutar las partidas del PP 0068 de manera inmediata sin temor a observaciones de la Contraloría por gasto injustificado.

### 3. Ficha EDAN Perú v2.0 (SINPAD / INDECI)
* **Definición:** Formulario oficial estandarizado de *Evaluación de Daños y Análisis de Necesidades* que administran el INDECI y los Centros de Operaciones de Emergencia (COEL/COER) en la plataforma SINPAD.
* **Formulario 2A (Padrón Preliminar):** Registra el censo de familias damnificadas y afectadas, infraestructura pública colapsada y necesidades de bienes de ayuda humanitaria (BAH).
* **Módulo Satélite AMARU:** [`core/modulo_satelite_edan_cgr.py`](file:///d:/curso-gcp-google-adk-01/lab2/core/modulo_satelite_edan_cgr.py) precarga automáticamente los datos hidroclimáticos y bloquea el envío al SINPAD hasta que un Comité Humano Tripartito aprueba y firma el informe.

### 4. Principio de Soberanía Humana (Ley Nº 31814 - Human-in-the-Loop)
* **Mandato Legal:** Ley que promueve el uso de la Inteligencia Artificial en favor del desarrollo económico y social del país (reglamentada por D.S. Nº 085-2024-PCM).
* **Doctrina AMARU:** AMARU opera estrictamente como un **Sistema de Soporte a la Decisión Técnica (DSS)**. Ninguna IA toma decisiones de evacuación (SISMATE), contratación directa o ejecución de gasto público. La soberanía y la potestad decisoria corresponden exclusivamente a las autoridades humanas.

---

## 🔒 PARTE II: CIBERSEGURIDAD, ENVELOPE ENCRYPTION Y CRIPTOGRAFÍA ZERO-PII

### 5. Tokenización Zero-PII en Acción Humanitaria
* **Marco:** Estándares del Comité Internacional de la Cruz Roja (CICR) y Ley Nº 29733 (Protección de Datos Personales).
* **Mecanismo AMARU:** Antes de enviar datos del padrón de víctimas a los agentes de IA o nubes públicas, se ejecuta una función hash irrepetible:
  $$\text{Token} = \text{HMAC-SHA256}(\text{DNI} \parallel \text{Salt}_{\text{municipal}}, K_{\text{soberana}})$$
* **Propósito:** Previene que listas con nombres y ubicaciones de familias vulnerables queden expuestas a mafias de tráfico o pillaje en zonas de catástrofe.

### 6. Cifrado de Sobre (Envelope Encryption - KEK / DEK)
* **Estándar:** FIPS 140-3 Nivel 3 y NIST SP 800-57.
* **Mecanismo:** Los registros de llamadas de auxilio de [`agents/agente_voz_vapi.py`](file:///d:/curso-gcp-google-adk-01/lab2/agents/agente_voz_vapi.py) y el búfer de resiliencia off-grid se cifran en reposo con claves efímeras **AES-256-GCM (DEKs)**, las cuales a su vez se almacenan protegidas por claves maestras **KEK** custodiadas en módulos de seguridad de hardware en la nube (KMS HSM).

### 7. Sellado Criptográfico FIPS 180-4 (SHA-256)
* **Definición:** Generación de una huella digital matemática de 256 bits sobre cada reporte de aforo o índice pericial (`IPH-FEN`, `IRCE-FEN`, `ISH-CHIRI`) emitido por [`core/storage_vault.py`](file:///d:/curso-gcp-google-adk-01/lab2/core/storage_vault.py).
* **Propósito:** Garantiza que el informe no ha sido alterado ni manipulado post-facto, brindando plena validez pericial ante auditorías forenses de la Contraloría General de la República (CGR).

### 8. Defensas OWASP Top 10 para LLM (LLM01 / LLM06)
* **LLM01 (Prompt Injection Defense):** Filtro de sanitización en [`core/file_sanitizer.py`](file:///d:/curso-gcp-google-adk-01/lab2/core/file_sanitizer.py) que neutraliza cargas maliciosas embebidas en reportes ciudadanos o archivos de audio.
* **LLM06 (Sensitive Information Disclosure):** Aislamiento de ventanas de contexto en [`core/circuit_breaker.py`](file:///d:/curso-gcp-google-adk-01/lab2/core/circuit_breaker.py) para impedir la fuga de directorios de Defensa Civil.

---

## 🤖 PARTE III: INTELIGENCIA ARTIFICIAL Y ARQUITECTURA MULTI-AGENTE

### 9. Enjambre Multi-Agente Desacoplado (Sovereign Swarm Architecture)
* **Definición:** Arquitectura distribuida donde cada agente autónomo tiene responsabilidades estrictamente acotadas (Agente Georriesgo, Agente Memoria Histórica, Agente Crioclimático, Agente Normativo, Agente Vigía OSINT) orquestados centralmente por [`core/orchestrator.py`](file:///d:/curso-gcp-google-adk-01/lab2/core/orchestrator.py).

### 10. Física Determinista vs. Cajas Negras (Explainable AI)
* **Principio:** Los modelos probabilísticos o generativos (LLMs) son propensos a alucinaciones estadísticas inaceptables en gestión de riesgos de vida o muerte. AMARU utiliza **ecuaciones físicas deterministas y auditables** (Manning para hidrodinámica, Stefan-Boltzmann para radiación nocturna) y emplea los LLMs exclusivamente para la síntesis de lenguaje natural y triaje.

### 11. Proceso de Jerarquía Analítica de Saaty (AHP)
* **Definición:** Método multicriterio matemático empleado en el cálculo del `IRCE-FEN` para ponderar factores de amenaza, vulnerabilidad y capacidad de respuesta.
* **Control de Consistencia:** Exige que la Razón de Consistencia matemática cumpla estrictamente $CR \le 0.10$, descartando juicios subjetivos o inconsistentes.

### 12. Cortacircuitos Algorítmico (Algorithmic Circuit Breaker)
* **Definición:** Mecanismo de seguridad en [`core/circuit_breaker.py`](file:///d:/curso-gcp-google-adk-01/lab2/core/circuit_breaker.py) que aísla de inmediato cualquier sensor o API que entregue datos física o matemáticamente imposibles (ej. precipitación negativa o temperaturas absurdas).

---

## 🌊❄️ PARTE IV: MARCO CIENTÍFICO HIDROCLIMÁTICO Y CRIOCLIMÁTICO

### 13. IPH-FEN (Índice de Previsión de Huaicos ante El Niño)
* **Definición:** Indicador físico de desborde y transporte de sedimentos que combina el esfuerzo cortante de fondo ($\tau = \gamma R S$), la rugosidad de Manning ($n$), la pendiente del cono aluvial y el tiempo de concentración de Kirpich ($T_c$).

### 14. IRCE-FEN (Índice de Riesgo Compuesto de Emergencia)
* **Definición:** Índice paramétrico que cruza la amenaza marina (TSM Niño 1+2), los avisos meteorológicos de SENAMHI y la densidad poblacional vulnerable para los 1,891 distritos nacionales.

### 15. ISH-CHIRI (Índice de Severidad de Heladas)
* **Definición:** Modelo térmico de La Niña que predice el desplome bajo cero ($<-15^\circ\text{C}$ a $-25^\circ\text{C}$) mediante balances nocturnos de radiación de onda larga (Stefan-Boltzmann), sensación térmica por viento (*Wind-Chill Index*) y estancamiento de aire gélido (*Cold Air Pooling*) en cuencas altoandinas.

### 16. El Reloj del FEN & Ventana de Oro de Noviembre
* **Definición:** Cronómetro polar de 360° que delimita el período crítico de verano (Diciembre-Marzo) e identifica **Noviembre como el último mes táctico** para descolmatar ríos y reforzar bocatomas antes de las avenidas fluviales.

### 17. El Reloj de La Niña & Ventana de Oro de Abril
* **Definición:** Cronómetro polar táctico para heladas y friajes que delimita el arco glacial (Mayo-Julio) e identifica **Abril como la ventana mandatoria** para vacunar alpacas gestantes, distribuir forraje y adecuar térmicamente escuelas rurales bajo directivas PREVAED.

### 18. Nodos Telemétricos IoT Ultrasónicos No Invasivos (AMARU-NODE V1)
* **Definición:** Estaciones hidrométricas autónomas con panel solar, batería LiFePO4, sensor ultrasónico IP67 y telemetría LoRaWAN/Celular montadas en barandas de puentes por encima del nivel de agua sin obras civiles invasivas.
