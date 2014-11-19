from Qt import loadUiType
import os

uidir = os.path.dirname(os.path.realpath(__file__))
Ui_displayBox,          base = loadUiType(uidir + '/displayBox.ui')
Ui_ExperimentDialog,    base = loadUiType(uidir + '/experimentDialog.ui')
Ui_FileModeDialog,      base = loadUiType(uidir + '/fileModeDialog.ui')
Ui_ModelProperties,     base = loadUiType(uidir + '/modelProperties.ui')
Ui_PattersonProperties, base = loadUiType(uidir + '/pattersonProperties.ui')
Ui_PreferencesDialog,   base = loadUiType(uidir + '/preferencesDialog.ui')
Ui_SelectIndexDialog,   base = loadUiType(uidir + '/selectIndexDialog.ui')
Ui_SizingWidget,        base = loadUiType(uidir + '/sizingWidget.ui')
Ui_TagsDialog,          base = loadUiType(uidir + '/tagsDialog.ui')
