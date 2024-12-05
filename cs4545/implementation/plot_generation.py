import ast
import os.path
import re
from pathlib import Path

import click
import yaml
from matplotlib import pyplot as plt
from test_graph import get_connectivity
import pandas as pd


def load_algo(file_path):
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
    max_value = 0

    for i in range(num_nodes):
        if i in id_byzantine_nodes:
            continue

        file = f"../../output/node-{i}.yml"

        with open(file, 'r') as f:
            data = yaml.safe_load(f)
            delivery_time = data['delivery_time']
            delivery_time_dict = ast.literal_eval(delivery_time)

            if isinstance(delivery_time_dict, dict) and len(delivery_time_dict) > 0:
                max_value = max(delivery_time_dict.values())

    latency = max_value
    return latency


def calculate_num_broadcasts_and_starting_nodes(scenario, id_byzantine_nodes):
    num_broadcasts_correct_nodes = 0
    num_broadcasts_f_nodes = 0
    start_nodes = 0

    for id, node in scenario.items():
        if 'messages' in node:
            if id in id_byzantine_nodes:
                num_broadcasts_f_nodes += len(node['messages'])
            else:
                start_nodes += 1
                num_broadcasts_correct_nodes += len(node['messages'])

    return num_broadcasts_correct_nodes, num_broadcasts_f_nodes, start_nodes


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


@click.group()
def cli():
    pass


# python3 plot_generation.py aggregate
@cli.command("aggregate")
@click.option("--topology_file", default="../../topologies/dolev.yaml")
@click.option("--output", default="output")
def aggregate(topology_file, output):
    topology = load_algo(topology_file)
    output_dir = Path(output)

    # collect stats from iteration
    num_nodes = load_number_of_nodes("../../run_brb.sh")
    scenario = load_algo("../../scenarios/scenario1.yaml")
    f, id_byzantine_nodes = load_byzantine_nodes(scenario)
    message_complexity = load_total_messages_received(num_nodes)
    latency = calculate_latency(num_nodes, id_byzantine_nodes)
    network_connectivity = get_connectivity()
    num_broadcasts_correct_nodes, num_broadcasts_f_nodes, starting_nodes = calculate_num_broadcasts_and_starting_nodes(
        scenario, id_byzantine_nodes)

    # save stats
    run_stats = {
        "n": num_nodes,
        "f": f,
        "starting_nodes": starting_nodes,
        "message_complexity": message_complexity,
        "broadcasts": num_broadcasts_correct_nodes,
        "latency": latency,
        "network_connectivity": network_connectivity,
    }

    df = None
    experiment_file = "../experiments/experimentBrachaOptim2.csv"
    if os.path.exists(experiment_file) and os.path.getsize(experiment_file) > 0:
        df = pd.read_csv(experiment_file)
    else:
        df = pd.DataFrame(
            columns=['n', 'f', 'starting_nodes', 'message_complexity', 'broadcasts', 'latency', 'network_connectivity'])

    new_row = pd.DataFrame([run_stats])
    df = pd.concat([df, new_row], ignore_index=True)

    df.to_csv(experiment_file, index=False)


@cli.command("plot")
@click.option("--experiment_file", default="../experiments/experimentBrachaOptim1.csv")
@click.option("--output", default="../experiments")
@click.option("--metric", default="message_complexity", type=click.Choice(['message_complexity', 'latency'], case_sensitive=False))
def plot(experiment_file, output, metric):
    df = pd.read_csv(experiment_file)
    df_filtered = df[df['broadcasts'] == 1]

    df_avg = df_filtered.groupby('n', as_index=False)[metric].mean()
    df_avg = df_avg.sort_values(by='n')

    network_size = df_avg['n']
    metric_values = df_avg[metric]

    plt.figure(figsize=(8, 6))
    plt.plot(network_size, metric_values, marker='o', color='red',
             label=f"F=1, Broadcasts=1, Network Connectivity=3")

    plt.xlabel("Network Size", fontsize=12)
    plt.ylabel(metric.replace('_', ' ').capitalize(), fontsize=12)
    plt.title(f"{metric.replace('_', ' ').capitalize()} vs Network Size", fontsize=14)
    plt.legend()

    output_file = os.path.join(output, f"{metric}_vs_network_size_bracha.png")
    plt.savefig(output_file)

    plt.tight_layout()
    plt.show()


