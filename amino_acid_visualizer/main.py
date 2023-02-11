import math
import random
from datetime import datetime
from PySide6 import QtWidgets, QtCore
from PySide6.QtCore import QSize
from pikachu.general import svg_from_smiles, highlight_subsmiles_multiple
from rdkit import Chem
from rdkit.Chem.Descriptors import ExactMolWt
import sys
from PySide6.QtWidgets import QMainWindow, QLabel, QWidget, QVBoxLayout, QGridLayout, QPushButton, \
    QLineEdit, QMessageBox, QHBoxLayout, QFileDialog
from PySide6.QtCore import Qt
from PySide6.QtSvgWidgets import QSvgWidget

svg = open('./venv/Lib/site-packages/pikachu/smiles/smiles.py', "rt")
data = svg.read()
data = data.replace("'p', 's'", "'p', 's', 'Se'")
svg.close()

svg = open('./venv/Lib/site-packages/pikachu/smiles/smiles.py', "wt")
svg.write(data)
svg.close()

acceptable_acids = "RHKDESTNQCUGPAVILMFYW"
amino_acids_full = {"R": "Arginine", "H": "Histidine", "K": "Lysine", "D": "Aspartic Acid", "E": "Glutamic Acid",
                    "S": "Serine", "T": "Threonine", "N": "Asparagine", "Q": "Glutamine", "C": "Cysteine",
                    "U": "Selenocysteine", "G": "Glycine", "P": "Proline", "A": "Alanine", "V": "Valine",
                    "I": "Isoleucine", "L": "Leucine", "M": "Methionine", "F": "Phenylalanine", "Y": "Tyrosine",
                    "W": "Tryptophan"}
amino_acids = {}

for acid in acceptable_acids:
    r = lambda: random.randint(0, 255)
    amino_acids[acid] = '#%02X%02X%02X' % (r(), r(), r())


def is_valid_sequence_string(sequence_string):
    for acid in sequence_string:
        if acid not in acceptable_acids:
            return False

    return True


def get_smiles_from_sequence(sequence_string):
    if "U" in sequence_string:

        new_sequence_string = ""

        non_metals = []

        # Sulfur - 0, Selenium - 1
        for i, acid in enumerate(sequence_string):

            if acid == "C":
                non_metals.append(0)
                new_sequence_string += acid
            elif acid == "M":
                non_metals.append(0)
                new_sequence_string += acid
            elif acid == "U":
                non_metals.append(1)
                new_sequence_string += "C"
            else:
                new_sequence_string += acid

        smiles = Chem.MolToSmiles(Chem.MolFromSequence(new_sequence_string))
        new_smiles = ""
        iterator = 0

        for ch in smiles:
            if ch == "S":
                if non_metals[iterator]:
                    new_smiles += "[Se]"
                else:
                    new_smiles += "S"

                iterator += 1
            else:
                new_smiles += ch

        return new_smiles

    else:
        return Chem.MolToSmiles(Chem.MolFromSequence(sequence_string))


def generate_structural_pattern(sequence_string):
    print(get_smiles_from_sequence(sequence_string))
    svg_from_smiles(get_smiles_from_sequence(sequence_string), "structural_pattern.svg")


def generate_structural_pattern_with_highlights(sequence_string):
    subsmiles = []
    subsmiles_colors = []

    for acid in sequence_string:
        smile = get_smiles_from_sequence(acid)
        subsmiles.append(smile)
        subsmiles_colors.append(amino_acids[acid])

    highlight_subsmiles_multiple(sorted(subsmiles, key=len), "".join(subsmiles), colours=subsmiles_colors,
                                 visualisation='svg', out_file='structural_pattern_with_highlights.svg')

    svg = open('structural_pattern_with_highlights.svg', "rt")
    data = svg.read()
    data = data.replace('style="fill: #ffffff', 'style="fill: transparent')
    svg.close()

    svg = open('structural_pattern_with_highlights.svg', "wt")
    svg.write(data)
    svg.close()


def get_molecular_mass(sequence_string):
    selenocysteine_counter = 0

    for ch in sequence_string:
        if ch == "U":
            selenocysteine_counter += 1

    sequence_string = sequence_string.replace("U", "")

    return ExactMolWt(Chem.MolFromSequence(sequence_string)) + (168.05 * selenocysteine_counter)


# -------------------------------------------------------------------------------------------------------------------------------------------------------

