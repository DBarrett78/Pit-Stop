import networkx as nx
import osmnx as ox
import geopandas as gpd
import matplotlib.pyplot as plt
from sklearn.cluster import DBSCAN
import numpy as np

print(f"OX {ox.__version__}")
print(f"GPD {gpd.__version__}")

place_name = "Berkeley County, South Carolina, USA"
tags = {"brand": "Walmart"}  # broader and more consistent than name

# Query OSM for all features matching the tags in the place
walmart_locations = ox.features_from_place(place_name, tags=tags)

# Filter for relevant geometry types (points, polygons)
walmart_locations = walmart_locations[walmart_locations.geometry.type.isin(["Point", "Polygon"])]
walmart_locations = walmart_locations.reset_index()

print(f"Found {len(walmart_locations)} Walmart locations in {place_name}")
print(walmart_locations[["name", "geometry", "addr:street"]])

# Step 1: Reproject to a projected CRS (EPSG:3857)
projected = walmart_locations.to_crs(epsg=3857)

# Step 2: Calculate centroids safely now that we're in meters
projected["geometry"] = projected.geometry.centroid

# Step 3: Extract coordinates for clustering
coords = np.array([(geom.x, geom.y) for geom in projected.geometry])

# Step 4: Use DBSCAN clustering with eps=100 meters, min_samples=1 (each point at least in its own cluster)
db = DBSCAN(eps=500, min_samples=1).fit(coords)

# Step 5: Add cluster labels to GeoDataFrame
projected["cluster"] = db.labels_

# Step 6: Keep only one store per cluster (e.g., the first store in each cluster)
unique_stores = projected.groupby("cluster").first().reset_index(drop=True)

# Re-assign CRS after groupby, because it gets lost
unique_stores = gpd.GeoDataFrame(unique_stores, geometry='geometry', crs=projected.crs)

print(f"Reduced from {len(projected)} to {len(unique_stores)} unique Walmart locations after clustering.")

# Create the street network graph
G = ox.graph_from_place(place_name, network_type="drive")

# Convert graph nodes to GeoDataFrame with same CRS as unique stores
gdf_nodes = ox.graph_to_gdfs(G, nodes=True, edges=False)

# Reproject unique stores to graph CRS (to align for plotting)
unique_stores = unique_stores.to_crs(gdf_nodes.crs)

# Check geometry validity
print(f"Empty geometries: {unique_stores.is_empty.sum()}")
print(f"Non-null geometries: {unique_stores.geometry.notnull().sum()}")

# Plot street network graph
edge_centrality = nx.closeness_centrality(nx.line_graph(G))
nx.set_edge_attributes(G, edge_centrality, "edge_centrality")
ec = ox.plot.get_edge_colors_by_attr(G, "edge_centrality", cmap="inferno")
fig, ax = ox.plot_graph(G, show=False, close=False, edge_color=ec)

# Plot Walmart locations on the graph
unique_stores.plot(ax=ax, color='red', markersize=50, alpha=0.7)

plt.title(f"Unique Walmart Locations in {place_name} on Street Network")
plt.show()