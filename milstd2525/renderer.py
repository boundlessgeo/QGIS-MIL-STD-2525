# -*- coding: utf-8 -*-

"""
***************************************************************************
    renderer.py
    ---------------------
    Date                 : December 2015
    Copyright            : (C) 2015-2016, 2018 Boundless, 2019 Planet Inc.
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""
from __future__ import absolute_import

__author__ = 'Planet Federal'
__date__ = 'September 2019'
__copyright__ = '(C) 2015-2016, 2018 Boundless, ' \
                '2019 Planet Inc, https://planet.com'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os

from qgis.PyQt import uic

from qgis.core import QgsFeatureRenderer 
from qgis.core import QgsRendererAbstractMetadata 
# from qgis.core import QgsMarkerSymbol
# from qgis.core import QgsSymbol
from qgis.gui import QgsRendererWidget
from qgis.core import QgsFieldProxyModel

from milstd2525.milstd2525symbology import symbolForCode, getDefaultSymbol


pluginPath = os.path.dirname(__file__)

WIDGET, BASE = uic.loadUiType(
    os.path.join(pluginPath, 'ui', 'milstd2525rendererwidgetbase.ui'))


class MilStd2525Renderer(QgsFeatureRenderer):
    def __init__(self, size=40, field='', context=None):
        QgsFeatureRenderer.__init__(self, 'MilStd2525Renderer')
        self.field = field
        self.size = int(size)
        self._defaultSymbol = getDefaultSymbol(int(size))
        self.cached = {}
        self.context = context

    def symbolForFeature(self, feature, context):
        idx = feature.fieldNameIndex(self.field) \
            if self.field is not None else -1
        if idx != -1:
            code = feature.attributes()[idx]
            if code not in self.cached:
                symbol = symbolForCode(code, self.size)
                if symbol is None:
                    self.cached[code] = self._defaultSymbol
                else:
                    self.cached[code] = symbol.clone()
            # Should be done in startRender, but new symbols unavialable there
            self.cached[code].startRender(context)
            return self.cached[code]
        else:
            return self._defaultSymbol

    def startRender(self, context=None, fields=None):
        self.context = context
        # This is handled in symbolForFeature for cached symbols
        # for k in list(self.cached.keys()):
        #     self.cached[k].startRender(context=context, fields=fields)
        self._defaultSymbol.startRender(context=context, fields=fields)
        super().startRender(context=context, fields=fields)

    def stopRender(self, context=None):
        for s in list(self.cached.values()):
            s.stopRender(context)
        self._defaultSymbol.stopRender(context)
        super().stopRender(context)

    def usedAttributes(self, context):
        return [self.field]

    def symbols(self, context):
        return list(self.cached.values())

    def clone(self):
        r = MilStd2525Renderer(
            size=self.size, field=self.field, context=self.context)
        r.cached = self.cached
        return r

    def save(self, doc, context):
        elem = doc.createElement('renderer-v2')
        elem.setAttribute('type', 'MilStd2525Renderer')
        elem.setAttribute('size', self.size)
        elem.setAttribute('field', self.field)
        return elem

    # noinspection PyUnusedLocal,PyMethodMayBeStatic
    def load(self, symbology_elem, context):
        size = int(symbology_elem.attribute('size'))
        field = symbology_elem.attribute('field')
        r = MilStd2525Renderer(size=size, field=field, context=context)
        return r


# noinspection PyPep8Naming
class MilStd2525RendererWidget(QgsRendererWidget, WIDGET):
    def __init__(self, layer, style, renderer):
        super(MilStd2525RendererWidget, self).__init__(layer, style)
        self.setupUi(self)

        if renderer is None or renderer.type() != 'MilStd2525Renderer':
            fields = [f.name() for f in layer.dataProvider().fields()]
            if fields:
                field = fields[0]
            else:
                field = None
            self.r = MilStd2525Renderer(field=field)
        else:
            self.r = renderer.clone()

        self.cmbField.setLayer(layer)
        self.cmbField.setFilters(QgsFieldProxyModel.String)

        self.spnSize.setValue(self.r.size)

        self.cmbField.fieldChanged.connect(self.fieldChanged)
        self.spnSize.valueChanged[float].connect(self.sizeChanged)

    def sizeChanged(self, value):
        self.r.size = value

    def fieldChanged(self):
        self.r.field = self.cmbField.currentText()

    def renderer(self):
        return self.r


class MilStd2525RendererMetadata(QgsRendererAbstractMetadata):
    def __init__(self):
        QgsRendererAbstractMetadata.__init__(
            self, 'MilStd2525Renderer', 'MIL-STD-2525 renderer')

    def createRenderer(self, element, context):
        size = int(element.attribute('size'))
        field = element.attribute('field')
        # print(size, field)
        return MilStd2525Renderer(size=size, field=field, context=context)

    def createRendererWidget(self, layer, style, renderer):
        return MilStd2525RendererWidget(layer, style, renderer)
