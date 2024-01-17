import streamlit as st
import pandas as pd
import gspread
from google.oauth2 import service_account
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

def cargar_datos():
    gc = gspread.service_account(filename="key.json")

    sh_calidad = gc.open("Calidad")
    worksheet_calidad = sh_calidad.get_worksheet(0)
    df_calidad = pd.DataFrame(worksheet_calidad.get_all_records())

    sh_llegadas = gc.open("Llegadas")
    worksheet_llegadas = sh_llegadas.get_worksheet(0)
    df_llegadas = pd.DataFrame(worksheet_llegadas.get_all_records())

    return df_calidad, df_llegadas

def filtrar_df_calidad(df_calidad, manual_seleccionado, mes_seleccionado, quincena_seleccionada, ano_seleccionado):
    df_filtrado = df_calidad[
        (df_calidad['Manual'] == manual_seleccionado) &
        (df_calidad['Mes'] == mes_seleccionado) &
        (df_calidad['Quincena'] == quincena_seleccionada) &
        (df_calidad['Año'] == ano_seleccionado)
    ]
    return df_filtrado

def agrupar_y_calcular(df_agrupado, df_llegadas):
    df_agrupado = pd.merge(df_agrupado, df_llegadas, how='inner', left_on=['Mos', 'Talla'], right_on=['Mos', 'Talla'])
    df_agrupado['Valor_Total'] = df_agrupado['Aprobadas'] * df_agrupado['Costo_Unidad']
    suma_valor_total = df_agrupado['Valor_Total'].sum()
    return df_agrupado, suma_valor_total

def mostrar_tabla_y_grafica(df_agrupado, manual_seleccionado, ano_seleccionado):
    st.table(df_agrupado[['Mos', 'Talla', 'Aprobadas', 'Costo_Unidad', 'Valor_Total']])
    
    df_agrupado_grafica = df_agrupado.groupby(['Mos', 'Talla', 'Mes']).agg({'Aprobadas': 'sum'}).reset_index()
    df_agrupado_grafica = pd.merge(df_agrupado_grafica, df_llegadas, how='inner', left_on=['Mos', 'Talla'], right_on=['Mos', 'Talla'])
    df_agrupado_grafica['Valor_Total'] = df_agrupado_grafica['Aprobadas'] * df_agrupado_grafica['Costo_Unidad']

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(df_agrupado_grafica['Mes'], df_agrupado_grafica['Valor_Total'], color='blue')
    ax.set_xlabel('Mes')
    ax.set_ylabel('Valor Total')
    formatter = '${x:,.0f}'
    ax.yaxis.set_major_formatter(mtick.StrMethodFormatter(formatter))
    plt.xticks(rotation=45, ha="right")
    ax.set_title(f'Valor Total por Mes para {manual_seleccionado} en {ano_seleccionado}')
    st.pyplot(fig)

def pagina_nomina():
    st.header("Nómina por Artesana")
    
    df_calidad, df_llegadas = cargar_datos()

    manual_seleccionado = st.selectbox('Selecciona un Manual', df_calidad['Manual'].unique())
    mes_seleccionado = st.selectbox('Selecciona un Mes', df_calidad['Mes'].unique())
    quincena_seleccionada = st.selectbox('Selecciona una Quincena', df_calidad['Quincena'].unique())
    ano_seleccionado = st.selectbox('Selecciona un Año', df_calidad['Año'].unique())

    df_filtrado = filtrar_df_calidad(df_calidad, manual_seleccionado, mes_seleccionado, quincena_seleccionada, ano_seleccionado)
    df_agrupado, suma_valor_total = agrupar_y_calcular(df_filtrado, df_llegadas)

    st.metric(label='El total de la nómina es', value=f'${suma_valor_total:,.0f}')
    
    df_agrupado['Costo_Unidad'] = '$ ' + df_agrupado['Costo_Unidad'].apply('{:,}'.format)
    df_agrupado['Valor_Total'] = '$ ' + df_agrupado['Valor_Total'].apply('{:,}'.format)
    
    mostrar_tabla_y_grafica(df_agrupado, manual_seleccionado, ano_seleccionado)

