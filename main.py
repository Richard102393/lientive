import streamlit as st
import pandas as pd
import gspread
from google.oauth2 import service_account
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import os
import toml
import json
from streamlit_gsheets import GSheetsConnection

def pagina_nomina():
    st.header("Nómina por Artesana")
    conn = st.connection("gsheets", type=GSheetsConnection)

    Calidad = "https://docs.google.com/spreadsheets/d/1jwZCPhpChjRWo0nqOGUTX8-hn8teUfZQRxFU50x0wnU/edit#gid=0"
    Llegadas = "https://docs.google.com/spreadsheets/d/1DHZfhULnNZEMNrcDi-5mgdIDQ_ZDM9gAWrQHfdTIR-Y/edit#gid=0"

    df_calidad = conn.read(spreadsheet=Calidad)
    df_llegadas = conn.read(spreadsheet=Llegadas)
    

    # Filtros dinámicos para las columnas
    manual_seleccionado = st.selectbox('Selecciona un Manual', df_calidad['Manual'].unique())

    # Organizar los filtros Mes, Quincena y Año en una sola fila con tres columnas
    col1, col2, col3 = st.columns(3)

    # Filtro para Mes
    with col1:
        mes_seleccionado = st.selectbox('Selecciona un Mes', df_calidad['Mes'].unique())

    # Filtro para Quincena
    with col2:
        quincena_seleccionada = st.selectbox('Selecciona una Quincena', df_calidad['Quincena'].unique())

    # Filtro para Año
    with col3:
        ano_seleccionado = st.selectbox('Selecciona un Año', df_calidad['Año'].unique())

    # Aplicar filtros
    df_filtrado = df_calidad[
        (df_calidad['Manual'] == manual_seleccionado) &
        (df_calidad['Mes'] == mes_seleccionado) &
        (df_calidad['Quincena'] == quincena_seleccionada) &
        (df_calidad['Año'] == ano_seleccionado)
    ]

    # Agrupar por Mos y Talla y sumar las Aprobadas
    df_agrupado = df_filtrado.groupby(['Mos', 'Talla']).agg({'Aprobadas': 'sum'}).reset_index()

    # Convertir 'Mos' y 'Talla' a tipo cadena
    df_agrupado['Mos'] = df_agrupado['Mos'].astype(str)
    df_agrupado['Talla'] = df_agrupado['Talla'].astype(str)
    df_llegadas['Mos'] = df_llegadas['Mos'].astype(str)

    # Unir los DataFrames utilizando 'Mos' como clave
    df_agrupado = pd.merge(df_agrupado, df_llegadas, how='inner', left_on=['Mos','Talla'], right_on=['Mos','Talla'])

    # Calcular la columna 'Valor_Total'
    df_agrupado['Valor_Total'] = df_agrupado['Aprobadas'] * df_agrupado['Costo_Unidad']

    # Calcular la suma total de 'Valor_Total'
    suma_valor_total = df_agrupado['Valor_Total'].sum()

    # Mostrar la KPI
    st.metric(label='El total de la nomina es', value=f'${suma_valor_total:,.0f}')


    # Dar formato de dinero a las columnas 'Costo_Unidad' y 'Valor_Total'
    df_agrupado['Costo_Unidad'] = '$ ' + df_agrupado['Costo_Unidad'].apply('{:,}' .format)
    df_agrupado['Valor_Total'] = '$ ' + df_agrupado['Valor_Total'].apply('{:,}' .format)

    # Seleccionar columnas deseadas incluyendo la nueva 'Valor_Total'
    df_Nomina = df_agrupado[['Mos', 'Talla', 'Aprobadas', 'Costo_Unidad', 'Valor_Total']]

    st.table(df_Nomina)

    # Aplicar filtros
    df_filtrado_grafica = df_calidad[
        (df_calidad['Manual'] == manual_seleccionado) &
        (df_calidad['Año'] == ano_seleccionado)
    ]

    # Agrupar por Mos, Talla y Mes, y sumar las Aprobadas
    df_agrupado_grafica = df_filtrado_grafica.groupby(['Mos', 'Talla', 'Mes']).agg({'Aprobadas': 'sum'}).reset_index()

    # Convertir 'Mos' y 'Talla' a tipo cadena
    df_agrupado_grafica['Mos'] = df_agrupado_grafica['Mos'].astype(str)
    df_agrupado_grafica['Talla'] = df_agrupado_grafica['Talla'].astype(str)
    df_llegadas['Mos'] = df_llegadas['Mos'].astype(str)

    # Unir los DataFrames utilizando 'Mos' como clave
    df_agrupado_grafica = pd.merge(df_agrupado_grafica, df_llegadas, how='inner', left_on=['Mos', 'Talla'], right_on=['Mos', 'Talla'])

    # Calcular la columna 'Valor_Total'
    df_agrupado_grafica['Valor_Total'] = df_agrupado_grafica['Aprobadas'] * df_agrupado_grafica['Costo_Unidad']

    # Agrupar por Mes y sumar 'Valor_Total'
    df_agrupado_grafica_f = df_agrupado_grafica.groupby(['Mes']).agg({'Valor_Total': 'sum'}).reset_index()

    # Crear una gráfica de barras
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(df_agrupado_grafica_f['Mes'], df_agrupado_grafica_f['Valor_Total'], color='blue')
    ax.set_xlabel('Mes')
    ax.set_ylabel('Valor Total')

    # Formatear el eje y para mostrar los valores en formato de moneda
    formatter = '${x:,.0f}'
    ax.yaxis.set_major_formatter(mtick.StrMethodFormatter(formatter))
    # Rotar las etiquetas del eje x para que sean legibles
    plt.xticks(rotation=45, ha="right")

    ax.set_title(f'Valor Total por Mes para {manual_seleccionado} en {ano_seleccionado}')

    # Mostrar la gráfica en Streamlit
    st.pyplot(fig)

