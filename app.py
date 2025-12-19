import dash
from dash import dash_table, dcc, html, Input, Output, State, ALL, ctx
import plotly.express as px
import pandas as pd
import mysql_utils
import mongodb_utils
import neo4j_utils

# Initialize Dash app
app = dash.Dash()

# Load MySQL Data
all_keywords_df = mysql_utils.get_all_keywords()
all_keywords = all_keywords_df['name'].tolist()

# App Layout
app.layout = html.Div([
    html.H2("University Application Encyclopedia", style={'textAlign': 'center', 'fontSize': 30}),
    
    html.Div([
        html.Div([
            html.H4("Top Keywords"),
            dcc.Slider(
                id='top-n-slider',
                min=5,
                max=50,
                step=5,
                value=10,
                marks={i: str(i) for i in [5, 10, 20, 50]}
            ),
            dcc.Graph(id='bubble-chart')
        ], className='chart-box'),

        html.Div([
            html.H4("Keyword Trend Over Time"),
            dcc.Dropdown(
                id='keyword-selector',
                options=[{'label': k, 'value': k} for k in all_keywords],
                # value=['machine learning'],
                multi=True
            ),
            dcc.Graph(id='line-chart')
        ], className='chart-box')
    ], className='chart-row'),
    html.Div([
        html.Div([
            html.H4("Publications List for Selected Keyword"),
            dcc.Dropdown(
                id="publication-keyword-selector",
                options=[{'label': k, 'value': k} for k in all_keywords],
                placeholder="Select a keyword"
            ),
            dash_table.DataTable(
                id="publication-table",
                columns=[
                    {"name": "Title", "id": "title"},
                    {"name": "Venue", "id": "venue"},
                    {"name": "Year", "id": "year"},
                    {"name": "Citations", "id": "numCitations"},
                    {"name": "Actions", "id": "edit-btn", "presentation": "input"}
                ],
                style_table={'overflowX': 'auto'},
                style_cell={
                    'textAlign': 'left',
                    'padding': '5px',
                    'whiteSpace': 'normal',
                    'height': 'auto',
                },
                style_header={
                    'backgroundColor': 'lightgrey',
                    'fontWeight': 'bold'
                },
                page_size=10
            )
        ], className='chart-box'),

        html.Div([
            html.H4("Universities for Selected Keyword"),
            dcc.Input(
                id='keyword-input',
                type='text',
                placeholder='Enter a keyword',
                debounce=True  # Optional: wait until user finishes typing
            ),
            html.Button('Search', id='search-button-university'),
            dcc.Graph(id='university-bar-chart'),
            dash_table.DataTable(
                id="university-table",
                columns=[
                    {"name": "University", "id": "university"},
                    {"name": "Faculty Count", "id": "facultyCount"}
                ],
                style_table={'overflowX': 'auto'},
                style_cell={
                    'textAlign': 'left',
                    'padding': '5px',
                    'whiteSpace': 'normal',
                    'height': 'auto',
                },
                style_header={
                    'backgroundColor': 'lightgrey',
                    'fontWeight': 'bold'
                },
                page_size=10
            )
        ], className='chart-box'),
    ], className='chart-row'),
    
    html.Div([
        html.Div([
            html.H4("Top 5 Professors by Keyword-related Citations"),
            dcc.Dropdown(
                id='professor-keyword-selector',
                options=[{'label': k, 'value': k} for k in all_keywords],
                # value='machine learning',
                multi=False,
                placeholder="Select a keyword"
            ),
            html.Div(id='professor-cards', className="professor-container"),
        ], className='chart-box'),

        html.Div([
            html.H4("Publications of selected professor"),
            dcc.Input(
                id='faculty-input',
                type='text',
                placeholder='Enter faculty names (first and last) separated by commas e.g. Peggy Agouris, Tim Davis',
                style={'width': '60%'}
            ),
            html.Button('Search', id='search-button-faculty'),
            dash_table.DataTable(
                id='faculty-publications-table',
                columns=[
                    {'name': 'Faculty', 'id': 'faculty'},
                    {'name': 'Year', 'id': 'year'},
                    {'name': 'Title', 'id': 'title'}
                ],
                style_table={'overflowX': 'auto'},
                style_cell={
                    'textAlign': 'left',
                    'padding': '10px',
                    'whiteSpace': 'normal',
                    'height': 'auto',
                    'backgroundColor': '#fffdf5'  # Light pastel background
                },
                style_header={
                    'backgroundColor': '#4a90e2',
                    'color': 'white',
                    'fontWeight': 'bold'
                },
                page_size=10
            )
        ], className='chart-box'),
    ], className='chart-row'),
    

    # Hidden div to store the selected publication id
    dcc.Store(id="selected-publication-id"),

    # Add a new Store for selected professor id
    dcc.Store(id="selected-professor-id"),

    # Modal for editing (just HTML elements without dbc)
    html.Div([
        html.Div([  # Modal content
            html.H4("Edit Publication"),
            dcc.Input(id="edit-title", type="text", placeholder="Title", disabled=True, style={'width': '100%'}),
            dcc.Input(id="edit-venue", type="text", placeholder="Venue", disabled=True, style={'width': '100%'}),
            dcc.Input(id="edit-year", type="number", placeholder="Year", disabled=True, style={'width': '100%'}),
            dcc.Input(id="edit-citations", type="number", placeholder="Number of Citations", style={'width': '100%', 'marginTop': '10px'}),
            html.Button("Save Changes", id="save-publication-btn", n_clicks=0, style={'marginTop': '10px'}),
            html.Button("Cancel", id="cancel-edit-btn", n_clicks=0, style={'marginLeft': '10px', 'marginTop': '10px'})
        ], className="modal-content"),
    ], id="edit-modal", className="modal", style={"display": "none"}),

    html.Div([
        html.Div([  # Modal content
            html.H4("Edit Professor Photo"),
            html.Div([
                html.Img(id="professor-current-photo", className='professor-photo-preview'),
                html.P("Current Photo URL", style={'marginTop': '5px'})
            ], style={'textAlign': 'center', 'marginBottom': '15px'}),
            dcc.Input(id="edit-professor-name", type="text", placeholder="Name", disabled=True, style={'width': '100%', 'marginBottom': '10px'}),
            dcc.Input(id="edit-professor-photo-url", type="text", placeholder="Photo URL", style={'width': '100%', 'marginBottom': '10px'}),
            html.Button("Save Photo URL", id="save-professor-btn", n_clicks=0, style={'marginTop': '10px'}),
            html.Button("Cancel", id="cancel-professor-edit-btn", n_clicks=0, style={'marginLeft': '10px', 'marginTop': '10px'})
        ], className="modal-content"),
    ], id="professor-edit-modal", className="modal", style={"display": "none"})
])


