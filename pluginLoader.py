#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2014 trgk

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

import os
import sys
import types
from importlib.machinery import SourceFileLoader

# Get absolute path of current executable
if getattr(sys, "frozen", False):
    # frozen
    basepath = os.path.dirname(sys.executable)
else:
    # unfrozen
    basepath = os.path.dirname(os.path.realpath(__file__))


def getGlobalPluginDirectory():
    return os.path.join(basepath, "plugins")


def getPluginPath(pluginName):
    if pluginName[-3:] == ".py" or pluginName[-4:] == ".eps":
        pluginPath = os.path.abspath(pluginName)
    else:
        # Try eps
        pluginPath = os.path.join(basepath, "plugins", "%s.eps" % pluginName)
        if not os.path.exists(pluginPath):
            pluginPath = os.path.join(basepath, "plugins", "%s.py" % pluginName)

    return pluginPath


def empty():
    pass


freeze_enabled = True
prompt_enabled = False
scbank_enabled = False
scbankSettings = None


def isFreezeIssued():
    return freeze_enabled


def isPromptIssued():
    return prompt_enabled


def isSCBankIssued():
    return scbank_enabled


def getSCBankSettings():
    return scbankSettings


def loadPluginsFromConfig(ep, config):
    global freeze_enabled, prompt_enabled, scbank_enabled, scbankSettings

    """ Load plugin from config file """
    pluginList = [name for name in config.keys() if name != "main"]
    if any("unlimiter" in name.casefold() for name in pluginList):
        from eudplib.eudlib.utilf.listloop import _turnUnlimiterOn

        _turnUnlimiterOn()

    pluginFuncDict = {}

    initialDirectory = os.getcwd()
    initialPath = sys.path[:]

    for pluginName in pluginList:
        if pluginName == "freeze":
            if "freeze" in config[pluginName]:
                freeze_enabled = False
                continue
            print("Freeze plugin loaded")
            if "prompt" in config[pluginName]:
                prompt_enabled = True
            continue

        elif pluginName == "SCBank":
            scbank_enabled = True
            print("SCBank plugin loaded")
            SCBankSettings = config[pluginName]
            try:
                msqc_settings = config["MSQC"]
            except KeyError:
                raise Exception("MSQC must be enabled to use SCBank")
            if pluginList.index("SCBank") > pluginList.index("MSQC"):
                raise Exception("SCBank should be written before MSQC")
            try:
                scbank_key = SCBankSettings["key"]
            except (KeyError):
                raise Exception("SCBank key must be provided")
            import base64
            import binascii

            try:
                base64.b64decode(scbank_key)
            except binascii.Error:
                raise Exception("SCBank key must be base64 encoded")
            #from scbank_core import init_settings

            msqc_scbank = init_settings(SCBankSettings)
            msqc_settings.update(msqc_scbank)
            config["MSQC"] = msqc_settings
            continue

        pluginSettings = config[pluginName]

        print("Loading plugin %s..." % pluginName)

        # real python name
        pluginPath = getPluginPath(pluginName)

        try:
            pluginDir = os.path.dirname(pluginPath)
            if pluginDir and pluginDir not in sys.path:
                sys.path.insert(1, os.path.abspath(pluginDir))

            moduleName = os.path.splitext(os.path.basename(pluginPath))[0]
            pluginModule = types.ModuleType(moduleName)
            pluginModule.__dict__["settings"] = pluginSettings

            if pluginPath.endswith(".eps"):
                loader = ep.EPSLoader(moduleName, pluginPath)
            else:
                loader = SourceFileLoader(moduleName, pluginPath)

            pluginModule.__name__ = moduleName
            pluginModule.__loader__ = loader
            sys.modules[moduleName] = pluginModule

            loader.exec_module(pluginModule)

            pluginDict = pluginModule.__dict__

            if pluginDict:
                onPluginStart = pluginDict.get("onPluginStart", empty)
                beforeTriggerExec = pluginDict.get("beforeTriggerExec", empty)
                afterTriggerExec = pluginDict.get("afterTriggerExec", empty)
                pluginFuncDict[pluginName] = (
                    onPluginStart,
                    beforeTriggerExec,
                    afterTriggerExec,
                )

        except (KeyboardInterrupt, SystemExit):
            raise

        except Exception:
            raise RuntimeError('Error loading plugin "%s"' % pluginName)

        finally:
            os.chdir(initialDirectory)
            sys.path[:] = initialPath[:]

    if isFreezeIssued():
        print(
            """\
                          *                                         *
        *                                        *
                        [[ freeze activated ]]
                                  *                       *
                *                                                          *\
"""
        )
    if "freeze" in pluginList:
        pluginList.remove("freeze")
    elif "SCBank" in pluginList:
        pluginList.remove("SCBank")

    return pluginList, pluginFuncDict
