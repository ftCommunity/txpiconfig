#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Config -- An application to configure a TX-Pi.
#
# Written in 2019 by Lars Heuer
#
# To the extent possible under law, the author(s) have dedicated all copyright
# and related and neighboring rights to this software to the public domain
# worldwide. This software is distributed without any warranty.
# You should have received a copy of the CC0 Public Domain Dedication along
# with this software.
#
# If not, see <http://creativecommons.org/publicdomain/zero/1.0/>.
#
"""TX-Pi Configuration - Copyright (c) 2019 -- Lars Heuer
"""
import os
import re
import sys
import subprocess
import configparser
from functools import partial
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from TouchStyle import TouchApplication, TouchWindow, TouchMessageBox
try:
    from TouchStyle import BusyAnimation
except ImportError:
    from launcher import BusyAnimation


_parser = configparser.ConfigParser()
with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'manifest'), encoding='utf-8') as f:
    _parser.read_file(f)

__version__ = _parser.get('app', 'version', fallback='n/a')

del _parser


def _app_path():
    """\
    Returns the path of the application directory.
    """
    return os.path.dirname(os.path.realpath(__file__))


class ConfigApp(TouchApplication):
    """Application to configure the TX-Pi.
    """
    def __init__(self, args):
        super(ConfigApp, self).__init__(args)
        translator = QTranslator()
        if translator.load(QLocale.system(), os.path.join(_app_path(), 'config_')):
            # Translation successfully loaded, install translator
            self.installTranslator(translator)
        win = TouchWindow(QCoreApplication.translate('ConfigApp', 'Config'))
        self.win = win
        self._busy_animation = None
        menu = win.addMenu()
        container = PaneContainer(self, menu=menu)
        # Register config panes
        container.add_pane(Services(container))
        container.add_pane(Hostname(container))
        win.setCentralWidget(container)
        action = menu.addAction(QCoreApplication.translate('ConfigApp', 'About'))
        action.triggered.connect(self.on_menu_about)
        win.show()
        self.exec_()

    def iambusy(self, busy):
        self._blur_window(busy)
        self._busy(busy)

    def _busy(self, busy):
        """\
        Shows / disables a busy animation.

        :type busy: bool
        :param busy: ``True`` to show a busy animation, ``False`` to stop the animation.
        """
        if busy and self._busy_animation is None:
            self._busy_animation = BusyAnimation(self, self.win)
            self._busy_animation.show()
        elif not busy and self._busy_animation is not None:
            self._busy_animation.close()
            self._busy_animation = None

    def on_menu_about(self):
        """Shows an about dialog.
        """
        about_dlg = TouchMessageBox(QCoreApplication.translate('ConfigApp', 'About'), self.win)
        about_dlg.setCancelButton()
        # Add the application icon
        about_dlg.addPixmap(QPixmap(os.path.join(_app_path(), 'icon.png')))
        # Show app name, author, version
        about_dlg.setText('<font size="2">{name}<br><font size="1">{descr}<br><br>'
                          'Version {version}<br>(c) 2019 Lars Heuer<br>'
                          '<br>Icon (c) Johan H. W. Basberg'
                          '<br>Public Domain<br>https://thenounproject.com/term/gear/1241/' \
                            .format(name=QCoreApplication.translate('ConfigApp', 'Configuration'),
                                    descr=QCoreApplication.translate('ConfigApp', 'Configure the TX-Pi'),
                                    version=__version__))
        # Close about dialog
        about_dlg.setPosButton(QCoreApplication.translate('ConfigApp', 'Okay'))
        about_dlg.exec_()

    def _blur_window(self, blur):
        """Blurs the window.

        :type blur: bool
        :param blur: ``True`` to enable blurring effect, ``False`` to disable blurring.
        """
        # Since the graphic effect is owned by the widget, two effects are needed.
        cw_effect, tb_effect = None, None
        if blur:
            cw_effect = QGraphicsBlurEffect(self)
            tb_effect = QGraphicsBlurEffect(self)
        self.win.centralWidget.setGraphicsEffect(cw_effect)
        self.win.titlebar.setGraphicsEffect(tb_effect)


