import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

def obtener_datos():
    conn = st.connection("gsheets", type=GSheetsConnection)

    Calidad = "https://docs.google.com/spreadsheets/d/1jwZCPhpChjRWo0nqOGUTX8-hn8teUfZQRxFU50x0wnU/edit#gid=0"
    Llegadas = "https://docs.google.com/spreadsheets/d/1DHZfhULnNZEMNrcDi-5mgdIDQ_ZDM9gAWrQHfdTIR-Y/edit#gid=0"
    Asignaciones = "https://docs.google.com/spreadsheets/d/1Aac0QojXVm9FMkVbnwEXVfYiiDn04LXgjFp-Eg54nAw/edit#gid=0"
    Transferencias = "https://docs.google.com/spreadsheets/d/1g0_O-q0jbrWarGo_l8p-Pk58pIsZIFThH5A8jb07gJs/edit#gid=0"

    df_calidad = conn.read(spreadsheet=Calidad)
    df_llegadas = conn.read(spreadsheet=Llegadas)
    df_Asignaciones  = conn.read(spreadsheet=Asignaciones)
    df_Transferencias = conn.read(spreadsheet=Transferencias)

    return df_calidad, df_llegadas, df_Asignaciones, df_Transferencias


def pagina_nomina():
    st.header("Nómina por Artesana")
    df_calidad, df_llegadas, df_Asignaciones, df_Transferencias = obtener_datos()
    
    df_Asignaciones = df_Asignaciones.groupby(['Mos','Manual','Talla']).agg({'Cantidad': 'sum'}).reset_index()
    df_calidad = df_calidad.groupby(['Mos','Manual','Talla','Mes','Año', 'Quincena']).agg({'Aprobadas': 'sum','Devueltas': 'sum'}).reset_index()
    df_Transferencias = df_Transferencias.groupby(['Mos','Manual','Talla']).agg({'Cantidad': 'sum'}).reset_index()

    dt_t = df_llegadas.merge(df_Asignaciones, how='inner', left_on=['Mos', 'Talla'], right_on=['Mos', 'Talla'])
    dt_t = dt_t.merge(df_calidad, how='left', on=['Mos', 'Talla', 'Manual'])
    dt_t = dt_t.merge(df_Transferencias, how='left', on=['Mos', 'Talla', 'Manual'])
    
    dt_t = dt_t.dropna(subset=['Mes', 'Quincena', 'Año'])

    # Convertir Mes, Quincena y Año a enteros
    dt_t['Mes'] = dt_t['Mes'].astype(int)
    dt_t['Quincena'] = dt_t['Quincena'].astype(int)
    dt_t['Año'] = dt_t['Año'].astype(int)
    dt_t['Mos'] = dt_t['Mos'].astype(int)
    # Ordenar Mes, Quincena y Año
    meses_ordenados = sorted(dt_t['Mes'].unique())
    quincenas_ordenadas = sorted(dt_t['Quincena'].unique())
    anos_ordenados = sorted(dt_t['Año'].unique())



    # Filtros dinámicos para las columnas
    manual_seleccionado = st.selectbox('Selecciona un Manual', df_calidad['Manual'].unique())

    # Organizar los filtros Mes, Quincena y Año en una sola fila con tres columnas
    col1, col2, col3 = st.columns(3)
    # Filtro para Mes
    with col1:
        mes_seleccionado = st.selectbox('Selecciona un Mes', meses_ordenados)

# Filtro para Quincena
    with col2:
        quincena_seleccionada = st.selectbox('Selecciona una Quincena', quincenas_ordenadas)

# Filtro para Año
    with col3:
        ano_seleccionado = st.selectbox('Selecciona un Año', anos_ordenados)

   

    # Aplicar filtros
    dt_t = dt_t[
        (dt_t['Manual'] == manual_seleccionado) &
        (dt_t['Mes'] == mes_seleccionado) &
        (dt_t['Quincena'] == quincena_seleccionada) &
        (dt_t['Año'] == ano_seleccionado)
    ]

    dt_t['Valor_Total'] = dt_t['Aprobadas'] * dt_t['Costo_Unidad']

    # Calcular la suma total de 'Valor_Total'
    suma_valor_total = dt_t['Valor_Total'].sum()

    # Mostrar la KPI
    st.metric(label='El total de la nomina es', value=f'${suma_valor_total:,.0f}')


    # Dar formato de dinero a las columnas 'Costo_Unidad' y 'Valor_Total'
    dt_t['Costo_Unidad'] = '$ ' + dt_t['Costo_Unidad'].apply('{:,.0f}' .format)
    dt_t['Valor_Total'] = '$ ' + dt_t['Valor_Total'].apply('{:,.0f}' .format)

    # Seleccionar columnas deseadas incluyendo la nueva 'Valor_Total'
    dt_t = dt_t[['Mos', 'Talla', 'Aprobadas', 'Costo_Unidad', 'Valor_Total']]
    
    st.table(dt_t.set_index('Mos'))

    

