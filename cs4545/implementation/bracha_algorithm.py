import json
import os
import math
import uuid
from collections import defaultdict
from datetime import datetime
import time
from typing import Set
from typing_extensions import override
from .dolev_algorithm import DolevAlgorithm, DolevMessage
from .dolev_algorithm import Path as CustomPath
from cs4545.system.da_types import *


@dataclass(msg_id=5)
class BrachaMessage:
    id: str
    content: str
    time: float
    type: str

    def __hash__(self) -> int:
        return (self.id, self.content).__hash__()

    def __eq__(self, other) -> bool:
        return self.id == other.id and self.content == other.content

def generate_unique_id():
    return uuid.uuid4().hex

class BrachaAlgorithm(DolevAlgorithm):

    def __init__(self, settings: CommunitySettings) -> None:
        super().__init__(settings)
        self.n = int(os.environ.get("N"))                                # nr of nodes in the network
        self.opt1 = int(os.environ.get("OPT1"))                          # is opt1 turned on (1) or off (0)
        self.opt2 = int(os.environ.get("OPT2"))
        self.opt3 = int(os.environ.get("OPT3"))
        self.add_message_handler(BrachaMessage, self.on_send_hop)
        self.sent_ready: Dict[BrachaMessage, bool] = defaultdict(bool)
        self.sent_echo: Dict[BrachaMessage, bool] = defaultdict(bool)
        self.brb_delivered: Dict[BrachaMessage, bool] = defaultdict(bool)
        self.echos: Dict[BrachaMessage, Set[int]] = defaultdict(set)     # for each msg, store list of nodes which sent you echo
        self.readys: Dict[BrachaMessage, Set[int]] = defaultdict(set)
        self.brb_broadcast: List[BrachaMessage] = []                     # list of msg to broadcast for starting nodes
        self.last_message_time = None
        if self.opt3 == 1:
            assert self.n > 3 * self.f + 1

    async def on_start(self):
        instruction = self.instructions[self.node_id]

        if "messages" in instruction:
            messages = instruction["messages"]
            for (i, message) in enumerate(messages):
                # Get unique id for a message
                unique_id = generate_unique_id()
                print(f"Bracha Node {self.node_id} is broadcasting message {unique_id}: {message}")
                self.brb_broadcast.append(BrachaMessage(unique_id, message, time.time(), "send"))

        # If node has messages to deliver, then it is a starting node
        for message in self.brb_broadcast:
            if self.opt2 == 1:  # single hop send messages
                self.single_hop_send_message(message)
            else:
                self.broadcast(message) # use dolev broadcast

        # Start monitoring for inactivity
        await asyncio.create_task(self.monitor_inactivity())

    # Function to broadcast a BrachaMessage as a string
    def broadcast(self, message: BrachaMessage):
        string_to_broadcast = json.dumps(message.__dict__)
        super().on_broadcast_string(string_to_broadcast)

    # OPT2
    def single_hop_send_message(self, msg: BrachaMessage):
        for neighbor_id, peer in self.nodes.items():
            self.delayed_send(peer, msg)

    # Wrapper for OPT2
    @message_wrapper(BrachaMessage)
    async def on_send_hop(self, peer: Peer, msg: BrachaMessage) -> None:
        if self.opt2 == 1:
            self.send_echo(msg)  # continue protocol

    # OPT3
    def echo_and_ready_sets(self, starter_id: int):
        echo_set_size = math.ceil((self.n + self.f + 1) / 2) + self.f
        echo_set = [(starter_id + i) % self.n for i in range(1, echo_set_size + 1)]

        ready_set_size = 2 * self.f + 1 + self.f
        ready_set = [(starter_id + self.n - i) % self.n for i in range(1, ready_set_size + 1)]

        return echo_set, ready_set

    # OPT3
    # Method is called after a SEND msg is delivered to this node
    def handle_send_opt3(self, starter_id: int, msg: BrachaMessage):
        # if I am in echo set do echo
        # if I am in ready set do ready
        # else: relay messages, do nothing
        echo_set, ready_set = self.echo_and_ready_sets(starter_id)
        if self.node_id in echo_set:
            self.send_echo(msg)
        if self.node_id in ready_set:
            self.send_ready(msg)

    # Callback function called from Dolev whenever a message of the corresponding type was delivered
    def receive_message(self, content: str, start_node: int):
        self._message_history.receive_message()
        self.last_message_time = datetime.now()

        # Parse content
        brb_content: BrachaMessage = self.parse_json_message(content)

        if brb_content.type == "send" and brb_content not in self.sent_echo:
            if self.opt3 == 1:
                self.handle_send_opt3(start_node, brb_content)
            else:
                self.send_echo(brb_content)

        if brb_content.type == "echo":
            self.echos[brb_content].add(start_node)
            self.handle_echo_message(brb_content)
            if self.opt1 == 1:
                self.handle_echo_amplification(brb_content)

        if brb_content.type == "ready":
            self.readys[brb_content].add(start_node)
            self.handle_ready_amplification(brb_content)
            self.handle_ready_delivery(brb_content)
            if self.opt1 == 1:
                self.accelerate_echo_delivery(brb_content)

    def send_echo(self, msg: BrachaMessage):
        self.sent_echo[msg] = True
        self.broadcast(self.create_message(msg, "echo"))

    # Used in opt3
    def send_ready(self, msg: BrachaMessage):
        self.sent_ready[msg] = True
        self.broadcast(self.create_message(msg, "ready"))

    def handle_echo_message(self, msg: BrachaMessage):
        if len(self.echos[msg]) >= math.ceil((self.n + self.f + 1) / 2) and self.sent_ready[msg] == False:
            self.sent_ready[msg] = True
            self.broadcast(self.create_message(msg, "ready"))

    # Part of OPT1
    def handle_echo_amplification(self, msg: BrachaMessage):
        if len(self.echos[msg]) >= self.f + 1 and self.sent_echo[msg] == False:
            self.send_echo(msg)

    # Second part of OPT1
    def accelerate_echo_delivery(self, msg: BrachaMessage):
        if self.sent_ready[msg] == True and self.sent_echo[msg] == False:
            self.send_echo(msg)

    def handle_ready_amplification(self, msg: BrachaMessage):
        if len(self.readys[msg]) >= self.f + 1 and self.sent_ready[msg] == False:
            self.sent_ready[msg] = True
            self.broadcast(self.create_message(msg, "ready"))

    def handle_ready_delivery(self, msg: BrachaMessage):
        if len(self.readys[msg]) >= 2 * self.f + 1 and self.brb_delivered[msg] == False:
            self.brb_delivered[msg] = True
            print(f"[BRB Delivered] {msg.content} at {time.time() - msg.time}")

    def parse_json_message(self, message: str):
        msg = json.loads(message)
        return BrachaMessage(**msg)

    def create_message(self, msg: BrachaMessage, t: str):
        return BrachaMessage(msg.id, msg.content, msg.time, t)

    def delayed_send(self, peer, msg, max_delay=200):
        ms = random.random() * max_delay

        async def delayed():
            await asyncio.sleep(ms / 1000)
            self.ez_send(peer, msg)

        asyncio.create_task(delayed())

    async def monitor_inactivity(self):
        await super().monitor_inactivity()


