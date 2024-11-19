import os
import uuid
from datetime import datetime
from collections import defaultdict

import yaml
import random
import asyncio

from typing import Set, List
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

            self.delivered = {}                                               # dict for every message if it was delivered;
            self.paths = {}                                                   # paths of nodes for each message; (message - List[Path])
            self.f = int (os.environ.get("F"))                                # get the nr of faulty nodes from common env vars
            self.msg_to_broadcast: List[DolevMessage] = []                    # if current p_i is starting node, it needs to broadcast these messages
            self.add_message_handler(DolevMessage, self.on_message)
            self.last_message_time = None
            self.neighbors_delivered: Dict[DolevMessage, Set[int]] = defaultdict(set)  # dict for a node telling it what neighbors have delivered a msg

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
            self.last_message_time = datetime.now()

            sender_id = self.node_id_from_peer(peer)
            # print(f"[Node {self.node_id}] Got a message from node: {sender_id}.\t")

            # Optimization MD.3
            if not payload.path.nodes:
                self.neighbors_delivered[payload].add(sender_id)

            # Optimization MD.5
            if self.delivered.get(payload) is not None:
                return

            payload.path.add(sender_id)

            if payload not in self.paths:
                self.paths[payload] = []

            self.paths[payload].append(payload.path)

            # Optimization MD.4
            if self.delivered.get(payload):
                print("Run the optimization 2")
                return

            # Optimization MD.1
            if payload.path.start in self.nodes and payload.path.start == sender_id:
                print(f"[Node {self.node_id}] Delivered message {payload.id}.")
                self.delivered[payload] = True

            # Check for f+1 disjoint paths
            if Path.maximum_disjoint_set(self.paths[payload]) >= self.f + 1 and payload not in self.delivered:
                print(f"[Node {self.node_id}] Delivered message {payload.id}.")
                self.delivered[payload] = True

            # Optimization MD.2
            if self.delivered.get(payload) is not None:
                for neighbor_id, peer in self.nodes.items():
                    self.ez_send(peer, DolevMessage(payload.id, payload.content, Path(payload.path.start, [])))
                return

            # Broadcast message to all neighbors except the sender

            for neighbor_id, peer in self.nodes.items():
                # print(f"Node: {self.node_id}, Neighbor: {neighbor_id}, Paths: {self.paths[payload]}")
                # print(f"NEIGHBORS DELIVERED: {self.neighbors_delivered}")

                # Do not send back to nodes who already received this message
                if neighbor_id not in payload.path.nodes and neighbor_id not in self.neighbors_delivered[payload]:
                    delay = random_delay()
                    # print(f"[Node {self.node_id}] Will wait for {delay:.2f} seconds before rebroadcasting message {payload.id} to {neighbor_id}.")
                    await asyncio.sleep(delay)
                    # print(f"[Node {self.node_id}] Rebroadcasting message {payload.id} to {neighbor_id}.")
                    rebroadcast_msg = DolevMessage(payload.id, payload.content, payload.path)
                    self.ez_send(peer, rebroadcast_msg)
                    # print(f"Current {self.node_id} Neighbor {neighbor_id}, Path {payload.path.nodes}")

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

    async def on_broadcast(self, message: DolevMessage):
        await super().on_broadcast(message)