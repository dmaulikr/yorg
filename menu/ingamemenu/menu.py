from copy import deepcopy
from yyagl.gameobject import GameObject, Gui
from yyagl.engine.gui.menu import Menu
from .ingamepage import InGamePage


class InGameMenuGui(Gui):

    def __init__(self, mdt, menu_args):
        Gui.__init__(self, mdt)
        menu_args_c = deepcopy(menu_args)
        menu_args_c.background_img = ''
        menu_args_c.btn_size = (-8.6, 8.6, -.42, .98)
        self.menu = Menu(menu_args_c)
        page = InGamePage(menu_args_c)
        page.gui.attach(self.on_ingame_back)
        page.gui.attach(self.on_ingame_exit)
        self.menu.push_page(page)

    def on_ingame_back(self):
        self.notify('on_ingame_back')

    def on_ingame_exit(self):
        self.notify('on_ingame_exit')

    def destroy(self):
        self.menu = self.menu.destroy()
        Gui.destroy(self)


class InGameMenu(GameObject):
    gui_cls = InGameMenuGui

    def __init__(self, menu_args):
        init_lst = [[('gui', self.gui_cls, [self, menu_args])]]
        GameObject.__init__(self, init_lst)
