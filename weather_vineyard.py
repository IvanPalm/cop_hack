### Get weather dat for vineyeard in Southern Germany
import pandas as pd
from pyowm.owm import OWM

openweather_key = '3da2f63daffc7bb861a6241e6f448cd6'

lat = 48.759269
lon = 9.21895
village = 'Rohracker'

owm = OWM(openweather_key)
mgr = owm.weather_manager()

# Check available weather stations
obs_list = mgr.weather_around_coords(lat, lon)
len(obs_list)
for obs in obs_list:
    print(obs.weather.temperature('celsius')['temp'])
# 5 different weather stations in the surrounding of the ref coordinates

st_df = pd.DataFrame([obs.location.id, obs.location.lat, obs.location.lon] for obs in obs_list)
st_df.columns = ['st_id', 'st_lat', 'st_log']

# Check whether village has one station too
obs = mgr.weather_at_place(village + ',DE')
st_vill = [obs.location.id, obs.location.lat, obs.location.lon]

st_df = st_df.append(pd.Series(st_vill, index=st_df.columns), ignore_index=True)
st_df.to_csv('weather_stations.csv')

# Selected Weather Station
station=st_vill[0]