def pagina_estados_mos():
    st.header("Estados de la MOS")
    df_calidad, df_llegadas, df_Asignaciones, df_Transferencias = obtener_datos()

    df_Transferencias = df_Transferencias.groupby(['Mos','Manual','Talla']).agg({'Cantidad': 'sum'}).reset_index()
    #df_llegadas = df_llegadas.groupby(['Mos','Talla']).agg({'Cantidad': 'sum'}).reset_index()
    df_Asignaciones = df_Asignaciones.groupby(['Mos','Manual','Talla']).agg({'Cantidad': 'sum'}).reset_index()
    df_calidad = df_calidad.groupby(['Mos','Manual','Talla']).agg({'Aprobadas': 'sum','Devueltas': 'sum'}).reset_index()
   
    dt_t = df_llegadas.merge(df_Asignaciones, how='inner', left_on=['Mos', 'Talla'], right_on=['Mos', 'Talla'])
    dt_t = dt_t.merge(df_calidad, how='left', on=['Mos', 'Talla', 'Manual'])
    dt_t = dt_t.merge(df_Transferencias, how='left', on=['Mos', 'Talla', 'Manual'])

    # Filtros dinámicos para las columnas
    Mos_selecionada = st.selectbox('Selecciona un Mos', df_llegadas['Mos'].unique())   
    
    df_llegadas = df_llegadas[
        (df_llegadas['Mos'] == Mos_selecionada)
    ]

    df_Transferencias = df_Transferencias[
        (df_Transferencias['Mos'] == Mos_selecionada)
    ]
    
    df_Asignaciones = df_Asignaciones[
        (df_Asignaciones['Mos'] == Mos_selecionada)
    ]
    
    df_calidad = df_calidad[
        (df_calidad['Mos'] == Mos_selecionada)
    ]

    dt_t = dt_t[
        (dt_t['Mos'] == Mos_selecionada)
    ]

    total_lote = df_llegadas['Cantidad'].sum() 
    total_Asignado = df_Asignaciones['Cantidad'].astype(int).sum()
    total_Calidad = df_calidad['Aprobadas'].astype(int).sum()
    total_Devueltas = df_calidad['Devueltas'].astype(int).sum()
    total_transferencias = df_Transferencias['Cantidad'].astype(int).sum()

    col1, col2, col3 = st.columns(3)

    # Filtro para Mes
    with col1:
       # Mostrar la métrica
        st.metric(label='El total del lote', value=total_lote.astype(int))

    # Filtro para Quincena
    with col2:
        st.metric(label='El total Asignado', value= total_Asignado - total_transferencias)
    # Filtro para Año
    with col3:
       st.metric(label='Pendiente por Asignar', value= (total_lote - total_Asignado + total_transferencias).astype(int))

     # Organizar los filtros Mes, Quincena y Año en una sola fila con tres columnas
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(label='Total Aprobadas', value=total_Calidad)
    with col2:
        st.metric(label='Total Devueltas', value=total_Devueltas)
    with col3:
       st.metric(label='Pendiente por Aprobar', value= (total_lote-total_Calidad).astype(int))

    # Seleccionar las columnas Mos, Manual, Talla, Cantidad_y, Aprobadas, Devueltas
    columnas_seleccionadas = ['Manual', 'Talla', 'Cantidad_y', 'Aprobadas', 'Devueltas', 'Cantidad']
    dt_t_seleccionado = dt_t[columnas_seleccionadas].fillna(0)

    dt_t_seleccionado.rename(columns={'Cantidad_y': 'Asignadas', 'Cantidad': 'Transferencias'}, inplace=True)

    #Crear la columna 'Pendiente' como la resta de 'Cantidad_y' y 'Aprobadas'
    dt_t_seleccionado['Pendiente'] = dt_t_seleccionado['Asignadas'] - dt_t_seleccionado['Aprobadas'] - dt_t_seleccionado['Transferencias']

    dt_t_seleccionado = dt_t_seleccionado.sort_values(by='Pendiente', ascending=False)
 
 
    st.dataframe(dt_t_seleccionado.set_index('Manual'))


def pagina_liquidacion_nomina():
    st.header("Liquidación de Nómina")
    conn = st.connection("gsheets", type=GSheetsConnection)
    
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