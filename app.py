import dash
import dash_html_components as html
import plotly.graph_objects as go
import dash_core_components as dcc
import plotly.express as px
from dash.dependencies import Input, Output
from dash import Dash, dcc, html, Input, Output
import pandas as pd
from datetime import date, datetime
import os


app = dash.Dash()
server = app.server

# df1 = pd.read_excel("data structure.xlsx")
df = pd.read_csv("https://raw.githubusercontent.com/hchuwei/host-plotly/main/global_raw_data_for_plot_all_dp.csv")
df["beDate"] = pd.to_datetime(df["beDate"])

date_values = [f"{y}-{str(m).zfill(2)}" for y in [18, 19, 20] for m in [i for i in range(1,13)]] + [f"21-{str(m).zfill(2)}" for m in range(1,5)]
date_map = {i:date_values[i] for i in range(0,40)}
app.layout = html.Div(id = 'parent', children = [
    html.H1(id = 'H1', children = 'Price Comparison Board', style = {'textAlign':'center',\
                                            'marginTop':40,'marginBottom':40}),

        dcc.Dropdown( id = 'dropdown',
        options = [{'label': i, 'value': i} for i in df[df["region"]=="JAPAN"]['clean_importerName'].unique()],
        value = 'ACETAMINOPHEN'),
        dcc.RangeSlider(0, 38, step=1, marks = date_map, id='my-range-slider', value = [12,24]),
        dcc.Graph(id = 'bar_plot'),
        html.Button("Download Excel", id="btn_xlsx"),
        dcc.Download(id="download-dataframe-xlsx"),])


@app.callback(
    [Output(component_id='bar_plot', component_property= 'figure'),
     Output("download-dataframe-xlsx", "data"),],
    [Input(component_id='dropdown', component_property= 'value'),
     Input("btn_xlsx", "n_clicks"),
    Input('my-range-slider', 'value')],
    prevent_initial_call=True,)

def graph_update(dropdown_value, n_clicks, value):
    
    start_date = datetime.strptime(date_map[value[0]], '%y-%m')
    end_date = datetime.strptime(date_map[value[1]+1], '%y-%m')
    print(date_map[value[0]], start_date)
    print(date_map[value[1]], end_date)
    df2 = df[(df["beDate"]<end_date)&(df["beDate"]>=start_date)]
    
    quantity = df2.groupby(["clean_importerName", "mapped molecule", "region", "Company type"])[["quantity"]].sum().reset_index().rename(columns = {"quantity":"sum quantity"})
    price = df2.groupby(["clean_importerName", "mapped molecule", "region", "Company type"])[["unitPrice"]].median().reset_index().rename(columns = {"unitPrice":"mid price"})
    df3 = pd.merge(quantity, price, on = ["clean_importerName", "mapped molecule",  "region", "Company type"], how = "right").reset_index()
    
    dropdown_df = df3[df3['clean_importerName'] == dropdown_value]
    filtered_molecule = df[df['clean_importerName'] == dropdown_value]["mapped molecule"].unique()
    filtered_df = df3[(df3['clean_importerName'] != dropdown_value)&(df3["mapped molecule"].isin(filtered_molecule))]
    print(len(df3), len(filtered_df), len(filtered_molecule))
    fig = px.scatter(
            filtered_df, x="mapped molecule", y="mid price", 
            color="region", symbol="Company type",
            labels={
                "mapped molecule": "Import molecules",
                "mid price": "median unit price (USD/kg)",
                         },
            hover_data=['clean_importerName', "sum quantity"])
    fig.add_trace(
        go.Scatter(
            mode='markers',
            name = f"{dropdown_value} import price",
            x=dropdown_df["mapped molecule"],
            y=dropdown_df["mid price"],
            text=dropdown_df['sum quantity'],
            marker=dict(
                symbol = "line-ew",
                color='MediumPurple',
                size=50,
                line=dict(
                    color='MediumPurple'
                    )
                    ),
                    showlegend=False
                    )
                    )
    fig.update_traces(marker=dict(size=12,
                                  line=dict(width=2,
                                            color='DarkSlateGrey')),
                      selector=dict(mode='markers'), showlegend = True)
    fig.update_traces(marker=dict(size=80,
                                  line=dict(width=3,
                                            color='green')),
                      selector=dict(name=f"{dropdown_value} import price"), showlegend = True)
    fig.update_layout(hoverlabel_align = 'right')
    
    whole_range = pd.concat([dropdown_df, filtered_df], axis=0)
    l, r = whole_range["mid price"].min(), whole_range["mid price"].max()
    fig.update_yaxes(range = [max(l-(r-l)*0.1, 0), r+(r-l)*0.1])
    fig.add_annotation(text="Source: PSSE data; * unit price are median of every importers",
                      xref="paper", yref="paper",
                      x=0, y=-0.2, showarrow=False, font_size = 10)
    if n_clicks is not None:
        return fig, dcc.send_data_frame(df2[df2["mapped molecule"].isin(filtered_molecule)].to_excel, f"{dropdown_value}_related_data_{date_map[value[0]]}_{date_map[value[1]]}.xlsx", sheet_name="result")
    return fig, None


if __name__ == '__main__': 
    app.run_server(debug=True)
