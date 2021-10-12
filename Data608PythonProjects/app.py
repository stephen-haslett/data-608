# Import necessary Python libraries.
import pandas as pd
import numpy as np
import plotly.graph_objs as go

# Import Dash related libraries.
import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output

# Pull in the New York City tree census data using the socrata API.
for count in range(0, 5000, 1000):
    url = ('https://data.cityofnewyork.us/resource/nwxe-4ae8.json?$limit=1000&$offset=' + str(count) +\
           '&$select=borocode,spc_common,health,steward,count(tree_id)' +\
           '&$group=borocode,spc_common,health,steward').replace(' ', '%20')
    trees = pd.read_json(url)

    if count == 0:
        trees_data = pd.DataFrame(columns=list(trees.columns.values))
    trees_data = trees_data.append(trees)

trees_data = trees_data.reset_index(drop=True)

# Drop rows that contain missing data.
trees_data = trees_data.dropna(axis=0, how='any')

# Massage the data for question One - "What proportion of trees are in good, fair,
# or poor health according to the ‘health’ variable?"
totals = trees_data.groupby(['borocode', 'spc_common'])['count_tree_id'].sum()
totals = totals.reset_index(drop=False)
totals.columns = ['borocode', 'spc_common', 'total_for_specie_in_borough']

# Borough tree species health totals.
species_health_boro_total = trees_data.groupby(['borocode', 'spc_common', 'health'])['count_tree_id'].sum()
species_health_boro_total = species_health_boro_total.reset_index(drop=False)
species_health_boro_total.columns = ['borocode', 'spc_common', 'health', 'total']

# Tree proportions.
tree_props = pd.merge(species_health_boro_total, totals, on=['borocode', 'spc_common'])
tree_props['ratio'] = tree_props['total'] / tree_props['total_for_specie_in_borough']
tree_props['spc_common'] = tree_props['spc_common'].apply(lambda x: x.title())


# Sort data for the species dropdown filter.
species_filter_data = np.sort(tree_props.spc_common.unique())

# Massage the data for question Two - "Are stewards (steward activity measured by the ‘steward’ variable)
# having an impact on the health of trees?"
# Data indexes.
data_index_rating = {'Poor': 1, 'Fair': 2, 'Good': 3}
data_index_quantity = {'3or4': 3, '4orMore': 4, 'None': 1, '1or2': 2}
data_index_boro = {1: 'Manhattan', 2: 'Bronx', 3: 'Brooklyn', 4: 'Queens', 5: 'Staten Island'}

# Trees Data.
trees_data['borocode'] = pd.to_numeric(trees_data['borocode'])

# Steward totals.
steward_totals = trees_data.groupby(['borocode', 'spc_common', 'steward'])['count_tree_id'].sum()
steward_totals = steward_totals.reset_index(drop=False)
steward_totals.columns = ['borocode', 'spc_common', 'steward', 'steward_total']

# Steward Data.
steward_data = pd.merge(trees_data, steward_totals, on=['borocode', 'spc_common', 'steward'])
steward_data['health_level'] = steward_data['health'].map(data_index_rating)
steward_data['health_index'] = (steward_data['count_tree_id'] / steward_data['steward_total']) * steward_data['health_level']

# Total tree health index.
total_health_index = steward_data.groupby(['borocode', 'spc_common', 'steward'])['health_index'].sum()
total_health_index = total_health_index.reset_index(drop=False)
total_health_index.columns = ['borocode', 'spc_common', 'steward', 'total_health_index']
total_health_index['steward_level'] = total_health_index['steward'].map(data_index_quantity)
total_health_index['borough'] = total_health_index['borocode'].map(data_index_boro)
total_health_index['spc_common'] = total_health_index['spc_common'].apply(lambda x: x.title())

# Render the Dash app for Question One.
app = dash.Dash(__name__, external_stylesheets=['https://codepen.io/chriddyp/pen/bWLwgP.css'])

app.layout = html.Div([
    html.H4('Tree Species'),
    dcc.Dropdown(
        id='specie',
        options=[{'label': i, 'value': i} for i in species_filter_data],
        value="American Beech",
        style={'height': 'auto', 'width': '300px'}
    ),

    dcc.Graph(id='graph-ratio'),

    dcc.Graph(id='graph-health')

], style={'columnCount': 1})

@app.callback(
    Output('graph-ratio', 'figure'),
    [Input('specie', 'value')])
def update_figure_question_one(species_selection):
    filtered_data = tree_props[tree_props.spc_common == species_selection]
    manhattan = filtered_data[filtered_data.borocode == 1]
    bronx = filtered_data[filtered_data.borocode == 2]
    brooklyn = filtered_data[filtered_data.borocode == 3]
    queens = filtered_data[filtered_data.borocode == 4]
    staten_island = filtered_data[filtered_data.borocode == 5]

    traces_question_one = [go.Bar(
        x=queens['health'],
        y=queens['ratio'],
        name='Queens',
        opacity=0.9
    ), go.Bar(
        x=manhattan['health'],
        y=manhattan['ratio'],
        name='Manhattan',
        opacity=0.9
    ), go.Bar(
        x=bronx['health'],
        y=bronx['ratio'],
        name='Bronx',
        opacity=0.9
    ), go.Bar(
        x=brooklyn['health'],
        y=brooklyn['ratio'],
        name='Brooklyn',
        opacity=0.9
    ), go.Bar(
        x=staten_island['health'],
        y=staten_island['ratio'],
        name='Staten Island',
        opacity=0.9
    )]

    return {
        'data': traces_question_one,
        'layout': go.Layout(
            title='Question One - What proportion of trees are in good, fair, or poor health according to the ‘health’ variable ?',
            xaxis={'title': 'Health'},
            yaxis={'title': 'Proportion of Trees in Borough'},
            margin={'l': 40, 'b': 40, 't': 10, 'r': 10},
            legend=dict(x=-.1, y=1.2),
            legend_title_text='Borough'
        )
    }


# Render the Dash app for Question Two.
@app.callback(
    Output('graph-health', 'figure'),
    [Input('specie', 'value')])
def update_figure_question_two(species_selection):
    filtered_data = total_health_index[total_health_index.spc_common == species_selection]
    traces_question_two = []

    for i in filtered_data.borough.unique():
        borough_data = filtered_data[filtered_data['borough'] == i]
        traces_question_two.append(go.Scatter(
            x=borough_data['steward_level'],
            y=borough_data['total_health_index'],
            mode='markers',
            opacity=0.7,
            marker={
                'size': 15,
                'line': {'width': 0.5, 'color': 'white'}
            },
            name=i
        ))

    return {
        'data': traces_question_two,
        'layout': go.Layout(
            title='Question Two - Are stewards (steward activity measured by the ‘steward’ variable) having an impact on the health of trees?',
            yaxis={'title': 'Health Index'},
            xaxis=dict(tickvals=[1, 2, 3, 4], ticktext=['None', '1or2', '3or4', '4orMore'], title='Steward'),
            margin={'l': 40, 'b': 40, 't': 10, 'r': 10},
            legend=dict(x=-.1, y=1.2),
            legend_title_text='Borough'
        )
    }


if __name__ == '__main__':
    app.run_server(debug=False)