def pagina_estados_mos():
    st.header("Estados de la MOS")
    gc = gspread.service_account(filename="key.json")
        # Abrir y establecer el libro con el que se va a trabajar
    sh_Calidad = gc.open("Calidad")
    worksheet_calidad = sh_Calidad.get_worksheet(0)

    # Abrir y establecer el libro con el que se va a trabajar
    sh_Llegadas = gc.open("Llegadas")
    worksheet_Llegadas = sh_Llegadas.get_worksheet(0)

    sh_Asignaciones = gc.open("Asignaciones")
    worksheet_Asignaciones = sh_Asignaciones.get_worksheet(0)

    # Convertir la hoja de cálculo a un DataFrame de Pandas para Calidad
    df_calidad = pd.DataFrame(worksheet_calidad.get_all_records())

    #Convertir la hoja de cálculo a un DataFrame de Pandas para Llegadas
    df_llegadas = pd.DataFrame(worksheet_Llegadas.get_all_records())

    df_Asignaciones  = pd.DataFrame(worksheet_Asignaciones .get_all_records())
    
    df_L = df_llegadas.groupby(['Mos','Talla']).agg({'Cantidad': 'sum'}).reset_index()
    df_A = df_Asignaciones.groupby(['Mos','Manual','Talla']).agg({'Cantidad': 'sum'}).reset_index()
    df_C = df_calidad.groupby(['Mos','Manual','Talla']).agg({'Aprobadas': 'sum','Devueltas': 'sum'}).reset_index()
    df_u = df_A.merge(df_C, how='left')

    # Filtros dinámicos para las columnas
    Mos_selecionada = st.selectbox('Selecciona un Mos', df_L['Mos'].unique())   
    
    df_L = df_L[
        (df_L['Mos'] == Mos_selecionada)
    ]
    
    df_total_Asignado = df_u.loc[(df_u['Mos'] == Mos_selecionada)].fillna(0)
    df_u = df_u.loc[(df_u['Mos'] == Mos_selecionada)].fillna(0)
    df_u['Pendiente'] = df_u['Cantidad'] - df_u['Aprobadas']
    df_u = df_u.sort_values(by='Pendiente', ascending=False)
    df_u[['Cantidad', 'Aprobadas', 'Pendiente', 'Devueltas']] = df_u[['Cantidad', 'Aprobadas', 'Pendiente','Devueltas']].applymap('{:,.0f}'.format)
    df_u.set_index('Mos', inplace=True)


    total_lote = df_L['Cantidad'].sum() 
    total_Asignado = df_total_Asignado['Cantidad'].astype(int).sum()
    total_Calidad = df_total_Asignado['Aprobadas'].astype(int).sum()
    total_Devueltas = df_total_Asignado['Devueltas'].astype(int).sum()
    
    col1, col2, col3 = st.columns(3)

    # Filtro para Mes
    with col1:
       # Mostrar la métrica
        st.metric(label='El total del lote', value=total_lote)

    # Filtro para Quincena
    with col2:
        st.metric(label='El total Asignado', value=total_Asignado)
    # Filtro para Año
    with col3:
       st.metric(label='Pendiente por Asignar', value=total_lote-total_Asignado)

     # Organizar los filtros Mes, Quincena y Año en una sola fila con tres columnas
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(label='Total Aprobadas', value=total_Calidad)
    with col2:
        st.metric(label='Total Devueltas', value=total_Devueltas)
    with col3:
       st.metric(label='Pendiente por Aprobar', value=total_lote-total_Calidad)

    st.dataframe(df_u)