class ByzantineBrachaAlgorithm(BrachaAlgorithm):

    def __init__(self, settings: CommunitySettings) -> None:
        super().__init__(settings)

    async def on_start(self):
        await super().on_start()

    def broadcast(self, message: BrachaMessage):
        string_to_broadcast = json.dumps(message.__dict__)
        self.on_broadcast_string(string_to_broadcast)

    @override
    def on_broadcast_string(self, msg: str):
        message = DolevMessage(generate_unique_id(), msg, CustomPath(self.node_id, []), time.time())

        number_neighbors = random.randint(0, len(self.nodes) - 1)
        selected_neighbors = random.sample(list(self.nodes.items()), k=number_neighbors)

        for neighbor_id, peer in selected_neighbors:
            self.delayed_send(peer, message)

        self.delivered[message] = True
        self.receive_message(msg, self.node_id)  # deliver to yourself when broadcasting

    @override
    def receive_message(self, content: str, start_node: int):
        brb_content: BrachaMessage = self.parse_json_message(content)
        modified_msg = brb_content.content
        new_start = start_node

        actions = ["skip", "alter content", "alter start"]
        action = random.choice(actions)

        if action == "skip":
            return
        if action == "alter content":
            random_content_number = random.randint(0, 1000)
            modified_msg = f"Tampered content {str(random_content_number)}"
        if action == "alter start":
            new_start = random.randint(0, len(self.nodes.items()))

        new_brb = BrachaMessage(brb_content.id, modified_msg, time.time(), brb_content.type)
        new_brb_content = json.dumps(new_brb.__dict__)

        # number_neighbors = random.randint(0, len(self.nodes) - 1)
        # selected_neighbors = random.sample(list(self.nodes.items()), k=number_neighbors)
        #
        # for neighbor_id, peer in selected_neighbors:
        #     self.ez_send(peer, new_brb)

        super().receive_message(new_brb_content, new_start)