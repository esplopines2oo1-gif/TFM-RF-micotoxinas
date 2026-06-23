"""
RANDOM FOREST PARA PREDECIR CONTAMINACION POR MICOTOXINAS EN PERU
UN MODELO POR MICOTOXINA - PROYECCIÓN DE PROBABILIDAD POR TOXINA Y AÑO
ESCENARIO: +1°C PARA 2031
ENTRENAMIENTO: 70% | PRUEBA: 30%
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import (learning_curve, cross_val_score,
                                     StratifiedKFold, train_test_split,
                                     cross_val_predict)
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (roc_auc_score, confusion_matrix, roc_curve,
                             accuracy_score, precision_recall_curve,
                             average_precision_score, classification_report)
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

try:
    plt.style.use('ggplot')
except Exception:
    pass
sns.set_palette("Set2")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 10



#   1. Constantes biológicas


TEMP_OPTIMA = {
    'AFB1':   {'min': 25, 'max': 35, 'optima': 33, 'hongo': 'Aspergillus flavus'},
    'FUM':    {'min': 25, 'max': 30, 'optima': 30, 'hongo': 'Fusarium verticillioides'},
    'DON':    {'min': 20, 'max': 25, 'optima': 23, 'hongo': 'Fusarium graminearum'},
    'ZEN':    {'min': 20, 'max': 25, 'optima': 25, 'hongo': 'Fusarium graminearum'},
    'T2_HT2': {'min': 20, 'max': 25, 'optima': 20, 'hongo': 'Fusarium langsethiae'},
    'OTA':    {'min': 25, 'max': 30, 'optima': 28, 'hongo': 'Aspergillus ochraceus'},
}

HUMEDAD_OPTIMA = {
    'AFB1':   {'min': 88,  'max': 90,  'optima': 89.0},
    'FUM':    {'min': 85,  'max': 95,  'optima': 90.0},
    'DON':    {'min': 95,  'max': 100, 'optima': 98.0},
    'ZEN':    {'min': 91,  'max': 98,  'optima': 94.5},
    'T2_HT2': {'min': 93,  'max': 99,  'optima': 96.0},
    'OTA':    {'min': 95,  'max': 100, 'optima': 98.0},
}

# Nombres de columnas en el Excel 
COLS_TOXINAS = {
    'AFB1 (ppb)':      'AFB1',
    'FUM  (ppb)':      'FUM',
    'DON  (ppb)':      'DON',
    'ZEN  (ppb)':      'ZEN',
    'T-2/HT-2  (ppb)': 'T2_HT2',
    'OTA  (ppb)':      'OTA',
}

COLS_CLIMA = ['temperature_2m_mean', 'temperature_2m_max',
              'relative_humidity_2m_mean', 'precipitation_sum']

MESES_A_NUM = {
    'Enero': 1, 'Febrero': 2, 'Marzo': 3, 'Abril': 4,
    'Mayo': 5, 'Junio': 6, 'Julio': 7, 'Agosto': 8,
    'Septiembre': 9, 'Octubre': 10, 'Noviembre': 11, 'Diciembre': 12,
}
NUM_A_MES   = {v: k for k, v in MESES_A_NUM.items()}
ORDEN_MESES = list(MESES_A_NUM.keys())


#   2. Mapeo completo de matrices a ciudades y valores base


MATRIZ_CIUDAD = {
    # PALMISTE / PALMA ACEITERA → Pucallpa (Selva)
    'TORTA DE PALMISTE': 'Pucallpa',
    'TORTA PALMISTE':    'Pucallpa',
    'TORTA DE PALMA':    'Pucallpa',
    'PALMISTE':          'Pucallpa',
    'ACEITE DE PALMA':   'Pucallpa',

    # MAIZ y derivados → Trujillo (Costa Norte)
    'MAIZ':                    'Trujillo',
    'MAÍZ':                    'Trujillo',
    'MAIZ ROYAL':              'Trujillo',
    'MAIZ NACIONAL':           'Trujillo',
    'MAIZ B':                  'Trujillo',
    'MAIZ ARGENTINO':          'Trujillo',
    'MAIZ FREYA':              'Trujillo',
    'MAIZ AMARILLO':           'Trujillo',
    'MAIZ AMARILLO DURO':      'Trujillo',
    'MAIZ BLANCO':             'Trujillo',
    'MAIZ MORADO':             'Trujillo',
    'MAIZ GIGANTE':            'Trujillo',
    'MAIZ AVICOLA AVIKONOR':   'Trujillo',
    'MAÍZ AVICOLA':            'Trujillo',
    'MAÍZ - IMPRESSION HAY':   'Trujillo',
    'MAÍZ (M01)':              'Trujillo',
    'MAÍZ (M02)':              'Trujillo',
    'MAÍZ (M03)':              'Trujillo',
    'MAÍZ (M04)':              'Trujillo',

    # TRIGO y derivados → Cusco (Sierra)
    'TRIGO':                    'Cusco',
    'SUB PRODUCTO DE TRIGO':    'Cusco',
    'SUB PRODUCTO DE TRIGO ':   'Cusco',
    'SUB. DE TRIGO':            'Cusco',
    'SUBPRODUCTO DE TRIGO':     'Cusco',
    'SUBRPRODUCTO DE TRIGO':    'Cusco',
    'POLVILLO':                 'Cusco',
    'POLVILLO 1':               'Cusco',
    'POLVILLO 2':               'Cusco',
    'POLVILLO-AVICOLA AVIKONOR':'Cusco',
    'HARINA DE TRIGO':          'Cusco',
    'SALVADO DE TRIGO':         'Cusco',
    'GLUTEN':                   'Cusco',
    'AFRECHO':                  'Cusco',
    'CEBADA':                   'Cusco',
    'QUINUA':                   'Cusco',
    'KIWICHA':                  'Cusco',

    # ARROZ y derivados → Iquitos (Selva)
    'ARROCILLO':            'Iquitos',
    'ARROZ':                'Iquitos',
    'ARROZ PELADO':         'Iquitos',
    'ARROZ INTEGRAL':       'Iquitos',
    'SUBPRODUCTO DE ARROZ': 'Iquitos',

    # SOJA y derivados → Lima (Costa Central)
    'SOJA':                        'Lima',
    'TORTA DE SOJA':               'Lima',
    'TORTA SOYA':                  'Lima',
    'HARINA INTEGRAL DE SOYA':     'Lima',
    'SOJA -AVICOLA AVIKONOR':      'Lima',
    'PASTA DE GIRASOL':            'Lima',
    'HIS':                         'Lima',
    'INTEGRAL AVICOLA AVIKONOR':   'Lima',
}

# Temperatura y humedad base por ciudad (fallback cuando no hay dato climático)
CIUDAD_TEMP_BASE = {
    'Lima':     19.5,
    'Trujillo': 20.5,
    'Cusco':    13.0,
    'Iquitos':  26.5,
    'Pucallpa': 26.0,
}

CIUDAD_HUMEDAD_BASE = {
    'Lima':     85,
    'Trujillo': 82,
    'Cusco':    60,
    'Iquitos':  88,
    'Pucallpa': 87,
}


def asignar_ciudad(matriz):
    """Asigna ciudad según el tipo de matriz (mapeo exhaustivo + coincidencia parcial)."""
    if pd.isna(matriz):
        return 'Lima'
    m = str(matriz).upper().strip()
    # 1. Coincidencia exacta
    if m in MATRIZ_CIUDAD:
        return MATRIZ_CIUDAD[m]
    # 2. Coincidencia parcial (la clave está contenida en el valor o viceversa)
    for key, ciudad in MATRIZ_CIUDAD.items():
        if key in m or m in key:
            return ciudad
    return 'Lima'



#   3. Funciones auxiliares


def calcular_factor_riesgo_temp(temp_actual, toxina):
    if toxina not in TEMP_OPTIMA or pd.isna(temp_actual):
        return 0.0
    info = TEMP_OPTIMA[toxina]
    t_min, t_max, t_opt = info['min'], info['max'], info['optima']
    if t_min <= temp_actual <= t_max:
        rango = (t_max - t_min) / 2
        return max(0.3, 1 - abs(temp_actual - t_opt) / rango) if rango else 1.0
    return 0.1


def calcular_factor_riesgo_humedad(humedad_actual, toxina):
    if toxina not in HUMEDAD_OPTIMA or pd.isna(humedad_actual):
        return 0.0
    info = HUMEDAD_OPTIMA[toxina]
    h_min, h_max, h_opt = info['min'], info['max'], info['optima']
    if humedad_actual < h_min:
        return max(0.1, 0.3 * (humedad_actual / h_min))
    elif h_min <= humedad_actual <= h_max:
        rango = (h_max - h_min) / 2
        return max(0.5, 1 - abs(humedad_actual - h_opt) / rango) if rango else 1.0
    return max(0.2, 0.5 * (h_max / humedad_actual))


def calcular_riesgo_total(temp_actual, humedad_actual):
    riesgos = []
    for toxina in TEMP_OPTIMA:
        rt = calcular_factor_riesgo_temp(temp_actual, toxina)
        rh = calcular_factor_riesgo_humedad(humedad_actual, toxina)
        riesgos.append(np.sqrt(rt * rh))
    return float(np.mean(riesgos))


def esta_contaminado(valor):
    if pd.isna(valor) or valor == "":
        return 0
    s = str(valor).strip()
    if s.startswith('<'):  return 0
    if s.startswith('>'):  return 1
    try:
        float(s.replace(',', '.'))
        return 1
    except ValueError:
        return 0



#   4. Cargar datos

print("Cargando datos")

df_micotoxinas = pd.read_excel('datos Peru micotoxinas.xlsx')
df_clima       = pd.read_excel('detalle por ubicacion.xlsx')
print(f"  Micotoxinas : {df_micotoxinas.shape[0]} filas")
print(f"  Clima       : {df_clima.shape[0]} filas")



#   5. Procesar micotoxinas

print("Procesando datos de micotoxinas")

df_micotoxinas.columns = df_micotoxinas.columns.str.strip()
if 'Mes' in df_micotoxinas.columns:
    df_micotoxinas['Mes'] = df_micotoxinas['Mes'].astype(str).str.strip()

cols_presentes = {k: v for k, v in COLS_TOXINAS.items()
                  if k in df_micotoxinas.columns}
if not cols_presentes:
    raise ValueError("No se encontraron columnas de micotoxinas.")

for col_excel, tok in cols_presentes.items():
    df_micotoxinas[f'contam_{tok}'] = df_micotoxinas[col_excel].apply(esta_contaminado)

df_micotoxinas['contaminada'] = df_micotoxinas[
    [f'contam_{tok}' for tok in cols_presentes.values()]
].max(axis=1)

print(f"  Toxinas encontradas: {list(cols_presentes.values())}")
for tok in cols_presentes.values():
    n = df_micotoxinas[f'contam_{tok}'].sum()
    print(f"  {tok}: {n} muestras contaminadas ({n/len(df_micotoxinas):.1%})")

#  Asignar ciudad a cada muestra usando el mapeo exhaustivo  
df_micotoxinas['ciudad'] = df_micotoxinas['Matriz'].apply(asignar_ciudad)

# Diagnóstico de asignación
print("\n  Distribución de muestras por ciudad:")
print(df_micotoxinas['ciudad'].value_counts().to_string())
print()


#   6. Procesar clima

print("Procesando datos climáticos")

df_clima.columns = df_clima.columns.str.strip()
for col in COLS_CLIMA:
    if col in df_clima.columns:
        df_clima[col] = (df_clima[col].astype(str)
                         .str.replace(',', '.', regex=False)
                         .pipe(pd.to_numeric, errors='coerce'))

df_clima['date']    = pd.to_datetime(df_clima['date'])
df_clima['Año']     = df_clima['date'].dt.year
df_clima['Mes_num'] = df_clima['date'].dt.month
df_clima['Mes']     = df_clima['Mes_num'].map(NUM_A_MES)

col_loc = next((c for c in ['location', 'ciudad', 'Location']
                if c in df_clima.columns), df_clima.columns[-1])

df_clima_agrupado = (
    df_clima.groupby(['Año', 'Mes', col_loc])
    .agg({c: 'mean' for c in COLS_CLIMA if c in df_clima.columns})
    .reset_index()
    .rename(columns={col_loc: 'ciudad'})
)



#   7. Unir y rellenar valores climáticos faltantes
#      Prioridad: dato real del clima → media histórica de la ciudad
#      → valor base (CIUDAD_TEMP_BASE / CIUDAD_HUMEDAD_BASE)

df_completo = df_micotoxinas.merge(
    df_clima_agrupado, on=['Año', 'Mes', 'ciudad'], how='left'
)
df_completo['Mes_num'] = df_completo['Mes'].map(MESES_A_NUM)

# Paso 1: rellenar con la media histórica de cada ciudad
for ciudad in df_completo['ciudad'].unique():
    mask = df_completo['ciudad'] == ciudad
    for col in COLS_CLIMA:
        if col in df_completo.columns:
            media = df_completo.loc[mask, col].mean()
            df_completo.loc[mask & df_completo[col].isna(), col] = media

# Paso 2: si aún hay NaN (ciudad sin ningún dato climático),
#          usar el valor base definido en CIUDAD_TEMP_BASE / CIUDAD_HUMEDAD_BASE
base_fallback = {
    'temperature_2m_mean':        CIUDAD_TEMP_BASE,
    'temperature_2m_max':         {c: v + 5 for c, v in CIUDAD_TEMP_BASE.items()},
    'relative_humidity_2m_mean':  CIUDAD_HUMEDAD_BASE,
    'precipitation_sum':          {'Lima': 2, 'Trujillo': 3, 'Cusco': 50,
                                   'Iquitos': 250, 'Pucallpa': 200},
}

for col, ciudad_dict in base_fallback.items():
    if col in df_completo.columns:
        for ciudad, valor in ciudad_dict.items():
            mask = (df_completo['ciudad'] == ciudad) & df_completo[col].isna()
            df_completo.loc[mask, col] = valor

# Reportar cobertura de datos climáticos reales por ciudad
print("\n  Cobertura de datos climáticos reales por ciudad:")
for ciudad in sorted(df_completo['ciudad'].unique()):
    mask   = df_completo['ciudad'] == ciudad
    total  = mask.sum()
    con_clima = df_completo.loc[mask, 'temperature_2m_mean'].notna().sum()
    # En este punto ya rellenamos, así que mostramos antes del relleno
    # (el dato ya fue imputado, indicamos total)
    print(f"    {ciudad:<12}: {total:>4} muestras")

df_completo['riesgo_total'] = df_completo.apply(
    lambda r: calcular_riesgo_total(r['temperature_2m_mean'],
                                     r['relative_humidity_2m_mean']), axis=1
)
df_completo = df_completo.dropna(
    subset=['temperature_2m_mean', 'relative_humidity_2m_mean', 'contaminada']
)

print(f"\n  Dataset final: {df_completo.shape[0]} muestras")
print(f"  Ciudades: {df_completo['ciudad'].unique().tolist()}")

# Verificación: temperatura media observada por ciudad
print("\n  Temperatura media por ciudad (datos reales + imputados):")
resumen_temp = (df_completo.groupby('ciudad')[['temperature_2m_mean',
                                                'relative_humidity_2m_mean']]
                .mean().round(1))
print(resumen_temp.to_string())
print()



#   8. Codificar categóricas
 
le_ciudad = LabelEncoder().fit(df_completo['ciudad'].unique())
le_matriz = LabelEncoder().fit(df_completo['Matriz'].unique())

df_completo['Matriz_enc'] = le_matriz.transform(df_completo['Matriz'])
df_completo['ciudad_enc'] = le_ciudad.transform(df_completo['ciudad'])

PREDICTORES = ['Matriz_enc', 'ciudad_enc',
               'temperature_2m_mean', 'relative_humidity_2m_mean', 'riesgo_total']


 
#   9. Entrenar UN MODELO RF POR TOXINA

print("\n=== ENTRENANDO UN MODELO RF POR TOXINA ===")

modelos_por_toxina   = {}
metricas_por_toxina  = {}
test_data_por_toxina = {}

for tok in cols_presentes.values():
    col_y = f'contam_{tok}'
    y_tok = df_completo[col_y]

    if y_tok.nunique() < 2:
        print(f"  {tok}: solo una clase, se omite.")
        continue

    n_pos = y_tok.sum()
    n_neg = (y_tok == 0).sum()
    print(f"\n    {tok} ({TEMP_OPTIMA[tok]['hongo']})")
    print(f"     Contaminadas: {n_pos} | No contaminadas: {n_neg}")

    X = df_completo[PREDICTORES].copy()
    y = y_tok.copy()

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )

    min_class = y_train.value_counts().min()
    n_splits  = min(5, min_class)

    rf = RandomForestClassifier(
        n_estimators=200,
        max_depth=8,
        min_samples_split=10,
        oob_score=True,
        random_state=42,
        n_jobs=-1,
    )
    rf.fit(X_train, y_train)

    cv        = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
    cv_scores = cross_val_score(rf, X_train, y_train, cv=cv, scoring='roc_auc')

    y_test_pred  = rf.predict(X_test)
    y_test_proba = rf.predict_proba(X_test)[:, 1]
    auc_test     = roc_auc_score(y_test, y_test_proba)
    ap_test      = average_precision_score(y_test, y_test_proba)

    print(f"     AUC-ROC : {auc_test:.3f}")
    print(f"     Avg Prec: {ap_test:.3f}")
    print(f"     OOB     : {rf.oob_score_:.3f}")
    print(f"     CV AUC  : {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")
    print(f"     Accuracy: {accuracy_score(y_test, y_test_pred):.3f}")

    modelos_por_toxina[tok]   = rf
    metricas_por_toxina[tok]  = {
        'AUC_test': auc_test,
        'AP_test':  ap_test,
        'OOB':      rf.oob_score_,
        'CV_mean':  cv_scores.mean(),
        'CV_std':   cv_scores.std(),
        'Accuracy': accuracy_score(y_test, y_test_pred),
        'n_pos':    int(n_pos),
        'n_splits': n_splits,
    }
    test_data_por_toxina[tok] = (X_test, y_test, y_test_pred, y_test_proba)



#   10. Gráficos de diagnóstico por toxina
 
print("\nGenerando gráficos de diagnóstico por toxina...")

n_tok  = len(modelos_por_toxina)
n_cols = 3
n_rows = int(np.ceil(n_tok / n_cols))

# 10.1 Curvas ROC
fig, ax = plt.subplots(figsize=(10, 7))
colores_roc = plt.cm.Set2(np.linspace(0, 1, n_tok))

for i, (tok, rf) in enumerate(modelos_por_toxina.items()):
    _, y_test, _, y_proba = test_data_por_toxina[tok]
    fpr, tpr, _ = roc_curve(y_test, y_proba)
    auc = metricas_por_toxina[tok]['AUC_test']
    ax.plot(fpr, tpr, linewidth=2, color=colores_roc[i],
            label=f'{tok} (AUC={auc:.3f})')

ax.plot([0, 1], [0, 1], 'k--', alpha=0.4)
ax.set_title('Curvas ROC por Micotoxina', fontsize=14, fontweight='bold')
ax.set_xlabel('Tasa Falsos Positivos')
ax.set_ylabel('Tasa Verdaderos Positivos')
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('roc_por_toxina.png', dpi=150, bbox_inches='tight')
plt.show()
print("  ✓ roc_por_toxina.png")

# 10.2 Matrices de confusión
fig, axes = plt.subplots(n_rows, n_cols, figsize=(18, 6 * n_rows))
axes_flat = np.array(axes).flatten()
fig.suptitle('Matrices de Confusión por Micotoxina', fontsize=15, fontweight='bold')

for i, (tok, rf) in enumerate(modelos_por_toxina.items()):
    ax = axes_flat[i]
    _, y_test, y_pred, _ = test_data_por_toxina[tok]
    cm = confusion_matrix(y_test, y_pred)
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax,
                xticklabels=['No contam.', 'Contam.'],
                yticklabels=['No contam.', 'Contam.'])
    ax.set_title(f'{tok}\n{TEMP_OPTIMA[tok]["hongo"]}', fontsize=10)
    ax.set_xlabel('Predicho'); ax.set_ylabel('Actual')

for j in range(n_tok, len(axes_flat)):
    axes_flat[j].set_visible(False)

plt.tight_layout()
plt.savefig('confusion_por_toxina.png', dpi=150, bbox_inches='tight')
plt.show()
print("  ✓ confusion_por_toxina.png")

# 10.3 Importancia de variables
fig, axes = plt.subplots(n_rows, n_cols, figsize=(18, 6 * n_rows))
axes_flat = np.array(axes).flatten()
fig.suptitle('Importancia de Variables por Micotoxina', fontsize=15, fontweight='bold')
nombres_vars = ['Matriz', 'Ciudad', 'Temperatura', 'Humedad', 'Riesgo Total']

for i, (tok, rf) in enumerate(modelos_por_toxina.items()):
    ax = axes_flat[i]
    imp_df = pd.DataFrame({
        'variable':    nombres_vars,
        'importancia': rf.feature_importances_,
    }).sort_values('importancia', ascending=True)
    bars = ax.barh(imp_df['variable'], imp_df['importancia'],
                   color='steelblue', edgecolor='k')
    for bar, val in zip(bars, imp_df['importancia']):
        ax.text(val + 0.002, bar.get_y() + bar.get_height()/2,
                f'{val:.3f}', va='center', fontsize=9)
    ax.set_title(tok, fontsize=11, fontweight='bold')
    ax.set_xlabel('Importancia (Gini)')
    ax.grid(True, alpha=0.3, axis='x')

for j in range(n_tok, len(axes_flat)):
    axes_flat[j].set_visible(False)

plt.tight_layout()
plt.savefig('importancia_por_toxina.png', dpi=150, bbox_inches='tight')
plt.show()
print("  ✓ importancia_por_toxina.png")

# 10.4 Resumen métricas
fig, axes = plt.subplots(1, 3, figsize=(16, 5))
fig.suptitle('Comparativa de Métricas por Toxina', fontsize=14, fontweight='bold')

toxinas_ok = list(modelos_por_toxina.keys())
auc_vals   = [metricas_por_toxina[t]['AUC_test'] for t in toxinas_ok]
oob_vals   = [metricas_por_toxina[t]['OOB']      for t in toxinas_ok]
ap_vals    = [metricas_por_toxina[t]['AP_test']  for t in toxinas_ok]
x          = np.arange(len(toxinas_ok))

for ax, vals, ylabel, title, umbral in [
    (axes[0], auc_vals, 'AUC-ROC',          'AUC-ROC en Test',      0.7),
    (axes[1], oob_vals, 'OOB Score',         'OOB Score',            0.7),
    (axes[2], ap_vals,  'Average Precision', 'Precision Media (AP)', 0.5),
]:
    colors = ['steelblue' if v >= umbral else 'coral' for v in vals]
    ax.bar(x, vals, color=colors, edgecolor='k')
    ax.axhline(umbral, color='red', linestyle='--', linewidth=1.5,
               label=f'Umbral {umbral}')
    ax.set_xticks(x); ax.set_xticklabels(toxinas_ok, rotation=30)
    ax.set_ylabel(ylabel); ax.set_title(title)
    ax.set_ylim(0, 1.05); ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3, axis='y')
    for j, v in enumerate(vals):
        ax.text(j, v + 0.02, f'{v:.3f}', ha='center',
                fontsize=9, fontweight='bold')

plt.tight_layout()
plt.savefig('metricas_por_toxina.png', dpi=150, bbox_inches='tight')
plt.show()
print("  ✓ metricas_por_toxina.png")



#   11. PROYECCIÓN POR TOXINA Y AÑO (+1.6°C acumulado 2026-2031)
#       El delta de temperatura se aplica diferenciado por ciudad,
#       respetando el valor de temperatura real (o imputado) de cada
#       muestra → el modelo "ve" la temperatura específica de la
#       ciudad/matriz en el escenario climático futuro.

print("\n=== PROYECCIÓN POR TOXINA Y AÑO (2026-2031, +1.6°C) ===")

años_futuros     = list(range(2026, 2032))
incremento_total = 1.6 / 6

tasa_actual = {
    tok: df_completo[f'contam_{tok}'].mean()
    for tok in modelos_por_toxina
}

proyeccion = []

for año in años_futuros:
    delta = min(1.6, (año - 2025) * incremento_total)
    df_fut = df_completo.copy()

    # Aplicar delta sobre la temperatura real de cada muestra
    df_fut['temperature_2m_mean'] += delta
    df_fut['temperature_2m_max']  += delta

    # Recalcular riesgo con la nueva temperatura
    df_fut['riesgo_total'] = df_fut.apply(
        lambda r: calcular_riesgo_total(r['temperature_2m_mean'],
                                         r['relative_humidity_2m_mean']), axis=1
    )
    df_fut['Matriz_enc'] = le_matriz.transform(df_fut['Matriz'])
    df_fut['ciudad_enc'] = le_ciudad.transform(df_fut['ciudad'])

    X_fut = df_fut[PREDICTORES].copy()

    for tok, rf in modelos_por_toxina.items():
        proba = rf.predict_proba(X_fut)[:, 1]

        # Probabilidad desglosada por ciudad (diagnóstico)
        for ciudad in df_fut['ciudad'].unique():
            mask_c = df_fut['ciudad'] == ciudad
            if mask_c.sum() == 0:
                continue
            proyeccion.append({
                'Año':        año,
                'Toxina':     tok,
                'Hongo':      TEMP_OPTIMA[tok]['hongo'],
                'Ciudad':     ciudad,
                'Delta_temp': delta,
                'Temp_media': df_fut.loc[mask_c, 'temperature_2m_mean'].mean(),
                'prob_media': float(proba[mask_c.values].mean()),
                'pct_contam': float((proba[mask_c.values] > 0.5).mean() * 100),
            })

df_proy = pd.DataFrame(proyeccion)

# Agregado global por año/toxina (promedio ponderado por nº muestras)
df_proy_global = (
    df_proy.groupby(['Año', 'Toxina', 'Hongo', 'Delta_temp'])
    .agg(prob_media=('prob_media', 'mean'),
         pct_contam=('pct_contam', 'mean'))
    .reset_index()
)

# Tabla resumen 2031
print(f"\n{'Toxina':<10} {'Actual':>8} {'2031 prob.':>12} {'2031 % >0.5':>13} {'Cambio pp':>10}")
print("-" * 57)
for tok in modelos_por_toxina:
    actual = tasa_actual[tok]
    fila   = df_proy_global[(df_proy_global['Año'] == 2031) &
                             (df_proy_global['Toxina'] == tok)].iloc[0]
    cambio = fila['pct_contam'] / 100 - actual
    print(f"  {tok:<8} {actual:>8.1%} {fila['prob_media']:>12.3f} "
          f"{fila['pct_contam']:>12.1f}% {cambio*100:>+9.1f}pp")

# Tabla por ciudad y toxina en 2031
print("\n  Probabilidad media por ciudad en 2031:")
proy_2031 = df_proy[df_proy['Año'] == 2031]
tabla_ciudad = proy_2031.pivot_table(
    index='Ciudad', columns='Toxina', values='prob_media', aggfunc='mean'
).round(3)
print(tabla_ciudad.to_string())


 
#   12. Gráficos de proyección

colores_proy = plt.cm.Set2(np.linspace(0, 1, len(modelos_por_toxina)))

# 12.1 Probabilidad media global por toxina
fig, axes = plt.subplots(1, 2, figsize=(18, 7))
fig.suptitle('Proyección de Contaminación por Micotoxina (2026-2031, +1.6°C)',
             fontsize=14, fontweight='bold')

for i, tok in enumerate(modelos_por_toxina):
    df_t = df_proy_global[df_proy_global['Toxina'] == tok]
    axes[0].plot(df_t['Año'], df_t['prob_media'],
                 'o-', color=colores_proy[i], linewidth=2.5,
                 markersize=7, label=tok)
    axes[1].plot(df_t['Año'], df_t['pct_contam'],
                 'o-', color=colores_proy[i], linewidth=2.5,
                 markersize=7, label=tok)
    axes[1].scatter(2025, tasa_actual[tok] * 100,
                    color=colores_proy[i], marker='*', s=120, zorder=5)

axes[0].axvline(2025.5, color='gray', linestyle=':', alpha=0.6, label='Inicio proyección')
axes[1].axvline(2025.5, color='gray', linestyle=':', alpha=0.6, label='★ Valor actual 2025')

axes[0].set_title('Probabilidad media de contaminación')
axes[0].set_ylabel('Probabilidad media'); axes[0].set_ylim(0, 1)
axes[1].set_title('% muestras clasificadas como contaminadas\n(★ = valor actual observado)')
axes[1].set_ylabel('Contaminación estimada (%)'); axes[1].set_ylim(0, 105)

for ax in axes:
    ax.set_xlabel('Año')
    ax.legend(bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.set_xticks(años_futuros)

plt.tight_layout()
plt.savefig('proyeccion_por_toxina.png', dpi=150, bbox_inches='tight')
plt.show()
print("  ✓ proyeccion_por_toxina.png")

# 12.2 Proyección por ciudad (heatmap para 2031)
fig, axes = plt.subplots(1, len(modelos_por_toxina),
                         figsize=(4 * len(modelos_por_toxina), 5))
fig.suptitle('Probabilidad de Contaminación por Ciudad en 2031 (+1.6°C)',
             fontsize=13, fontweight='bold')

if len(modelos_por_toxina) == 1:
    axes = [axes]

ciudades_ord = ['Pucallpa', 'Iquitos', 'Trujillo', 'Lima', 'Cusco']

for i, tok in enumerate(modelos_por_toxina):
    ax = axes[i]
    proy_tok = (proy_2031[proy_2031['Toxina'] == tok]
                .set_index('Ciudad')['prob_media'])
    vals = [proy_tok.get(c, np.nan) for c in ciudades_ord]

    colors_bar = plt.cm.RdYlGn_r(np.array([v if not np.isnan(v) else 0
                                             for v in vals]))
    bars = ax.barh(ciudades_ord, vals, color=colors_bar, edgecolor='k')
    for bar, val in zip(bars, vals):
        if not np.isnan(val):
            ax.text(val + 0.01, bar.get_y() + bar.get_height()/2,
                    f'{val:.3f}', va='center', fontsize=9)
    ax.set_xlim(0, 1)
    ax.set_title(tok, fontweight='bold')
    ax.set_xlabel('Prob. media')
    ax.axvline(0.5, color='red', linestyle='--', alpha=0.5)
    ax.grid(True, alpha=0.3, axis='x')

plt.tight_layout()
plt.savefig('proyeccion_ciudad_2031.png', dpi=150, bbox_inches='tight')
plt.show()
print("  ✓ proyeccion_ciudad_2031.png")

# 12.3 Incremento anual de probabilidad
fig, ax = plt.subplots(figsize=(12, 6))
for i, tok in enumerate(modelos_por_toxina):
    df_t = df_proy_global[df_proy_global['Toxina'] == tok].sort_values('Año')
    incrementos = df_t['prob_media'].diff().fillna(0).values
    ax.plot(años_futuros, incrementos,
            'o-', color=colores_proy[i], linewidth=2,
            markersize=6, label=tok)

ax.axhline(0, color='black', linewidth=1)
ax.set_title('Incremento Anual de Probabilidad de Contaminación por Toxina\n'
             '(+1.6°C acumulado 2026-2031)', fontsize=13, fontweight='bold')
ax.set_xlabel('Año'); ax.set_ylabel('Δ Probabilidad respecto al año anterior')
ax.legend(bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=9)
ax.grid(True, alpha=0.3); ax.set_xticks(años_futuros)
plt.tight_layout()
plt.savefig('incremento_anual_por_toxina.png', dpi=150, bbox_inches='tight')
plt.show()
print("  ✓ incremento_anual_por_toxina.png")


 
#   13. Curva de aprendizaje (toxina con más muestras positivas)

tok_ref = max(modelos_por_toxina, key=lambda t: metricas_por_toxina[t]['n_pos'])
rf_ref  = modelos_por_toxina[tok_ref]
n_ref   = metricas_por_toxina[tok_ref]['n_splits']

fig, ax = plt.subplots(figsize=(10, 6))
train_sizes, tr_sc, te_sc = learning_curve(
    rf_ref, df_completo[PREDICTORES], df_completo[f'contam_{tok_ref}'],
    cv=n_ref, n_jobs=-1,
    train_sizes=np.linspace(0.3, 1.0, 6),
    scoring='roc_auc',
)
tr_m, tr_s = tr_sc.mean(axis=1), tr_sc.std(axis=1)
te_m, te_s = te_sc.mean(axis=1), te_sc.std(axis=1)

ax.plot(train_sizes, tr_m, 'o-', color='blue', label='Entrenamiento')
ax.fill_between(train_sizes, tr_m - tr_s, tr_m + tr_s, alpha=0.1, color='blue')
ax.plot(train_sizes, te_m, 'o-', color='red',  label='Validación')
ax.fill_between(train_sizes, te_m - te_s, te_m + te_s, alpha=0.1, color='red')

brecha = tr_m[-1] - te_m[-1]
ax.set_title(f'Curva de Aprendizaje — {tok_ref}\n'
             f'Brecha = {brecha:.3f} '
             f'({"sobreajuste" if brecha > 0.1 else "aceptable"})',
             fontsize=12)
ax.set_xlabel('Muestras de entrenamiento')
ax.set_ylabel('AUC-ROC')
ax.legend(); ax.grid(True, alpha=0.3); ax.set_ylim(0.5, 1.05)
plt.tight_layout()
plt.savefig('curva_aprendizaje.png', dpi=150, bbox_inches='tight')
plt.show()
print("  ✓ curva_aprendizaje.png")



#   14. Resumen final

print("\n" + "=" * 65)
print("RESUMEN FINAL — UN MODELO RF POR MICOTOXINA")
print("=" * 65)

print("\nMÉTRICAS POR TOXINA:")
print(f"  {'Toxina':<10} {'AUC':>7} {'OOB':>7} {'AP':>7} {'CV':>14} {'Acc':>8}")
print("  " + "-" * 58)
for tok in modelos_por_toxina:
    m = metricas_por_toxina[tok]
    print(f"  {tok:<10} {m['AUC_test']:>7.3f} {m['OOB']:>7.3f} "
          f"{m['AP_test']:>7.3f} "
          f"{m['CV_mean']:>6.3f}±{m['CV_std']:.3f} "
          f"{m['Accuracy']:>8.3f}")

print("\nPROYECCIÓN 2031 (+1.6°C) — PROBABILIDAD MEDIA:")
print(f"  {'Toxina':<10} {'Actual':>8} {'2031':>8} {'Δ prob':>8}")
print("  " + "-" * 38)
for tok in modelos_por_toxina:
    actual = tasa_actual[tok]
    fila   = df_proy_global[(df_proy_global['Año'] == 2031) &
                             (df_proy_global['Toxina'] == tok)].iloc[0]
    delta  = fila['prob_media'] - actual
    print(f"  {tok:<10} {actual:>8.3f} {fila['prob_media']:>8.3f} {delta:>+8.3f}")

print(f"""
ARCHIVOS GENERADOS:
  • roc_por_toxina.png
  • confusion_por_toxina.png
  • importancia_por_toxina.png
  • metricas_por_toxina.png
  • proyeccion_por_toxina.png
  • proyeccion_ciudad_2031.png         
  • incremento_anual_por_toxina.png
  • curva_aprendizaje.png
""")
print("ANÁLISIS COMPLETADO")
