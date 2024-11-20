import os
import uuid
from datetime import datetime
from collections import defaultdict
# from colorama import Fore

import yaml
import random
import asyncio

from typing import Set, List

from typing_extensions import override

from cs4545.system.da_types import *

@dataclass
class Path:
    start: int
    nodes: List[int]

    def add(self, new_node_id: int):
        self.nodes.append(new_node_id)
        return self.nodes

    def node_disjoint(self, other: "Path") -> bool:
        if self.start != other.start:
            return False
        for node in self.nodes:
            if node in other.nodes and node != self.start:
                return False
        return True

    @staticmethod
    def all_disjoint(paths: List["Path"]):
        for i in range(len(paths)):
            for j in range(i + 1, len(paths)):
                if not paths[i].node_disjoint(paths[j]):
                    return False
        return True

    @staticmethod
    def maximum_disjoint_set(paths: List["Path"]):
        subsets = [[]]
        for index in range(0, len(paths)):
            subsets += [subset + [index] for subset in subsets]
        size = 0
        for subset in subsets[1:]:
            if Path.all_disjoint([paths[s] for s in subset]):
                size = max(size, len(subset))
        return size

@dataclass(msg_id=4)
class DolevMessage:
    id: str
    content: str
    path: Path

    def __hash__(self) -> int:
        return (self.id, self.content).__hash__()

    def __eq__(self, other) -> bool:
        if not isinstance(other, DolevMessage):
            return False
        return self.id == other.id and self.content == other.content

def generate_unique_id():
    return uuid.uuid4().hex


def random_delay(min_delay: float = 0.1, max_delay: float = 1.0) -> float:
    """
    Return a random delay between `min_delay` and `max_delay` seconds.
    """
    return random.uniform(min_delay, max_delay)


