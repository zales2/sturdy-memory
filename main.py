import base64
import io
import re

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import pandas as pd
import plotly.graph_objs as go
from dash.dependencies import Input, Output, State


def findallintext( partoftxt, txt ):
    matches = []
    for match in re.finditer(txt, partoftxt):
        matches.append( match.start() )
    return matches

def numberofcolumns( str ):
    
    match = findallintext( str, '\t' )
    newline = str.find( '\n' )
    seperators = 1    
    for i in range( len( match ) + 1 ):
        try:
            if match[ i + 1 ] < newline:
                seperators += 1
            else:
                break
        except IndexError:
            break
    return seperators
           
def readexcel( decoded ):
   
    excel = pd.read_excel( io.BytesIO( decoded ))
    
    return excel

def readpasted( pasted ):
    
    # liczba kolumn - 1
    columns = numberofcolumns( pasted )
    pasted = '\t' + pasted
    #liczba wierszy + 1
    newlines = findallintext( pasted, '\n' )
    newlineslen = len( newlines )
    if pasted[ -1 ] != '\n':
        newlineslen += 1

    pasted = pasted.replace("\n", "\t").replace(",", ".")
    pasted += "\t"
    
    match = findallintext( pasted, "\t" )
    matchiter = 0
    pastedlist = []
    for _ in range( newlineslen ):
        linelist = []
        for _ in range( columns + 1 ):
            linelist.append( pasted[ match[ matchiter ] + 1 : match[ matchiter + 1 ] ] )
            matchiter += 1
        pastedlist.append( linelist[ : ] )

    df = pd.DataFrame( pastedlist )
    lendf = len(df.columns)
    
    alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    columnlist = []
    for i in range( lendf ):
        columnlist.append( alphabet[ i ] )
    df.columns = columnlist

    return df

def readcsv( decoded ):

    csv = pd.read_csv( io.StringIO( decoded.decode( 'utf-8' ) ), sep = ',' ) 
    
    return csv

class File:
    
    def __init__(self, type, decoded):
        self.type = type
        self.decoded = decoded
        
    
    def convertopandas(self):
        
        if ( 'xlsx' or 'xls' ) in self.type:
            table = readexcel( self.decoded )
        elif 'csv' in self.type:
            table = readcsv( self.decoded )
        else:
            table = readpasted( self.decoded )
            
        return table
    
listoffile = []

app = dash.Dash(__name__)
server = app.server

app.config.suppress_callback_exceptions = True

app.layout = html.Div([
    dcc.Store( id = 'memory' ),
    dcc.Location( id = 'url', refresh = False ),
    html.Div( id = 'page-content' ) 
 ])

#strona główna
data_page = html.Div([

    html.Div([
        html.Div([
            'PlotMaker', 
            html.Span( ' v1.0', id = 'version')], id = 'title'
        )
    ]),

    html.Div([
            
        html.Div([
            'Wklej tutaj swoją tabelę',
            dcc.Textarea( id = 'pastedata', placeholder = 'najlepiej z pliku .xls lub .xlsx', value = '' ),
        ], className = 'data' ),
        
        html.Div([
            'Drop (.csv, .xlsx)',
            dcc.Upload([ html.Div([ 'Upuść lub ', html.Span( 'załaduj pliki', id = 'uploadlink' )], id = 'upload-div' )], id = 'upload' ),
        ], className = 'data' ),

         html.Div( 'Zanim przejdziesz dalej, zaczekaj aż dane się załadują.', id = 'load-data' ),

        html.Div([
            dcc.Link( 'Przejdź dalej', href = '/plot', id = 'summitlink' )
        ], className = 'summit' )

    ], className = 'app' )

 ], className = 'container' )

