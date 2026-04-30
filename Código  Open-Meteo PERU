!pip install openmeteo-requests
!pip install requests-cache retry-requests numpy pandas


import openmeteo_requests
import pandas as pd
import numpy as np
import requests_cache
from retry_requests import retry
import time

# Verificar si se está ejecutando en Google Colab para habilitar descarga automática
try:
    from google.colab import files
    IN_COLAB = True
    print("Ejecutando en Google Colab - se habilitara descarga automatica")
except ImportError:
    IN_COLAB = False
    print("Ejecutando en entorno local - los archivos se guardaran en el directorio actual")

# Configuración de caché y reintentos para las solicitudes HTTP
cache_session = requests_cache.CachedSession('.cache', expire_after=3600)  # Caché de 1 hora
retry_session = retry(cache_session, retries=5, backoff_factor=1.0)  # Reintentos con espera progresiva
openmeteo = openmeteo_requests.Client(session=retry_session)

# Coordenadas de las 7 ubicaciones representativas de Perú
peru_coords = [
    {"name": "Lima", "lat": -12.05, "lon": -77.25},      # Costa central
    {"name": "Trujillo", "lat": -8.12, "lon": -79.03},   # Costa norte
    {"name": "Tacna", "lat": -18.01, "lon": -70.25},     # Costa sur
    {"name": "Cusco", "lat": -13.53, "lon": -71.97},     # Sierra sur
    {"name": "Huaraz", "lat": -9.53, "lon": -77.53},     # Sierra central
    {"name": "Iquitos", "lat": -3.75, "lon": -73.25},    # Selva norte
    {"name": "Pucallpa", "lat": -8.38, "lon": -74.55}    # Selva central
]

# URL de la API de Open-Meteo para datos históricos
url = "https://archive-api.open-meteo.com/v1/archive"

# Parámetros base para la solicitud de datos
params_base = {
    "start_date": "1985-01-01",                                    # Fecha inicial del período
    "end_date": "2026-03-31",                                      # Fecha final del período
    "daily": ["temperature_2m_mean", "temperature_2m_max", "temperature_2m_min",  # Variables diarias
              "relative_humidity_2m_mean", "relative_humidity_2m_max",
              "relative_humidity_2m_min", "precipitation_sum"],
    "timezone": "America/Lima"                                     # Zona horaria de Perú
}

all_data = []  # Lista para almacenar los DataFrames de cada ubicación

