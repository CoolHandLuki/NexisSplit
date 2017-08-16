#!/usr/bin/python3
# -*- coding: utf-8 -*-
# LexisNexis split 2.0
# Author: Lukas Hufnagel-Hadar
# Licensed under the GPLv3: https://www.gnu.org/licenses/gpl-3.0.en.html

import matplotlib
matplotlib.use("Qt5Agg")

import NexisSplit
import sys, codecs

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QFileDialog, QPushButton, QLineEdit, QVBoxLayout, QHBoxLayout, QPlainTextEdit, QSizePolicy

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.pyplot import figure as Figure
    
class MainWindow(QWidget):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.regex = "Dokument\ [0-9]{1,3}\ von\ [0-9]{1,3}"
        self.months = ["Januar","Februar","März","April","Mai","Juni","Juli","August","September","Oktober","November","Dezember"]
        self._corpus = []
        self.currentArticleIndex = 0
        self.initUI()
        
    def initUI(self):
        # Set up the main window's default properties:
        self.setGeometry(100, 100, 800, 300)
        self.setWindowTitle("LexisNexis Split 2.0")
        
        # Add the UI elements to select the corpus files:
        loadFilesButton = QPushButton("Open")
        regexEntryFieldDescriptor = QLabel("Regex<a href=\"https://docs.python.org/3/howto/regex.html\">*</a> to split the corpus to:")
        regexEntryFieldDescriptor.setOpenExternalLinks(True)
        self.regexEntryField = QLineEdit(self.regex)
        monthsEntryFieldDescriptor = QLabel("Comma seperated months:")
        self.monthsEntryField = QLineEdit(", ".join(self.months))
        splitCorpusButton = QPushButton("Split corpus")
        saveArticlesByNumberButton = QPushButton("Save articles by number")
        saveArticlesByDateButton = QPushButton("Save articles by date")
        saveArticlesByMediumButton = QPushButton("Save articles by medium")
        labelCorpusDisplay = QLabel("Current article")
        self.labelDate = QLabel("publication date")
        self.labelMedium = QLabel("medium")
        self.articleDisplay = QPlainTextEdit()
        self.articleDisplay.setReadOnly(True)
        previousButton = QPushButton("<")
        nextButton = QPushButton(">")
        self.articleNumberEntryField = QLineEdit("")
        self.labelArticlesLength = QLabel("")
        plotCorpusButton = QPushButton("Plot corpus")
        
        # Create layouts for the main window and add it's widgets,
        # Left side for loading a corpora, displaying their names, setting
        # a regular expression, splitting the corpora, saving according to
        # date, medium and just in order of loading.
        leftLayout = QVBoxLayout()
        leftLayout.addWidget(loadFilesButton)
        leftLayout.addWidget(regexEntryFieldDescriptor)
        leftLayout.addWidget(self.regexEntryField)
        leftLayout.addWidget(monthsEntryFieldDescriptor)
        leftLayout.addWidget(self.monthsEntryField)
        leftLayout.addWidget(splitCorpusButton)
        leftLayout.addWidget(saveArticlesByNumberButton)
        leftLayout.addWidget(saveArticlesByDateButton)
        leftLayout.addWidget(saveArticlesByMediumButton)
        leftLayout.addWidget(labelCorpusDisplay)
        leftLayout.addWidget(self.labelDate)
        leftLayout.addWidget(self.labelMedium)
        leftLayout.addWidget(self.articleDisplay)
        leftLayout.addWidget(previousButton)
        leftLayout.addWidget(self.articleNumberEntryField)
        leftLayout.addWidget(self.labelArticlesLength)
        leftLayout.addWidget(nextButton)
        
        # Right side for graph and clustering
        self.rightLayout = QVBoxLayout()
        self.rightLayout.addWidget(plotCorpusButton)

        # Combine the layouts into a main layout:
        mainLayout = QHBoxLayout()
        mainLayout.addLayout(leftLayout)
        mainLayout.addLayout(self.rightLayout)
        self.setLayout(mainLayout)
        
        # Define the signals & slots behavior:
        self.regexEntryField.textEdited.connect(self._update_variables)
        self.monthsEntryField.textEdited.connect(self._update_variables)
        loadFilesButton.clicked.connect(self._get_files)
        splitCorpusButton.clicked.connect(self._invoke_splitter)
        saveArticlesByNumberButton.clicked.connect(self._save_articles)
        saveArticlesByDateButton.clicked.connect(self._save_articles)
        saveArticlesByMediumButton.clicked.connect(self._save_articles)
        plotCorpusButton.clicked.connect(self._draw_plot)
        previousButton.clicked.connect(self._set_current_article)
        nextButton.clicked.connect(self._set_current_article)
        self.articleNumberEntryField.returnPressed.connect( \
                                                self._set_current_article)
        
        # Finally, draw mainWindow:
        self.show()

    def _save_articles(self):
        sender = self.sender()
        if "number" in sender.text():
            mode = "byNumber"
        elif "date" in sender.text():
            mode = "byDate"
        elif "medium" in sender.text():
            mode = "byMedium"
        selectSaveLocationDialog = QFileDialog()
        selectSaveLocationDialog.setFileMode(QFileDialog.DirectoryOnly)
        if selectSaveLocationDialog.exec_():