# Callback for bubble chart based on slider
@app.callback(
    Output('bubble-chart', 'figure'),
    Input('top-n-slider', 'value')
)
def update_bubble_chart(top_n):
    df = mysql_utils.get_top_keywords(top_n)
    fig = px.scatter(
        df,
        x='keyword',
        y='popularity',
        size='popularity',
        color='keyword',
        title=f'Top {top_n} Keywords (Since 2012)',
        size_max=60
    )
    fig.update_layout(xaxis_tickangle=45)
    return fig


# Callback to update line chart
@app.callback(
    Output('line-chart', 'figure'),
    Input('keyword-selector', 'value')
)
def update_line_chart(selected_keywords):
    if not selected_keywords:
        # Return an empty figure with a title
        return px.line(title='Select keyword(s) to display trends')
    
    # Get data from Neo4j
    df = neo4j_utils.get_keyword_trend(selected_keywords)
      
    # Handle empty dataframe case
    if df.empty:
        return px.line(title='No data found for selected keywords')
    

    
    # Create the figure
    fig = px.line(
        df,
        x='year',
        y='publication_count',
        color='keyword',
        markers=True,
        title='Keyword Trend Over Time'
    )
    return fig


# Callback: Update Publications List
@app.callback(
    Output('publication-table', 'data'),
    Input('publication-keyword-selector', 'value')
)
def update_publication_table(selected_keyword):
    if not selected_keyword:
        return []
    pubs = mongodb_utils.get_top_publications(selected_keyword)
    if not pubs:
        return []

    pub_df = pd.DataFrame(pubs)
    pub_df['edit-btn'] = ['Edit' for _ in range(len(pub_df))]
     # Create unique link for each edit
    return pub_df[['title', 'venue', 'year', 'numCitations', 'edit-btn']].to_dict('records')