def make_request_with_retry(coord, max_retries=3):
    """
    Función que realiza la solicitud a la API con reintentos automáticos
    coord: diccionario con nombre, latitud y longitud de la ubicación
    max_retries: número máximo de reintentos en caso de error
    """
    for attempt in range(max_retries):
        try:
            # Copiar los parámetros base y añadir coordenadas
            params = params_base.copy()
            params["latitude"] = coord["lat"]
            params["longitude"] = coord["lon"]

            print(f"    Realizando peticion a la API...")
            responses = openmeteo.weather_api(url, params=params)
            return responses[0]  # Retorna la primera (y única) respuesta

        except Exception as e:
            error_msg = str(e)
            # Si se excede el límite de la API, esperar más tiempo antes de reintentar
            if "limit exceeded" in error_msg:
                wait_time = 30 * (attempt + 1)
                print(f"    Limite excedido. Reintento {attempt+1}/{max_retries} en {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"    Error: {e}")
                return None

    print(f"    Fallaron todos los reintentos para {coord['name']}")
    return None

print("INICIANDO DESCARGA DE DATOS HISTORICOS DE PERU (2000-2025)")
print(f"Ubicaciones a procesar: {len(peru_coords)}")
print(f"Periodo: {params_base['start_date']} a {params_base['end_date']}")
print(f"Espera de 60 segundos entre cada ubicacion")

# Bucle para procesar cada ubicación
for i, coord in enumerate(peru_coords):
    print(f"\n[{i+1}/{len(peru_coords)}] Procesando: {coord['name']} ({coord['lat']}, {coord['lon']})")

    response = make_request_with_retry(coord)

    if response:
        try:
            # Extraer los datos diarios de la respuesta de la API
            daily = response.Daily()
            daily_temperature_2m_mean = daily.Variables(0).ValuesAsNumpy()      # Temperatura media
            daily_temperature_2m_max = daily.Variables(1).ValuesAsNumpy()       # Temperatura máxima
            daily_temperature_2m_min = daily.Variables(2).ValuesAsNumpy()       # Temperatura mínima
            daily_relative_humidity_2m_mean = daily.Variables(3).ValuesAsNumpy() # Humedad media
            daily_relative_humidity_2m_max = daily.Variables(4).ValuesAsNumpy()  # Humedad máxima
            daily_relative_humidity_2m_min = daily.Variables(5).ValuesAsNumpy()  # Humedad mínima
            daily_precipitation_sum = daily.Variables(6).ValuesAsNumpy()         # Precipitación acumulada

            # Crear el rango de fechas correspondiente
            start_date = pd.to_datetime(daily.Time() + response.UtcOffsetSeconds(), unit="s", utc=True)
            end_date = pd.to_datetime(daily.TimeEnd() + response.UtcOffsetSeconds(), unit="s", utc=True)

            # Crear DataFrame con los datos de la ubicación
            df = pd.DataFrame({
                "date": pd.date_range(
                    start=start_date,
                    end=end_date,
                    freq=pd.Timedelta(seconds=daily.Interval()),
                    inclusive="left"
                ),
                "location": coord["name"],
                "latitude": coord["lat"],
                "longitude": coord["lon"],
                "temperature_2m_mean": daily_temperature_2m_mean,
                "temperature_2m_max": daily_temperature_2m_max,
                "temperature_2m_min": daily_temperature_2m_min,
                "relative_humidity_2m_mean": daily_relative_humidity_2m_mean,
                "relative_humidity_2m_max": daily_relative_humidity_2m_max,
                "relative_humidity_2m_min": daily_relative_humidity_2m_min,
                "precipitation_sum": daily_precipitation_sum
            })

            all_data.append(df)  # Almacenar DataFrame para luego combinar
            dias = len(df)
            print(f"    {coord['name']} completado exitosamente")
            print(f"       {dias} dias descargados ({dias//365:.0f} años)")

        except Exception as e:
            print(f"    Error procesando datos de {coord['name']}: {e}")
    else:
        print(f"    No se pudo obtener datos para {coord['name']}")

    # Esperar 60 segundos entre ubicaciones para no sobrecargar la API
    if i < len(peru_coords) - 1:
        print(f"    Esperando 60 segundos antes de la siguiente ubicacion")
        for remaining in range(60, 0, -10):
            print(f"       Esperando {remaining} segundos restantes")
            time.sleep(10)
        print(f"       Continuando con la siguiente ubicacion")

print("\nPROCESANDO RESULTADOS FINALES")

if all_data:
    print(f"Ubicaciones procesadas exitosamente: {len(all_data)}/{len(peru_coords)}")

    # Combinar todos los DataFrames en uno solo
    combined_df = pd.concat(all_data, ignore_index=True)

    # Eliminar la información de zona horaria de la columna de fechas
    combined_df['date'] = combined_df['date'].dt.tz_localize(None)

    print("\nCalculando promedio nacional diario")
    # Calcular el promedio nacional para cada día (media de todas las ubicaciones)
    national_daily_avg = combined_df.groupby('date').agg({
        'temperature_2m_mean': 'mean',
        'temperature_2m_max': 'mean',
        'temperature_2m_min': 'mean',
        'relative_humidity_2m_mean': 'mean',
        'relative_humidity_2m_max': 'mean',
        'relative_humidity_2m_min': 'mean',
        'precipitation_sum': 'mean'
    }).reset_index()

    national_daily_avg = national_daily_avg.sort_values('date').reset_index(drop=True)

    # Extraer año y mes para análisis temporal
    national_daily_avg['year'] = pd.to_datetime(national_daily_avg['date']).dt.year
    national_daily_avg['month'] = pd.to_datetime(national_daily_avg['date']).dt.month

    # Diccionario para convertir números de mes a nombres en español
    meses_espanol = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
        5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
        9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
    }
    national_daily_avg['mes'] = national_daily_avg['month'].map(meses_espanol)

    print("\nGenerando tablas con años como columnas y meses como filas")

    # Calcular medias mensuales para el promedio nacional
    monthly_means = national_daily_avg.groupby(['year', 'month', 'mes']).agg({
        'temperature_2m_mean': 'mean',
        'temperature_2m_max': 'mean',
        'temperature_2m_min': 'mean',
        'relative_humidity_2m_mean': 'mean',
        'relative_humidity_2m_max': 'mean',
        'relative_humidity_2m_min': 'mean',
        'precipitation_sum': 'sum'
    }).round(2).reset_index()

    monthly_means = monthly_means.sort_values(['year', 'month'])

    # Tabla de temperatura media (formato matriz: meses como filas, años como columnas)
    temp_matrix = monthly_means.pivot(
        index='mes',
        columns='year',
        values='temperature_2m_mean'
    ).round(2)

    # Reordenar los meses en orden cronológico
    temp_matrix = temp_matrix.reindex(['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                                        'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'])
    temp_matrix = temp_matrix.reset_index()
    temp_matrix.columns.name = None

    # Tabla de temperatura máxima (formato matriz)
    tmax_matrix = monthly_means.pivot(
        index='mes',
        columns='year',
        values='temperature_2m_max'
    ).round(2)
    tmax_matrix = tmax_matrix.reindex(['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                                        'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'])
    tmax_matrix = tmax_matrix.reset_index()
    tmax_matrix.columns.name = None

    # Tabla de temperatura mínima (formato matriz)
    tmin_matrix = monthly_means.pivot(
        index='mes',
        columns='year',
        values='temperature_2m_min'
    ).round(2)
    tmin_matrix = tmin_matrix.reindex(['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                                        'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'])
    tmin_matrix = tmin_matrix.reset_index()
    tmin_matrix.columns.name = None

    # Tabla de humedad media (formato matriz)
    humidity_matrix = monthly_means.pivot(
        index='mes',
        columns='year',
        values='relative_humidity_2m_mean'
    ).round(2)
    humidity_matrix = humidity_matrix.reindex(['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                                                'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'])
    humidity_matrix = humidity_matrix.reset_index()
    humidity_matrix.columns.name = None

    # Tabla de precipitación mensual (formato matriz)
    precip_matrix = monthly_means.pivot(
        index='mes',
        columns='year',
        values='precipitation_sum'
    ).round(2)
    precip_matrix = precip_matrix.reindex(['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                                            'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'])
    precip_matrix = precip_matrix.reset_index()
    precip_matrix.columns.name = None

    print("\nCalculando medias por ubicacion")

    # Lista para almacenar los datos procesados de cada ubicación
    ubicaciones_stats = []
    for ubicacion in peru_coords:
        # Filtrar datos de la ubicación actual
        ubicacion_data = combined_df[combined_df['location'] == ubicacion['name']].copy()

        if len(ubicacion_data) > 0:
            # Extraer año y mes
            ubicacion_data['year'] = pd.to_datetime(ubicacion_data['date']).dt.year
            ubicacion_data['month'] = pd.to_datetime(ubicacion_data['date']).dt.month
            ubicacion_data['mes'] = ubicacion_data['month'].map(meses_espanol)

            # Calcular medias mensuales por ubicación
            ubicacion_mensual = ubicacion_data.groupby(['year', 'month', 'mes']).agg({
                'temperature_2m_mean': 'mean',
                'relative_humidity_2m_mean': 'mean',
                'precipitation_sum': 'sum'
            }).round(2).reset_index()

            ubicacion_mensual = ubicacion_mensual.sort_values(['year', 'month'])

            # Crear matriz de temperatura por ubicación
            temp_ubicacion = ubicacion_mensual.pivot(
                index='mes',
                columns='year',
                values='temperature_2m_mean'
            ).round(2)
            temp_ubicacion = temp_ubicacion.reindex(['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                                                      'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'])
            temp_ubicacion = temp_ubicacion.reset_index()
            temp_ubicacion.columns.name = None

            # Crear matriz de humedad por ubicación
            hum_ubicacion = ubicacion_mensual.pivot(
                index='mes',
                columns='year',
                values='relative_humidity_2m_mean'
            ).round(2)
            hum_ubicacion = hum_ubicacion.reindex(['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                                                    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'])
            hum_ubicacion = hum_ubicacion.reset_index()
            hum_ubicacion.columns.name = None

            # Crear matriz de precipitación por ubicación
            precip_ubicacion = ubicacion_mensual.pivot(
                index='mes',
                columns='year',
                values='precipitation_sum'
            ).round(2)
            precip_ubicacion = precip_ubicacion.reindex(['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                                                          'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'])
            precip_ubicacion = precip_ubicacion.reset_index()
            precip_ubicacion.columns.name = None

            # Combinar las tres variables en un solo DataFrame
            ubicacion_combinada = temp_ubicacion.copy()
            ubicacion_combinada = ubicacion_combinada.rename(columns={'mes': 'Mes'})

            # Añadir columnas para temperatura, humedad y precipitación de cada año
            for col in ubicacion_combinada.columns:
                if col != 'Mes':
                    ubicacion_combinada[f'{col}_Temp_Media'] = temp_ubicacion[col]
                    ubicacion_combinada[f'{col}_Humedad_Media'] = hum_ubicacion[col]
                    ubicacion_combinada[f'{col}_Precip_Sum'] = precip_ubicacion[col]

            # Ordenar las columnas: Mes, luego para cada año: Temp, Humedad, Precip
            columnas_orden = ['Mes']
            for col in ubicacion_combinada.columns:
                if col != 'Mes' and isinstance(col, str) and '_Temp_Media' in col:
                    year_num = col.replace('_Temp_Media', '')
                    columnas_orden.append(f'{year_num}_Temp_Media')
                    columnas_orden.append(f'{year_num}_Humedad_Media')
                    columnas_orden.append(f'{year_num}_Precip_Sum')

            ubicacion_combinada = ubicacion_combinada[columnas_orden]

            # Almacenar los datos de la ubicación
            ubicaciones_stats.append({
                'name': ubicacion['name'],
                'data': ubicacion_combinada
            })
            print(f"    {ubicacion['name']}: datos procesados")

    print("\nCalculando estadisticas descriptivas del periodo completo...")

    # DataFrame para almacenar estadísticas descriptivas de todas las variables
    estadisticas_diarias = pd.DataFrame()

    # Lista de variables a analizar
    variables_estadisticas = [
        'temperature_2m_mean', 'temperature_2m_max', 'temperature_2m_min',
        'relative_humidity_2m_mean', 'relative_humidity_2m_max', 'relative_humidity_2m_min',
        'precipitation_sum'
    ]

    # Nombres legibles para las variables
    nombres_variables = [
        'Temperatura Media (C)', 'Temperatura Maxima (C)', 'Temperatura Minima (C)',
        'Humedad Media (%)', 'Humedad Maxima (%)', 'Humedad Minima (%)',
        'Precipitacion (mm)'
    ]

    # Calcular estadísticas para cada variable
    for var, nombre in zip(variables_estadisticas, nombres_variables):
        estadisticas_diarias[nombre] = [
            national_daily_avg[var].mean(),           # Media aritmética
            national_daily_avg[var].median(),         # Mediana
            national_daily_avg[var].std(),            # Desviación estándar
            national_daily_avg[var].min(),            # Valor mínimo
            national_daily_avg[var].max(),            # Valor máximo
            national_daily_avg[var].quantile(0.25),   # Primer cuartil (Q1)
            national_daily_avg[var].quantile(0.75)    # Tercer cuartil (Q3)
        ]

    estadisticas_diarias.index = [
        'Media', 'Mediana', 'Desviacion Estandar',
        'Minimo', 'Maximo', 'Percentil 25 (Q1)', 'Percentil 75 (Q3)'
    ]

    estadisticas_diarias = estadisticas_diarias.round(2)

    print("\nCalculando climatologia mensual...")

    # Calcular climatología mensual (promedios por mes en todo el período)
    climatologia_mensual = national_daily_avg.groupby('mes').agg({
        'temperature_2m_mean': ['mean', 'std', 'min', 'max'],
        'temperature_2m_max': ['mean', 'std', 'min', 'max'],
        'temperature_2m_min': ['mean', 'std', 'min', 'max'],
        'relative_humidity_2m_mean': ['mean', 'std', 'min', 'max'],
        'precipitation_sum': ['mean', 'std', 'min', 'max']
    }).round(2)

    # Renombrar columnas para hacerlas más descriptivas
    climatologia_mensual.columns = [
        'Temp_Media', 'Temp_Media_Std', 'Temp_Media_Min', 'Temp_Media_Max',
        'Temp_Max', 'Temp_Max_Std', 'Temp_Max_Min', 'Temp_Max_Max',
        'Temp_Min', 'Temp_Min_Std', 'Temp_Min_Min', 'Temp_Min_Max',
        'Humedad_Media', 'Humedad_Media_Std', 'Humedad_Media_Min', 'Humedad_Media_Max',
        'Precip_Media', 'Precip_Media_Std', 'Precip_Media_Min', 'Precip_Media_Max'
    ]

    # Reordenar meses y resetear índice
    orden_meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                   'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
    climatologia_mensual = climatologia_mensual.reindex(orden_meses)
    climatologia_mensual = climatologia_mensual.reset_index()
    climatologia_mensual = climatologia_mensual.rename(columns={'mes': 'Mes'})

    print("\nCalculando estadisticas anuales...")

    # Calcular estadísticas anuales (promedios por año)
    estadisticas_anuales = national_daily_avg.groupby('year').agg({
        'temperature_2m_mean': ['mean', 'min', 'max', 'std'],
        'relative_humidity_2m_mean': ['mean', 'min', 'max', 'std'],
        'precipitation_sum': ['sum', 'mean', 'std']
    }).round(2)

    # Renombrar columnas
    estadisticas_anuales.columns = [
        'Temp_Media_Anual', 'Temp_Min_Anual', 'Temp_Max_Anual', 'Temp_Std_Anual',
        'Humedad_Media_Anual', 'Humedad_Min_Anual', 'Humedad_Max_Anual', 'Humedad_Std_Anual',
        'Precip_Total_Anual', 'Precip_Media_Diaria', 'Precip_Std_Diaria'
    ]
    estadisticas_anuales = estadisticas_anuales.reset_index()

    # Nombre del archivo de salida
    output_file = 'peru_weather_1985_2025.xlsx'
    print(f"\nGuardando archivo Excel: {output_file}")

    # Crear archivo Excel con múltiples hojas
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # Hojas con formato matriz (años como columnas, meses como filas)
        temp_matrix.to_excel(writer, sheet_name='Temperatura_Media_Mensual', index=False)
        tmax_matrix.to_excel(writer, sheet_name='Temperatura_Max_Mensual', index=False)
        tmin_matrix.to_excel(writer, sheet_name='Temperatura_Min_Mensual', index=False)
        humidity_matrix.to_excel(writer, sheet_name='Humedad_Media_Mensual', index=False)
        precip_matrix.to_excel(writer, sheet_name='Precipitacion_Mensual', index=False)

        # Hojas con medias por ubicación (una hoja por cada ciudad)
        for ubicacion in ubicaciones_stats:
            nombre_hoja = f'Medias_{ubicacion["name"]}'
            ubicacion['data'].to_excel(writer, sheet_name=nombre_hoja, index=False)
            print(f"    Hoja '{nombre_hoja}' agregada")

        # Hojas con estadísticas
        estadisticas_diarias.to_excel(writer, sheet_name='Estadisticas_Descriptivas')
        climatologia_mensual.to_excel(writer, sheet_name='Climatologia_Mensual', index=False)
        estadisticas_anuales.to_excel(writer, sheet_name='Estadisticas_Anuales', index=False)

        # Hojas con datos detallados
        national_daily_avg.to_excel(writer, sheet_name='Diario_Promedio_Nacional', index=False)
        combined_df.to_excel(writer, sheet_name='Detalle_por_Ubicacion', index=False)
        monthly_means.to_excel(writer, sheet_name='Mensual_Por_Ano', index=False)

        # Ajustar automáticamente el ancho de las columnas para mejor legibilidad
        for sheet_name in writer.sheets:
            worksheet = writer.sheets[sheet_name]
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)  # Límite máximo de 50 caracteres
                worksheet.column_dimensions[column_letter].width = adjusted_width

    print(f"\nArchivo Excel guardado: {output_file}")
    print("\nHojas incluidas:")
    print("   - Temperatura_Media_Mensual: Temperatura media por mes y año")
    print("   - Temperatura_Max_Mensual: Temperatura maxima por mes y año")
    print("   - Temperatura_Min_Mensual: Temperatura minima por mes y año")
    print("   - Humedad_Media_Mensual: Humedad relativa media por mes y año")
    print("   - Precipitacion_Mensual: Precipitacion acumulada por mes y año")
    print("   [MEDIAS POR UBICACION]")
    for ubicacion in ubicaciones_stats:
        print(f"   - Medias_{ubicacion['name']}: Temperatura, humedad y precipitacion mensual")
    print("   [ESTADISTICAS DESCRIPTIVAS]")
    print("   - Estadisticas_Descriptivas: Media, mediana, std, min, max, percentiles")
    print("   - Climatologia_Mensual: Promedios mensuales con desviacion y extremos")
    print("   - Estadisticas_Anuales: Resumen anual con estadisticas completas")
    print("   - Diario_Promedio_Nacional: Datos diarios del promedio nacional")
    print("   - Detalle_por_Ubicacion: Datos diarios por cada ciudad")
    print("   - Mensual_Por_Ano: Medias mensuales por año (formato largo)")

    # Descargar automáticamente si está en Google Colab
    if IN_COLAB:
        files.download(output_file)
        print(f"\nDescargando archivo {output_file} a tu ordenador...")
    else:
        print(f"\nArchivo disponible en: {output_file}")

    # Mostrar resumen de estadísticas generales en la consola
    print("\nESTADISTICAS GENERALES DEL PERIODO 2000-2025")

    print(f"\nTEMPERATURAS:")
    print(f"   Temperatura media nacional: {national_daily_avg['temperature_2m_mean'].mean():.1f}C")
    print(f"   Temperatura maxima promedio: {national_daily_avg['temperature_2m_max'].mean():.1f}C")
    print(f"   Temperatura minima promedio: {national_daily_avg['temperature_2m_min'].mean():.1f}C")

    print(f"\nHUMEDAD:")
    print(f"   Humedad relativa media: {national_daily_avg['relative_humidity_2m_mean'].mean():.1f}%")
    print(f"   Humedad maxima promedio: {national_daily_avg['relative_humidity_2m_max'].mean():.1f}%")
    print(f"   Humedad minima promedio: {national_daily_avg['relative_humidity_2m_min'].mean():.1f}%")

    print(f"\nPRECIPITACION:")
    print(f"   Precipitacion total acumulada (2000-2025): {national_daily_avg['precipitation_sum'].sum():.1f} mm")
    print(f"   Precipitacion media anual: {national_daily_avg.groupby('year')['precipitation_sum'].sum().mean():.1f} mm/anio")

    print("\nESTADISTICAS DESCRIPTIVAS DE TEMPERATURA MEDIA:")
    print(f"   Media: {estadisticas_diarias.loc['Media', 'Temperatura Media (C)']}C")
    print(f"   Mediana: {estadisticas_diarias.loc['Mediana', 'Temperatura Media (C)']}C")
    print(f"   Desviacion estandar: {estadisticas_diarias.loc['Desviacion Estandar', 'Temperatura Media (C)']}C")
    print(f"   Minimo: {estadisticas_diarias.loc['Minimo', 'Temperatura Media (C)']}C")
    print(f"   Maximo: {estadisticas_diarias.loc['Maximo', 'Temperatura Media (C)']}C")

    print("\nMESES MAS CALIDOS Y FRIOS:")
    climatologia_temp = climatologia_mensual[['Mes', 'Temp_Media']].copy()
    mes_calido = climatologia_temp.loc[climatologia_temp['Temp_Media'].idxmax()]
    mes_frio = climatologia_temp.loc[climatologia_temp['Temp_Media'].idxmin()]
    print(f"   Mes mas calido: {mes_calido['Mes']} ({mes_calido['Temp_Media']}C)")
    print(f"   Mes mas frio: {mes_frio['Mes']} ({mes_frio['Temp_Media']}C)")

    print("\nMESES MAS HUMEDOS Y SECOS:")
    climatologia_humedad = climatologia_mensual[['Mes', 'Humedad_Media']].copy()
    mes_humedo = climatologia_humedad.loc[climatologia_humedad['Humedad_Media'].idxmax()]
    mes_seco = climatologia_humedad.loc[climatologia_humedad['Humedad_Media'].idxmin()]
    print(f"   Mes mas humedo: {mes_humedo['Mes']} ({mes_humedo['Humedad_Media']}%)")
    print(f"   Mes mas seco: {mes_seco['Mes']} ({mes_seco['Humedad_Media']}%)")

    print("\nMESES CON MAS Y MENOS PRECIPITACION:")
    climatologia_precip = climatologia_mensual[['Mes', 'Precip_Media']].copy()
    mes_lluvioso = climatologia_precip.loc[climatologia_precip['Precip_Media'].idxmax()]
    mes_seco_precip = climatologia_precip.loc[climatologia_precip['Precip_Media'].idxmin()]
    print(f"   Mes mas lluvioso: {mes_lluvioso['Mes']} ({mes_lluvioso['Precip_Media']:.1f} mm)")
    print(f"   Mes mas seco: {mes_seco_precip['Mes']} ({mes_seco_precip['Precip_Media']:.1f} mm)")

    print("\nMEDIAS POR UBICACION:")
    for ubicacion in ubicaciones_stats:
        datos_ubicacion = combined_df[combined_df['location'] == ubicacion['name']]
        if len(datos_ubicacion) > 0:
            print(f"\n   {ubicacion['name']}:")
            print(f"      Temperatura media: {datos_ubicacion['temperature_2m_mean'].mean():.1f}C")
            print(f"      Humedad media: {datos_ubicacion['relative_humidity_2m_mean'].mean():.1f}%")
            print(f"      Precipitacion total: {datos_ubicacion['precipitation_sum'].sum():.1f} mm")

else:
    print("\nERROR: No se pudo obtener datos de ninguna ubicacion")
    print("   Verifica tu conexion a internet y vuelve a intentarlo")

print("\nPROCESO COMPLETADO")
