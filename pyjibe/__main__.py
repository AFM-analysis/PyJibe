def main(splash=True):
    import os
    import pkg_resources
    import sys

    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import QEventLoop

    app = QApplication(sys.argv)
    # Note:
    # Having the image file *not* in a submodule of PyJibe
    # seems to cause the splash to display earlier, because
    # presumably `pkg_resources` internally imports modules.
    imdir = pkg_resources.resource_filename("pyjibe", "img")

    if splash:
        from PyQt6.QtWidgets import QSplashScreen
        from PyQt6.QtGui import QPixmap
        splash_path = os.path.join(imdir, "splash.png")
        splash_pix = QPixmap(splash_path)
        splash = QSplashScreen(splash_pix)
        splash.setMask(splash_pix.mask())
        splash.show()
        # make sure Qt really displays the splash screen
        app.processEvents(QEventLoop.ProcessEventsFlag.AllEvents, 300)

    from PyQt6 import QtCore, QtGui
    from .head import PyJibe

    # Set Application Icon
    icon_path = os.path.join(imdir, "icon.png")
    app.setWindowIcon(QtGui.QIcon(icon_path))

    # Use dots as decimal separators
    QtCore.QLocale.setDefault(QtCore.QLocale(QtCore.QLocale.Language.C))

    window = PyJibe()

    if splash:
        splash.finish(window)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