class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()

        self.setWindowTitle("Structural Pattern")
        self.setFixedSize(QSize(600, 400))

        self.sequence = QLineEdit()
        self.sequence.setPlaceholderText("Provide Sequence")

        self.mainLayout = QVBoxLayout()
        self.mainLayout.addWidget(self.sequence)

        self.acidButtons = QGridLayout()

        for i, acid in enumerate(acceptable_acids):
            button = QPushButton(acid)

            button.pressed.connect(lambda a=acid: self.addAcid(a))

            self.acidButtons.addWidget(button, math.floor(i / 7), i - (7 * math.floor(i / 7)))

        self.mainLayout.addLayout(self.acidButtons)

        self.generateButton = QPushButton("Generate")
        self.generateButton.pressed.connect(self.displayStructuralPattern)
        self.mainLayout.addWidget(self.generateButton)

        self.svgLayout = QHBoxLayout()
        self.mainLayout.addLayout(self.svgLayout)

        self.mass = QLabel("")
        self.mass.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.mainLayout.addWidget(self.mass)

        self.saveButton = QPushButton("Save Svgs")
        self.saveButton.setHidden(True)
        self.mainLayout.addWidget(self.saveButton)

        self.mainLayout.addStretch()

        widget = QWidget()
        widget.setLayout(self.mainLayout)
        self.setCentralWidget(widget)

    def addAcid(self, acid):
        self.sequence.setText(self.sequence.text() + acid)

    def raiseError(self, message):
        self.error = True
        QMessageBox.critical(None, 'Error!', message, QMessageBox.Ok)

    def showSvg(self, file, sequence_string=None):
        svg = QSvgWidget(file)
        svg.renderer().setAspectRatioMode(Qt.KeepAspectRatio)

        layout = QHBoxLayout()
        layout.addWidget(svg, 90)

        if sequence_string:
            legend = QVBoxLayout()

            for acid in amino_acids:
                if acid in sequence_string:
                    legend_item = QHBoxLayout()

                    color = QLabel("")
                    color.setFixedSize(25, 25)
                    color.setStyleSheet("background-color: " + amino_acids[acid])
                    legend_item.addWidget(color)

                    name = QLabel(acid + " - " + amino_acids_full[acid])
                    legend_item.addWidget(name)

                    legend.addLayout(legend_item)

            legend.addStretch()
            layout.addLayout(legend, 10)

        self.win = QWidget()
        self.win.setWindowTitle('Svg Preview')
        self.win.setLayout(layout)
        self.win.showMaximized()

    def saveSvgs(self):
        directory = QFileDialog().getExistingDirectory(self, "Select directory")

        svg = open('structural_pattern.svg', "rt")
        data = svg.read()
        svg.close()

        new_svg = open(directory + "/" + str(datetime.now().strftime("%d_%m_%Y_%H_%M_%S_")) + ".svg", "x")
        new_svg.write(data)
        new_svg.close()

        svgH = open('structural_pattern_with_highlights.svg', "rt")
        data = svgH.read()
        svgH.close()

        new_svgH = open(directory + "/H" + str(datetime.now().strftime("%d_%m_%Y_%H_%M_%S")) + ".svg", "x")
        new_svgH.write(data)
        new_svgH.close()

    def displayStructuralPattern(self):
        self.error = False

        # for acid, color in amino_acids.items():
        #     print(acid + " - " + color)

        sequence = self.sequence.text()

        if sequence:

            try:
                generate_structural_pattern(sequence)
                generate_structural_pattern_with_highlights(sequence)
            except:
                self.raiseError("This is invalid sequence!")

            if not self.error:

                while self.svgLayout.count() > 0:
                    self.svgLayout.itemAt(0).widget().setParent(None)

                svg = QSvgWidget("structural_pattern.svg")
                svg.renderer().setAspectRatioMode(Qt.KeepAspectRatio)
                svg.mouseReleaseEvent = lambda event: self.showSvg("structural_pattern.svg")
                self.svgLayout.addWidget(svg, 50)

                svgH = QSvgWidget("structural_pattern_with_highlights.svg")
                svgH.renderer().setAspectRatioMode(Qt.KeepAspectRatio)
                svgH.mouseReleaseEvent = lambda event: self.showSvg("structural_pattern_with_highlights.svg", sequence)
                self.svgLayout.addWidget(svgH, 50)

                self.saveButton.setHidden(False)
                self.saveButton.pressed.connect(self.saveSvgs)

                self.mass.setText("Mass: " + str(round(get_molecular_mass(sequence), 5)))
        else:
            self.raiseError("Please Provide Sequence!")


if not QtWidgets.QApplication.instance():
    app = QtWidgets.QApplication(sys.argv)
else:
    app = QtWidgets.QApplication.instance()

window = MainWindow()
window.show()

app.exec()
