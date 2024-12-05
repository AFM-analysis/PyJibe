def main(splash=True):
    import importlib.resources
    import sys

    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import QEventLoop

    app = QApplication(sys.argv)
    # Note:
    # Having the image file *not* in a submodule of PyJibe
    # seems to cause the splash to display earlier, because
    # presumably `importlib.resources` internally imports modules.

    if splash:
        from PyQt5.QtWidgets import QSplashScreen
        from PyQt5.QtGui import QPixmap
        ref = importlib.resources.files("pyjibe.img") / "splash.png"
        with importlib.resources.as_file(ref) as splash_path:
            splash_pix = QPixmap(str(splash_path))
        splash = QSplashScreen(splash_pix)
        splash.setMask(splash_pix.mask())
        splash.show()
        # make sure Qt really displays the splash screen
        app.processEvents(QEventLoop.AllEvents, 300)

    from PyQt5 import QtCore, QtGui
    from .head import PyJibe

    # Set Application Icon
    ref = importlib.resources.files("pyjibe.img") / "icon.png"
    with importlib.resources.as_file(ref) as icon_path:
        app.setWindowIcon(QtGui.QIcon(str(icon_path)))

    # Use dots as decimal separators
    QtCore.QLocale.setDefault(QtCore.QLocale(QtCore.QLocale.C))

    window = PyJibe()

    if splash:
        splash.finish(window)

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
