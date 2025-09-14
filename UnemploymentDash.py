# %% [markdown]
# # Unemployment rate dashboard
# 
# The dataset used in this dashboard application is gathered from World Bank. 
# The dataset consist of the unemployement rate for different countries in the world all back to 1991.

# %%
# Loading packages
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from dash import Dash, dcc, html
from dash.dependencies import Input, Output

import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template
import plotly.graph_objects as go
import plotly.express as px
import plotly.graph_objects as go

# %%
from pandas_datareader import wb
# Dictionary with indicators-name pairs
ind_dict = {
    'SL.UEM.TOTL.ZS' : 'unemployment',
   'SL.UEM.TOTL.FE.ZS': 'female',
    'SL.UEM.TOTL.MA.ZS' : 'male'
}

# Extract data and reset index
df_wb = wb.download(indicator = ind_dict.keys(), country = 'all', start = 1990, end = 2025).reset_index()

# Rename indicators
df_wb.rename(columns = ind_dict, inplace = True)

# Convert year to int
df_wb['year'] = df_wb['year'].astype(int)

# 2 decimals
df_wb = df_wb.round(2)

# Convert inflation column to percentage

print(df_wb['country'].nunique())
df_wb

# %%
world_df = df_wb.loc[df_wb['country'] == 'World']
world_df

# %%
import plotly.graph_objects as go

def plot_unemployment():
    # Create a line graph using plotly
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=world_df['year'], y=world_df['male'], mode='lines+markers', name='Male'))
    fig.add_trace(go.Scatter(x=world_df['year'], y=world_df['female'], mode='lines+markers', name='Female'))
    
    fig.update_layout(
        title='Unemployment by Gender in the World',
        xaxis_title='Year',
        yaxis_title='Unemployment'
    )
    
    fig.show()
plot_unemployment()


# %%


# %%
import pycountry
country_set = set([country.name for country in pycountry.countries])

# filter the DataFrame to only include the countries
df_country = df_wb[df_wb['country'].isin(country_set)].reset_index(drop = True)

# Create a mapping of country names to ISO Alpha-3 codes
country_codes = {}
for country in pycountry.countries:
    country_codes[country.name] = country.alpha_3
    

# Add a new column 'iso3c' with ISO Alpha-3 codes
df_country['iso3c'] = df_country['country'].map(country_codes)

# Remove the column to be moved from its current position
column_to_move = df_country.pop('iso3c')

# Insert the column at the desired location (next to 'country' column)
df_country.insert(1, 'iso3c', column_to_move)

df_country


# %%
from pycountry_convert import country_alpha2_to_continent_code

# Adding a column for continent
def country_2_continent(country_name):
    continent_mapping = {
        'AF': 'Africa',
        'AS': 'Asia',
        'EU': 'Europe',
        'NA': 'North America',
        'SA': 'South America',
        'OC': 'Oceania',
        'AN': 'Antarctica'
    }
    try:
        country_alpha2 = pycountry.countries.get(name=country_name).alpha_2
        continent_code = country_alpha2_to_continent_code(country_alpha2)
        continent = continent_mapping.get(continent_code, 'Unknown')
    except:
        continent = 'Unknown'
    return continent

df_country['continent'] = df_country['country'].apply(country_2_continent)

# Remove the column to be moved from its current position
column_to_move = df_country.pop('continent')

# Insert the column at the desired location (next to 'country' column)
df_country.insert(2, 'continent', column_to_move)

df_country = df_country[df_country['continent'] != 'Unknown']

df_country

# %%
# Group the data by 'year' and 'continent' and calculate the average unemployment rate
df_continents = df_country.groupby(['year', 'continent'])['unemployment'].mean().reset_index()
load_figure_template('DARKLY')
fig_regions = px.line(
    df_continents,
    x = 'year',
    y = 'unemployment',
    color = 'continent',          # seperate line plot for each region
    markers = True,            # add a marker to each observaton on the line
    color_discrete_sequence=px.colors.sequential.Viridis
)

fig_regions.update_layout(
    title = 'Average Unemployment Rate for all continents',
    yaxis_title = "Unemployment",
    xaxis_title = "Year"
)


# %%
def top_10_unemployment(year, continent):
    # Filter the df_country DataFrame for the specified year
    year_data = df_country[df_country['year'] == year]
    
    if continent:
        # Filter the data for the specified continent
        continent_data = year_data[year_data['continent'] == continent]
        
        # Sort the filtered DataFrame by the unemployment column in descending order
        sorted_df = continent_data.sort_values('unemployment', ascending=False)
        
        # Select the top 10 countries with the highest unemployment rates within the continent
        top_10_countries = sorted_df.head(10)
    else:
        # Sort the DataFrame by the unemployment column in descending order
        sorted_df = year_data.sort_values('unemployment', ascending=False)
        
        # Select the top 10 countries with the highest unemployment rates globally
        top_10_countries = sorted_df.head(10)
    
    # Create a bar plot using plotly
    fig = px.bar(
        top_10_countries,
        x='country',
        y='unemployment',
        color='country',
        color_discrete_sequence=px.colors.sequential.Viridis
    )
    
    fig.update_layout(
        title = f'Top 10 Countries with Highest Unemployment Rate ({year}) in {continent}',
        xaxis_title='Country',
        yaxis_title='Unemployment Rate'
    )
    load_figure_template('DARKLY')
    
    return fig
top_10_unemployment(2007, "South America")

