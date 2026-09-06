# FICHA TÉCNICA: NODO DE TELEMETRÍA HIDROLÓGICA IoT NO INVASIVO (AMARU-NODE V1)

**Proyecto:** AMARU - Inteligencia Climática Anticipatoria  
**Programa:** WFP Innovation Accelerator x AFCIA LAC 2026  
**Clasificación:** Documento Técnico Reservado / Sala de Mando C2  
**Fecha:** Septiembre 2026  
**Ubicación de Despliegue Piloto:** 4 puntos críticos de aforo (cuenca Cañete / Piura: puentes y compuertas de derivación)

---

## 1. DESCRIPCIÓN GENERAL DEL DISPOSITIVO

El **AMARU-NODE V1** es una estación de telemetría hidrométrica de bajo costo, no invasiva y energéticamente autónoma, diseñada para monitorear en tiempo real la variación de la lámina de agua y la velocidad de ascenso del nivel fluvial en canales de riego, compuertas de derivación y puentes vehiculares rurales.

A diferencia de las estaciones hidrológicas tradicionales (que requieren pozas de amortiguación o sensores sumergibles susceptibles de ser arrastrados o colmatados por sedimentos y troncos durante huaicos), el nodo opera **completamente fuera del agua**, montado en la superestructura de puentes o estribos mediante medición por eco ultrasónico o radar de pulso guiado.

```
                  ┌─────────────────────────────────────────┐
                  │   PANEL SOLAR 15W + GABINETE IP67       │
                  │   - MCU ESP32-S3 Ultra Low Power        │
                  │   - Batería LiFePO4 (3.2V / 6000 mAh)   │
                  │   - Módulo 4G/LTE-M + Antena VHF/LoRa   │
                  └────────────────────┬────────────────────┘
                                       │ (Viga / Puente)
                                       ▼
                             ┌───────────────────┐
                             │ SENSOR ULTRASÓNICO│
                             │ (Haz cónico 15°)  │
                             └─────────┬─────────┘
                                       │  ((( Pulso )))
                                       ▼
                 ~~~~~~~~~~~~~~~~~~ Nivel de Agua ~~~~~~~~~~~~~~~~~~
                                 Cauce del Río / Canal
```

---

## 2. ESPECIFICACIONES TÉCNICAS DE HARDWARE

### 2.1. Sensor de Medición de Nivel (No Invasivo)
* **Tecnología:** Transductor ultrasónico sellado industrial con compensación automática de temperatura.
* **Modelo Base de Referencia:** Sensores tipo MaxBotix MB7389 (WR30) o transductor ultrasónico IP68 industrial (ej. A02YYUW / JSN-SR04T grado industrial).
* **Rango de Medición:** 0.30 m hasta 7.50 m (opción extendida hasta 10 m para puentes de gran gálibo).
* **Resolución:** 1 mm.
* **Precisión:** ± 1% del valor medido.
* **Ángulo de Haz:** Cónico estrecho (15° a 20°), minimizando falsos ecos producidos por vegetación marginal o pilas de puente.
* **Frecuencia Acústica:** 40 kHz a 42 kHz.

### 2.2. Unidad de Control y Procesamiento (MCU)
* **Microcontrolador:** ESP32-S3 de ultra-bajo consumo con doble núcleo Xtensa® de 32 bits a 240 MHz.
* **Memoria:** 8 MB PSRAM / 16 MB Flash SPI para almacenamiento local de datos tipo "caja negra" (registro histórico de hasta 180 días sin conexión).
* **Ciclo de Operación (Sleep Duty Cycle):**
  * *Modo Estiaje / Rutina:* Despierta cada 15 minutos, realiza ráfaga de 10 mediciones, descarta valores atípicos (filtro mediana), transmite telemetría y vuelve a *Deep Sleep* (consumo < 15 µA).
  * *Modo Alerta / Crecida Activa:* Si el gradiente $\Delta h / \Delta t$ supera 10 cm en 15 minutos, el nodo conmuta automáticamente a **muestreo continuo cada 2 minutos** y transmisión inmediata.

### 2.3. Comunicaciones y Telemetría Multicapa
* **Capa 1 (Celular Primaria):** Módulo Quectel BG95-M3 o SIMCom SIM7000G multibanda (LTE-M / NB-IoT / fallback 2G GPRS) con soporte de tarjeta nano-SIM multired (compatible con Claro, Movistar, Entel, Bitel).
* **Capa 2 (Respaldo en Baja/Nula Conectividad):**
  * Transmisión por **SMS estándar** (payload comprimido de 32 bytes con marca de tiempo, nivel en milímetros, voltaje de batería y suma de verificación CRC-16).
  * Enlace por radiofrecuencia local **LoRa / VHF (433/915 MHz)** hacia repetidor o receptor comunitario en casa comunal de la Comisión de Regantes (alcance de 5 a 12 km con línea de vista).

