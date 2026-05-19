"""
RANDOM FOREST - PREDICCIÓN DE CONCENTRACIÓN DE MICOTOXINAS (ppb)
UN MODELO POR MICOTOXINA - PROYECCIÓN DE CONCENTRACIÓN POR TOXINA Y AÑO
ESCENARIO: +1.6°C ACUMULADO PARA 2031
ENTRENAMIENTO: 70% | PRUEBA: 30%
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import (cross_val_score,
                                     KFold, train_test_split)
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (mean_squared_error, mean_absolute_error,
                             r2_score)
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

LIMITES_CONTAMINACION = {
    'AFB1': 1.3, 'FUM': 150, 'DON': 150,
    'ZEN': 35,   'T2_HT2': 40, 'OTA': 1,
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
    if m in MATRIZ_CIUDAD:
        return MATRIZ_CIUDAD[m]
    for key, ciudad in MATRIZ_CIUDAD.items():
        if key in m or m in key:
            return ciudad
    return 'Lima'


#   3. Funciones auxiliares

def convertir_a_numerico(valor):
    """Convierte valores de concentración a numérico, manejando <LOD y >LOD."""
    if pd.isna(valor) or valor == "":
        return np.nan
    s = str(valor).strip()
    if s.startswith('<'):
        return np.nan
    if s.startswith('>'):
        try:
            return float(s[1:].replace(',', '.'))
        except:
            return np.nan
    try:
        return float(s.replace(',', '.'))
    except:
        return np.nan


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


#   4. Cargar datos

print("CARGANDO DATOS")

df_micotoxinas = pd.read_excel('datos Peru micotoxinas.xlsx')
df_clima       = pd.read_excel('detalle por ubicacion.xlsx')
print(f"  Micotoxinas : {df_micotoxinas.shape[0]} filas")
print(f"  Clima       : {df_clima.shape[0]} filas")


#   5. Procesar micotoxinas

print("PROCESANDO DATOS DE MICOTOXINAS")

df_micotoxinas.columns = df_micotoxinas.columns.str.strip()
if 'Mes' in df_micotoxinas.columns:
    df_micotoxinas['Mes'] = df_micotoxinas['Mes'].astype(str).str.strip()

cols_presentes = {k: v for k, v in COLS_TOXINAS.items()
                  if k in df_micotoxinas.columns}
if not cols_presentes:
    raise ValueError("No se encontraron columnas de micotoxinas.")

# Convertir a valores numéricos
for col_excel, tok in cols_presentes.items():
    df_micotoxinas[f'{tok}_num'] = df_micotoxinas[col_excel].apply(convertir_a_numerico)

# Asignar ciudad a cada muestra
df_micotoxinas['ciudad'] = df_micotoxinas['Matriz'].apply(asignar_ciudad)

print(f"  Toxinas encontradas: {list(cols_presentes.values())}")
print(f"  Muestras totales: {len(df_micotoxinas)}")
for tok in cols_presentes.values():
    n = df_micotoxinas[f'{tok}_num'].notna().sum()
    media = df_micotoxinas[f'{tok}_num'].mean()
    print(f"  {tok}: {n} valores numéricos, media = {media:.2f} ppb")

print("\n  Distribución de muestras por ciudad:")
print(df_micotoxinas['ciudad'].value_counts().to_string())


#   6. Procesar clima

print("PROCESANDO DATOS CLIMÁTICOS")

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

print("UNIENDO DATOS Y RELLENANDO FALTANTES")

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

# Paso 2: fallback con valores base
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

# Calcular riesgo total
df_completo['riesgo_total'] = df_completo.apply(
    lambda r: calcular_riesgo_total(r['temperature_2m_mean'],
                                     r['relative_humidity_2m_mean']), axis=1
)

print(f"\n  Dataset final: {df_completo.shape[0]} muestras")
print(f"  Ciudades: {df_completo['ciudad'].unique().tolist()}")

print("\n  Temperatura y humedad media por ciudad:")
resumen_temp = (df_completo.groupby('ciudad')[['temperature_2m_mean',
                                                'relative_humidity_2m_mean']]
                .mean().round(1))
print(resumen_temp.to_string())


#   8. Codificar categóricas

print("CODIFICANDO VARIABLES CATEGÓRICAS")

le_ciudad = LabelEncoder().fit(df_completo['ciudad'].unique())
le_matriz = LabelEncoder().fit(df_completo['Matriz'].unique())

df_completo['Matriz_enc'] = le_matriz.transform(df_completo['Matriz'])
df_completo['ciudad_enc'] = le_ciudad.transform(df_completo['ciudad'])

PREDICTORES = ['Matriz_enc', 'ciudad_enc',
               'temperature_2m_mean', 'relative_humidity_2m_mean', 'riesgo_total']


#   9. Entrenar UN MODELO RF POR TOXINA (REGRESIÓN)

print("ENTRENANDO UN MODELO RF POR TOXINA (REGRESIÓN)")

modelos_por_toxina   = {}
metricas_por_toxina  = {}
test_data_por_toxina = {}

for tok in cols_presentes.values():
    col_y = f'{tok}_num'
    
    # Filtrar solo muestras con valor numérico
    df_tok = df_completo[df_completo[col_y].notna()].copy()
    
    if len(df_tok) < 20:
        print(f"\n  {tok}: muy pocas muestras ({len(df_tok)}), se omite.")
        continue

    y_tok = df_tok[col_y]
    
    print(f"\n  {'='*50}")
    print(f"  {tok} ({TEMP_OPTIMA[tok]['hongo']})")
    print(f"  Muestras: {len(df_tok)} | Media: {y_tok.mean():.2f} ppb | "
          f"Mediana: {y_tok.median():.2f} ppb")

    X = df_tok[PREDICTORES].copy()
    y = y_tok.copy()

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42
    )

    rf = RandomForestRegressor(
        n_estimators=200,
        max_depth=8,
        min_samples_split=10,
        random_state=42,
        n_jobs=-1,
    )
    rf.fit(X_train, y_train)

    cv = KFold(n_splits=min(5, len(X_train)//10), shuffle=True, random_state=42)
    cv_rmse = cross_val_score(rf, X_train, y_train, cv=cv, 
                               scoring='neg_root_mean_squared_error')
    cv_r2 = cross_val_score(rf, X_train, y_train, cv=cv, scoring='r2')

    y_test_pred = rf.predict(X_test)
    rmse_test = np.sqrt(mean_squared_error(y_test, y_test_pred))
    mae_test  = mean_absolute_error(y_test, y_test_pred)
    r2_test   = r2_score(y_test, y_test_pred)

    # R² OOB (Out-of-Bag) para Random Forest
    oob_preds = np.array([rf.oob_prediction_ 
                           for _ in range(1)]).mean() if hasattr(rf, 'oob_prediction_') else None

    print(f"     RMSE test: {rmse_test:.2f} ppb")
    print(f"     MAE test:  {mae_test:.2f} ppb")
    print(f"     R² test:   {r2_test:.3f}")
    print(f"     CV RMSE:   {-cv_rmse.mean():.2f} ± {cv_rmse.std():.2f}")
    print(f"     CV R²:     {cv_r2.mean():.3f} ± {cv_r2.std():.3f}")

    modelos_por_toxina[tok]   = rf
    metricas_por_toxina[tok]  = {
        'RMSE_test': rmse_test,
        'MAE_test':  mae_test,
        'R2_test':   r2_test,
        'CV_RMSE_mean': -cv_rmse.mean(),
        'CV_RMSE_std':  cv_rmse.std(),
        'CV_R2_mean':   cv_r2.mean(),
        'CV_R2_std':    cv_r2.std(),
        'n_muestras':   len(df_tok),
        'media_ppb':    y_tok.mean(),
    }
    test_data_por_toxina[tok] = (X_test, y_test, y_test_pred, df_tok)


#   10. Gráficos de diagnóstico por toxina

print("GENERANDO GRÁFICOS DE DIAGNÓSTICO")

n_tok  = len(modelos_por_toxina)
n_cols = 3
n_rows = int(np.ceil(n_tok / n_cols))

# 10.1 Predicho vs Real
fig, axes = plt.subplots(n_rows, n_cols, figsize=(18, 6 * n_rows))
axes_flat = np.array(axes).flatten()
fig.suptitle('Predicho vs Real por Micotoxina', fontsize=15, fontweight='bold')

for i, (tok, rf) in enumerate(modelos_por_toxina.items()):
    ax = axes_flat[i]
    X_test, y_test, y_pred, _ = test_data_por_toxina[tok]
    ax.scatter(y_test, y_pred, alpha=0.6, edgecolors='k', linewidth=0.5)
    
    # Línea diagonal (predicción perfecta)
    max_val = max(y_test.max(), y_pred.max())
    ax.plot([0, max_val], [0, max_val], 'r--', linewidth=1, label='Pred. perfecta')
    
    # Línea de tendencia real
    z = np.polyfit(y_test, y_pred, 1)
    ax.plot(y_test, np.poly1d(z)(y_test), 'b-', linewidth=2, 
            label=f'y={z[0]:.2f}x+{z[1]:.1f}')
    
    m = metricas_por_toxina[tok]
    limite = LIMITES_CONTAMINACION.get(tok, 0)
    ax.axhline(limite, color='orange', linestyle=':', alpha=0.7, 
               label=f'Límite: {limite} ppb')
    ax.axvline(limite, color='orange', linestyle=':', alpha=0.7)
    
    ax.set_title(f'{tok} — {TEMP_OPTIMA[tok]["hongo"]}\n'
                 f'RMSE={m["RMSE_test"]:.1f} | R²={m["R2_test"]:.3f}', 
                 fontsize=10)
    ax.set_xlabel('Real (ppb)'); ax.set_ylabel('Predicho (ppb)')
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

for j in range(n_tok, len(axes_flat)):
    axes_flat[j].set_visible(False)

plt.tight_layout()
plt.savefig('predicho_vs_real.png', dpi=150, bbox_inches='tight')
plt.show()
print("   predicho_vs_real.png")

# 10.2 Residuos
fig, axes = plt.subplots(n_rows, n_cols, figsize=(18, 6 * n_rows))
axes_flat = np.array(axes).flatten()
fig.suptitle('Distribución de Residuos por Micotoxina', fontsize=15, fontweight='bold')

for i, (tok, rf) in enumerate(modelos_por_toxina.items()):
    ax = axes_flat[i]
    X_test, y_test, y_pred, _ = test_data_por_toxina[tok]
    residuos = y_test - y_pred
    
    ax.hist(residuos, bins=20, color='steelblue', edgecolor='k', alpha=0.7)
    ax.axvline(0, color='red', linestyle='--', linewidth=2)
    ax.axvline(residuos.mean(), color='green', linestyle='-', linewidth=2, 
               label=f'Media: {residuos.mean():.2f}')
    
    ax.set_title(f'{tok} — RMSE={metricas_por_toxina[tok]["RMSE_test"]:.1f} ppb', 
                 fontsize=10)
    ax.set_xlabel('Residuo (Real - Predicho)'); ax.set_ylabel('Frecuencia')
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

for j in range(n_tok, len(axes_flat)):
    axes_flat[j].set_visible(False)

plt.tight_layout()
plt.savefig('residuos_por_toxina.png', dpi=150, bbox_inches='tight')
plt.show()
print("   residuos_por_toxina.png")

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
print("   importancia_por_toxina.png")

# 10.4 Resumen métricas
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.suptitle('Comparativa de Métricas por Toxina', fontsize=14, fontweight='bold')

toxinas_ok = list(modelos_por_toxina.keys())
rmse_vals  = [metricas_por_toxina[t]['RMSE_test'] for t in toxinas_ok]
r2_vals    = [metricas_por_toxina[t]['R2_test']   for t in toxinas_ok]
x          = np.arange(len(toxinas_ok))

# RMSE
colors_rmse = plt.cm.RdYlGn_r(np.array(rmse_vals) / max(rmse_vals))
bars1 = axes[0].bar(x, rmse_vals, color=colors_rmse, edgecolor='k')
axes[0].set_xticks(x); axes[0].set_xticklabels(toxinas_ok, rotation=30)
axes[0].set_ylabel('RMSE (ppb)'); axes[0].set_title('Error RMSE en Test')
axes[0].grid(True, alpha=0.3, axis='y')
for j, v in enumerate(rmse_vals):
    axes[0].text(j, v + max(rmse_vals)*0.02, f'{v:.1f}', ha='center',
                fontsize=9, fontweight='bold')

# R²
colors_r2 = ['steelblue' if v >= 0.5 else 'coral' for v in r2_vals]
bars2 = axes[1].bar(x, r2_vals, color=colors_r2, edgecolor='k')
axes[1].axhline(0.5, color='green', linestyle='--', linewidth=1.5, label='R²=0.5')
axes[1].axhline(0.0, color='red', linestyle='-', linewidth=1, alpha=0.3)
axes[1].set_xticks(x); axes[1].set_xticklabels(toxinas_ok, rotation=30)
axes[1].set_ylabel('R²'); axes[1].set_title('R² en Test')
axes[1].set_ylim(min(min(r2_vals), 0) - 0.1, 1.05)
axes[1].legend(fontsize=9)
axes[1].grid(True, alpha=0.3, axis='y')
for j, v in enumerate(r2_vals):
    axes[1].text(j, v + 0.02, f'{v:.3f}', ha='center',
                fontsize=9, fontweight='bold')

plt.tight_layout()
plt.savefig('metricas_por_toxina.png', dpi=150, bbox_inches='tight')
plt.show()
print("   metricas_por_toxina.png")

#   11. PROYECCIÓN POR TOXINA Y AÑO (+1.6°C acumulado 2026-2031)

print("PROYECCIÓN POR TOXINA Y AÑO (2026-2031, +1.6°C)")

años_futuros     = list(range(2026, 2032))
incremento_total = 1.6 / 6

# Concentración media actual
concentracion_actual = {
    tok: df_completo[f'{tok}_num'].mean()
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
        pred_ppb = rf.predict(X_fut)
        # Las predicciones no pueden ser negativas
        pred_ppb = np.maximum(0, pred_ppb)

        # Predicción desglosada por ciudad
        for ciudad in df_fut['ciudad'].unique():
            mask_c = df_fut['ciudad'] == ciudad
            if mask_c.sum() == 0:
                continue
            proyeccion.append({
                'Año':           año,
                'Toxina':        tok,
                'Hongo':         TEMP_OPTIMA[tok]['hongo'],
                'Ciudad':        ciudad,
                'Delta_temp':    delta,
                'Temp_media':    df_fut.loc[mask_c, 'temperature_2m_mean'].mean(),
                'conc_media':    float(pred_ppb[mask_c.values].mean()),
                'conc_mediana':  float(np.median(pred_ppb[mask_c.values])),
                'conc_p25':      float(np.percentile(pred_ppb[mask_c.values], 25)),
                'conc_p75':      float(np.percentile(pred_ppb[mask_c.values], 75)),
                'pct_sobre_limite': float(
                    (pred_ppb[mask_c.values] > LIMITES_CONTAMINACION.get(tok, 999)).mean() * 100
                ),
            })

df_proy = pd.DataFrame(proyeccion)

# Agregado global por año/toxina
df_proy_global = (
    df_proy.groupby(['Año', 'Toxina', 'Hongo', 'Delta_temp'])
    .agg(conc_media=('conc_media', 'mean'),
         conc_mediana=('conc_mediana', 'mean'),
         conc_p25=('conc_p25', 'mean'),
         conc_p75=('conc_p75', 'mean'),
         pct_sobre_limite=('pct_sobre_limite', 'mean'))
    .reset_index()
)

# Tabla resumen 2031
print(f"\n  RESUMEN 2031 (+1.6°C):")
print(f"  {'Toxina':<10} {'Actual':>10} {'2031':>10} {'Δ ppb':>10} {'Δ %':>8} "
      f"{'%>Límite':>10} {'Impacto':>10}")
print("  " + "-"*72)
for tok in modelos_por_toxina:
    actual = concentracion_actual[tok]
    fila   = df_proy_global[(df_proy_global['Año'] == 2031) &
                             (df_proy_global['Toxina'] == tok)].iloc[0]
    cambio_ppb = fila['conc_media'] - actual
    cambio_pct = (cambio_ppb / actual * 100) if actual > 0 else 0
    impacto = ("ALTO" if cambio_pct > 20 else "MEDIO" if cambio_pct > 10
               else "BAJO" if cambio_pct > 0 else "DISMINUYE")
    print(f"  {tok:<10} {actual:>10.2f} {fila['conc_media']:>10.2f} "
          f"{cambio_ppb:>+10.2f} {cambio_pct:>+7.1f}% "
          f"{fila['pct_sobre_limite']:>9.1f}% {impacto:>10}")

# Tabla por ciudad y toxina en 2031
print("\n  Concentración media por ciudad en 2031 (ppb):")
proy_2031 = df_proy[df_proy['Año'] == 2031]
tabla_ciudad = proy_2031.pivot_table(
    index='Ciudad', columns='Toxina', values='conc_media', aggfunc='mean'
).round(2)
print(tabla_ciudad.to_string())

#   12. Gráficos de proyección

colores_proy = plt.cm.Set2(np.linspace(0, 1, len(modelos_por_toxina)))

# 12.1 Concentración media global por toxina
fig, axes = plt.subplots(1, 2, figsize=(18, 7))
fig.suptitle('Proyección de Concentración por Micotoxina (2026-2031, +1.6°C)',
             fontsize=14, fontweight='bold')

for i, tok in enumerate(modelos_por_toxina):
    df_t = df_proy_global[df_proy_global['Toxina'] == tok]
    limite = LIMITES_CONTAMINACION.get(tok, 0)
    
    # Concentración media
    axes[0].plot(df_t['Año'], df_t['conc_media'],
                 'o-', color=colores_proy[i], linewidth=2.5,
                 markersize=7, label=tok)
    axes[0].fill_between(df_t['Año'], df_t['conc_p25'], df_t['conc_p75'],
                         alpha=0.15, color=colores_proy[i])
    
    # % sobre límite
    axes[1].plot(df_t['Año'], df_t['pct_sobre_limite'],
                 'o-', color=colores_proy[i], linewidth=2.5,
                 markersize=7, label=tok)

axes[0].axvline(2025.5, color='gray', linestyle=':', alpha=0.6, label='Inicio proyección')
axes[1].axvline(2025.5, color='gray', linestyle=':', alpha=0.6)

axes[0].set_title('Concentración media (ppb)')
axes[0].set_ylabel('Concentración (ppb)')
axes[1].set_title('% muestras sobre límite reglamentario')
axes[1].set_ylabel('% sobre límite')

for ax in axes:
    ax.set_xlabel('Año')
    ax.legend(bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.set_xticks(años_futuros)

plt.tight_layout()
plt.savefig('proyeccion_por_toxina.png', dpi=150, bbox_inches='tight')
plt.show()
print("   proyeccion_por_toxina.png")

# 12.2 Proyección por ciudad (concentración en 2031)
fig, axes = plt.subplots(1, len(modelos_por_toxina),
                         figsize=(4 * len(modelos_por_toxina), 5))
fig.suptitle('Concentración Media por Ciudad en 2031 (+1.6°C)',
             fontsize=13, fontweight='bold')

if len(modelos_por_toxina) == 1:
    axes = [axes]

ciudades_ord = ['Pucallpa', 'Iquitos', 'Trujillo', 'Lima', 'Cusco']

for i, tok in enumerate(modelos_por_toxina):
    ax = axes[i]
    limite = LIMITES_CONTAMINACION.get(tok, 0)
    proy_tok = (proy_2031[proy_2031['Toxina'] == tok]
                .set_index('Ciudad')['conc_media'])
    vals = [proy_tok.get(c, np.nan) for c in ciudades_ord]
    
    # Color basado en % del límite
    norm_vals = [v / limite if limite > 0 and not np.isnan(v) else 0 for v in vals]
    colors_bar = plt.cm.RdYlGn_r(np.array(norm_vals))
    
    bars = ax.barh(ciudades_ord, vals, color=colors_bar, edgecolor='k')
    for bar, val in zip(bars, vals):
        if not np.isnan(val):
            ax.text(val + max(vals)*0.01, bar.get_y() + bar.get_height()/2,
                    f'{val:.1f}', va='center', fontsize=9)
    ax.axvline(limite, color='red', linestyle='--', alpha=0.7,
               label=f'Límite {limite} ppb')
    ax.set_title(tok, fontweight='bold')
    ax.set_xlabel('ppb'); ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3, axis='x')

plt.tight_layout()
plt.savefig('proyeccion_ciudad_2031.png', dpi=150, bbox_inches='tight')
plt.show()
print("   proyeccion_ciudad_2031.png")


#   13. Resumen final

print("\n" + "=" * 70)
print("RESUMEN FINAL — UN MODELO RF POR MICOTOXINA (REGRESIÓN)")
print("=" * 70)

print("\nMÉTRICAS POR TOXINA:")
print(f"  {'Toxina':<10} {'RMSE':>8} {'MAE':>8} {'R²':>7} {'CV RMSE':>14} {'Muestras':>10}")
print("  " + "-" * 65)
for tok in modelos_por_toxina:
    m = metricas_por_toxina[tok]
    print(f"  {tok:<10} {m['RMSE_test']:>8.2f} {m['MAE_test']:>8.2f} "
          f"{m['R2_test']:>7.3f} "
          f"{m['CV_RMSE_mean']:>6.2f}±{m['CV_RMSE_std']:.2f} "
          f"{m['n_muestras']:>10}")

print("\nPROYECCIÓN 2031 (+1.6°C) — CONCENTRACIÓN MEDIA:")
print(f"  {'Toxina':<10} {'Actual':>10} {'2031':>10} {'Δ ppb':>10} {'Δ %':>8}")
print("  " + "-" * 52)
for tok in modelos_por_toxina:
    actual = concentracion_actual[tok]
    fila   = df_proy_global[(df_proy_global['Año'] == 2031) &
                             (df_proy_global['Toxina'] == tok)].iloc[0]
    delta  = fila['conc_media'] - actual
    pct    = (delta / actual * 100) if actual > 0 else 0
    print(f"  {tok:<10} {actual:>10.2f} {fila['conc_media']:>10.2f} "
          f"{delta:>+10.2f} {pct:>+7.1f}%")

print(f"""
ARCHIVOS GENERADOS:
  • predicho_vs_real.png
  • residuos_por_toxina.png
  • importancia_por_toxina.png
  • metricas_por_toxina.png
  • proyeccion_por_toxina.png
  • proyeccion_ciudad_2031.png
""")
print("ANÁLISIS COMPLETADO")
