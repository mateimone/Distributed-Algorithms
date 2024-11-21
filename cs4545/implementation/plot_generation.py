import ast
import os.path
import re
from pathlib import Path

import click
import yaml
from matplotlib import pyplot as plt
from test_graph import get_connectivity
import pandas as pd

def load_dolev(file_path):
    with open(file_path, 'r') as f:
        config = yaml.safe_load(f)
    return config

# Used for calculating message complexity
def load_total_messages_received(num_nodes):
    exchanged_msgs = 0
    for i in range(num_nodes):
        file = f"../../output/node-{i}.yml"

        with open(file, 'r') as f:
            data = yaml.safe_load(f)
            exchanged_msgs += data['messages_received']

    return exchanged_msgs

def calculate_latency(num_nodes, id_byzantine_nodes):
    latency = 0
    l = 0
    for i in range(num_nodes):
        if i in id_byzantine_nodes:
            continue

        file = f"../../output/node-{i}.yml"

        with open(file, 'r') as f:
            data = yaml.safe_load(f)
            delivery_time = data['delivery_time']
            delivery_time_dict = ast.literal_eval(delivery_time)

            if isinstance(delivery_time_dict, dict):
                max_value = max(delivery_time_dict.values())

            l += max_value

    latency = l / (num_nodes - len(id_byzantine_nodes))
    return latency


def load_byzantine_nodes(scenario):
    num = 0
    ids = []
    for id, node in scenario.items():
        if node['type'] == 'byzantine':
            ids.append(id)
            num += 1
    return num, ids

def load_number_of_nodes(script):
    with open(script, 'r') as f:
        script_content = f.read()
    match = re.search(r'NUM_NODES=(\d+)', script_content)
    if match:
        return int(match.group(1))
    else:
        raise ValueError(f'Could not find number of nodes in {script}')

def plot_results(latencies, message_counts):
    pass

@click.group()
def cli():
    pass

# python3 plot_generation.py aggregate
@cli.command("aggregate")
@click.option("--topology_file", default="../../topologies/dolev.yaml")
@click.option("--output", default="output")
def aggregate(topology_file, output):
    topology = load_dolev(topology_file)
    output_dir = Path(output)

    # collect stats from iteration
    num_nodes = load_number_of_nodes("../../run_dolev.sh")
    scenario = load_dolev("../../scenarios/scenario1.yaml")
    f, id_byzantine_nodes = load_byzantine_nodes(scenario)
    message_complexity = load_total_messages_received(num_nodes)
    latency = calculate_latency(num_nodes, id_byzantine_nodes)
    network_connectivity = get_connectivity()

    # save stats
    run_stats = {
        "n": num_nodes,
        "message_complexity": message_complexity,
        "f": f,
        "latency": latency,
        "network_connectivity": network_connectivity,
    }

    df = None
    experiment_file = "../experiments/current.csv"
    if os.path.exists(experiment_file) and os.path.getsize(experiment_file) > 0:
        df = pd.read_csv(experiment_file)
    else:
        df = pd.DataFrame(columns=['n', 'f', 'message_complexity', 'latency', 'network_connectivity'])

    new_row = pd.DataFrame([run_stats])
    df = pd.concat([df, new_row], ignore_index=True)

    df.to_csv(experiment_file, index=False)

if __name__ == "__main__":
    cli()
