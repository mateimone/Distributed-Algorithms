import uuid
import json
import time
from collections import defaultdict

from ipv8.community import CommunitySettings
from datetime import datetime

from typing_extensions import override

from .bracha_algorithm import BrachaAlgorithm
from cs4545.system.da_types import *


@dataclass(msg_id=6)
class RCOMessage:
    id: str
    content: str
    time: float
    bid: int         # Id of the node who started the broadcast of this message
    VC: List[int]

    def __hash__(self) -> int:
        return (self.id, self.content).__hash__()

    def __eq__(self, other) -> bool:
        return self.id == other.id and self.content == other.content

def generate_unique_id():
    return uuid.uuid4().hex

class RCOAlgorithm(BrachaAlgorithm):

    def __init__(self, settings: CommunitySettings) -> None:
        super().__init__(settings)
        self.VC = [0] * self.n                              # Vector Clock of this process
        self.pending:[RCOMessage] = []                      # Messages you received and which are pending to be delivered by you
        self.rco_broadcast: List[RCOMessage] = []           # Messages you start to broadcast
        self.rco_delivered: Dict[RCOMessage, bool] = defaultdict(bool)
        self.last_message_time = None

    async def on_start(self):
        instruction = self.instructions[self.node_id]

        if "messages" in instruction:
            messages = instruction["messages"]
            for (i, message) in enumerate(messages):
                # Get unique id for a message
                unique_id = generate_unique_id()
                print(f"RCO Node {self.node_id} is broadcasting message {unique_id}: {message}")
                self.rco_broadcast.append(RCOMessage(unique_id, message, time.time(), self.node_id, self.VC))

        # If node has messages to deliver, then it is a starting node
        for message in self.rco_broadcast:
            self.broadcast_rco(message)

        # Start monitoring for inactivity
        await asyncio.create_task(self.monitor_inactivity())

    # Function to broadcast a RCOMessage as a string
    def broadcast_rco(self, message: RCOMessage):
        self.rco_delivered[message] = True
        string_to_broadcast = json.dumps(message.__dict__)
        super().broadcast_string(string_to_broadcast)

        self.increment_VC(self.node_id)
        print(f"[RCO Delivered] {message.content} at {time.time() - message.time}, my VC {self.VC}")
        self.append_output(f"[RCO Delivered] {message.content} at {time.time() - message.time}, my VC {self.VC}")

    def increment_VC(self, node_id: int):
        self.VC[node_id] += 1

    def deliver_pending(self):
        if len(self.pending) == 0:
            return

        last_message = next((x for x in self.pending if self.compareVC(x.VC)), None)

        if last_message is None:
            return

        self.pending.remove(last_message)
        self.rco_delivered[last_message] = True
        self.increment_VC(last_message.bid)      # Increment your VC of the broadcaster node
        print(f"[RCO Delivered] {last_message.content} at {time.time() - last_message.time}, my VC {self.VC}")
        self.append_output(f"[RCO Delivered] {last_message.content} at {time.time() - last_message.time}, my VC {self.VC}")
        self.deliver_pending()

    def rco_receive_message(self, content: str):
        self._message_history.receive_message()
        self.last_message_time = datetime.now()

        # Parse content
        rco_content: RCOMessage = self.parse_json_into_rcoMessage(content)

        if self.node_id != rco_content.bid:
            self.pending.append(rco_content)
            self.deliver_pending()

    def parse_json_into_rcoMessage(self, message: str):
        msg = json.loads(message)
        return RCOMessage(**msg)

    def compareVC(self, VC_x: List[int]):
        return all(x >= y for x, y in zip(self.VC, VC_x))

    async def monitor_inactivity(self):
        await super().monitor_inactivity()