import streamlit as st
import pandas as pd
import gspread
from google.oauth2 import service_account
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from streamlit_gsheets import GSheetsConnection

# Iniciar el Drive

conn = st.connection("gsheets", type=GSheetsConnection)

Calidad = "https://docs.google.com/spreadsheets/d/1jwZCPhpChjRWo0nqOGUTX8-hn8teUfZQRxFU50x0wnU/edit#gid=0"
Llegadas = "https://docs.google.com/spreadsheets/d/1DHZfhULnNZEMNrcDi-5mgdIDQ_ZDM9gAWrQHfdTIR-Y/edit#gid=0"
Asignaciones = "https://docs.google.com/spreadsheets/d/1Aac0QojXVm9FMkVbnwEXVfYiiDn04LXgjFp-Eg54nAw/edit#gid=0"
Transferencias = "https://docs.google.com/spreadsheets/d/1g0_O-q0jbrWarGo_l8p-Pk58pIsZIFThH5A8jb07gJs/edit#gid=0"

df_calidad = conn.read(spreadsheet=Calidad)
df_llegadas = conn.read(spreadsheet=Llegadas)
df_Asignaciones  = conn.read(spreadsheet=Asignaciones)
df_Transferencias = conn.read(spreadsheet=Transferencias)


df_Asignaciones = df_Asignaciones.groupby(['Mos','Manual','Talla']).agg({'Cantidad': 'sum'}).reset_index()
df_calidad = df_calidad.groupby(['Mos','Manual','Talla','Mes','Año']).agg({'Aprobadas': 'sum','Devueltas': 'sum'}).reset_index()
df_Transferencias = df_Transferencias.groupby(['Mos','Manual','Talla']).agg({'Cantidad': 'sum'}).reset_index()

dt_t = df_llegadas.merge(df_Asignaciones, how='inner', left_on=['Mos', 'Talla'], right_on=['Mos', 'Talla'])
dt_t = dt_t.merge(df_calidad, how='left', on=['Mos', 'Talla', 'Manual'])
dt_t = dt_t.merge(df_Transferencias, how='left', on=['Mos', 'Talla', 'Manual'])
dt_t = dt_t.loc[(dt_t['Mos'] == 13714)]

valores_unicos = dt_t['Cantidad_x'].unique()
Total_unidades = valores_unicos.sum()
print(Total_unidades)

Transferencias = dt_t['Cantidad'].sum()
print(Transferencias)

asignaciones = dt_t['Cantidad_y'].sum()
print(asignaciones)

Aprobadas = dt_t['Aprobadas'].sum()
print(Aprobadas)

# Seleccionar las columnas Mos, Manual, Talla, Cantidad_y, Aprobadas, Devueltas
columnas_seleccionadas = ['Mos', 'Manual', 'Talla', 'Cantidad_y', 'Aprobadas', 'Devueltas', 'Cantidad']
dt_t_seleccionado = dt_t[columnas_seleccionadas].fillna(0)

#Crear la columna 'Pendiente' como la resta de 'Cantidad_y' y 'Aprobadas'
dt_t_seleccionado['Pendiente'] = dt_t_seleccionado['Cantidad_y'] - dt_t_seleccionado['Aprobadas'] - dt_t_seleccionado['Cantidad']

dt_t_seleccionado = dt_t_seleccionado.sort_values(by='Pendiente', ascending=False)

# Imprimir el resultado
print(dt_t_seleccionado)