### 2.4. Sistema de Alimentación Autónomo
* **Panel Fotovoltaico:** Módulo solar monocristalino de 15 W / 18 V con recubrimiento ETFE para resistencia a intemperie.
* **Batería:** Acumulador LiFePO4 (Fosfato de Hierro y Litio) de 3.2V / 6000 mAh (más de 2,000 ciclos de carga útil y estabilidad térmica desde -10 °C hasta +60 °C).
* **Autonomía sin Sol:** Mínimo 14 días continuos en modo alerta (nubosidad persistente o lluvias continuas).

### 2.5. Gabinete y Resistencia Mecánica
* **Grado de Protección:** Gabinete estanco de policarbonato IP67 / NEMA 4X resistente a radiación UV y corrosión salina.
* **Fijación:** Brazo en voladizo de acero galvanizado en caliente con pernos de anclaje expansivos de 3/8", protegido con jaula antivandálica y candado de seguridad.

---

## 3. ESTRUCTURA DEL PAYLOAD DE DATOS (PROTOCOLO LIGERO)

Para optimizar costos de transmisión satelital/SMS y operar con conectividad inestable, el nodo emite paquetes binarios de longitud fija (32 bytes):

| Campo | Tipo de Dato | Tamaño | Descripción |
| :--- | :---: | :---: | :--- |
| `DEVICE_ID` | `uint16` | 2 bytes | Identificador único del sensor (0 a 65535). |
| `TIMESTAMP` | `uint32` | 4 bytes | Tiempo Unix UTC (segundos). |
| `DISTANCE_MM` | `uint16` | 2 bytes | Distancia sensor-superficie de agua (0 a 10,000 mm). |
| `WATER_LEVEL_CM` | `uint16` | 2 bytes | Nivel calibrado respecto a cota cero de solera. |
| `DELTA_H` | `int16` | 2 bytes | Variación de nivel en los últimos 15 min (+ / - cm). |
| `TEMP_C` | `int8` | 1 byte | Temperatura ambiente (°C) para compensación sonora. |
| `BATT_MV` | `uint16` | 2 bytes | Voltaje de batería (mV) para monitoreo de salud. |
| `STATUS_FLAGS` | `uint8` | 1 byte | Banderas de alerta (crecida, vibración, sabotaje). |
| `CRC16` | `uint16` | 2 bytes | Suma de comprobación de integridad de datos. |

---

## 4. PRESUPUESTO UNITARIO REFERENCIAL (4 NODOS PILOTO)

Dentro de la partida de **USD 12,000 para Equipamiento IoT y Sensores** del presupuesto del Sprint WFP, el costo desglosado por nodo es el siguiente:

| Componente | Especificación | Costo Unitario (USD) | Subtotal 4 Nodos |
| :--- | :--- | :---: | :---: |
| **Sensor de Nivel** | Transductor ultrasónico IP68 industrial de haz estrecho | $180 | $720 |
| **Placa Base y MCU** | ESP32-S3 + memoria industrial + circuito de carga MPPT | $90 | $360 |
| **Módulo Comunicación** | Modem LTE-M/NB-IoT + antena dipolo + transceptor LoRa/VHF | $85 | $340 |
| **Sistema Energía Solar** | Panel solar 15W + batería LiFePO4 + cables marinos | $75 | $300 |
| **Gabinete y Soporte** | Caja IP67 + brazo voladizo galvanizado + herrajes | $120 | $480 |
| **Consumibles e Instalación** | SIM cards M2M anuales, selladores, pruebas en banco | $50 | $200 |
| **Unidades de Respaldo** | 1 nodo completo de repuesto en caso de impacto | $550 | $550 |
| **Pasarelas de Enlace / Gateway** | 2 concentradores locales LoRa-4G en locales comunales | $300 | $600 |
| **Logística y Calibración en Campo** | Brigada de montaje, pruebas de eco y calibración topográfica | - | $7,450* |
| **TOTAL PARTIDA IoT WFP** | **Despliegue integral de 4 puntos de aforo piloto** | - | **$11,000** |

*\*El remanente de la partida cubre calibraciones topográficas de campo con estación total para definir la cota cero de solera de cada cauce.*

---

## 5. INTEGRACIÓN CON EL MOTOR AMARU

Los datos recibidos por el nodo ingresan directamente al **Agente Hidroclimatológico** de AMARU:
1. El agente compara el nivel reportado con las curvas H-Q (Gasto vs. Tirante) de la sección calibrada.
2. Si el tirante sobrepasa el umbral de desborde o la fuerza tractiva crítica calculada para el lecho de la quebrada, se dispara la alerta temprana.
3. Se genera de inmediato el mensaje automatizado de emergencia hacia el canal de Telegram, la pasarela de SMS multired y los boletines de radio comunitaria VHF.
