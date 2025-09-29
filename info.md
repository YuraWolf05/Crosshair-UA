Name ReticleX

pyqt5\Scripts\activate  
python "B:\Games\ReticleX UA\ReticleX UA.py"
pyinstaller --onefile --noconsole "B:\Games\ReticleX UA\ReticleX UA.py"
pyinstaller --onefile --noconsole --icon=ReticleX.ico "B:\Games\ReticleX UA\ReticleX UA.py"

python -m venv pyqt5
pyqt5\Scripts\activate
python -m pip install --upgrade pip
pip install PyQt5
pip install pyinstaller
pip install keyboard