# Callback: Update faculty-publication List
@app.callback(
    Output('faculty-publications-table', 'data'),
    Input('search-button-faculty', 'n_clicks'),
    State('faculty-input', 'value'),
    prevent_initial_call=True
)

def update_faculty_publications(n_clicks, name_input):

    if not name_input:
        return[]
    
    # Proceed with your database query logic here
    publications = mongodb_utils.get_publications_for_faculty(name_input)

    if publications:
        # Map the query result into the format the table expects
        formatted_data = [
            {
                "faculty": pub['faculty'],
                "year": pub['year'],
                "title": pub['title']
                # "venue": pub['venue'] if pub['venue'] else "N/A",  # Set default if None
                
            }
            for pub in publications
        ]
        return formatted_data
    else:
        return []

# Callback: Update university/keyword List
@app.callback(
    Output('university-bar-chart', 'figure'),
    Output("university-table", "data"),
    Input("search-button-university", "n_clicks"),
    State('keyword-input', 'value'),
    prevent_initial_call=True
)

def update_university_table(n_clicks, selected_keyword):
    if not selected_keyword:
        return [], px.scatter(title="No keyword selected")
    data = mongodb_utils.get_universities_by_keyword(selected_keyword)

    if not data:
        return [], px.scatter(title=f"No results for '{selected_keyword}'")
    
    # Create the bar chart
    fig = px.bar(
        data,
        x='university',
        y='facultyCount',
        title=f"Faculty Count for '{selected_keyword}'",
        color_discrete_sequence=['#FFB347']  # pastel orange
    )
    fig.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='#1f3a93')  # pastel blue text
    )

    return fig, data

@app.callback(
    Output('professor-cards', 'children'), 
    Input('professor-keyword-selector', 'value'),
)
def update_professor_cards(selected_keyword):
    if not selected_keyword:
        return html.Div("No keyword selected.")

    df = mysql_utils.get_top_faculty_by_keyword(selected_keyword)

    if df.empty:
        return html.Div("No professors found.")

    cards = []
    for _, row in df.iterrows():
        # Add professor ID for reference
        professor_id = row['id'] 
        
        cards.append(html.Div([
            html.Div([
                html.Img(src=row['photo_url'], className='professor-photo', style={
                    'width': '150px',
                    'height': '150px',
                    'objectFit': 'cover',
                    'borderRadius': '8px',
                    'marginBottom': '10px' 
                }),
                html.Button("Edit Photo", 
                           id={'type': 'edit-professor-btn', 'index': professor_id},
                           className='edit-professor-btn',
                           n_clicks=0)
            ], className='professor-photo-container'),
            html.H5(row['name']),
            html.P(f"University: {row['university']}"),
            html.P(f"Position: {row['position']}"),
            html.P(f"Research Interest: {row['research_interest']}"),
            html.P(f"Email: {row['email']}"),
            html.P(f"Phone: {row['phone']}"),
            html.P(f"Total Citations: {row['total_citations']}")
        ], className='professor-card'))

    return cards

# Open Modal when Edit clicked
@app.callback(
    Output("edit-modal", "style"),
    Output("selected-publication-id", "data"),
    Output("edit-citations", "value"),
    Input("publication-table", "active_cell"),
    Input("save-publication-btn", "n_clicks"),
    Input("cancel-edit-btn", "n_clicks"),
    State("publication-table", "data"),
    prevent_initial_call=True
)
def control_modal(active_cell, save_clicks, cancel_clicks, table_data):
    triggered_id = dash.callback_context.triggered_id

    # CASE 1: Edit button clicked → Open the modal
    if triggered_id == "publication-table" and active_cell and active_cell['column_id'] == 'edit-btn':
        row = table_data[active_cell['row']]
        pub = mongodb_utils.get_publication_by_title(row['title'])  # Find publication by title
        pub_id = str(pub["_id"]) if pub["_id"] else None
        return {"display": "block"}, pub_id, pub["numCitations"]
    
    # CASE 2: Save or Cancel clicked → Close the modal
    elif triggered_id in ["save-publication-btn", "cancel-edit-btn"]:
        return {"display": "none"}, None, None

    # Default fallback
    return {"display": "none"}, None, None


