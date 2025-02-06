import pandas as pd
import plotly.express as px
from plotly.offline import plot
import plotly.io as pio
from plotly.graph_objs import Figure
import plotly.graph_objects as go


def create_barchart_div(home_df: pd.DataFrame, visitor_df: pd.DataFrame) -> str:
    home_points = home_df.rename(columns={"PtsScored": "Home"}).reindex(columns=["Player Name", "Home"])
    visitor_points = visitor_df.rename(columns={"PtsScored": "Visitor"}).reindex(columns=["Player Name", "Visitor"])
    agg_df = pd.concat([home_points, visitor_points], ignore_index=True)
    agg_df = agg_df.groupby("Player Name", as_index=False).agg(lambda x: list(set(x.dropna()))[0] if x.any() else None)

    # Create figure with both traces
    fig_px = px.bar(agg_df, x="Player Name", y=["Home", "Visitor"], barmode="group")

    # Convert to go.Figure and include both traces
    fig = go.Figure(data=fig_px.data)  # Includes all traces

    # Customize layout
    fig.update_layout(
        plot_bgcolor="#5e678e",  # Background color
        paper_bgcolor="#5e678e",  # Outer background
        font=dict(color="white"),  # Text color
        title=dict(text="Players by Points Scored", font=dict(size=20, color="white"))
    )

    # Get the HTML div string
    plot_div = plot(fig, output_type="div", include_plotlyjs=True)  # Get HTML div without extra JS

    return plot_div

def create_linechart_div(df: pd.DataFrame, value_col: str, selected_player: str):
    selected_row = df.loc[df["Player Name"] == selected_player]
    try:
        selected_row = selected_row.drop(columns=selected_row.filter(like="Unnamed").columns)
    except:
        pass

    match_names = selected_row.columns.to_list()
    match_names.remove("Player Name")
    new_df = pd.DataFrame(data={
        "Match Name": match_names,
        value_col: selected_row.to_numpy().flatten()[1:] # player name exist at first column
    })

    # Create a Plotly figure
    fig = Figure(data=[px.line(new_df, x="Match Name", y=value_col).data[0]])
    fig.update_traces(mode="lines+markers", marker=dict(size=15, color="#8061ff"))
    fig.update_layout(
        plot_bgcolor="#5e678e",  # Background color
        paper_bgcolor="#5e678e",  # Outer background
        font=dict(color="white"),  # Text color
        title=dict(text=f"{selected_player} by {value_col}", font=dict(size=20, color="white")),
    )
    fig.update_layout(
        autosize=True,  # Enable auto-sizing
        width=None,  # Let the container define the width
        height=None,  # Let the container define the height
        margin=dict(l=10, r=10, t=50, b=10),  # Reduce margins for better fit
    )

    # Get the HTML div string
    plot_div = pio.to_json(fig)

    return plot_div

def reset_plots(request):
    if request.session.get("pts_plot"):
        del request.session["pts_plot"]
        del request.session["p_names"]
    elif request.session.get("no_plot"):
        del request.session["no_plot"]