class PaneContainer(QStackedWidget):
    """\
    Container for panes.
    """
    def __init__(self, app, menu):
        """\
        Initializes the pane with a default pane.

        :param parent: An instance of TouchApplication
        :param menu: The context menu. It's used to add items to switch between
                     the panes.
        """
        super(PaneContainer, self).__init__()
        self._menu = menu
        self._app = app
        startpane = QWidget()
        layout = QVBoxLayout()
        lbl = QLabel()
        lbl.setPixmap(QPixmap(os.path.join(_app_path(), 'icon.png')))
        layout.addLayout(PaneContainer._hcenter_widget(lbl))
        layout.addWidget(QLabel(''))
        lbl = QLabel(QCoreApplication.translate('ConfigApp', 'Welcome'))
        lbl.setObjectName('smalllabel')
        layout.addLayout(PaneContainer._hcenter_widget(lbl))
        lbl = QLabel(QCoreApplication.translate('ConfigApp', 'Please choose an item from the menu.'))
        lbl.setObjectName('tinylabel')
        layout.addLayout(PaneContainer._hcenter_widget(lbl))
        layout.addStretch()
        startpane.setLayout(layout)
        self.addWidget(startpane)

    @staticmethod
    def _hcenter_widget(widget):
        """\
        Centers the provided widget horizontally.

        :return: QHBoxLayout with the provided widget.
        """
        hbox = QHBoxLayout()
        hbox.addStretch()
        hbox.addWidget(widget)
        hbox.addStretch()
        return hbox

    def add_pane(self, pane):
        """\
        Adds a pane and registers the pane within the menu.

        :param pane: The pane to add.
        """
        idx = self.addWidget(pane)
        action = self._menu.addAction(pane.name)
        action.triggered.connect(partial(self._show_pane, index=idx))

    def _show_pane(self, index):
        """\
        Called to switch panes.

        :param int index: Index of the pane to switch to.
        """
        switch = True
        if self.currentIndex() != 0:
            switch = self.currentWidget().validate()
        if switch:
            self.widget(index).before_focus()
            self.setCurrentIndex(index)
            self.widget(index).has_focus()


class Pane(QWidget):
    """\
    A Pane is a page within the PaneContainer.

    A pane may be invisible or visible.

    Inherit from this class for additional config pages and register them
    in the ConfigApp's constructor.
    """
    def __init__(self, parent, name):
        """\
        Initializes the pane.

        :param name: The name of the pane. The name will also be used as menu
                     item. The name will be translated automatically.
        """
        super(Pane, self).__init__(parent)
        self.name = QCoreApplication.translate('ConfigApp', name)
        self._app = None

    def run_script(self, name, arg, callback):
        """\
        Runs the script with the provided name as background process
        and informs `callback` about the result.

        :param str name: The script name.
        :param str arg: A single argument like 'enable' or 'disable'
        :param callback: A function accepting the arguments ``exit_code`` and ``exit_status``
        """
        def on_script_finished(exit_code, exit_status):
            self.parent()._app.iambusy(False)
            callback(exit_code, exit_status)

        self.parent()._app.iambusy(True)
        script = os.path.join(_app_path(), 'scripts', name)
        proc = QProcess(self)
        proc.finished.connect(on_script_finished)
        proc.start('sudo {0} {1}'.format(script, arg))

    def ask_for_reboot(self):
        """\
        Opens a dialog which recommends to reboot the device to apply changes.

        The user may cancel it.
        """
        dlg = TouchMessageBox(QCoreApplication.translate('ConfigApp', 'Reboot'), self)
        dlg.setCancelButton()
        dlg.addPixmap(QPixmap(os.path.join(_app_path(), 'reboot.png')))
        dlg.setText('<font size="2">{0}<br><br><font size="1">{1}' \
                            .format(QCoreApplication.translate('ConfigApp', "It's recommended to restart the device."),
                                    QCoreApplication.translate('ConfigApp', 'Do you want to reboot now?')))
        dlg.setPosButton(QCoreApplication.translate('ConfigApp', 'Reboot'))
        res, txt = dlg.exec_()
        if res:
            subprocess.call(['sudo', 'reboot'])

    def before_focus(self):
        """\
        Method called from PaneContainer right before activating this pane.

        Does nothing by default.
        """
        pass

    def has_focus(self):
        """\
        Method called from PaneContainer to indicate that this pane is active.

        Does nothing by default.
        """
        pass

    def validate(self):
        """\
        Method called from PaneContainer to indicate that this pane will be
        moved to the background.

        If this method returns ``False``, the pane stays at the top and the
        requested pane change is canceled.

        This method can be used to remind the user that the pane contains
        unsaved changes etc.

        Note: This method may not be called if the application is closed.

        Does nothing by default but returns ``True`` to allow pane changes.
        """
        return True


# Service names
_SERVICE_SSH = 'ssh'
_SERVICE_VNC = 'x11vnc'


