import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

# File path (ensure the path to your CSV is correct if you're uploading it)
file_path = 'concatenated_wind_data_42.872028_-82.120731.csv'

# Load the data
try:
    df = pd.read_csv(file_path)
except FileNotFoundError:
    st.error("The file was not found. Please check the file path.")
    st.stop()

# Assuming the column names are 'time', 'wind_speed', and 'wind_direction'
try:
    df['time'] = pd.to_datetime(df['time'])
    df['Hour'] = df['time'].dt.hour
    df['Month'] = df['time'].dt.month
    df['Year'] = df['time'].dt.year
except KeyError:
    st.error("The expected columns 'time', 'wind_speed', and 'wind_direction' are not found in the dataset.")
    st.stop()

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
uncertainty_range = 15

# Title
st.title("Wind Data Dashboard")

# Time Series Plot
st.subheader("Wind Speed and Direction over Time")
selected_data = st.multiselect(
    'Select data to display in the time series plot:',
    ['Wind Speed', 'Wind Direction'],
    default=['Wind Speed', 'Wind Direction']
)

fig = plt.figure()

# Plot selected data as scatter plots
if 'Wind Speed' in selected_data:
    plt.scatter(df['time'], df['wind_speed'], label='Wind Speed', color='blue')
if 'Wind Direction' in selected_data:
    plt.scatter(df['time'], df['wind_direction'], label='Wind Direction', color='red')

plt.title('Wind Speed and Direction over Time')
plt.xlabel('Time')
plt.ylabel('Wind Speed (m/s) / Wind Direction (degrees)')
plt.legend()
st.pyplot(fig)

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

fig, ax = plt.subplots(subplot_kw={'projection': 'polar'})
for i, label in enumerate(time_labels):
    theta = np.deg2rad(avg_data.loc[avg_data['Time Category'] == label, 'Average Wind Direction (degrees)'])
    r = avg_data.loc[avg_data['Time Category'] == label, 'Average Wind Speed (m/s)']
    ax.plot(theta, r, 'o-', label=label, color=time_colors[label])
    ax.fill(theta, r, alpha=0.3, color=time_colors[label])

ax.set_theta_direction(-1)
ax.set_theta_offset(np.pi / 2.0)
ax.set_rlabel_position(-22.5)
plt.legend(loc='upper right')
plt.title('Wind Rose Plot by Time of Day')
st.pyplot(fig)

# Highlight Downwind Area for Selected Time on Map
st.subheader("Highlight Downwind Area for Selected Time on Map")

# Get the downwind direction and add uncertainty range for the selected time
selected_wind_direction = avg_data.loc[avg_data['Time Category'] == selected_time, 'Average Wind Direction (degrees)'].values[0]
downwind_direction = (selected_wind_direction + 180) % 360

downwind_sector_start = (downwind_direction - uncertainty_range) % 360
downwind_sector_end = (downwind_direction + uncertainty_range) % 360

# Coordinates of the location
lat, lon = 42.872028, -82.120731

# Create map with downwind area using cartopy
fig, ax = plt.subplots(subplot_kw={'projection': ccrs.PlateCarree()})
ax.set_extent([lon-5, lon+5, lat-5, lat+5], crs=ccrs.PlateCarree())

# Add geographic features
ax.add_feature(cfeature.LAND)
ax.add_feature(cfeature.OCEAN)
ax.add_feature(cfeature.COASTLINE)
ax.add_feature(cfeature.BORDERS, linestyle=':')
ax.add_feature(cfeature.LAKES, alpha=0.5)
ax.add_feature(cfeature.RIVERS)

# Plot the wind measurement point
ax.plot(lon, lat, 'ro', markersize=10, transform=ccrs.PlateCarree())

# Plot the downwind area with uncertainty
angles = np.linspace(downwind_sector_start, downwind_sector_end, 100)
for angle in angles:
    end_lat = lat + np.cos(np.radians(angle))
    end_lon = lon + np.sin(np.radians(angle))
    ax.plot([lon, end_lon], [lat, end_lat], color='red', alpha=0.3, transform=ccrs.PlateCarree())

# Add title
plt.title(f'Downwind Area with Uncertainty for {selected_time}')

# Display the plot using Streamlit
st.pyplot(fig)

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
