import math
import os
import uuid
from datetime import datetime
from collections import defaultdict
# from colorama import Fore

import yaml
import random
import asyncio
import time

from typing import Set, List

from typing_extensions import override

from cs4545.system.da_types import *

@dataclass
class Path:
    start: int
    nodes: List[int]

    def add(self, new_node_id: int):
        new_nodes = self.nodes + [new_node_id]
        return Path(self.start, new_nodes)

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
class Message:
    id: str
    content: str
    path: Path
    time: float
    type: str

    def __hash__(self) -> int:
        return (self.id, self.content, self.type).__hash__()

    def __eq__(self, other) -> bool:
        return self.id == other.id and self.content == other.content and self.type == other.type

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
            self.delivered: Dict[Message, bool] = defaultdict(bool)      # dict for every message if it was delivered;
            self.paths = {}                                                   # paths of nodes for each message; (message - List[Path])
            self.f = int (os.environ.get("F"))                                # get the nr of faulty nodes from common env vars
            self.msg_to_broadcast: List[Message] = []                    # if current p_i is starting node, it needs to broadcast these messages
            self.add_message_handler(Message, self.on_message)
            self.last_message_time = None
            self.neighbors_delivered: Dict[Message, Set[int]] = defaultdict(set)  # dict for a node telling it what neighbors have delivered a msg
            self.sent_messages: Set[Message] = set()
            self.n = int (os.environ.get("N"))
            self.correct_nodes = [int(node_id) for node_id, node_data in self.instructions.items() if node_data['type'] == "bracha"]

            self.echo_message_sent: Dict[Message, bool] = defaultdict(bool)  # Did I send the Echo variant of the Original message?
            self.ready_message_sent: Dict[Message, bool] = defaultdict(bool)  # Did I send the Ready variant of the Original message?
            # Both dictionaries will have as key the ORIGINAL message (with type=send)
            self.ready_delivered: Dict[Message, bool] = defaultdict(bool)
            self.echo_messages_received: Dict[Message, List[Message]] = defaultdict(list)
            self.ready_messages_received: Dict[Message, List[Message]] = defaultdict(list)

    async def on_start(self):
        instruction = self.instructions[self.node_id]

        if "messages" in instruction:
            messages = instruction["messages"]
            for (i, message) in enumerate(messages):
                # Get unique id for a message
                unique_id = generate_unique_id()
                print(f"Node {self.node_id} is broadcasting message {unique_id}: {message}")
                self.msg_to_broadcast.append(Message(unique_id, message, Path(self.node_id,[]), time.time(), "send"))

        # If node has messages to deliver, then it is a starting node
        for message in self.msg_to_broadcast:
            self.sent_messages.add(message)
            self.on_broadcast(message)

        # Start monitoring for inactivity
        await asyncio.create_task(self.monitor_inactivity())

    def on_broadcast(self, message: Message):
        # print(f"Node {self.node_id} is starting the algorithm")

        # Broadcast message to neighbors
        for neighbor_id, peer in self.nodes.items():
            delay = random_delay()
            time.sleep(delay)
            # print("Broadcasting")
            # print(self.delivered)
            self.ez_send(peer, message)

        self.delivered[message] = True

    @message_wrapper(Message)
    async def on_message(self, peer: Peer, payload: Message) -> None:
        try:
            self._message_history.receive_message()
            self.last_message_time = datetime.now()

            sender_id = self.node_id_from_peer(peer)

            # If we delivered msg w/ payload.id previously, don't do anything anymore
            # Optimization MD.5
            if payload in self.delivered:
                return

            newpath = payload.path.add(sender_id)
            if payload not in self.paths:
                self.paths[payload] = []
            self.paths[payload].append(newpath)

            # If neighbor n sent you empty path for given msg m, whenever you get msg m with n in path don't do anything
            # Optimization MD.4
            for n_delivered in self.neighbors_delivered[payload]:
                if n_delivered in newpath.nodes:
                    return

            # # Neighbor sent you empty path => They delivered message w/ payload.id
            # # Optimization MD.3
            if len(newpath.nodes) == 1 and newpath.nodes[0] == sender_id:
                self.neighbors_delivered[payload].add(sender_id)
                if newpath.start == sender_id: # MD1
                    self.delivered[payload] = True

            # Check for f+1 disjoint paths
            if Path.maximum_disjoint_set(self.paths[payload]) >= self.f + 1 and payload not in self.delivered:
                self.delivered[payload] = True
                # print(f"[Delivered] {payload.content} at {time.time() - payload.time}")

            # Broadcast message to all neighbors except the sender and those that have already delivered
            for neighbor_id, peer in self.nodes.items():
                # Do not send back to nodes who already received this message or neighbors that delivered
                if neighbor_id not in newpath.nodes and neighbor_id not in self.neighbors_delivered[payload] and neighbor_id != newpath.start:
                    delay = random_delay()
                    time.sleep(delay)
                    relay_msg = Message(payload.id, payload.content, newpath, payload.time, payload.type)
                    self.ez_send(peer, relay_msg)

            # Optimization MD.2
            if payload in self.delivered:
                self.message_delivered_time[(payload.id, payload.content).__hash__()] = time.time() - payload.time
                #     print(f"[Delivered] {payload.content} at {time.time() - payload.time}")
                for neighbor_id, peer in self.nodes.items():
                    if neighbor_id not in self.neighbors_delivered[payload]:
                        self.ez_send(peer, Message(payload.id, payload.content, Path(payload.path.start, []),
                                                        payload.time, payload.type))
                if payload.type == "send":
                    self.on_message_bracha(peer, payload)
                elif payload.type == "echo":
                    original_content = payload.content.split("from")
                    original_content = original_content[0].strip()
                    original_message = Message(payload.id, original_content, payload.path, payload.time, "send")
                    if payload not in self.echo_messages_received[original_message]:
                        self.echo_messages_received[original_message].append(payload)

                    # print(f"[Delivered] {payload.content} at {time.time() - payload.time}, Type: {payload.type}")
                    # print(f"Currently, {self.echo_messages_received}.")
                    original_message_echo = Message(original_message.id, original_message.content, original_message.path, original_message.time, "echo")

                    self.on_message_bracha(peer, original_message_echo)  # Original Message but with modified type!!!!
                elif payload.type == "ready":
                    original_content = payload.content.split("from")
                    original_content = original_content[0].strip()
                    original_message = Message(payload.id, original_content, payload.path, payload.time, "send")
                    if payload not in self.ready_messages_received[original_message]:
                        self.ready_messages_received[original_message].append(payload)
                    # original_message.type = "ready"
                    original_message_ready = Message(original_message.id, original_message.content, original_message.path, original_message.time, "ready")
                    self.on_message_bracha(peer, original_message_ready)
                return

        except Exception as e:
            print(f"Error in on_message: {e}")
            raise e

    def on_message_bracha(self, peer: Peer, payload: Message) -> None:
        if payload.type == "send" and not self.echo_message_sent[payload]:
            # print("I got a send message")
            echo_payload = Message(payload.id, payload.content + f" from {self.node_id}", Path(self.node_id, []), payload.time, "echo")
            self.echo_message_sent[payload] = True
            self.on_broadcast(echo_payload)
        elif payload.type == "echo" and not self.ready_message_sent[Message(payload.id, payload.content, Path(self.node_id, []), payload.time, "send")]:
            ready_payload = Message(payload.id, payload.content + f" from {self.node_id}", Path(self.node_id, []), payload.time, "ready")
            original_message = Message(payload.id, payload.content, Path(self.node_id, []), payload.time, "send")
            number_received_echo = len(self.echo_messages_received[original_message]) + 1

            # print(f"{payload.content}: Echo messages received: {number_received_echo}")
            if (number_received_echo >= int(math.ceil(float(self.n + self.f + 1)/2.0))) and not self.ready_message_sent[original_message]:
                self.ready_message_sent[original_message] = True
                # print(f"[Delivered] Echo {payload.content} at {time.time() - payload.time}")
                self.on_broadcast(ready_payload)
        elif payload.type == "ready" and not self.ready_delivered[Message(payload.id, payload.content, Path(self.node_id, []), payload.time, "send")]:
            ready_payload = Message(payload.id, payload.content + f" from {self.node_id}", Path(self.node_id, []), payload.time, "ready")
            original_message = Message(payload.id, payload.content, Path(self.node_id, []), payload.time, "send")
            number_received_ready = len(self.ready_messages_received[original_message]) + 1
            # print(f)
            if number_received_ready >= self.f + 1 and not self.ready_message_sent[original_message]:
                self.ready_message_sent[original_message] = True
                self.on_broadcast(ready_payload)
            if number_received_ready >= 2 * self.f + 1:
                print(f"[Delivered] Ready {payload.content} at {time.time() - payload.time}")
                self.ready_delivered[original_message] = True

    async def monitor_inactivity(self):
        inactivity_threshold = 100  # In seconds

        while True:
            await asyncio.sleep(1)  # Check every second
            if self.last_message_time:
                elapsed_time = (datetime.now() - self.last_message_time).total_seconds()
                if elapsed_time > inactivity_threshold:
                    print(
                        f"[Node {self.node_id}] Stopping due to inactivity. Last message received {elapsed_time:.2f} seconds ago"
                    )
                    self.stop()  # Stop the algorithm, save node stats to output folder
                    break


