from direct.gui.DirectButton import DirectButton
from yyagl.engine.gui.page import Page, PageFacade
from yyagl.gameobject import GameObject
from .serverpage import ServerPage
from .clientpage import ClientPage
from .thankspage import ThanksPageGui


class MultiplayerPageGui(ThanksPageGui):

    def __init__(self, mdt, menu_args, mp_props):
        self.props = mp_props
        ThanksPageGui.__init__(self, mdt, menu_args)

    def bld_page(self):
        menu_gui = self.mdt.menu.gui
        serverpage_props = ServerPageProps(
            self.props.cars, self.props.car_path, self.props.phys_path,
            self.props.tracks, self.props.tracks_tr, self.props.track_img,
            self.props.player_name, self.props.drivers_img,
            self.props.cars_img, self.props.drivers)
        scb = lambda: self.mdt.menu.push_page(ServerPage(
            self.mdt.menu.gui.menu_args, serverpage_props, self.mdt.menu))
        menu_data = [
            ('Server', scb),
            ('Client', lambda: self.mdt.menu.push_page(ClientPage(
                self.mdt.menu.gui.menu_args, self.mdt.menu)))]
        widgets = [
            DirectButton(text=menu[0], pos=(0, 1, .4-i*.28), command=menu[1],
                         **menu_gui.menu_args.btn_args)
            for i, menu in enumerate(menu_data)]
        map(self.add_widget, widgets)
        ThanksPageGui.bld_page(self)


class MultiplayerPage(Page):
    gui_cls = MultiplayerPageGui

    def __init__(self, menu_args, mp_props):
        self.menu_args = menu_args
        init_lst = [
            [('event', self.event_cls, [self])],
            [('gui', self.gui_cls, [self, self.menu_args, mp_props])]]
        GameObject.__init__(self, init_lst)
        PageFacade.__init__(self)
        # invoke Page's __init__

    def destroy(self):
        GameObject.destroy(self)
        PageFacade.destroy(self)