# Save the selection in a list, iterate over it trying to load each
# file through the codecs module to better support UTF-8 encoded files,
# write each corpus to tempCorpus and finally display the result
# in the corpusDisplay widget.
            savePath = selectSaveLocationDialog.selectedFiles()[0]
            self.splitter._save_articles(mode = mode, path = savePath, \
                                    docSeparator = "Dokument 999 von 999")

        
    def _update_variables(self):
        self.regex = self.regexEntryField.text()
        self.months = self.monthsEntryField.text().replace(" ","").split(",")

    def _set_current_article(self):
        sender = self.sender()
        # A reference our sender, so we can do different things based on which
        # made the function call.
        
        if isinstance(sender, QLineEdit):
            if int(sender.text()) - 1 >= 0 and int(sender.text()) -1 < \
            len(self.splitter.articles):
                self.currentArticleIndex = int(sender.text()) - 1
        # From the lineEdit, set the value directly.

        elif isinstance(sender, MainWindow):
            self.currentArticleIndex = 0
        # If we initialize everything from _invoke_splitter(), also set the
        # value directly.
        
        elif isinstance(sender, QPushButton):
            if sender.text() == "<":
                if self.currentArticleIndex == 0:
                    pass
                else:
                    self.currentArticleIndex -= 1
            elif sender.text() == ">":
                if self.currentArticleIndex >= len(self.splitter.articles) - 1:
                    pass
                else:
                    self.currentArticleIndex += 1
        # Move forward and backward through our corpus.

        article = self.splitter.articles[self.currentArticleIndex]
        self.labelDate.setText(article.date)
        self.labelMedium.setText(article.medium)
        self.articleDisplay.clear()
        for line in article.text:
            self.articleDisplay.appendPlainText(line)
        self.articleDisplay.verticalScrollBar().setValue(0)
        self.articleNumberEntryField.setText(str(self.currentArticleIndex + 1))
        # Lastly, update all the widgets
        
    def _draw_plot(self):
        if hasattr(self, "plotCanvas"):
            self.rightLayout.removeWidget(self.plotCanvas)
        # Try and delete already exisiting widgets or they will multiply.

        self.plotCanvas = MplCanvas(self.splitter.df["articles"], \
                                        parent=self)
        self.rightLayout.addWidget(self.plotCanvas)
        
    def _invoke_splitter(self):
        self.splitter = NexisSplit.LexisNexisSplitter(self.regex,\
                                           self._corpus, self.months)
        self.splitter._split_corpus()
        self.labelArticlesLength.setText("/ " + \
                                         str(len(self.splitter.articles)))
        self._set_current_article()
        self.splitter._group_articles_by_date()
        self.splitter._group_articles_by_medium()
        self.splitter._prepare_frequency_plotting()
        
    def _get_files(self):
        # Create an empty pseudo file for two reasons:
        # 1. In order to be able to pass a file instead of an string to
        #    NexisSplit() [to make NexisSplit usable as a class by itself] and
        # 2. Do it here instead of globally, so that we overwrite previously
        #    imported content and thus don't run the risk of importing files
        #    twice into our corpus.
        self.corpus = []

        # Create a dialog to select our corpus files.
        selectCorpusDialog = QFileDialog()
        selectCorpusDialog.setFileMode(QFileDialog.ExistingFiles)
        if selectCorpusDialog.exec_():
            
        # Save the selection in a list, iterate over it trying to load each
        # file through the codecs module to better support UTF-8 encoded files,
        # write each corpus to tempCorpus and finally display the result
        # in the corpusDisplay widget.
            self.articleDisplay.clear()
            pathsToCorpora = selectCorpusDialog.selectedFiles()
            for pathToCorpus in pathsToCorpora:
                # We need to append line by line instead of just setting
                # QPlainTextEdit.setText or '\r\n' will be everywhere.
                with codecs.open(pathToCorpus, "r") as f:
                    # for line in f.readlines():
                    #    self.tempCorpus.append(line)
                    #    self.corpusDisplay.appendPlainText(line)
                    self._corpus.extend(f.readlines())
                    self.articleDisplay. \
                        appendPlainText(pathToCorpus.split("/")[-1])   

class MplCanvas(FigureCanvas):
    def __init__(self, articlesPerDayDF, parent=None):
        self.fig = Figure()
        super(MplCanvas, self).__init__(self.fig)
        self.setParent(parent)
        FigureCanvas.setSizePolicy(self, QSizePolicy.Expanding, \
                                   QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)        
        self.axes = self.fig.add_subplot(111)
        self.axes.plot(articlesPerDayDF)

def main():
    app = QApplication(sys.argv)
    mw = MainWindow()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