class Services(Pane):
    """\
    Pane to configure servers.
    """
    def __init__(self, parent):
        super(Services, self).__init__(parent, name='Services')
        self._cb_ssh = QCheckBox(QCoreApplication.translate('ConfigApp', 'SSH server'))
        self._cb_vnc = QCheckBox(QCoreApplication.translate('ConfigApp', 'VNC server'))
        layout = QVBoxLayout()
        lbl = QLabel(QCoreApplication.translate('ConfigApp', 'Enable / disable servers'))
        layout.addWidget(lbl)
        layout.addWidget(QLabel(''))
        layout.addWidget(self._cb_ssh)
        layout.addWidget(QLabel(''))
        layout.addWidget(self._cb_vnc)
        layout.addStretch()
        lbl = QLabel(QCoreApplication.translate('ConfigApp', 'The state of the servers is persistent.'))
        lbl.setWordWrap(True)
        lbl.setObjectName('tinylabel')
        layout.addWidget(lbl)
        lbl = QLabel(QCoreApplication.translate('ConfigApp', 'It remains after reboot / shutdown.'))
        lbl.setWordWrap(True)
        lbl.setObjectName('tinylabel')
        layout.addWidget(lbl)
        self.setLayout(layout)
        self._cb_ssh.toggled.connect(lambda checked: self._toggle_service(_SERVICE_SSH, checked))
        self._cb_vnc.toggled.connect(lambda checked: self._toggle_service(_SERVICE_VNC, checked))

    def before_focus(self):
        """\
        Update check boxes.
        """
        self._update_current_service_status()

    def _update_current_service_status(self):
        """\
        Updates the the internal state and the checkboxes acc. to the current
        status of the services.
        """
        self._cb_ssh.setEnabled(False)
        self._cb_vnc.setEnabled(False)
        self._ssh_enabled = self._get_service_status(_SERVICE_SSH)
        self._vnc_enabled = self._get_service_status(_SERVICE_VNC)
        # Avoid that a toggled signal is sent
        self._cb_ssh.blockSignals(True)
        self._cb_vnc.blockSignals(True)
        self._cb_ssh.setChecked(self._ssh_enabled)
        self._cb_vnc.setChecked(self._vnc_enabled)
        # Signals may be emitted again.
        self._cb_ssh.blockSignals(False)
        self._cb_vnc.blockSignals(False)
        self._cb_ssh.setEnabled(True)
        self._cb_vnc.setEnabled(True)

    @staticmethod
    def _get_service_status(service_name):
        """\
        Returns the service status for the provided service.

        :param name: Service name
        :return: Boolean value if the service is active or not.
        """
        proc = subprocess.Popen(['systemctl', 'status',  service_name],
                                stdout=subprocess.PIPE)
        output, err = proc.communicate()
        return b'Active: active (running)' in output

    def _toggle_service(self, service_name, enable):
        """\
        Enable / disable the provided service.

        If enabled, systemd enables and starts the service; otherwise the
        service is disabled and stopped.

        :param service_name: The service name.
        :param enable: Boolean indicating if the service should become enabled.
        """
        self._cb_ssh.setEnabled(False)
        self._cb_vnc.setEnabled(False)
        self.run_script(service_name, ('enable' if enable else 'disable'),
                        self._on_toggle_finished)

    def _on_toggle_finished(self, exit_code, exit_status):
        """\
        Called when a service was enabled / disabled.

        :param exit_code:
        :param exit_status:
        """
        if exit_code == 0:
            self._cb_ssh.setEnabled(True)
            self._cb_vnc.setEnabled(True)
        else:
            # Something went wrong, update the current state of the services
            self._update_current_service_status()


_HOSTNAME_PATTERN = re.compile(r'^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$')

class Hostname(Pane):
    """\
    Pane to configure the hostname.
    """
    def __init__(self, parent):
        super(Hostname, self).__init__(parent, name='Hostname')
        self._edit_hostname = QLineEdit(self)
        self._btn_apply = QPushButton(QCoreApplication.translate('ConfigApp', 'Apply'))
        self._btn_apply.clicked.connect(self._on_apply)
        layout = QVBoxLayout()
        lbl = QLabel(QCoreApplication.translate('ConfigApp', 'Hostname'))
        layout.addWidget(lbl)
        layout.addWidget(self._edit_hostname)
        layout.addStretch()
        layout.addWidget(self._btn_apply)
        self.setLayout(layout)
        # The event "textEdited" does not work if the TouchStyle keyboard shows up
        self._edit_hostname.textChanged.connect(self._on_hostname_edited)

    def before_focus(self):
        """\
        Update hostname.
        """
        # Gets enabled if hostname changes, see _on_hostname_edited
        self._btn_apply.setEnabled(False)
        #self._retrieve_hostname()

    def _retrieve_hostname(self):
        """\
        Reads the current hostname and updates the edit box with the current
        hostname.
        """
        self._edit_hostname.setEnabled(False)
        self._btn_apply.setEnabled(False)
        self._edit_hostname.setText(self._get_hostname())
        self._edit_hostname.setEnabled(True)

    @staticmethod
    def _get_hostname():
        """\
        Returns the current hostname as string.
        """
        with open('/etc/hostname', 'r') as f:
            return f.read().strip()

    def _on_hostname_edited(self, txt):
        """\
        Checks if the `txt` looks like a valid hostname and enables / disables
        the "Apply" button.
        """
        self._btn_apply.setEnabled(_HOSTNAME_PATTERN.match(txt) is not None)

    def _on_apply(self):
        """\
        Called to save a changed hostname.
        """
        #self._edit_hostname.setEnabled(False)
        #self._btn_apply.setEnabled(False)
        #self.run_script('hostname', self._edit_hostname.text(),
        #                self._on_apply_finished)
        self._on_apply_finished(0, 0)

    def _on_apply_finished(self, exit_code, exit_status):
        """\
        Called when the hostname change was finished.

        :param exit_code:
        :param exit_status:
        """
        if exit_code == 0:
            self._edit_hostname.setEnabled(True)
            self.ask_for_reboot()
        else:
            # Something went wrong
            self._retrieve_hostname()


if __name__ == "__main__":
    ConfigApp(sys.argv)
