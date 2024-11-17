import os
import uuid
import yaml
import random
import asyncio

from typing import Set
from cs4545.system.da_types import *

@dataclass(msg_id=4)
class DolevMessage:
    id: int
    content: str
    path: List[int]

@dataclass
class Path:
    start: int
    nodes: List[int]


def generate_unique_id():
    # Generate UUID and mask it to the 64-bit range
    return uuid.uuid4().int & ((1 << 32) - 1)  # Limit the size to 32 bits so that we don't have problems with ipv8


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

            self.delivered = {}                                     # dict for every message id if it was delivered
            self.paths = {}                                         # paths of nodes for each message id;
            self.f = int (os.environ.get("F"))                      # get the nr of faulty nodes from common env vars
            self.msg_to_broadcast: List[DolevMessage] = []          # if current p_i is starting node, it needs to broadcast these messages
            self.add_message_handler(DolevMessage, self.on_message)

    async def on_start(self):
        instruction = self.instructions[self.node_id]

        if "messages" in instruction:
            messages = instruction["messages"]
            for (i, message) in enumerate(messages):
                # Get unique id for a message
                unique_id = generate_unique_id()
                print(f"Node {self.node_id} is broadcasting message {unique_id}: {message}")
                self.msg_to_broadcast.append(DolevMessage(unique_id, message, []))

        # If node has messages to deliver, then it is a starting node
        for message in self.msg_to_broadcast:
            self.delivered[message.id] = False
            await self.on_broadcast(message)

    async def on_broadcast(self, message: DolevMessage):
        print(f"Node {self.node_id} is starting the algorithm")

        # Send message to yourself
        self.ez_send(self.get_peers()[0], message)

        # Broadcast message to neighbors
        for neighbor_id, peer in self.nodes.items():
            delay = random_delay()  # Get a random delay
            print(f"Node {self.node_id} will wait for {delay:.2f} seconds before sending message {message.id}.")
            await asyncio.sleep(delay)  # Introduce the random delay
            print(f"Sending message {message.id} to node {neighbor_id} from {self.node_id}")
            self.ez_send(peer, message)

        self.delivered[message.id] = True

    @message_wrapper(DolevMessage)
    async def on_message(self, peer: Peer, payload: DolevMessage) -> None:
        try:
            sender_id = self.node_id_from_peer(peer)
            print(f"[Node {self.node_id}] Got a message from node: {sender_id}.\t")

            new_path = payload.path + [sender_id]
            if payload.id not in self.paths:
                self.paths[payload.id] = []

            self.paths[payload.id].append(new_path)

            # Check for f+1 disjoint paths
            if self.disjoint_paths(payload.id) and payload.id not in self.delivered:
                print(f"[Node {self.node_id}] Delivering message {payload.id}.")
                self.delivered[payload.id] = True

            # Broadcast message to all neighbors except the sender
            for neighbor_id, peer in self.nodes.items():
                # Do not send back to nodes who already received this message
                if neighbor_id not in new_path:
                    delay = random_delay()  # Get a random delay
                    print(f"[Node {self.node_id}] Will wait for {delay:.2f} seconds before rebroadcasting message {payload.id} to {neighbor_id}.")
                    await asyncio.sleep(delay)  # Introduce the random delay
                    print(f"[Node {self.node_id}] Rebroadcasting message {payload.id} to {neighbor_id}.")
                    rebroadcast_msg = DolevMessage(payload.id, payload.content, new_path)
                    self.ez_send(peer, rebroadcast_msg)

        except Exception as e:
            print(f"Error in on_message: {e}")
            raise e



    def disjoint_paths(self, msg_id: int) -> bool:
        # path = self.paths[msg_id]
        # for i in range (len(path)):
        #     for j in range(len(path)):
        return False




class ByzantineDolevAlgorithm(DolevAlgorithm):

    def __init__(self, settings: CommunitySettings) -> None:
        super().__init__(settings)

    async def on_start(self):
        await super().on_start()

    async def on_broadcast(self, message: DolevMessage):
        await super().on_broadcast(message)