class ByzantineDolevAlgorithm(DolevAlgorithm):

    def __init__(self, settings: CommunitySettings) -> None:
        super().__init__(settings)

    async def on_start(self):
        await super().on_start()

    @override
    def on_broadcast(self, message: Message):
        print(f"Node {self.node_id} is maliciously starting the algorithm")

        # Broadcast message to neighbors
        number_neighbors = random.randint(1, len(self.nodes))
        selected_neighbors = random.sample(list(self.nodes.items()), k=number_neighbors)

        new_start = random.choice(self.correct_nodes)
        message.path.start = new_start
        for neighbor_id, peer in selected_neighbors:
            delay = random_delay()
            time.sleep(delay)
            self.ez_send(peer, message)

        self.delivered[message] = True


    async def monitor_inactivity(self):
        await super().monitor_inactivity()

    @override
    @message_wrapper(Message)
    async def on_message(self, peer: Peer, payload: Message):
        self.last_message_time = datetime.now()
        self._message_history.receive_message()

        new_nodes = payload.path.nodes.copy()
        new_payload_content = payload.content
        new_start = payload.path.start
        new_type = payload.type

        actions = ["empty path", "alter start", "shuffle path", "remove nodes"]
        action = random.choice(actions)
        # new_type = random.choice(["send", "echo", "ready"])
        # new_nodes = []
        # if action == "skip":
        #     return
        if action == "empty path":
            new_nodes = []
        # if action == "alter content":
        #     random_content_number = random.randint(0, 1000)
        #     new_payload_content = f"Tampered content {str(random_content_number)}"
        if action == "alter start":
            new_start = random.randint(0, len(self.nodes.items()))
        if action == "shuffle path":
            random.shuffle(new_nodes)
        if action == "remove nodes":
            if len(new_nodes) == 0:
                num_nodes_to_remove = 0
            else:
                num_nodes_to_remove = random.randint(1, len(new_nodes))
            for _ in range(num_nodes_to_remove):
                if new_nodes:
                    removed_node = random.choice(new_nodes)
                    new_nodes.remove(removed_node)

        new_path = Path(new_start, new_nodes)
        new_payload = Message(payload.id, new_payload_content, new_path, payload.time, new_type)

        # print(f"Original Payload: {payload}")
        # print(f"Altered Payload: {new_payload}")

        number_neighbors = random.randint(1, len(self.nodes)-1)
        selected_neighbors = random.sample(list(self.nodes.items()), k=number_neighbors)

        for neighbor_id, peer in selected_neighbors:
            delay = random_delay()
            time.sleep(delay)
            self.ez_send(peer, new_payload)


