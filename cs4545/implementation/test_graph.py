import networkx as nx
import matplotlib.pyplot as plt
import yaml
import sys

def get_connectivity():
    adjacency_yaml = "../../topologies/dolev.yaml"

    try:
        adjacency = yaml.safe_load(open(adjacency_yaml))
        print(adjacency)
    except yaml.YAMLError as exc:
        print("Error parsing YAML:", exc)
        sys.exit(1)


    G = nx.Graph()

    for node, neighbors in adjacency.items():
        for neighbor in neighbors:
            G.add_edge(int(node), int(neighbor))

    print(nx.node_connectivity(G))
    return nx.node_connectivity(G)
get_connectivity()
# is_connected = nx.is_connected(G)
# print(f"Is the graph connected? {is_connected}")
#
# vertex_connectivity = nx.edge_connectivity(G)
# print(f"Vertex connectivity of the graph: {vertex_connectivity}")
#
#
# k_values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
#
# for k in k_values:
#     try:
#         is_k_connected = nx.is_k_edge_connected(G, k)
#         print(f"Is the graph {k}-connected? {is_k_connected}")
#     except nx.NetworkXError as e:
#         print(f"Error checking {k}-connectivity:", e)
#
# try:
#     min_vertex_cut = nx.minimum_node_cut(G)
#     print(f"Minimum vertex cut (size {len(min_vertex_cut)}): {min_vertex_cut}")
# except nx.NetworkXError as e:
#     print("Error finding minimum vertex cut:", e)
#
#
# def visualize_graph(G, vertex_cut):
#     plt.figure(figsize=(8, 6))
#
#     pos = nx.spring_layout(G, seed=42)
#
#     nx.draw_networkx_nodes(G, pos, node_size=700, node_color='lightblue', label='Nodes')
#
#     if vertex_cut:
#         nx.draw_networkx_nodes(G, pos, nodelist=vertex_cut, node_size=700, node_color='salmon', label='Vertex Cut')
#
#     nx.draw_networkx_edges(G, pos, width=2)
#
#     nx.draw_networkx_labels(G, pos, font_size=12, font_weight='bold')
#
#     plt.legend(scatterpoints=1)
#
#     plt.title("Graph Connectivity Visualization")
#     plt.axis('off')
#     plt.tight_layout()
#     plt.show()
#
#
# visualize_graph(G, min_vertex_cut)
