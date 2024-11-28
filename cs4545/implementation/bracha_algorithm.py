import math
import time
from collections import defaultdict
from typing import Set, List, Dict

from typing_extensions import override

from cs4545.implementation.dolev_algorithm import ByzantineDolevAlgorithm, DolevAlgorithm, Message, generate_unique_id, \
    random_delay, Path
from cs4545.system.da_types import CommunitySettings, Peer, message_wrapper

class BrachaAlgorithm(DolevAlgorithm):

    def __init__(self, settings: CommunitySettings) -> None:
        super().__init__(settings)
        self.msg_counter: Dict[Message, int] = defaultdict(int)
        self.msg_sent: Dict[Message, bool] = defaultdict(bool)
        self.ready_delivered: Dict[Message, bool] = defaultdict(bool)
        self.add_message_handler(Message, self.on_message_bracha)

    @override
    async def on_start(self):
        await super().on_start()

    @override
    def on_broadcast(self, message: Message):
        super().on_broadcast(message)

    # @override
    @message_wrapper(Message)
    async def on_message_bracha(self, peer: Peer, payload: Message):
        sender_id = self.node_id_from_peer(peer)
        # if payload.type == "send":
        #     print(f"{self.node_id} received send msg {payload.content}")
        # else:
            # print(payload.path.nodes)
        await super().on_message(peer, payload)

        if payload.type == "send" and not self.msg_sent[
            Message(payload.id, payload.content, Path(payload.path.start, []), payload.time, "echo")]:
            new_path = payload.path.add(sender_id)
            echo_payload = Message(payload.id, payload.content, Path(payload.path.start, []), payload.time,
                                   "echo")
            self.msg_sent[echo_payload] = True
            # print("Here")
            self.on_broadcast(echo_payload)

        if self.delivered[payload]:
            if payload.type == "echo":
                # if self.msg_counter[payload] == 0:
                #     self.msg_counter[payload] = 1
                self.msg_counter[payload] += 1
                # print(f"{payload.content}: Echo messages received: {self.msg_counter[payload]}")
                ready_payload = Message(payload.id, payload.content, Path(payload.path.start, []), payload.time, "ready")
                if (self.msg_counter[payload] >= int(math.ceil((float(self.n + self.f + 1))/2.0)) and
                        not self.msg_sent[ready_payload]):
                    self.msg_sent[ready_payload] = True
                    # print("Echo here")
                    self.on_broadcast(ready_payload)
                    # print(f"Received enough echo messages. Broadcasting Ready {payload.content}.")

            if payload.type == "ready" and not self.ready_delivered[payload]:
                ready_payload = Message(payload.id, payload.content, Path(payload.path.start, []), payload.time, "ready")
                # if self.msg_counter[payload] == 0:
                #     self.msg_counter[payload] = 1
                self.msg_counter[payload] += 1
                # print(f"Ready messages received: {self.msg_counter[payload]}")
                if self.msg_counter[payload] >= self.f + 1 and not self.msg_sent[payload]:
                    self.msg_sent[payload] = True
                    self.on_broadcast(ready_payload)
                if self.msg_counter[payload] >= 2 * self.f + 1:
                    print(f"[Delivered] Ready {payload.content} at {time.time() - payload.time}")
                    self.ready_delivered[payload] = True



class ByzantineBrachaAlgorithm(ByzantineDolevAlgorithm):

    def __init__(self, settings: CommunitySettings) -> None:
        super().__init__(settings)
        self.add_message_handler(Message, self.on_message_bracha)

    @override
    async def on_start(self):
        await super().on_start()

    @override
    def on_broadcast(self, message: Message):
        super().on_broadcast(message)

    @message_wrapper(Message)
    async def on_message_bracha(self, peer: Peer, payload: Message):
        await super().on_message(peer, payload)
