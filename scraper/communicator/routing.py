from channels import route_class
from channels.routing import route

from communicator import consumers

channel_routing = [
        route_class(consumers.CommunicatorConsumer, path=r'/comm/'),
        # route("websocket.receive", consumers.ws_message),
        ]
