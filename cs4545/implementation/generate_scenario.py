import yaml
import random
import argparse
import sys

def generate_nodes_config(total_nodes, num_dolev, num_byzantine, output_file='nodes_config.yaml'):
    """
    Generates a YAML configuration file for nodes with specified types and messages.

    Args:
        total_nodes (int): Total number of nodes.
        num_dolev (int): Number of 'dolev' type nodes.
        num_byzantine (int): Number of 'byzantine' type nodes.
        output_file (str): Name of the output YAML file.
    """
    if num_dolev + num_byzantine > total_nodes:
        print("Error: The sum of 'dolev' and 'byzantine' nodes exceeds the total number of nodes.")
        sys.exit(1)

    node_indices = list(range(total_nodes))

    # Randomly select 'dolev' nodes
    dolev_nodes = random.sample(node_indices, num_dolev) if num_dolev > 0 else []

    # The rest are 'byzantine'
    byzantine_nodes = [n for n in node_indices if n not in dolev_nodes][:num_byzantine]

    nodes_config = {}

    message_counter = 1  # To assign unique message numbers for 'dolev' messages

    for node in node_indices:
        node_entry = {}

        if node in dolev_nodes:
            node_entry["type"] = 'dolev'

            will_send = random.uniform(0, 1)
            if will_send > 0.5:
                num_messages = random.randint(0, 2)
            else:
                num_messages = 0
            messages = []
            for _ in range(num_messages):
                msg = f"Message example {message_counter}"
                messages.append(msg)
                message_counter += 1
            if messages:
                node_entry["messages"] = messages

        elif node in byzantine_nodes:
            node_entry["type"] = 'byzantine'

            num_messages = 1
            messages = []
            for _ in range(num_messages):
                msg = "Malicious message"
                messages.append(msg)
            if messages:
                node_entry["messages"] = messages
        else:
            # Nodes that are neither 'dolev' nor 'byzantine' can be assigned a default type or handled differently
            node_entry["type"] = "neutral"  # Optional: Change as needed

        nodes_config[node] = node_entry

    # Write to YAML file
    try:
        with open(output_file, 'w') as f:
            yaml.dump(nodes_config, f, sort_keys=True)
        print(f"Configuration successfully written to '{output_file}'.")
    except Exception as e:
        print(f"An error occurred while writing to the file: {e}")
        sys.exit(1)

def main():
    # Set up command-line argument parsing

    generate_nodes_config(
        total_nodes=10,
        num_dolev=9,
        num_byzantine=1,
        output_file="../../scenarios/scenario2.yaml"
    )

if __name__ == "__main__":
    main()