#strona wizualizacja
plot_page = html.Div([
    
    #dcc.Upload(["Upuść lub ", html.A("załaduj pliki")], id = "upload"),
    html.Div([
        html.Div([
            'PlotMaker', 
            html.Span( ' v1.0', id = 'version')], id = 'title'
        ),
        dcc.Link( html.Img( src = app.get_asset_url( 'home_page.jpg' ), id = 'home-image' ), href = '/')
    ]),
    
    html.Div([
        
        html.Div([
            
            dcc.Tabs(
                
                children = [
                    
                    dcc.Tab(
                        label = 'Tabela',
                        id = 'dash-table', 
                        selected_className= 'editplottab-sel'
                    ),
                    
                    dcc.Tab(
                        label = 'Wykres',
                        selected_className= 'editplottab-sel',
                        children = [
                            
                            html.Div([
                                
                                html.Div([
                                    'Wybierz rodzaj wykresu',
                                    dcc.Dropdown(
                                        id = 'dropplots',
                                        options =   [
                                            { 'label': 'Liniowy', 'value': 'lines' },
                                            { 'label': 'Liniowy ze znacznikami', 'value': 'lines+markers' },
                                            { 'label': 'Punktowy', 'value': 'markers' }, 
                                            { 'label': 'Słupkowy', 'value': 'bar' }   
                                        ],
                                        value = 'lines',
                                        className = 'dropedit',
                                        style = { 'border-color': 'red'}
                                    )
                                ], className = 'inputplot' ),
                                
                                html.Div([
                                    html.Div( 'Podaj tytuł wykresu (opcjonalne)' ),
                                    dcc.Input(type = 'text', id = 'inputtittle' , value = '', className = 'inp' )], className = 'inputplot' ),
                                
                                html.Div([
                                    html.Div( 'Podaj tytuł osi X (opcjonalne)' ),
                                    dcc.Input(type = 'text', id = 'inputx' , value = '', className = 'inp' )], className = 'inputplot' ),
                                
                                html.Div([
                                    html.Div( 'Podaj tytuł osi Y (opcjonalne)' ),
                                    dcc.Input(type = 'text', id = 'inputy' , value = '', className = 'inp' )], className = 'inputplot' ),
                                
                                html.Div([
                                    'Pokaż legendę',
                                    dcc.Dropdown(
                                        id = 'droplegend',
                                        options = [
                                            { 'label': 'Tak', 'value': True },
                                            { 'label': 'Nie', 'value': False }  
                                        ],
                                        value = False,
                                        className = 'dropedit',
                                        style = { 'border-color': 'red' },
                                    )
                                ], className = 'inputplot' ),
                                
                                html.Div([
                                    html.Div( 'Podaj tytuł legendy (opcjonalne)' ),
                                    dcc.Input(type = 'text', id = 'inputlegend', value = '', className = 'inp' )], className = 'inputplot' ),
                            ], className = 'editplot-input')
                        
                        ]

                    )

                ], className = 'editplottab'

            ),

        ], className = 'plotdivs' ),
        
        html.Div([
            dcc.Graph( id = 'plot' )
        ], className = 'plotdivs')

    ], className = "plotapp")
    
 ], className = 'container')

#convert plikow oraz wklejonego tekstu
@app.callback(
    Output( 'memory', 'data' ),
    [Input( 'upload', 'contents' ),
    Input( 'pastedata', 'value' )],
    State( 'upload', 'filename' ))
def file_to_memory( content, pasted, fname ):
    
    if len(pasted) > 5:
        decoded = pasted
        fname = 'pasted'
    else:
        type, filecode = content.split(",")
        decoded = base64.b64decode(filecode)

    listoffile.append( File( fname, decoded ) )
    listoffile[-1] = listoffile[-1].convertopandas()
    table = html.Div([
        html.Div('Pierwsza w kolejności kolumna jaką zaznaczysz, będzie stanowić oś "x" twojego wykresu, a następna oś "y".', id = 'instruction' ),
        html.H2(fname, id = 'data-name'),
        dash_table.DataTable(
            
            data = listoffile[-1].to_dict( 'records' ),
            columns = [{ 'name': col, 'id': col, 'selectable': True } for col in listoffile[-1].columns ],
            column_selectable = True,
            editable = False,
            page_action = 'native',
            page_current = 0,
            page_size = 10,
            selected_columns = [],
            style_cell = { 'maxWidth': '20px', 'minWidth': '20px', 'width': '20px', 'height': '20px' },
            style_cell_conditional=[{ 'textAlign': 'center' }],
            
            id = 'dash-table'
        )
    ])
    
    return table

#wklejanie tabeli
@app.callback(
    Output( 'dash-table', 'children' ),
    [Input( 'memory', 'data' )])
def paste_table( table ):
    return table

#załadowanie plików
@app.callback(
    Output( 'load-data', 'children' ),
    [Input( 'memory', 'data')])
def print_load_data(data):
    return 'Dane zostały załadowane, możesz przejść dalej!'

#plot
@app.callback(
    Output( 'plot', 'figure' ),
    [Input( 'dash-table', 'selected_columns' ),
    Input( 'dash-table', 'data' ),
    Input( 'dropplots' , 'value' ),
    Input( 'inputtittle', 'value' ),
    Input( 'inputx', 'value' ),
    Input( 'inputy', 'value' ),
    Input( 'droplegend', 'value' ),
    Input( 'inputlegend', 'value' )]
)
def make_plot( selcolumns, pddata, type, tittle, x, y, sellegend, leg ):
    
    pan = pd.DataFrame( pddata )
    
    fig = go.Figure()

    if type == 'bar':
        fig.add_trace( 
            go.Bar(
                x = pan[selcolumns[0]], 
                y = pan[selcolumns[1]],
                name = leg 
            )
        )

    else: 
        fig.add_trace( 
            go.Scatter(
                x = pan[selcolumns[0]], 
                y = pan[selcolumns[1]],
                mode = type,
                name = leg 
            )
        )

    fig.update_layout(
        title = tittle,
        title_x = 0.5,
        xaxis_title = x,
        yaxis_title = y,
        showlegend = sellegend,
        legend_title = 'Legenda'
    )

    return fig

#zmiana stron
@app.callback(
    Output( 'page-content', 'children'),
    [Input( 'url', 'pathname' )])
def display_path(pathname):
    if pathname == '/plot':
        return plot_page
    else:
        return data_page


if __name__ == '__main__':
    app.run_server( debug=True, dev_tools_ui=False, dev_tools_props_check=False )


   
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
