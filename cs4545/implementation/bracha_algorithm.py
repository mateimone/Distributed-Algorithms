import json
import os
import math
import uuid
from collections import defaultdict
from datetime import datetime
import time
from typing import Set
from .dolev_algorithm import DolevAlgorithm
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
        self.n = int (os.environ.get("N"))                                # nr of nodes in the network
        self.sent_ready: Dict[BrachaMessage, bool] = defaultdict(bool)
        self.sent_echo: Dict[BrachaMessage, bool] = defaultdict(bool)
        self.brb_delivered: Dict[BrachaMessage, bool] = defaultdict(bool)
        self.echos: Dict[BrachaMessage, Set[int]] = defaultdict(set)      # for each msg, store list of nodes which sent you echo
        self.readys: Dict[BrachaMessage, Set[int]] = defaultdict(set)
        self.brb_broadcast: List[BrachaMessage] = []                      # list of msg to broadcast for starting nodes

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
            self.broadcast(message)

        # Start monitoring for inactivity
        await asyncio.create_task(self.monitor_inactivity())

    # Function to broadcast a BrachaMessage as a string
    def broadcast(self, message: BrachaMessage):
        string_to_broadcast = json.dumps(message.__dict__)
        super().on_broadcast_string(string_to_broadcast)

    # Callback function called from Dolev whenever a message of the corresponding type was delivered
    def receive_message(self, content: str, start_node: int):
        self._message_history.receive_message()
        self.last_message_time = datetime.now()

        # Parse content
        brb_content: BrachaMessage = self.parse_json_message(content)
        if brb_content.type == "send" and brb_content not in self.sent_echo:
            self.sent_echo[brb_content] = True
            self.broadcast(self.create_message(brb_content, "echo"))
        if brb_content.type == "echo":
            self.echos[brb_content].add(start_node)
            self.handle_echo_message(brb_content)
        if brb_content.type == "ready":
            self.readys[brb_content].add(start_node)
            self.handle_ready_amplification(brb_content)
            self.handle_ready_delivery(brb_content)

    def handle_echo_message(self, msg: BrachaMessage):
        if len(self.echos[msg]) >= math.ceil((self.n + self.f + 1) / 2) and self.sent_ready[msg] == False:
            self.sent_ready[msg] = True
            self.broadcast(self.create_message(msg, "ready"))

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

    async def monitor_inactivity(self):
        await super().monitor_inactivity()

