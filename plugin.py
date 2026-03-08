# -*- coding: utf-8 -*-

from Plugins.Plugin import PluginDescriptor


def main(session, **kwargs):
    from Plugins.Extensions.ElieSatPanelGrid.main import EliesatPanel
    session.open(EliesatPanel)


def menuHook(menuid, **kwargs):
    if menuid == "mainmenu":
        return [("ElieSatPanelGrid", main, "eliesat_panel_grid", 46)]
    return []


def Plugins(**kwargs):
    return [
        PluginDescriptor(
            name="ElieSatPanelGrid",
            description="Enigma2 addons panel",
            where=PluginDescriptor.WHERE_PLUGINMENU,
            icon="assets/icon/panel_logo.png",
            fnc=main,
        ),
        PluginDescriptor(
            name="ElieSatPanelGrid",
            where=PluginDescriptor.WHERE_MENU,
            fnc=menuHook,
        ),
        PluginDescriptor(
            name="ElieSatPanelGrid",
            where=PluginDescriptor.WHERE_EXTENSIONSMENU,
            fnc=main,
        ),
    ]
