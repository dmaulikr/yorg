from abc import ABCMeta
from racing.game.gameobject import GameObjectMdt
from .logic import _Logic


class Season(GameObjectMdt):
    __metaclass__ = ABCMeta
    logic_cls = _Logic