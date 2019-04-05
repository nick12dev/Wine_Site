# pylint: disable=super-init-not-called

class OrderException(Exception):

    def __init__(self, msg):
        self.msg = msg