@cli.command("plot_multiple")
@click.option("--experiment_files",
              default="../experiments/experimentBrachaBaseline.csv,../experiments/experimentBrachaOptim1.csv,../experiments/experimentBrachaOptim2.csv,../experiments/experimentBrachaOptim3.csv")
@click.option("--output", default="../experiments")
def plot_multiple(experiment_files, output):
    experiment_files = experiment_files.split(',')
    metrics = ['message_complexity', 'latency']

    comparisons = [
        ("Optim1", "Baseline"),
        ("Optim2", "Baseline"),
        ("Optim3", "Baseline")
    ]

    x_ticks = [4, 5, 6, 7, 8, 10, 14, 17, 20, 22, 25, 26]

    def process_file(file):
        df = pd.read_csv(file)
        df_filtered = df[df['broadcasts'] == 1]
        df_avg = df_filtered.groupby('n', as_index=False)[metrics].mean()
        return df_avg.sort_values(by='n')

    data = {
        "Optim1": process_file("../experiments/experimentBrachaOptim1.csv"),
        "Optim2": process_file("../experiments/experimentBrachaOptim2.csv"),
        "Optim3": process_file("../experiments/experimentBrachaOptim3.csv"),
        "Baseline": process_file("../experiments/experimentBrachaBaseline.csv")
    }

    for opt_pair in comparisons:
        opt1, opt2 = opt_pair

        fig, axes = plt.subplots(1, 2, figsize=(16, 6))
        fig.suptitle(f"{opt1} vs {opt2}", fontsize=16)

        for idx, metric in enumerate(metrics):
            ax = axes[idx]

            for opt, style in zip([opt1, opt2], ['-', '--']):
                if opt in data:
                    df_avg = data[opt]
                    ax.plot(df_avg['n'], df_avg[metric], marker='o', linestyle=style, label=opt)

            ax.set_xticks(x_ticks)
            ax.set_xlim([min(x_ticks), max(x_ticks)])  # Ensure the limits fit the specified ticks

            ax.set_xlabel("Network Size", fontsize=12)
            ax.set_ylabel(metric.replace('_', ' ').capitalize(), fontsize=12)
            ax.set_title(f"{metric.replace('_', ' ').capitalize()} vs Network size", fontsize=14)
            ax.grid(True, which="both", linestyle='--', linewidth=0.5)
            ax.legend()

        output_file = os.path.join(output, f"{opt1}_vs_{opt2}_bracha.png")
        plt.savefig(output_file)

        plt.tight_layout()
        plt.show()

@cli.command("plot_all")
@click.option("--experiment_files", default="../experiments/experimentBrachaOptim1.csv,../experiments/experimentBrachaOptim2.csv,../experiments/experimentBrachaOptim3.csv,../experiments/experimentBrachaBaseline.csv")
@click.option("--output", default="../experiments")
def plot_all(experiment_files, output):
    experiment_files = experiment_files.split(',')
    labels = ["Optim1", "Optim2", "Optim3", "Baseline"]
    styles = ['-', '-', '-', '-']
    colors = ['blue', 'green', 'red', 'orange']

    metrics = ['message_complexity', 'latency']

    x_ticks = [4, 5, 6, 7, 8, 10, 14, 17, 20, 22, 25, 26]

    def process_file(file):
        df = pd.read_csv(file)
        df_filtered = df[df['broadcasts'] == 1]
        df_avg = df_filtered.groupby('n', as_index=False)[metrics].mean()
        return df_avg.sort_values(by='n')

    data = {label: process_file(file) for label, file in zip(labels, experiment_files)}

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle("Message Complexity and Latency for All Optimizations", fontsize=16)

    for idx, metric in enumerate(metrics):
        ax = axes[idx]

        for label, style, color in zip(labels, styles, colors):
            df_avg = data[label]
            ax.plot(df_avg['n'], df_avg[metric], marker='o', linestyle=style, color=color, label=label)

        ax.set_xticks(x_ticks)
        ax.set_xlim([min(x_ticks), max(x_ticks)])

        ax.set_xlabel("Network size", fontsize=12)
        ax.set_ylabel(metric.replace('_', ' ').capitalize(), fontsize=12)
        ax.set_title(f"{metric.replace('_', ' ').capitalize()} vs Network size", fontsize=14)
        ax.grid(True, which="both", linestyle='--', linewidth=0.5)
        ax.legend()

    output_file = os.path.join(output, "all_optimizations_comparison.png")
    plt.savefig(output_file)

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    cli()