# %%
def unemployment_map(year):
    # Filter the DataFrame for the specified year
    filtered_df = df_country[df_country['year'] == year]
    
    # Sort the filtered DataFrame by the 'iso3c' column in ascending order
    sorted_df = filtered_df.sort_values('iso3c')
    
    # Create the choropleth map using Plotly Express
    fig = px.choropleth(
        sorted_df,
        locations='iso3c',
        color='unemployment',
        color_continuous_scale='Viridis',
        range_color=(0, 20),
        labels={'unemployment': 'Unemployment Rate'},
        title=f'Global Unemployment Rate Map - Year {year}',
        height=600,
        projection='natural earth'  # You can change the projection as desired
    )
     # Add text annotations to the map
    fig.update_traces(text=sorted_df['country'], 
                      hovertemplate='<b>%{text}</b><br>Unemployment Rate: %{z}%')
       
    # Customize the map layout
    fig.update_layout(
        geo=dict(
            showframe=False,
            showcoastlines=False,
        )
    )
    load_figure_template('DARKLY')
    # Show the map
    return fig
unemployment_map(2024)

# %%
df_country

# %%
import plotly.graph_objects as go

def plot_country_unemployment(country=None, start_date=None, end_date=None):
    if country is None:
        # Plot world data
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=world_df['year'], y=world_df['male'], mode='lines+markers', name='Male'))
        fig.add_trace(go.Scatter(x=world_df['year'], y=world_df['female'], mode='lines+markers', name='Female'))
        title = 'Unemployment by Gender in the World'
    else:
        # Plot country-specific data
        data = df_country[(df_country['country'] == country) & (df_country['year'] >= start_date) & (df_country['year'] <= end_date)]
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=data['year'], y=data['male'], mode='lines+markers', name='Male'))
        fig.add_trace(go.Scatter(x=data['year'], y=data['female'], mode='lines+markers', name='Female'))
        title = f'Unemployment by Gender in {country}'

    fig.update_layout(
        title=title,
        xaxis_title='Year',
        yaxis_title='Unemployment'
        
    )
    load_figure_template('DARKLY')

    return fig


# %%
plot_country_unemployment("Norway",1992, 2024)

# %%
theme = dbc.themes.DARKLY
template = load_figure_template("SOLAR")
description ='The dataset used in this dashboard application is gathered from OECDs data bank. The dataset consist of the unemployement rate for different countries in the world all back to 1991. Not all countries have data related to the earliest dates.'

# %%
# ------------------ Create Dash App ------------------
app = Dash(__name__, external_stylesheets=[theme])

# ------------------ App Layout ------------------
app.layout = html.Div([
    # Header
    html.Div([
        html.H1("Global Unemployment Rate Dashboard",
                style={'textAlign': 'center', 'margin-bottom': '25px'}),
        dcc.Markdown(description),
    ], style={'margin-bottom': '30px'}),

    # Row 1: Regional inflation & Top 10 countries
    html.Div([
        # Inflation for regions
        html.Div([
            html.H3("Inflation for regions"),
            dcc.Graph(figure=fig_regions, style={'height': '400px'})
        ], style={'flex': '1', 'margin-right': '10px',  'margin-top':'45px'}),

        # Top 10 unemployment
        html.Div([
            dcc.Dropdown(
                id='continent-dropdown',
                options=[{'label': c, 'value': c} for c in df_country['continent'].unique()],
                value="Europe",
                placeholder="Select a continent",
                style={'width': '100%', 'color': 'black', 'margin-bottom': '10px'}
            ),
            dcc.Dropdown(
                id='year-dropdown',
                options=[{'label': y, 'value': y} for y in df_country['year'].unique()],
                value=2024,
                placeholder='Select a year',
                style={'width': '100%', 'color': 'black', 'margin-bottom': '10px'}
            ),
            dcc.Graph(id='top-10-barplot', style={'height': '400px'})
        ], style={'flex': '1', 'margin-left': '10px'})
    ], style={'display': 'flex', 'margin-bottom': '30px'}),
    # Row 2: Country-level line graph
    html.Div([
        dcc.Dropdown(
            id='country-dropdown',
            options=[{'label': c, 'value': c} for c in df_country['country'].unique()],
            value=None,
            placeholder='Select a country',
            style={'width': '40%', 'color': 'black', 'margin-bottom': '10px'}
        ),
        dcc.Graph(id='line-graph', style={'height': '400px'})
    ]),
    
    # Row 3: Unemployment map
    html.Div([
        dcc.Graph(id='unemployment-map', style={'height': '500px'}),
        dcc.Slider(
            id='year-slider1',
            min=df_country['year'].min(),
            max=df_country['year'].max(),
            value=df_country['year'].max(),
            marks={str(year): str(year) for year in df_country['year'].unique() if year % 5 == 0},
            step=1
        )
    ], style={'margin-bottom': '30px'})
], style={'margin': '20px'})  # Outer padding

# ------------------ Callbacks ------------------
@app.callback(
    Output('top-10-barplot', 'figure'),
    [Input('year-dropdown', 'value'),
     Input('continent-dropdown', 'value')]
)
def update_top_10(year, continent):
    load_figure_template('DARKLY')
    return top_10_unemployment(year, continent)

@app.callback(
    Output('unemployment-map', 'figure'),
    Input('year-slider1', 'value')
)
def update_unemployment_map(year):
    load_figure_template('DARKLY')
    return unemployment_map(year)

@app.callback(
    Output('line-graph', 'figure'),
    Input('country-dropdown', 'value')
)
def update_plot_country_inflation(country):
    load_figure_template('DARKLY')
    return plot_country_unemployment(country=country, start_date=1990, end_date=2025)

# ------------------ Run App ------------------
if __name__ == '__main__':
    app.run(debug=False, port=8051)  # Dash 3.x+ uses app.run() instead of run_server()

# %%


