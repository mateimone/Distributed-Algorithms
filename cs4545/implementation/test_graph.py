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