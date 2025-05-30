import networkx as nx
import osmnx as ox

ox.__version__

# download/model a street network for some city then visualize it
print("Graphing California")
G = ox.graph.graph_from_place("Berkeley County, South Carolina, USA", network_type="drive")
print("Plotting California")
fig, ax = ox.plot.plot_graph(G)

# get a fully bidirection network (as a MultiDiGraph)
print("Graphing Summerville")
ox.settings.bidirectional_network_types += "drive"
G = ox.graph.graph_from_place("Cane Bay Plantation", network_type="drive")

# convert your MultiDiGraph to an undirected MultiGraph
print("Undirected")
M = ox.convert.to_undirected(G)

# convert your MultiDiGraph to a DiGraph without parallel edges
print("Directed")
D = ox.convert.to_digraph(G)

# you can convert your graph to node and edge GeoPandas GeoDataFrames
print("GDF")
gdf_nodes, gdf_edges = ox.convert.graph_to_gdfs(G)
gdf_nodes.head()

gdf_edges.head()

# convert node/edge GeoPandas GeoDataFrames to a NetworkX MultiDiGraph
G2 = ox.convert.graph_from_gdfs(gdf_nodes, gdf_edges, graph_attrs=G.graph)
fig, ax = ox.plot.plot_graph(G2)

# what sized area does our network cover in square meters?
G_proj = ox.projection.project_graph(G)
nodes_proj = ox.convert.graph_to_gdfs(G_proj, edges=False)
graph_area_m = nodes_proj.union_all().convex_hull.area
graph_area_m

# show some basic stats about the network
ox.stats.basic_stats(G_proj, area=graph_area_m, clean_int_tol=15)

# save graph to disk as geopackage (for GIS) or graphml file (for gephi etc)
#ox.io.save_graph_geopackage(G, filepath="./data/mynetwork.gpkg")
# ox.io.save_graphml(G, filepath="./data/mynetwork.graphml")

# convert graph to line graph so edges become nodes and vice versa
edge_centrality = nx.closeness_centrality(nx.line_graph(G))
nx.set_edge_attributes(G, edge_centrality, "edge_centrality")

# color edges in original graph with closeness centralities from line graph
ec = ox.plot.get_edge_colors_by_attr(G, "edge_centrality", cmap="inferno")
fig, ax = ox.plot.plot_graph(G, edge_color=ec, edge_linewidth=2, node_size=0)

# impute missing edge speeds and calculate edge travel times with the speed module
G = ox.routing.add_edge_speeds(G)
G = ox.routing.add_edge_travel_times(G)

# get the nearest network nodes to two lat/lng points with the distance module
orig = ox.distance.nearest_nodes(G, X=-80.12053, Y=33.12943)
dest = ox.distance.nearest_nodes(G, X=-80.12757, Y=33.11436)

# find the shortest path between nodes, minimizing travel time, then plot it
route = ox.routing.shortest_path(G, orig, dest, weight="travel_time")
fig, ax = ox.plot.plot_graph_route(G, route, node_size=0, edge_color=ec)

# how long is our route in meters?
edge_lengths = ox.routing.route_to_gdf(G, route)["length"]
roadmeters = round(sum(edge_lengths))
print(roadmeters)

# how far is it between these two nodes as the crow flies?
# use OSMnx's vectorized great-circle distance (haversine) function
orig_x = G.nodes[orig]["x"]
orig_y = G.nodes[orig]["y"]
dest_x = G.nodes[dest]["x"]
dest_y = G.nodes[dest]["y"]
airmeters = round(ox.distance.great_circle(orig_y, orig_x, dest_y, dest_x))
print(airmeters)