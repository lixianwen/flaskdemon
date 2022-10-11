from blinker import Namespace
from flask import request_tearing_down

from business.config import MY_SENDER

my_signals = Namespace()
model_saved = my_signals.signal('model-saved')


@model_saved.connect_via(MY_SENDER)
def when_model_saved(sender, **extra):
    print('when_model_saved>>>>>')
    print(f'sender: {sender}')
    print(f'extra: {extra}')


def subscribe_request_tearing_down(app):
    @request_tearing_down.connect_via(app)
    def when_request_tearing_down(sender, **extra):
        print('when_request_tearing_down>>>')
        print(f'sender: {sender}')
        print(f'extra: {extra}')
