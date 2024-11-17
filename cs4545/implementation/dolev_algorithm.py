import os
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


class DolevAlgorithm(DistributedAlgorithm):

    def __init__(self, settings: CommunitySettings) -> None:
        super().__init__(settings)

        # Load YAML configuration file
        with open(os.environ.get("SCENARIO"), "r") as f:
            self.instructions = yaml.safe_load(f)

            self.delivered = False
            self.paths = {}                                         # paths of nodes for each message id;
            self.f = int (os.environ.get("F"))                      # get the nr of faulty nodes from common env vars
            self.msg_to_broadcast: List[DolevMessage] = []          # if current p_i is starting node, it needs to broadcast these messages
            self.add_message_handler(DolevMessage, self.on_message)

    async def on_start(self):
        instruction = self.instructions[self.node_id]

        if "messages" in instruction:
            messages = instruction["messages"]
            for (i, message) in enumerate(messages):
                print(f"Node {self.node_id} is broadcasting message {i}: {message}")
                self.msg_to_broadcast.append(DolevMessage(i, message, []))
        await super().on_start()

    async def on_start_as_starter(self):
        print(f"Node {self.node_id} is starting the algorithm")

        # Send messages to yourself
        for message in self.msg_to_broadcast:
            self.ez_send(self.get_peers()[0], message)

        # Broadcast messages to neighbors
        for neighbor_id, peer in self.nodes.items():
            for message in self.msg_to_broadcast:
                delay = self.random_delay()  # Get a random delay
                print(f"Node {self.node_id} will wait for {delay:.2f} seconds before sending message {message.id}.")
                await asyncio.sleep(delay)  # Introduce the random delay
                print(f"Sending message {message.id} to node {neighbor_id} from {self.node_id}")
                self.ez_send(peer, message)

        self.delivered = True

    @message_wrapper(DolevMessage)
    async def on_message(self, peer: Peer, payload: DolevMessage) -> None:
        self.running = True
        try:
            sender_id = self.node_id_from_peer(peer)
            print(f"[Node {self.node_id}] Got a message from node: {sender_id}.\t")

            new_path = payload.path + [sender_id]
            if payload.id not in self.paths:
                self.paths[payload.id] = []

            self.paths[payload.id].append(new_path)

            # Check if the node is connected to the source through f+1 disjoint paths
            if self._has_f_plus_1_disjoint_paths(payload.id) and not self.delivered:
                print(f"[Node {self.node_id}] Delivering message {payload.id}.")
                self.delivered = True

            # Broadcast message to all neighbors except the sender
            for neighbor_id, peer in self.nodes.items():
                # Do not send back to nodes who already received this message
                if neighbor_id not in new_path:
                    delay = self.random_delay()  # Get a random delay
                    print(f"[Node {self.node_id}] Will wait for {delay:.2f} seconds before rebroadcasting message {payload.id} to {neighbor_id}.")
                    await asyncio.sleep(delay)  # Introduce the random delay
                    print(f"[Node {self.node_id}] Rebroadcasting message {payload.id} to {neighbor_id}.")
                    rebroadcast_msg = DolevMessage(payload.id, payload.content, new_path)
                    self.ez_send(peer, rebroadcast_msg)

        except Exception as e:
            print(f"Error in on_message: {e}")
            raise e

    def random_delay(self, min_delay: float = 0.1, max_delay: float = 1.0) -> float:
        """
        Return a random delay between `min_delay` and `max_delay` seconds.
        """
        return random.uniform(min_delay, max_delay)

    def _has_f_plus_1_disjoint_paths(self, msg_id: int) -> bool:
        """
        Check if there are at least f+1 disjoint paths in self.paths for the message with msg_id.
        """
        if msg_id not in self.paths or not self.paths[msg_id]:
            print(f"No paths found for msg_id {msg_id}.")
            return False

        unique_paths = set(tuple(path) for path in self.paths[msg_id])
        return len(unique_paths) >= self.f + 1