def pagina_estados_mos():
    st.header("Estados de la MOS")

    df_calidad, df_llegadas = cargar_datos()

    sh_Asignaciones = gc.open("Asignaciones")
    worksheet_Asignaciones = sh_Asignaciones.get_worksheet(0)

    df_Asignaciones  = pd.DataFrame(worksheet_Asignaciones .get_all_records())
    
    df_L = df_llegadas.groupby(['Mos','Talla']).agg({'Cantidad': 'sum'}).reset_index()
    df_A = df_Asignaciones.groupby(['Mos','Manual','Talla']).agg({'Cantidad': 'sum'}).reset_index()
    df_C = df_calidad.groupby(['Mos','Manual','Talla']).agg({'Aprobadas': 'sum','Devueltas': 'sum'}).reset_index()
    df_u = df_A.merge(df_C, how='left')

    Mos_seleccionada = st.selectbox('Selecciona un Mos', df_L['Mos'].unique())   
    df_L = df_L[(df_L['Mos'] == Mos_seleccionada)]
    
    df_total_Asignado = df_u.loc[(df_u['Mos'] == Mos_seleccionada)].fillna(0)
    df_u = df_u.loc[(df_u['Mos'] == Mos_seleccionada)].fillna(0)
    df_u['Pendiente'] = df_u['Cantidad'] - df_u['Aprobadas']
    df_u = df_u.sort_values(by='Pendiente', ascending=False)
    df_u[['Cantidad', 'Aprobadas', 'Pendiente', 'Devueltas']] = df_u[['Cantidad', 'Aprobadas', 'Pendiente','Devueltas']].applymap('{:,.0f}'.format)
    df_u.set_index('Mos', inplace=True)

    total_lote = df_L['Cantidad'].sum() 
    total_Asignado = df_total_Asignado['Cantidad'].astype(int).sum()
    total_Calidad = df_total_Asignado['Aprobadas'].astype(int).sum()
    total_Devueltas = df_total_Asignado['Devueltas'].astype(int).sum()

    st.metric(label='El total del lote', value=total_lote)
    st.metric(label='El total Asignado', value=total_Asignado)
    st.metric(label='Pendiente por Asignar', value=total_lote-total_Asignado)
    st.metric(label='Total Aprobadas', value=total_Calidad)
    st.metric(label='Total Devueltas', value=total_Devueltas)
    st.metric(label='Pendiente por Aprobar', value=total_lote-total_Calidad)

    st.dataframe(df_u)

def pagina_liquidacion_nomina():
    st.header("Liquidación de Nómina")
    
    df_calidad, df_llegadas = cargar_datos()

    col1, col2, col3 = st.columns(3)
    ano_seleccionado = st.selectbox('Selecciona un Año', df_calidad['Año'].unique())
    mes_seleccionado = st.selectbox('Selecciona un Mes', df_calidad['Mes'].unique())
    quincena_seleccionada = st.selectbox('Selecciona una Quincena', df_calidad['Quincena'].unique())

    df_calidad = df_calidad[
        (df_calidad['Mes'] == mes_seleccionado) &
        (df_calidad['Quincena'] == quincena_seleccionada) &
        (df_calidad['Año'] == ano_seleccionado)
    ]
    df_calidad = df_calidad.groupby(['Mos', 'Talla','Manual']).agg({'Aprobadas': 'sum'}).reset_index()
    df_u = df_calidad.merge(df_llegadas, how='left')
    df_u['Nomina'] = df_u['Aprobadas'] * df_u['Costo_Unidad']
    df_u = df_u.groupby(['Manual']).agg({'Nomina': 'sum'})
    df_u = df_u.sort_values(by='Nomina', ascending=False)
    
    total_Nomina = df_u['Nomina'].sum() 
    st.metric(label='El total Nomina', value=total_Nomina)

    st.dataframe(df_u)
    print(df_u)

# Crear un menú lateral con enlaces a las diferentes páginas
pagina_actual = st.sidebar.radio("Selecciona una página", ["Nómina por Artesana", "Estados de la MOS", "Liquidación de Nómina"])

# Mostrar la página seleccionada
if pagina_actual == "Nómina por Artesana":
    pagina_nomina()
elif pagina_actual == "Estados de la MOS":
    pagina_estados_mos()
elif pagina_actual == "Liquidación de Nómina":
    pagina_liquidacion_nomina()