class DolevAlgorithm(DistributedAlgorithm):

    def __init__(self, settings: CommunitySettings) -> None:
        super().__init__(settings)

        # Load YAML configuration file
        with open(os.environ.get("SCENARIO"), "r") as f:
            self.instructions = yaml.safe_load(f)
            self.correct_nodes = [int(node_id) for node_id, node_data in self.instructions.items() if node_data['type'] == "dolev"]
            self.delivered = {}                                               # dict for every message if it was delivered;
            self.paths = {}                                                   # paths of nodes for each message; (message - List[Path])
            self.f = int (os.environ.get("F"))                                # get the nr of faulty nodes from common env vars
            self.msg_to_broadcast: List[DolevMessage] = []                    # if current p_i is starting node, it needs to broadcast these messages
            self.add_message_handler(DolevMessage, self.on_message)
            self.last_message_time = None
            self.neighbors_delivered: Dict[DolevMessage, Set[int]] = defaultdict(set)  # dict for a node telling it what neighbors have delivered a msg
            self.sent_messages: Set[DolevMessage] = set()

    async def on_start(self):
        instruction = self.instructions[self.node_id]

        if "messages" in instruction:
            messages = instruction["messages"]
            for (i, message) in enumerate(messages):
                # Get unique id for a message
                unique_id = generate_unique_id()
                print(f"Node {self.node_id} is broadcasting message {unique_id}: {message}")
                self.msg_to_broadcast.append(DolevMessage(unique_id, message, Path(self.node_id,[])))

        # If node has messages to deliver, then it is a starting node
        for message in self.msg_to_broadcast:
            self.delivered[message] = False
            self.sent_messages.add(message)
            await self.on_broadcast(message)

        # Start monitoring for inactivity
        await asyncio.create_task(self.monitor_inactivity())

    async def on_broadcast(self, message: DolevMessage):
        print(f"Node {self.node_id} is starting the algorithm")

        # Broadcast message to neighbors
        for neighbor_id, peer in self.nodes.items():
            delay = random_delay()
            #print(f"Node {self.node_id} will wait for {delay:.2f} seconds before sending message {message.id}.")
            await asyncio.sleep(delay)
            # print(f"Sending message {message.id} to node {neighbor_id} from {self.node_id}")
            self.ez_send(peer, message)

        self.delivered[message] = True

    @message_wrapper(DolevMessage)
    async def on_message(self, peer: Peer, payload: DolevMessage) -> None:
        try:
            # if self.node_id == 2:
            self._message_history.receive_message()
            self.last_message_time = datetime.now()

            sender_id = self.node_id_from_peer(peer)
            # print(f"[Node {self.node_id}] Got a message from node: {sender_id}.\t")

            # If neighbor n sent you empty path for given msg m, whenever you get msg m with n in path don't do anything
            # Optimization MD.4
            for n_delivered in self.neighbors_delivered[payload]:
                if n_delivered in payload.path.nodes:
                    # print("Let's see how many times this happens")
                    return

            # if sender_id in self.neighbors_delivered[payload] and sender_id in payload.path.nodes:
            #     return

            # # Neighbor sent you empty path => They delivered message w/ payload.id
            # # Optimization MD.3
            # if not payload.path.nodes:
            #     self.neighbors_delivered[payload].add(sender_id)

            # If we delivered msg w/ payload.id previously, don't do anything anymore
            # Optimization MD.5
            if self.delivered.get(payload) is not None:
                return

            payload.path.add(sender_id)
            # print(payload.path.nodes)

            if payload not in self.paths:
                self.paths[payload] = []

            self.paths[payload].append(payload.path)


            # # Optimization MD.1
            # color = '\033[32m'
            # if "Tampered" in payload.content or "Malicious" in payload.content:
            #     color = '\033[31m'
            # if payload.path.start in self.nodes and payload.path.start == sender_id:
            #     if payload.content == "lol":
            #         print(color + f"Node {self.node_id} Delivered message {payload.id}, {payload.content}, {payload.path.nodes}.")
            #     else:
            #         print(color + f"Node {self.node_id} Delivered message {payload.id}, {payload.content}.")
            #     self.delivered[payload] = True
            #
            # # Check for f+1 disjoint paths
            # if Path.maximum_disjoint_set(self.paths[payload]) >= self.f + 1 and payload not in self.delivered:
            #     if payload.content == "lol":
            #         print( color +
            #             f"Node {self.node_id} Delivered message {payload.id}, {payload.content}, {payload.path.nodes}.")
            #     else:
            #         print(color + f"Node {self.node_id} Delivered message {payload.id}, {payload.content}.")
            #     self.delivered[payload] = True

            # Optimization MD.2
            if self.delivered.get(payload) is not None:
                for neighbor_id, peer in self.nodes.items():
                    self.ez_send(peer, DolevMessage(payload.id, payload.content, Path(payload.path.start, [])))
                return

            # Broadcast message to all neighbors except the sender and those that have already delivered
            for neighbor_id, peer in self.nodes.items():
                # print(f"Node: {self.node_id}, Neighbor: {neighbor_id}, Paths: {self.paths[payload]}")
                # print(f"NEIGHBORS DELIVERED: {self.neighbors_delivered}")

                # Do not send back to nodes who already received this message or neighbors that delivered
                if neighbor_id not in payload.path.nodes and neighbor_id not in self.neighbors_delivered[payload]:
                    delay = random_delay()
                    # print(f"[Node {self.node_id}] Will wait for {delay:.2f} seconds before rebroadcasting message {payload.id} to {neighbor_id}.")
                    await asyncio.sleep(delay)
                    # print(f"[Node {self.node_id}] Rebroadcasting message {payload.id} to {neighbor_id}.")
                    rebroadcast_msg = DolevMessage(payload.id, payload.content, payload.path)
                    self.ez_send(peer, rebroadcast_msg)
                    # print(f"Current {self.node_id} Neighbor {neighbor_id}, Path {payload.path.nodes}")

            # Neighbor sent you empty path => They delivered message w/ payload.id
            # Optimization MD.3
            if not payload.path.nodes:
                self.neighbors_delivered[payload].add(sender_id)
            # Optimization MD.1
            color = '\033[32m'
            if "Tampered" in payload.content or "Malicious" in payload.content:
                color = '\033[31m'
            if self.delivered.get(payload) is None and payload.path.start in self.nodes and payload.path.start == sender_id:
                if payload.content == "lol":
                    print(
                        color + f"Node {self.node_id} Delivered message {payload.id}, {payload.content}, {payload.path.nodes}.")
                else:
                    print(color + f"Node {self.node_id} Delivered message {payload.id}, {payload.content}.")
                self.delivered[payload] = True

            # Check for f+1 disjoint paths
            if Path.maximum_disjoint_set(self.paths[payload]) >= self.f + 1 and payload not in self.delivered:
                if payload.content == "lol":
                    print(color +
                          f"Node {self.node_id} Delivered message {payload.id}, {payload.content}, {payload.path.nodes}.")
                else:
                    print(color + f"Node {self.node_id} Delivered message {payload.id}, {payload.content}.")
                self.delivered[payload] = True
        except Exception as e:
            print(f"Error in on_message: {e}")
            raise e

    async def monitor_inactivity(self):
        inactivity_threshold = 10  # In seconds

        while True:
            await asyncio.sleep(1)  # Check every second
            if self.last_message_time:
                elapsed_time = (datetime.now() - self.last_message_time).total_seconds()
                if elapsed_time > inactivity_threshold:
                    print(
                        f"[Node {self.node_id}] Stopping due to inactivity. Last message received {elapsed_time:.2f} seconds ago.")
                    self.stop()  # Stop the algorithm, save node stats to output folder
                    break


