from blinker import Namespace
from flask import request_tearing_down


my_signals = Namespace()
model_saved = my_signals.signal('model-saved')


def subscribe_model_saved(app):
    @model_saved.connect_via(app)
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
