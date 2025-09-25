# crosshair_ua_mod_hotkey
import sys
import json
import os
import ctypes
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
import keyboard  # global hotkey library

# Windows constants for layered & click-through window
GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOPMOST = 0x00000008

user32 = ctypes.windll.user32
SetWindowLong = user32.SetWindowLongW
GetWindowLong = user32.GetWindowLongW
SetLayeredWindowAttributes = ctypes.windll.user32.SetLayeredWindowAttributes

SETTINGS_FILE = "crosshair_settings.json"

# --- Overlay Window ---
class OverlayWindow(QtWidgets.QWidget):
    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WA_StyledBackground, False)
        self.setAutoFillBackground(False)
        screen_geo = QtWidgets.QApplication.primaryScreen().geometry()
        w, h = 400, 400
        x = screen_geo.center().x() - w // 2
        y = screen_geo.center().y() - h // 2
        self.setGeometry(x, y, w, h)
        self.show()
        self.setWindowTitle("Crosshair Overlay")
        self.click_through = False
        self.active = True

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(30)

    def toggle_active(self):
        self.active = not self.active
        self.setVisible(self.active)

    def paintEvent(self, event):
        if not self.active:
            return
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        color = QtGui.QColor(*self.settings['color'])
        painter.setOpacity(self.settings['opacity'])
        pen = QtGui.QPen(color)
        pen.setWidth(self.settings['thickness'])
        painter.setPen(pen)
        cx = self.width() // 2
        cy = self.height() // 2
        size = self.settings['size']
        gap = self.settings['gap']
        style = self.settings['style']

        if style == 'classic':
            painter.drawLine(cx - size - gap, cy, cx - gap, cy)
            painter.drawLine(cx + gap, cy, cx + size + gap, cy)
            painter.drawLine(cx, cy - size - gap, cx, cy - gap)
            painter.drawLine(cx, cy + gap, cx, cy + size + gap)
            if self.settings['center_dot']:
                dot_r = max(1, self.settings['thickness'])
                painter.drawEllipse(QtCore.QPoint(cx, cy), dot_r, dot_r)
        elif style == 'dot':
            dot_r = max(1, size // 4)
            painter.drawEllipse(QtCore.QPoint(cx, cy), dot_r, dot_r)
        elif style == 'circle':
            painter.drawEllipse(QtCore.QPoint(cx, cy), size, size)
        elif style == 'cross+dot':
            painter.drawLine(cx - size - gap, cy, cx - gap, cy)
            painter.drawLine(cx + gap, cy, cx + size + gap, cy)
            painter.drawLine(cx, cy - size - gap, cx, cy - gap)
            painter.drawLine(cx, cy + gap, cx, cy + size + gap)
            painter.drawEllipse(QtCore.QPoint(cx, cy), max(1, self.settings['thickness']), max(1, self.settings['thickness']))
        elif style == 'plus-circle':
            painter.drawLine(cx - size, cy, cx + size, cy)
            painter.drawLine(cx, cy - size, cx, cy + size)
            painter.drawEllipse(QtCore.QPoint(cx, cy), size, size)
        else:
            painter.drawLine(cx - size - gap, cy, cx - gap, cy)
            painter.drawLine(cx + gap, cy, cx + size + gap, cy)
            painter.drawLine(cx, cy - size - gap, cx, cy - gap)
            painter.drawLine(cx, cy + gap, cx, cy + size + gap)

        painter.end()


# --- Settings Window ---
class SettingsWindow(QtWidgets.QWidget):
    def __init__(self, overlay: OverlayWindow, settings):
        super().__init__()
        self.overlay = overlay
        self.settings = settings
        self.setWindowTitle("Crosshair V2 - Settings")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMinMaxButtonsHint)
        self.init_ui()

    def init_ui(self):
        layout = QtWidgets.QVBoxLayout()

        # Color picker
        color_btn = QtWidgets.QPushButton("Вибрати колір")
        color_btn.clicked.connect(self.pick_color)
        layout.addWidget(color_btn)

        # Size slider
        self.size_slider = QtWidgets.QSlider(Qt.Horizontal)
        self.size_slider.setRange(1, 300)
        self.size_slider.setValue(self.settings['size'])
        self.size_slider.valueChanged.connect(self.change_size)
        layout.addWidget(QtWidgets.QLabel("Розмір лінії"))
        layout.addWidget(self.size_slider)

        # Gap slider
        self.gap_slider = QtWidgets.QSlider(Qt.Horizontal)
        self.gap_slider.setRange(0, 100)
        self.gap_slider.setValue(self.settings['gap'])
        self.gap_slider.valueChanged.connect(self.change_gap)
        layout.addWidget(QtWidgets.QLabel("Порожнина (gap)"))
        layout.addWidget(self.gap_slider)

        # Thickness slider
        self.thick_slider = QtWidgets.QSlider(Qt.Horizontal)
        self.thick_slider.setRange(1, 10)
        self.thick_slider.setValue(self.settings['thickness'])
        self.thick_slider.valueChanged.connect(self.change_thickness)
        layout.addWidget(QtWidgets.QLabel("Товщина"))
        layout.addWidget(self.thick_slider)

        # Opacity slider
        self.opacity_slider = QtWidgets.QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(10, 255)
        self.opacity_slider.setValue(int(self.settings['opacity']*255))
        self.opacity_slider.valueChanged.connect(self.change_opacity)
        layout.addWidget(QtWidgets.QLabel("Прозорість"))
        layout.addWidget(self.opacity_slider)

        # Style combo
        self.style_combo = QtWidgets.QComboBox()
        self.style_combo.addItems(['classic','dot','circle','cross+dot','plus-circle'])
        self.style_combo.setCurrentText(self.settings['style'])
        self.style_combo.currentTextChanged.connect(self.change_style)
        layout.addWidget(QtWidgets.QLabel("Стиль прицілу"))
        layout.addWidget(self.style_combo)

        # Center dot checkbox
        self.center_dot_cb = QtWidgets.QCheckBox("Центральна точка")
        self.center_dot_cb.setChecked(self.settings['center_dot'])
        self.center_dot_cb.stateChanged.connect(self.toggle_center_dot)
        layout.addWidget(self.center_dot_cb)

        # Hotkey
        layout.addWidget(QtWidgets.QLabel("Гаряча клавіша для показу/сховання:"))
        self.hotkey_edit = QtWidgets.QLineEdit()
        self.hotkey_edit.setText(self.settings.get('hotkey', '+'))
        layout.addWidget(self.hotkey_edit)
        hotkey_btn = QtWidgets.QPushButton("Застосувати гарячу клавішу")
        layout.addWidget(hotkey_btn)

        def set_hotkey():
            new_key = self.hotkey_edit.text().strip()
            if not new_key:
                return
            try:
                keyboard.unhook_all_hotkeys()
                keyboard.add_hotkey(new_key, lambda: self.overlay.toggle_active())
                self.settings['hotkey'] = new_key
                QtWidgets.QMessageBox.information(self, "Гаряча клавіша",
                                                  f"Гаряча клавіша встановлена: {new_key}")
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, "Помилка",
                                              f"Не вдалося встановити гарячу клавішу: {e}")

        hotkey_btn.clicked.connect(set_hotkey)

        # Save button
        save_btn = QtWidgets.QPushButton("Зберегти налаштування")
        save_btn.clicked.connect(self.save_settings)
        layout.addWidget(save_btn)

        # Visibility button
        vis_btn = QtWidgets.QPushButton("Показати/Сховати (гаряча клавіша: +)")
        vis_btn.clicked.connect(self.overlay.toggle_active)
        layout.addWidget(vis_btn)

        # Close button
        close_btn = QtWidgets.QPushButton("Закрити")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

        self.setLayout(layout)
        self.setFixedSize(320, 500)

    def pick_color(self):
        initial = QtGui.QColor(*self.settings['color'])
        col = QtWidgets.QColorDialog.getColor(initial, self, "Виберіть колір прицілу")
        if col.isValid():
            self.settings['color'] = (col.red(), col.green(), col.blue())
            self.overlay.update()

    def change_size(self, v):
        self.settings['size'] = v
        self.overlay.update()

    def change_gap(self, v):
        self.settings['gap'] = v
        self.overlay.update()

    def change_thickness(self, v):
        self.settings['thickness'] = v
        self.overlay.update()

    def change_opacity(self, v):
        self.settings['opacity'] = v / 255.0
        self.overlay.update()

    def change_style(self, s):
        self.settings['style'] = s
        self.overlay.update()

    def toggle_center_dot(self, state):
        self.settings['center_dot'] = bool(state)
        self.overlay.update()

    def save_settings(self):
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(self.settings, f, indent=4)
        QtWidgets.QMessageBox.information(self, "Збережено", "Налаштування прицілу збережено.")


# --- Main ---
def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {
        'color': (0, 255, 0),
        'size': 30,
        'gap': 4,
        'thickness': 3,
        'opacity': 0.9,
        'style': 'classic',
        'center_dot': True,
        'hotkey': '+',
    }

def main():
    settings = load_settings()
    app = QtWidgets.QApplication(sys.argv)
    overlay = OverlayWindow(settings)
    settings_win = SettingsWindow(overlay, settings)
    settings_win.move(50, 50)
    settings_win.show()

    # Register hotkey at startup
    try:
        keyboard.add_hotkey(settings.get('hotkey', '+'), lambda: overlay.toggle_active())
    except Exception as e:
        print("Не вдалося зареєструвати гарячу клавішу. Спробуйте запустити від імені адміністратора.", e)

    def on_quit():
        try:
            keyboard.unhook_all_hotkeys()
        except:
            pass

    app.aboutToQuit.connect(on_quit)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
