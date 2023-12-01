from provider.provider import Provider


class TestProvider(Provider):
    def __init__(self):
        self.channels = {}

    def add_channel(self, channel):
        self.channels[channel.name] = channel

    def get_channel(self, name):
        return self.channels.get(name)

    def get_channels(self):
        return self.channels.values()

    def get_channel_names(self):
        return self.channels.keys()
