import os
import math
from collections import defaultdict
from datetime import datetime, time
from typing import Set, List
from .dolev_algorithm import DolevAlgorithm, Message, Path
from cs4545.system.da_types import *

class BrachaAlgorithm(DolevAlgorithm):

    def __init__(self, settings: CommunitySettings) -> None:
        super().__init__(settings)
        self.n = int (os.environ.get("N"))                          # nr of nodes in the network
        self.sent_ready: Dict[Message, bool] = defaultdict(bool)
        self.sent_echo: Dict[Message, bool] = defaultdict(bool)
        self.brb_delivered: Dict[Message, bool] = defaultdict(bool)
        self.echos: Dict[Message, Set[int]] = defaultdict(set)      # for each m, store list of nodes which sent you echo
        self.readys: Dict[Message, Set[int]] = defaultdict(set)

    async def on_start(self):
        await super().on_start()

    def on_broadcast(self, message: Message):
        super().on_broadcast(message)


    # Callback function called from Dolev whenever a message of the corresponding type was delivered
    def receive_message(self, msg: Message):
        self._message_history.receive_message()
        self.last_message_time = datetime.now()

        if msg.type == "send" and msg not in self.sent_echo:
            self.sent_echo[msg] = True
            self.on_broadcast(self.create_message(msg, "echo"))
        if msg.type == "echo":
            self.echos[msg].add(msg.path.start)
        if msg.type == "ready":
            self.readys[msg].add(msg.path.start)

        print(self.echos)
        print(self.readys)
        self.handle_echo_message(msg)
        self.handle_ready_amplification(msg)
        self.handle_ready_delivery(msg)

    def handle_echo_message(self, msg: Message):
        if len(self.echos) >= math.ceil((self.n + self.f + 1) / 2) and msg not in self.sent_ready:
            self.sent_ready[msg] = True
            self.on_broadcast(self.create_message(msg, "ready"))

    def handle_ready_amplification(self, msg: Message):
        if len(self.readys) >= self.f + 1 and msg not in self.sent_ready:
            self.sent_ready[msg] = True
            self.on_broadcast(self.create_message(msg, "ready"))

    def handle_ready_delivery(self, msg: Message):
        if len(self.readys) >= 2 * self.f + 1 and msg not in self.brb_delivered:
            self.brb_delivered[msg] = True
            print(f"[Delivered Ready] {msg.content} at {time.time() - msg.time}")

    async def monitor_inactivity(self):
        await super().monitor_inactivity()