class ByzantineDolevAlgorithm(DolevAlgorithm):

    def __init__(self, settings: CommunitySettings) -> None:
        super().__init__(settings)

    async def on_start(self):
        await super().on_start()

    @override
    async def on_broadcast(self, message: DolevMessage):
        print(f"Node {self.node_id} is maliciously starting the algorithm")

        # Broadcast message to neighbors
        number_neighbors = random.randint(1, len(self.nodes))
        selected_neighbors = random.sample(list(self.nodes.items()), k=number_neighbors)

        print(f"Node {self.node_id} has chosen to send to {number_neighbors} neighbors.")

        for neighbor_id, peer in selected_neighbors:
            delay = random_delay()
            # print(f"Node {self.node_id} will wait for {delay:.2f} seconds before sending message {message.id}.")
            await asyncio.sleep(delay)  # Introduce the random delay
            # print(f"Sending message {message.id} to node {neighbor_id} from {self.node_id}")
            self.ez_send(peer, message)

        self.delivered[message.id] = True

    # @override
    # @message_wrapper(DolevMessage)
    # async def on_message(self, peer: Peer, payload: DolevMessage):
    #     # claiming that malicious message was broadcast by a correct node
    #
    #     # start_node = random.sample(self.correct_nodes, 1)[0]
    #     print(f"Sender {self.node_id_from_peer(peer)} has sent 2 a path {payload.path.nodes}")
    #     new_payload = DolevMessage(payload.id, "lol", Path(payload.path.start, payload.path.nodes))
    #
    #     number_neighbors = random.randint(0, len(self.nodes))
    #     selected_neighbors = random.sample(list(self.nodes.items()), k=number_neighbors)
    #     # print("SELECTED NEIGHBORS", selected_neighbors)
    #     for neighbor_id, peer in selected_neighbors:
    #         self.ez_send(peer, new_payload)

    # async def monitor_inactivity(self):
    #     inactivity_threshold = 10  # In seconds
    #
    #     while True:
    #         await asyncio.sleep(1)  # Check every second
    #         if self.last_message_time:
    #             elapsed_time = (datetime.now() - self.last_message_time).total_seconds()
    #             if elapsed_time > inactivity_threshold:
    #                 print(
    #                     f"[Node {self.node_id}] Stopping due to inactivity. Last message received {elapsed_time:.2f} seconds ago.")
    #                 self.stop()  # Stop the algorithm, save node stats to output folder
    #                 break

    # async def on_broadcast(self, message: DolevMessage):
    #     await super().on_broadcast(message)

    # @message_wrapper(DolevMessage)
    # async def on_message(self, peer: Peer, payload: DolevMessage):
    #     await super().on_message(peer, payload)

    # random case
    @override
    @message_wrapper(DolevMessage)
    async def on_message(self, peer: Peer, payload: DolevMessage):
        print("Helloooo")
        number_neighbors = random.randint(0, len(self.nodes))
        selected_neighbors = random.sample(list(self.nodes.items()), k=number_neighbors)
        for neighbor_id, neighbor_peer in selected_neighbors:
            probability_to_fakely_deliver = random.uniform(0, 1)
            probability_to_alter_path = random.uniform(0, 1)
            probability_to_alter_content = random.uniform(0, 1)
            probability_to_alter_id = random.uniform(0, 1)
            probability_to_alter_start = random.uniform(0, 1)

            new_nodes = payload.path.nodes.copy()
            new_payload_content = payload.content
            new_id = payload.id
            new_start = payload.path.start
            print("hello?")
            if probability_to_fakely_deliver >= 0.2:
                print("empty path from byzantine")
                new_nodes = []
            elif probability_to_alter_path >= 0.5:
                alteration_choice = random.choice(['add_nodes', 'remove_nodes', 'shuffle_nodes', 'duplicate_nodes'])
                # if alteration_choice == 'add_nodes':
                #     num_nodes_to_add = random.randint(1, 3)
                #     for _ in range(num_nodes_to_add):
                #         fake_node_id = random.randint(0, max(self.nodes.keys()) + 50)
                #         new_nodes.append(fake_node_id)
                if alteration_choice == 'remove_nodes':
                    if len(new_nodes) == 0:
                        num_nodes_to_remove = 0
                    else:
                        num_nodes_to_remove = random.randint(1, len(new_nodes))
                    for _ in range(num_nodes_to_remove):
                        if new_nodes:
                            removed_node = random.choice(new_nodes)
                            new_nodes.remove(removed_node)
                elif alteration_choice == 'shuffle_nodes':
                    random.shuffle(new_nodes)
                # elif alteration_choice == 'duplicate_nodes':
                #     num_duplicates = random.randint(1, 2)
                #     for _ in range(num_duplicates):
                #         if new_nodes:
                #             node_to_duplicate = random.choice(new_nodes)
                #             insertion_index = random.randint(0, len(new_nodes))
                #             new_nodes.insert(insertion_index, node_to_duplicate)

            new_nodes.append(self.node_id)

            if probability_to_alter_content >= 0.01:
                random_content_number = random.randint(0, 100000)
                new_payload_content = f"Tampered content {str(random_content_number)}"

            if probability_to_alter_id >= 0.01:
                new_id = uuid.uuid4().hex

            if probability_to_alter_start >= 0.01:
                new_start = random.sample(self.correct_nodes, 1)[0]

            new_path = Path(new_start, new_nodes)

            new_payload = DolevMessage(new_id, new_payload_content, new_path)

            # print(f"Original Payload: {payload}")
            # print(f"Altered Payload: {new_payload}")
            # print(id(new_payload))

            self.ez_send(neighbor_peer, new_payload)