def pagina_liquidacion_nomina():
    st.header("Liquidación de Nómina")
    gc = gspread.service_account(filename="key.json")
    sh_Calidad = gc.open("Calidad")
    worksheet_calidad = sh_Calidad.get_worksheet(0)
    sh_Llegadas = gc.open("Llegadas")
    worksheet_Llegadas = sh_Llegadas.get_worksheet(0)
    df_calidad = pd.DataFrame(worksheet_calidad.get_all_records())
    df_llegadas = pd.DataFrame(worksheet_Llegadas.get_all_records())

    # Organizar los filtros Mes, Quincena y Año en una sola fila con tres columnas
    col1, col2, col3 = st.columns(3)

     # Filtro para Año
    with col1:
        ano_seleccionado = st.selectbox('Selecciona un Año', df_calidad['Año'].unique())
    
    # Filtro para Mes
    with col2:
        mes_seleccionado = st.selectbox('Selecciona un Mes', df_calidad['Mes'].unique())

    # Filtro para Quincena
    with col3:
        quincena_seleccionada = st.selectbox('Selecciona una Quincena', df_calidad['Quincena'].unique())

   

    # Aplicar filtros
    df_calidad = df_calidad[
        (df_calidad['Mes'] == mes_seleccionado) &
        (df_calidad['Quincena'] == quincena_seleccionada) &
        (df_calidad['Año'] == ano_seleccionado)
    ]
     # Agrupar por Mos y Talla y sumar las Aprobadas
    df_calidad = df_calidad.groupby(['Mos', 'Talla','Manual']).agg({'Aprobadas': 'sum'}).reset_index()
    df_u = df_calidad.merge(df_llegadas, how='left')
    df_u['Nomina'] = df_u['Aprobadas'] * df_u['Costo_Unidad']
    df_u = df_u.groupby(['Manual']).agg({'Nomina': 'sum'})
    df_u = df_u.sort_values(by='Nomina', ascending=False)
    
    total_Nomina = df_u['Nomina'].sum() 
    st.metric(label='El total Nomina', value=total_Nomina)

    st.dataframe(df_u)

# Crear un menú lateral con enlaces a las diferentes páginas
pagina_actual = st.sidebar.radio("Selecciona una página", ["Nómina por Artesana", "Estados de la MOS", "Liquidación de Nómina"])

# Mostrar la página seleccionada
if pagina_actual == "Nómina por Artesana":
    pagina_nomina()
elif pagina_actual == "Estados de la MOS":
    pagina_estados_mos()
elif pagina_actual == "Liquidación de Nómina":
    pagina_liquidacion_nomina()