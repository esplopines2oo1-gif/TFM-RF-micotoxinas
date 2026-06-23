#  Random Forest: Predicción de Micotoxinas en Perú bajo Escenarios de Cambio Climático

> Trabajo de Fin de Máster — Máster en Bioinformática y Bioestadística (UOC · Universitat de Barcelona)

---

##  Tabla de Contenidos

- [Descripción del Proyecto](#-descripción-del-proyecto)
- [Contexto y Motivación](#-contexto-y-motivación)
- [Micotoxinas Analizadas](#-micotoxinas-analizadas)
- [Datos](#-datos)
- [Arquitectura del Modelo](#-arquitectura-del-modelo)
- [Escenario Climático](#-escenario-climático)
- [Uso](#-uso)
- [Limitaciones y Trabajo Futuro](#-limitaciones-y-trabajo-futuro)
- [Licencia](#-licencia)

---

##  Descripción del Proyecto

Las micotoxinas son metabolitos tóxicos producidos por hongos de los géneros *Aspergillus*, *Penicillium* y *Fusarium*. Su presencia en cultivos representa un riesgo creciente para la seguridad alimentaria. El cambio climático, con el aumento de temperaturas, favorece la proliferación de estos hongos.

Este proyecto desarrolla **dos modelos predictivos basados en Random Forest** aplicados a datos reales de micotoxinas proporcionados por la empresa **BIŌNTE Animal Nutrition**:

1. **Clasificador (`RandomForestClassifier`)** — predice la *probabilidad de contaminación* para cada toxina.
2. **Regresor (`RandomForestRegressor`)** — predice la *concentración esperada en ppb* en muestras contaminadas.

Ambos integran variables climáticas históricas de **Open-Meteo** y una **variable de riesgo biológico** basada en rangos óptimos de temperatura y humedad de cada hongo. Las proyecciones se realizan bajo un escenario de **+1,6 °C para 2031**.

El código es **genérico, modular y reproducible**: cambiando el filtro de país, el análisis puede replicarse para cualquier otro país del dataset.

---

## Contexto y Motivación

El punto de partida es el impacto del cambio climático en la seguridad alimentaria. El aumento de temperaturas y la alteración de los patrones de humedad favorecen la proliferación de hongos toxigénicos.

Las micotoxinas afectan a la cadena alimentaria de dos formas:
- **Salud animal**: presentes en cereales para piensos, causan pérdidas productivas y mortalidad.
- **Salud humana**: se transfieren a través de productos de origen animal o por consumo directo (*carry-over*).

El calentamiento global favorece la evolución de cepas más termotolerantes, ampliando la capacidad de los hongos de infectar humanos, animales y plantas.

---

##  Micotoxinas Analizadas

| Código | Nombre completo | Hongo productor | Clasificación IARC |
|--------|----------------|-----------------|-------------------|
| **AFB1** | Aflatoxina B1 | *Aspergillus flavus / A. parasiticus* | Grupo 1 (carcinógeno) |
| **FUM** | Fumonisinas (B1, B2) | *Fusarium verticillioides / F. proliferatum* | Grupo 2B |
| **DON** | Deoxinivalenol | *Fusarium graminearum* | No clasificado |
| **ZEA** | Zearalenona | *Fusarium graminearum / F. culmorum* | Grupo 3 |
| **T-2/HT-2** | Toxinas T-2 y HT-2 | *Fusarium langsethiae / F. sporotrichioides* | No carcinogénico |
| **OTA** | Ocratoxina A | *Aspergillus ochraceus / Penicillium verrucosum* | Grupo 2B |

> Las constantes biológicas de temperatura y humedad se usan en el código para calcular la variable `riesgo_total`, una función de campana que cuantifica qué tan cerca están las condiciones ambientales del óptimo de cada hongo.

---

##  Datos

### Dataset de micotoxinas (BIŌNTE)
Datos reales de **374 muestras de Perú** (noviembre 2023 – diciembre 2025). Incluye: mes de análisis, matriz alimentaria, país, especie animal y concentraciones en ppb de las seis micotoxinas.

### Dataset climático (Open-Meteo)
Datos históricos desde 1985 para **7 ubicaciones representativas de Perú** (Lima, Trujillo, Tacna, Cusco, Huaraz, Iquitos, Pucallpa).

**Variables extraídas:** temperatura, humedad relativa y precipitación. Los datos se agregan mensualmente y se calculan variables de rezago (lag1, lag2, lag3) para evitar *data leakage*.

---

##  Arquitectura del Modelo

### Cuatro scripts, dos pipelines

**Script 1: Creación dataset micotoxinas** (limpieza de archivos Excel de BIŌNTE)

**Script 2: Creación dataset clima** (API Open-Meteo → agregación de datos)

Ambos flujos confluyen en:

- Fusión de datasets (left join por año, mes y ciudad)
- Imputación de valores NaN (media histórica por ciudad)
- Cálculo de la variable `riesgo_total`
- Encoding con LabelEncoder (variables categóricas: Matriz, Ciudad)

A partir de aquí, el pipeline se divide en dos ramas:

---

**Rama 1: Script 3 - RF Clasificación**

- `RandomForestClassifier`
- Variable objetivo: contaminada (0/1)
- 6 modelos independientes (uno por toxina)
- División 70/30 estratificada
- Validación cruzada 5-fold con métrica AUC-ROC
- `class_weight='balanced'`
- `oob_score=True`

**Rama 2: Script 4 - RF Regresión**

- `RandomForestRegressor`
- Variable objetivo: concentración en ppb
- 6 modelos independientes (uno por toxina)
- División 70/30
- Validación cruzada KFold 5 pliegues con métricas RMSE y R²
- `n_jobs=-1`
- `oob_score=True`

---

Ambas ramas finalizan con:

**Proyección +1,6 °C 2026→2031**

---

### Hiperparámetros comunes

```python
n_estimators = 200
max_depth = 8
min_samples_leaf = 10   # clasificador
min_samples_split = 10  # regresor
random_state = 42
oob_score = True
```
---

##  Escenario Climático

El escenario simula un **aumento lineal de +1,6 °C** desde 2025 hasta 2031, coherente con:

- **IPCC AR6 (2021)** — trayectoria SSP2-4.5 para Sudamérica tropical.
- **SENAMHI (2022)** — *Escenarios climáticos en Perú para el año 2030*.

Para cada año (2026–2031):

1. Se calcula el incremento acumulado proporcional
2. Se suma el delta a las columnas de temperatura
3. Se recalcula la variable `riesgo_total` con las nuevas temperaturas

---

## Limitaciones del trabajo

### Limitaciones identificadas
1. Tamaño muestral reducido (374 registros totales). T2/HT2 tiene solo 37 muestras.

2. Variables insuficientes para regresión. La concentración exacta depende de factores locales no recogidos (almacenamiento, tiempo de exposición).

3. Colinealidad potencial de riesgo_total con temperatura y humedad.

4. Escenario climático simplificado. Incremento uniforme sin modelar variabilidad interanual.

5. Datos limitados a dos años (2024–2025).

## Líneas de trabajo futuro

1. Ampliar el dataset con muestras de otros años y países.

2. Añadir variables: tipo de cultivo, prácticas de almacenamiento.

3. Explorar XGBoost o Gradient Boosting.

4. Aplicar transformación logarítmica a concentraciones.

5. Integrar proyecciones CMIP6 para otros escenarios.

6. Extender el análisis a Bolivia, Argentina y otros países.


## Licencia
Reconocimiento-NoComercial-SinObraDerivada 3.0 España (Creative Commons).
