import os
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import statistics

st.set_page_config(page_title="Recomendador de comisiones y equipos", layout="wide")

st.subheader('Recomendador de comisiones y equipos')


with st.sidebar:
    st.markdown('#### Proyección de venta mensual (unidades)')
    medios_litros = st.number_input(label ='1/2L: ', min_value=0, max_value=1000, step=2, value=2)
    cuatro_onzas = st.number_input(label ='4oz: ', min_value=0, max_value=1000, step=5)
    cinco_litros = st.number_input(label ='5L: ', min_value=0, max_value=1000, step=1)
    st.write('Total litros: ', round((medios_litros*0.5)+(cuatro_onzas*0.118294)+(cinco_litros*5),2))

    st.markdown('#### Parámetros')
    zona = st.selectbox('Zona: ', ['Guayaquil','Cuenca', 'Quito', 'Machala', 'Costa'])
    ordenes = st.number_input(label ='\# órdenes mensuales: ', min_value=0, max_value=30, step=1, value=2)
    peso_signature = st.slider("Participación línea signature: ", 0, 10, 5)
    peso_estacionales = st.slider("Participación línea estacionales: ", 0, 10, 5)
    peso_veganos = st.slider("Participación línea veganos: ", 0, 10, 0)
    peso_sin_azucar = st.slider("Participación línea sin azúcar: ", 0, 10, 0)
    peso_economica = st.slider("Participación línea económica: ", 0, 10, 0)


data = pd.read_csv('C:/Users/nicol/Documents/Encanteria/comercial/dashboards/recomendador_porcentajes_equipos/precios_costos.csv')

presentaciones = pd.DataFrame({
    'categoria' : ['1/2L', '4oz', '5L'],
    'unidades' : [medios_litros, cuatro_onzas, cinco_litros]
})

participacion = pd.DataFrame({
    'linea': ['signature', 'estacionales', 'veganos', 'sin azucar', 'economica'],
    'peso' : [peso_signature, peso_estacionales, peso_veganos, peso_sin_azucar, peso_economica]
})

comisiones = pd.DataFrame({
    '1/2L': np.arange(0.0, 0.36, 0.01),
    '4oz' : np.arange(0.0, 0.36, 0.01),
    '5L' : np.arange(0.0, 0.36, 0.01)
})

comisiones = pd.melt(comisiones,  value_vars=['1/2L', '4oz', '5L'], var_name='categoria', value_name='comision')

logistica = pd.DataFrame({
    'zona': ['Guayaquil','Cuenca', 'Quito', 'Machala', 'Costa'],
    'gasto_logistico': [((1160/30)+((650*2*1.25)/30)+(40/6))/10, ((1160/30)+((650*2*1.25)/30)+20+40)/10, 0, 40, ((1160/30)+((650*2*1.25)/30)+(40/6))/2.5]
})

logistica = logistica[logistica['zona']==zona].reset_index(drop=True)

data = data.merge(participacion, left_on = ['linea'], right_on= ['linea'])

data =data.groupby(['categoria']).agg(
    precio=('precio', lambda x: (x * data.loc[x.index, 'peso']).sum() / data.loc[x.index, 'peso'].sum()),
    costo = ('costo', lambda x: (x * data.loc[x.index, 'peso']).sum() / data.loc[x.index, 'peso'].sum())
)

data = data.merge(presentaciones, left_on=['categoria'], right_on=['categoria'])
data = data.merge(comisiones, left_on=['categoria'], right_on=['categoria'])
data['venta_bruta'] = data['precio']*data['unidades']
data['venta_neta'] = data['venta_bruta']*(1-data['comision'])
data['cogs'] = data['costo']*data['unidades']


data = data.groupby(['comision']).agg(
    venta_bruta = ('venta_bruta', 'sum'),
    venta_neta = ('venta_neta', 'sum'),
    cogs = ('cogs', 'sum')
)

data['gasto_logistico'] = logistica['gasto_logistico'][0]*ordenes
data['trade_marketing'] = data['venta_neta']*0.10
data['gasto_fijo'] = data['venta_neta']*0.25
data['EBITDA'] = data['venta_neta']-data['cogs']-data['gasto_logistico']-data['trade_marketing']-data['gasto_fijo']
data['depreciacion'] = np.where((data['EBITDA']/data['venta_neta'])>0.1, ((data['EBITDA']/data['venta_neta'])-0.1)*data['venta_neta'], 0)
data['equipo']  = round(data['depreciacion']*12*4,-1)
data = data[data['EBITDA']>0.05]
data = data[['equipo']]

st.dataframe(data)
