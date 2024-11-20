import yaml
from test_graph import get_connectivity

n_nodes = 10
exchanged_msgs = 0
time_to_broadcast = 0
network_connectivity = get_connectivity()

for i in range(n_nodes):
    file = f"../../output/node-{i}.yml"

    with open(file, 'r') as f:
        data = yaml.safe_load(f)
        exchanged_msgs += data['messages_received']
