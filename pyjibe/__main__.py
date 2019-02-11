def main(splash=True):
    import os
    import pkg_resources
    import sys

    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    # Note:
    # Having the image file *not* in a submodule of PyJibe
    # seems to cause the splash to display earlier, because
    # presumably `pkg_resources` internally imports modules.
    imdir = pkg_resources.resource_filename("pyjibe", "img")

    if splash:
        from PyQt5.QtWidgets import QSplashScreen
        from PyQt5.QtGui import QPixmap
        splash_path = os.path.join(imdir, "splash.png")
        splash_pix = QPixmap(splash_path)
        splash = QSplashScreen(splash_pix)
        splash.setMask(splash_pix.mask())
        splash.show()
        # make sure Qt really displays the splash screen
        app.processEvents()

    from PyQt5 import QtCore, QtGui
    from .head import PyJibe

    # Set Application Icon
    icon_path = os.path.join(imdir, "icon.png")
    app.setWindowIcon(QtGui.QIcon(icon_path))

    # Use dots as decimal separators
    QtCore.QLocale.setDefault(QtCore.QLocale(QtCore.QLocale.C))

    window = PyJibe()
    window.show()
    window.raise_()

    if splash:
        splash.finish(window)

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
