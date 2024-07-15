import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# File path (ensure the path to your CSV is correct if you're uploading it)
file_path = 'concatenated_wind_data_42.872028_-82.120731.csv'

# Load the data
df = pd.read_csv(file_path)

# Assuming the column names are 'time', 'wind_speed', and 'wind_direction'
df['time'] = pd.to_datetime(df['time'])
df['Hour'] = df['time'].dt.hour
df['Month'] = df['time'].dt.month
df['Year'] = df['time'].dt.year

# Categorize time of day
time_bins = [0, 6, 12, 18, 24]
time_labels = ['Early Morning', 'Morning', 'Afternoon', 'Evening']
df['Time Category'] = pd.cut(df['Hour'], bins=time_bins, labels=time_labels, right=False)

# Calculate averages
avg_wind_direction = df.groupby('Time Category')['wind_direction'].mean().reset_index()
avg_wind_speed = df.groupby('Time Category')['wind_speed'].mean().reset_index()

# Merge the average wind direction and speed into one DataFrame
avg_data = pd.merge(avg_wind_direction, avg_wind_speed, on='Time Category')
avg_data.columns = ['Time Category', 'Average Wind Direction (degrees)', 'Average Wind Speed (m/s)']

# Define uncertainty range (in degrees)
uncertainty_range = 30

# Title
st.title("Wind Data Dashboard")

# Time Series Plot
st.subheader("Wind Speed and Direction over Time")
selected_data = st.multiselect(
    'Select data to display in the time series plot:',
    ['Wind Speed', 'Wind Direction'],
    default=['Wind Speed', 'Wind Direction']
)

fig = go.Figure()

# Plot selected data as scatter plots
if 'Wind Speed' in selected_data:
    fig.add_trace(go.Scatter(x=df['time'], y=df['wind_speed'], mode='markers', name='Wind Speed',
                             marker=dict(color='blue')))
if 'Wind Direction' in selected_data:
    fig.add_trace(go.Scatter(x=df['time'], y=df['wind_direction'], mode='markers', name='Wind Direction',
                             yaxis='y2', marker=dict(color='red')))

# Update layout to include secondary y-axis if Wind Direction is selected
if 'Wind Direction' in selected_data:
    fig.update_layout(
        yaxis2=dict(
            title='Wind Direction (degrees)',
            overlaying='y',
            side='right'
        )
    )

fig.update_layout(
    title='Wind Speed and Direction over Time',
    xaxis_title='Time',
    yaxis_title='Wind Speed (m/s)'
)
st.plotly_chart(fig)

# Wind Rose Plot
st.subheader("Wind Rose Plot by Time of Day")

selected_time = st.selectbox("Select Time of Day", time_labels)

# Define colors for each time category
time_colors = {
    'Early Morning': 'blue',
    'Morning': 'green',
    'Afternoon': 'orange',
    'Evening': 'red'
}

angles = np.radians(avg_data['Average Wind Direction (degrees)'])
wind_speed = avg_data['Average Wind Speed (m/s)']

wind_rose_fig = go.Figure()
for i, label in enumerate(time_labels):
    opacity = 1.0 if label == selected_time else 0.5
    wind_rose_fig.add_trace(go.Scatterpolar(
        r=[0, wind_speed[i]],
        theta=[0, avg_data['Average Wind Direction (degrees)'][i]],
        mode='lines+markers+text',
        text=[label, label],
        textposition='top center',
        opacity=opacity,
        name=label,
        line=dict(color=time_colors[label]),
        marker=dict(color=time_colors[label])
    ))
wind_rose_fig.update_layout(
    title='Wind Direction Shift by Time of Day',
    polar=dict(
        radialaxis=dict(visible=True, range=[0, max(wind_speed)]),
        angularaxis=dict(rotation=90, direction='clockwise', tickvals=[0, 90, 180, 270], ticktext=['N', 'E', 'S', 'W'])
    )
)
st.plotly_chart(wind_rose_fig)

# Highlight Downwind Area for Selected Time
st.subheader("Highlight Downwind Area for Selected Time")

# Get the downwind direction and add uncertainty range for the selected time
selected_wind_direction = avg_data.loc[avg_data['Time Category'] == selected_time, 'Average Wind Direction (degrees)'].values[0]
downwind_direction = (selected_wind_direction + 180) % 360

downwind_sector_start = (downwind_direction - uncertainty_range) % 360
downwind_sector_end = (downwind_direction + uncertainty_range) % 360

downwind_fig = go.Figure()

# Plot filled sector to show the downwind area with uncertainty
theta_start = downwind_sector_start
theta_end = downwind_sector_end

downwind_fig.add_trace(go.Scatterpolar(
    r=[0, 1, 1, 0],
    theta=[theta_start, theta_start, theta_end, theta_end],
    fill='toself',
    fillcolor='rgba(255, 0, 0, 0.3)',
    line=dict(color='rgba(255, 0, 0, 0.3)')
))

downwind_fig.update_layout(
    title=f'Downwind Area with Uncertainty for {selected_time}',
    polar=dict(
        radialaxis=dict(visible=True, range=[0, 1]),
        angularaxis=dict(rotation=90, direction='clockwise', tickvals=[0, 90, 180, 270], ticktext=['N', 'E', 'S', 'W'])
    )
)

st.plotly_chart(downwind_fig)

# Summary Table
st.subheader("Summary Table of Average Wind Direction and Speed")
summary_table = """
| Time Category  | Average Wind Direction (degrees) | Average Wind Speed (m/s) |
|----------------|----------------------------------|---------------------------|
| Early Morning  | 153                              | 2.81                      |
| Morning        | 170                              | 2.76                      |
| Afternoon      | 175                              | 3.11                      |
| Evening        | 184                              | 3.42                      |
"""
st.markdown(summary_table)

# Interpretation
st.subheader("Interpretation")
st.markdown("""
### Wind Direction:
There is a slight shift in wind direction throughout the day. Early mornings have a more easterly component, which shifts towards a more southerly direction by the evening.

### Wind Speed:
Wind speed generally increases throughout the day, peaking in the evening.
""")