# Save edits back to MongoDB
@app.callback(
    Output("publication-keyword-selector", "value", allow_duplicate=True),
    Input("save-publication-btn", "n_clicks"),
    State("selected-publication-id", "data"),
    State("edit-citations", "value"),
    State("publication-keyword-selector", "value"),
    prevent_initial_call="initial_duplicate"
)
def save_edits(n_clicks, pub_id, new_citations, current_keyword):
    if pub_id and new_citations:
        pub = mongodb_utils.get_publication_by_id(pub_id)
        if new_citations != pub['numCitations']:
            mongodb_utils.update_publication(pub_id, new_citations)
    return current_keyword  # Return keyword again to refresh the table

# Callback to open the professor edit modal
@app.callback(
    Output("professor-edit-modal", "style"),
    Output("selected-professor-id", "data"),
    Output("edit-professor-name", "value"),
    Output("edit-professor-photo-url", "value"),
    Output("professor-current-photo", "src"),
    [Input({'type': 'edit-professor-btn', 'index': dash.dependencies.ALL}, 'n_clicks')],
    [State("professor-keyword-selector", "value")],
    prevent_initial_call=True
)
def open_professor_modal(edit_clicks, selected_keyword):
    ctx = dash.callback_context
    
    # Check if any button was clicked (all n_clicks will be None on initial load)
    if not ctx.triggered or not any(n is not None and n > 0 for n in edit_clicks if n is not None):
        raise dash.exceptions.PreventUpdate
        
    # Find which button was clicked
    button_id = None
    clicked_index = None
    
    for i, n_clicks in enumerate(edit_clicks):
        if n_clicks is not None and n_clicks > 0:
            # Get the corresponding index from ctx.triggered_id
            triggered_prop_id = ctx.triggered[0]['prop_id']
            try:
                # Extract the button ID from the property ID string
                button_dict = eval(triggered_prop_id.split('.')[0])
                if isinstance(button_dict, dict) and button_dict.get('type') == 'edit-professor-btn':
                    clicked_index = button_dict.get('index')
                    break
            except:
                continue
    
    # If we couldn't identify which button was clicked, prevent update
    if clicked_index is None:
        raise dash.exceptions.PreventUpdate
    
    # Get professor details from database based on ID
    professor_data = mysql_utils.get_faculty_by_id(clicked_index)
    
    if professor_data is not None:
        return {
            "display": "block"
        }, clicked_index, professor_data['name'], professor_data['photo_url'], professor_data['photo_url']
        
    # Default case - don't update
    raise dash.exceptions.PreventUpdate

# Callback to close the professor edit modal
@app.callback(
    Output("professor-edit-modal", "style", allow_duplicate=True),
    [Input("save-professor-btn", "n_clicks"),
     Input("cancel-professor-edit-btn", "n_clicks")],
    prevent_initial_call=True
)
def close_professor_modal(save_clicks, cancel_clicks):
    ctx = dash.callback_context
    
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate
        
    # Check if save or cancel button was actually clicked (not just initialized)
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    button_clicks = save_clicks if button_id == "save-professor-btn" else cancel_clicks
    
    if button_clicks is None or button_clicks == 0:
        raise dash.exceptions.PreventUpdate
        
    # Either save or cancel was clicked - close the modal
    return {"display": "none"}

# Save professor photo URL back to MySQL
@app.callback(
    Output("professor-keyword-selector", "value", allow_duplicate=True),
    Input("save-professor-btn", "n_clicks"),
    [State("selected-professor-id", "data"),
     State("edit-professor-photo-url", "value"),
     State("professor-keyword-selector", "value")],
    prevent_initial_call=True
)
def save_professor_photo(n_clicks, professor_id, new_photo_url, current_keyword):
    # Prevent callback execution if the button hasn't been clicked
    if n_clicks is None or n_clicks <= 0:
        raise dash.exceptions.PreventUpdate
        
    # Check if we have all required data
    if not professor_id or not new_photo_url:
        raise dash.exceptions.PreventUpdate
        
    # Update the photo URL in the database
    mysql_utils.update_faculty_photo_url(professor_id, new_photo_url)
    
    # Return the current keyword to refresh the professor cards
    return current_keyword

if __name__ == '__main__':
    app.run(debug=True)
    