# import math
# import os
# import uuid
# from datetime import datetime
# from collections import defaultdict
# # from colorama import Fore
#
# import yaml
# import random
# import asyncio
# import time
#
# from typing import Set, List, Dict, Tuple
#
# from typing_extensions import override
#
# from cs4545.system.da_types import *
#
# @dataclass
# class Path:
#     start: int
#     nodes: List[int]
#
#     def add(self, new_node_id: int):
#         new_nodes = self.nodes + [new_node_id]
#         return Path(self.start, new_nodes)
#
#     def node_disjoint(self, other: "Path") -> bool:
#         if self.start != other.start:
#             return False
#         for node in self.nodes:
#             if node in other.nodes and node != self.start:
#                 return False
#         return True
#
#     @staticmethod
#     def all_disjoint(paths: List["Path"]):
#         for i in range(len(paths)):
#             for j in range(i + 1, len(paths)):
#                 if not paths[i].node_disjoint(paths[j]):
#                     return False
#         return True
#
#     @staticmethod
#     def maximum_disjoint_set(paths: List["Path"]):
#         subsets = [[]]
#         for index in range(0, len(paths)):
#             subsets += [subset + [index] for subset in subsets]
#         size = 0
#         for subset in subsets[1:]:
#             if Path.all_disjoint([paths[s] for s in subset]):
#                 size = max(size, len(subset))
#         return size
#
# @dataclass(msg_id=4)
# class Message:
#     id: str
#     content: str
#     path: Path
#     time: float
#     type: str
#
# def generate_unique_id():
#     return uuid.uuid4().hex
#
# def random_delay(min_delay: float = 0.1, max_delay: float = 1.0) -> float:
#     """
#     Return a random delay between `min_delay` and `max_delay` seconds.
#     """
#     return random.uniform(min_delay, max_delay)
#
# def get_message_key(message: Message) -> Tuple[str, str, str]:
#     return (message.id, message.content, message.type)
#
# class DolevAlgorithm(DistributedAlgorithm):
#
#     def __init__(self, settings: CommunitySettings) -> None:
#         super().__init__(settings)
#
#         # Load YAML configuration file
#         with open(os.environ.get("SCENARIO"), "r") as f:
#             self.instructions = yaml.safe_load(f)
#             self.delivered: Dict[Tuple[str, str, str], bool] = defaultdict(bool)  # dict for every message if it was delivered;
#             self.paths: Dict[Tuple[str, str, str], List[Path]] = defaultdict(list)  # paths of nodes for each message;
#             self.f = int(os.environ.get("F"))  # get the nr of faulty nodes from common env vars
#             self.msg_to_broadcast: List[Message] = []  # if current p_i is starting node, it needs to broadcast these messages
#             self.add_message_handler(Message, self.on_message)
#             self.last_message_time = None
#             self.neighbors_delivered: Dict[Tuple[str, str, str], Set[int]] = defaultdict(set)  # dict for a node telling it what neighbors have delivered a msg
#             self.sent_messages: Set[Tuple[str, str, str]] = set()
#             self.n = int(os.environ.get("N"))
#             # self.correct_nodes = [int(node_id) for node_id, node_data in self.instructions.items() if node_data['type'] == "dolev"]
#
#             self.msg_counter: Dict[Tuple[str, str, str], int] = defaultdict(int)
#             self.msg_sent: Dict[Tuple[str, str, str], bool] = defaultdict(bool)
#             self.ready_delivered: Dict[Tuple[str, str, str], bool] = defaultdict(bool)
#             self.message_delivered_time: Dict[int, float] = {}
#
#     async def on_start(self):
#         instruction = self.instructions[self.node_id]
#
#         if "messages" in instruction:
#             messages = instruction["messages"]
#             for (i, message) in enumerate(messages):
#                 # Get unique id for a message
#                 unique_id = generate_unique_id()
#                 print(f"Node {self.node_id} is broadcasting message {unique_id}: {message}")
#                 self.msg_to_broadcast.append(Message(unique_id, message, Path(self.node_id, []), time.time(), "send"))
#
#         # If node has messages to deliver, then it is a starting node
#         for message in self.msg_to_broadcast:
#             self.sent_messages.add(get_message_key(message))
#             self.on_broadcast(message)
#
#         # Start monitoring for inactivity
#         await asyncio.create_task(self.monitor_inactivity())
#
#     def on_broadcast(self, message: Message):
#         # Broadcast message to neighbors
#         for neighbor_id, peer in self.nodes.items():
#             delay = random_delay()
#             time.sleep(delay)
#             self.ez_send(peer, message)
#
#         self.delivered[get_message_key(message)] = True
#
#     @message_wrapper(Message)
#     async def on_message(self, peer: Peer, payload: Message) -> None:
#         try:
#             payload_key = get_message_key(payload)
#             self._message_history.receive_message()
#             self.last_message_time = datetime.now()
#
#             sender_id = self.node_id_from_peer(peer)
#
#             # If we delivered msg w/ payload.id previously, don't do anything anymore
#             # Optimization MD.5
#             if payload_key in self.delivered:
#                 return
#
#             newpath = payload.path.add(sender_id)
#             if payload_key not in self.paths:
#                 self.paths[payload_key] = []
#             self.paths[payload_key].append(newpath)
#
#             # Optimization MD.4
#             for n_delivered in self.neighbors_delivered[payload_key]:
#                 if n_delivered in newpath.nodes:
#                     return
#
#             # Optimization MD.3
#             if len(newpath.nodes) == 1 and newpath.nodes[0] == sender_id:
#                 self.neighbors_delivered[payload_key].add(sender_id)
#                 if newpath.start == sender_id:  # MD1
#                     self.delivered[payload_key] = True
#
#             # Check for f+1 disjoint paths
#             if Path.maximum_disjoint_set(self.paths[payload_key]) >= self.f + 1 and payload_key not in self.delivered:
#                 self.delivered[payload_key] = True
#                 # print(f"[Delivered] {payload.content} at {time.time() - payload.time}")
#
#             # Broadcast message to all neighbors except the sender and those that have already delivered
#             for neighbor_id, peer in self.nodes.items():
#                 # Do not send back to nodes who already received this message or neighbors that delivered
#                 if neighbor_id not in newpath.nodes and neighbor_id not in self.neighbors_delivered[payload_key] and neighbor_id != newpath.start:
#                     delay = random_delay()
#                     time.sleep(delay)
#                     relay_msg = Message(payload.id, payload.content, newpath, payload.time, payload.type)
#                     self.ez_send(peer, relay_msg)
#
#             # Optimization MD.2
#             if payload_key in self.delivered:
#                 self.message_delivered_time[hash((payload.id, payload.content))] = time.time() - payload.time
#                 # if payload.type == "send":
#                 print(f"[Delivered] {payload.content} at {time.time() - payload.time}, Type: {payload.type}")
#                 self.on_message_bracha(peer, payload)
#                 for neighbor_id, peer in self.nodes.items():
#                     if neighbor_id not in self.neighbors_delivered[payload_key]:
#                         self.ez_send(peer, Message(payload.id, payload.content, Path(payload.path.start, []),
#                                                    payload.time, payload.type))
#                 return
#
#         except Exception as e:
#             print(f"Error in on_message: {e}")
#             raise e
#
#     def on_message_bracha(self, peer: Peer, payload: Message) -> None:
#         payload_key = get_message_key(payload)
#         if payload.type == "send" and not self.msg_sent[payload_key]:
#             # print("I got a send message")
#             echo_payload = Message(payload.id, payload.content + f" echo from {self.node_id}", Path(self.node_id, []), payload.time, "echo")
#             self.msg_sent[payload_key] = True
#             self.msg_sent[get_message_key(echo_payload)] = True
#             self.on_broadcast(echo_payload)
#         elif payload.type == "echo":
#             ready_payload = Message(payload.id, payload.content, Path(self.node_id, []), payload.time, "ready")
#             ready_payload_key = get_message_key(ready_payload)
#             if self.msg_counter[payload_key] == 0:
#                 self.msg_counter[payload_key] = 1
#             self.msg_counter[payload_key] += 1
#             # print(f"{payload.content}: Echo messages received: {self.msg_counter[payload_key]}")
#             if (self.msg_counter[payload_key] >= int(math.ceil(float(self.n + self.f + 1)/2.0))) and not self.msg_sent[ready_payload_key]:
#                 self.msg_sent[ready_payload_key] = True
#                 # print(f"[Delivered] Echo {payload.content} at {time.time() - payload.time}")
#                 # cont = payload.content.split("echo")
#                 # ready_payload.content = cont[0]
#                 self.on_broadcast(ready_payload)
#         elif payload.type == "ready" and not self.ready_delivered[payload_key]:
#             ready_payload = Message(payload.id, payload.content, Path(self.node_id, []), payload.time, "ready")
#             if self.msg_counter[payload_key] == 0:
#                 self.msg_counter[payload_key] = 1
#             self.msg_counter[payload_key] += 1
#
#             if self.msg_counter[payload_key] >= self.f + 1 and not self.msg_sent[payload_key]:
#                 self.msg_sent[payload_key] = True
#                 self.on_broadcast(payload)
#             if self.msg_counter[payload_key] >= 2 * self.f + 1:
#                 print(f"[Delivered] Ready {payload.content} at {time.time() - payload.time}")
#                 self.ready_delivered[payload_key] = True
#
#     async def monitor_inactivity(self):
#         inactivity_threshold = 100  # In seconds
#
#         while True:
#             await asyncio.sleep(1)  # Check every second
#             if self.last_message_time:
#                 elapsed_time = (datetime.now() - self.last_message_time).total_seconds()
#                 if elapsed_time > inactivity_threshold:
#                     print(
#                         f"[Node {self.node_id}] Stopping due to inactivity. Last message received {elapsed_time:.2f} seconds ago.")
#                     self.stop()  # Stop the algorithm, save node stats to output folder
#                     break
#
# class ByzantineDolevAlgorithm(DolevAlgorithm):
#
#     def __init__(self, settings: CommunitySettings) -> None:
#         super().__init__(settings)
#
#     async def on_start(self):
#         await super().on_start()
#
#     @override
#     def on_broadcast(self, message: Message):
#         print("No broadcast for you!")
#         return
#
#     async def monitor_inactivity(self):
#         await super().monitor_inactivity()
#
#     @override
#     @message_wrapper(Message)
#     async def on_message(self, peer: Peer, payload: Message):
#         return

