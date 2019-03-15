#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Louis Mueller
University of Minnesota UAV Lab

"""

import os.path
import numpy as np


def ParseAll(loadPathVsp, aircraftName, aeroName):


    loadVspAircraft = os.path.join(loadPathVsp, aircraftName)
    loadVspAero = os.path.join(loadVspAircraft, aeroName)
    loadVspParasiteDrag = os.path.join(loadVspAircraft, aircraftName + '_ParasiteDrag')

    # Parse VSP data
    vspData = {}
    vspData['stab'] = VspStab(loadVspAero)
    vspData['stabTab'] = Stab2Tables(vspData['stab'])

    vspData['history'] = VspHistory(loadVspAero)
    vspData['histTab'] = Hist2Tables(vspData['history'])

    vspData['drag'] = VspParasiteDrag(loadVspParasiteDrag)

    # Add the Parasite Drag to Stab data
    vspData['stab']['coef']['CD']['Base_Aero'] += vspData['drag']['Total']
    vspData['stabTab']['coef']['CD']['Base_Aero'] += vspData['drag']['Total']

    return(vspData)


#%% Parse the ParasiteDrag file into a Dictionary
def VspParasiteDrag(fileLoad):
    # In:
    # fileLoad  -  filePath generated by OpenVSP

    # Out:
    # vspDrag - Parsed data dictionary

    #%% Open File
    if '.csv' not in fileLoad:
        fileLoad = fileLoad + '.csv'

    file = open(fileLoad, "r", errors='ignore')

    fileList = [line.rstrip('\n') for line in file]

    file.close()

    #%% Just read the Totals line
    for iLine, currentLine in enumerate(fileList):
        if 'Totals:' in currentLine:
            totalLineSplit = currentLine.replace(',','').split()

    vspDrag = {}
    vspDrag['Total'] = float(totalLineSplit[2])

    #%%
    return(vspDrag)



#%% Parse the .stab file into a Dictionary
def VspStab(fileLoad):
    # In:
    # fileLoad  - filePath generated by OpenVSP, this

    # Out:
    # vspStab - Parsed data dictionary

    #%% Open File
    if '.stab' not in fileLoad:
        fileLoad = fileLoad + '.stab'

    file = open(fileLoad, "r")

    fileList = [line.rstrip('\n') for line in file]

    file.close()

    #%% Parse to determine parameters, First Pass
    # Find the top of each case
    iNameList = []
    iCaseList = []
    iDerivList = []
    iCoefList = []
    iResultList = []
    for iLine, currentLine in enumerate(fileList):
        if '# Name' in currentLine:
            iNameList.append(iLine)
        if 'Case' in currentLine:
            iCaseList.append(iLine)
        if 'Derivative:' in currentLine:
            iDerivList.append(iLine)
        if 'Coef' in currentLine:
            iCoefList.append(iLine)
        if '# Result' in currentLine:
            iResultList.append(iLine)

    # Case Condition Names
    condParamList = []
    for currentLine in fileList[(iNameList[0]+1) : (iCaseList[0]-2)]:
        if ('#' not in currentLine):
            condParamList.append(currentLine.split()[0])

    # Result Condition Names
    resultParamList = []
    for currentLine in fileList[(iResultList[0]+1) : (iResultList[0]+3)]:
        if ('#' not in currentLine):
            resultParamList.append(currentLine.split()[0])

    # Coeficient Section Names
    coefNameList = fileList[iCaseList[0]].split()[3:] # Get the Coeficient Names

    coefDepNameList = [] # Get the Dependents Names
    for currentLine in fileList[(iCaseList[0]+2) : (iDerivList[0]-2)]:
        currentLineSplit = currentLine.split()
        if ('#' not in currentLine) and ('+' not in currentLineSplit[0]):
            coefDepNameList.append(currentLineSplit[0])

    # Derivative Section Names
    derivNameList = coefNameList # Coef and Deriv Names are the Same
    derivDepNameList = fileList[iCoefList[0]].split()[1:] # Get the Dependant Variable Names for the Deriv Section


    #%% Initialize Dictionaries to store data
    numCase = len(iNameList)

    caseParam = {} # Case Parameter Dictionary
    for condParamName in condParamList:
        caseParam[condParamName] = np.full(numCase, np.nan) # Initialize

    resultParam = {} # Results Parameter Dictionary
    for resultParamName in resultParamList:
        resultParam[resultParamName] = np.full(numCase, np.nan) # Initialize

    coefTable = {}
    for coefParam in coefNameList:
        coefTable[coefParam] = {}
        for coefDepName in coefDepNameList:
            coefTable[coefParam][coefDepName] = np.full(numCase, np.nan) # Initialize

    derivTable = {}
    for derivParam in derivNameList:
        derivTable[derivParam] = {}
        for derivDepName in derivDepNameList:
            derivTable[derivParam][derivDepName] = np.full(numCase, np.nan) # Initialize


    #%% Parse the Data into the Dictionaries
    for iCase in range(0, numCase):
        # Condition Range
        for currentLine in (fileList[(iNameList[iCase]+1) : (iCaseList[iCase]-2)]):
            caseParam[currentLine.split()[0]][iCase] = float(currentLine.split()[1])

        # Results Range
        for currentLine in (fileList[(iResultList[iCase]+1) : (iResultList[iCase]+3)]):
            resultParam[currentLine.split()[0]][iCase] = float(currentLine.split()[1])

        # Coeficients Range, Stability Section
        for currentLine in (fileList[(iCaseList[iCase]+2) : (iCaseList[iCase]+9)]):
            coefDepName = currentLine.split()[0]
            dataVec = currentLine.split()[3:]
            for iCoef, coefName in enumerate(coefNameList):
                coefTable[coefName][coefDepName][iCase] = float(dataVec[iCoef])

        # Coeficients Range, Control Section
        for currentLine in (fileList[(iCaseList[iCase]+9) : (iDerivList[iCase]-2)]):
            coefDepName = currentLine.split()[0]
            dataVec = currentLine.split()[3:]
            for iCoef, coefName in enumerate(coefNameList):
                coefTable[coefName][coefDepName][iCase] = float(dataVec[iCoef])

        # Derivatives Range
        for currentLine in (fileList[(iDerivList[iCase]+6) : (iResultList[iCase]-3)]):
            coefName = currentLine.split()[0]
            dataVec = currentLine.split()[1:]
            for iDep, coefDepName in enumerate(derivDepNameList):
                derivTable[coefName][coefDepName][iCase] = float(dataVec[iDep])


    #%% Return
    vspStab = {}

#    vspStab['condKeys'] = condParamList
#    vspStab['resultKeys'] = resultParamList
#
#    vspStab['coefKeys'] = coefNameList
#    vspStab['coefDepKeys'] = coefDepNameList
#
#    vspStab['derivKeys'] = derivNameList
#    vspStab['derivDepKeys'] = derivDepNameList

    vspStab['cond'] = caseParam
    vspStab['results'] = resultParam
    vspStab['coef'] = coefTable
    vspStab['deriv'] = derivTable
    vspStab['surfNames'] = coefDepNameList[7:]

    return(vspStab)

#%% Transform the Flat VSP Data into table form
def Stab2Tables(vspStab):
    vspTable = {}

    # Leverage the fact that VSP cases are run varying alpha, then mach, then beta
    vspTable['tableDef'] = {}
    vspTable['tableDef']['brkPtVars'] = ['Beta_', 'Mach_', 'AoA_']
    vspBrkNames = ['BetaBrkPts_', 'MachBrkPts_', 'AoABrkPts_']

    # Breakpoints
    for iBreak, vspBrk in enumerate(vspTable['tableDef']['brkPtVars']):
        vspTable['tableDef'][vspBrkNames[iBreak]] = np.unique(vspStab['cond'][vspBrk])

    # Define the shape of the Aero Tables
    shapeTable = (len(vspTable['tableDef']['BetaBrkPts_']), len(vspTable['tableDef']['MachBrkPts_']), len(vspTable['tableDef']['AoABrkPts_']))


    # Create the Condition Tables
    vspTable['cond'] = {}
    for cond in vspStab['cond'].keys():
        vspTable['cond'][cond] = vspStab['cond'][cond].reshape(shapeTable)

    # Create the Coefficient Tables
    vspTable['coef'] = {}
    for coef in vspStab['coef'].keys():
        vspTable['coef'][coef] = {}
        for dep in vspStab['coef'][coef].keys():
            vspTable['coef'][coef][dep] = vspStab['coef'][coef][dep].reshape(shapeTable)

    # Create the Derivative Tables
    vspTable['deriv'] = {}
    for deriv in vspStab['deriv'].keys():
        vspTable['deriv'][deriv] = {}
        for dep in vspStab['deriv'][deriv].keys():
            vspTable['deriv'][deriv][dep] = vspStab['deriv'][deriv][dep].reshape(shapeTable)

    # Create the Results Tables
    vspTable['results'] = {}
    for results in vspStab['results'].keys():
        vspTable['results'][results] = vspStab['results'][results].reshape(shapeTable)

    return (vspTable)


#%% Parse the .adb.cases file into a Dictionary
def VspCases(fileLoad):
    # In:
    # fileLoad  - .adb.cases filePath generated by OpenVSP

    # Out:
    # vspCases - Parsed data dictionary

    #%% Open File
    if '.adb.cases' not in fileLoad:
        fileLoad = fileLoad + '.adb.cases'

    file = open(fileLoad, "r")

    caseList = [line.rstrip('\n') for line in file]

    file.close()

    #%% Parse to determine parameters, First Pass
    numCase = len(caseList)

    mach_nd = np.full(numCase, np.nan)
    alpha_deg = np.full(numCase, np.nan)
    beta_deg = np.full(numCase, np.nan)
    caseDesc = []

    for iCase, case in enumerate(caseList):
        caseSplit = case.split()
        mach_nd[iCase] = caseSplit[0]
        alpha_deg[iCase] = caseSplit[1]
        beta_deg[iCase] = caseSplit[2]
        caseDesc.append(' '.join(case.split()[3:]))

    # Get the Case index of all the 'Base Aero' Cases
    iBase = [i for i, e in enumerate(caseDesc) if e == 'Base Aero']

    # Stuff into Dictionary
    vspCases = {}
    vspCases['mach_nd'] = mach_nd
    vspCases['alpha_deg'] = alpha_deg
    vspCases['beta_deg'] = beta_deg
    vspCases['desc'] = caseDesc
    vspCases['caseBase'] = iBase

    #%%
    return(vspCases)


#%% Parse the .history file into a Dictionary
def VspHistory(fileLoad):
    # In:
    # fileLoad  - .history filePath generated by OpenVSP

    # Out:
    # vspHist - Parsed data dictionary

    vspCases = VspCases(fileLoad)

    #%% Open File
    if '.history' not in fileLoad:
        fileLoad = fileLoad + '.history'

    file = open(fileLoad, "r")

    fileList = [line.rstrip('\n') for line in file]

    file.close()

    #%% Parse to determine parameters, First Pass
    # Find the top of each case
    iNameList = []
    iCaseList = []
    iFrictList = []
    for iLine, currentLine in enumerate(fileList):
        if '# Name' in currentLine:
            iNameList.append(iLine)
        if 'Solver Case:' in currentLine:
            iCaseList.append(iLine)
        if 'Skin Friction Drag Break Out:' in currentLine:
            iFrictList.append(iLine)

    # Case Condition Names
    condParamList = []
    for currentLine in fileList[(iNameList[0]+1) : (iCaseList[0]-1)]:
        if (not currentLine == ''):
            condParamList.append(currentLine.split()[0])

    # Coeficient Section Names
    resultNameList = fileList[iCaseList[0]+2].replace('/', '_').split() # Get the Coeficient Names


    for currentLine in fileList[(iCaseList[0]+3) : (iFrictList[0]-1)]:
        if (not currentLine == ''):
            currentLineSplit = currentLine.split()

    # Pull off the final iteration(s)
    numIter = int(currentLineSplit[0])


    #%% Initialize Dictionaries to store data, only want the Base Cases
    numCase = len(iCaseList)
    iBase = vspCases['caseBase']
    numCaseBase = len(iBase)

    vspHist = {}

    # Pre-Allocate Conditions
    vspHist['cond'] = {}
    for cond in condParamList:
        vspHist['cond'][cond] = np.full(numCase, np.nan)

    # Pre-Allocate Results
    vspHist['results'] = {}
    for result in resultNameList:
        vspHist['results'][result] = np.full((numCase, numIter), np.nan)


    # Store Data only for the last iteration
    for iCase in range(0, numCase):
        # Store the Conditions
        for currentLine in fileList[(iNameList[iCase]+1) : (iCaseList[iCase]-1)]:
            if (not currentLine == ''):
                lineSplit = currentLine.split()
                vspHist['cond'][lineSplit[0]][iCase] = lineSplit[1]

        # Store the Results
        for iIter, resultLine in enumerate(fileList[(iCaseList[iCase]+3) : (iCaseList[iCase]+3+numIter)]):
            for iRes, res in enumerate(resultNameList):
                resultSplit = resultLine.split()
                vspHist['results'][res][iCase][iIter] = resultSplit[iRes]


    # Add the Control Group Deflections to the Conditions
    numCtrlGroup = int(numCase / numCaseBase - 8) # There are 8 pre-defined conditions already
    ControlGroup = []
    for iCtrlGroup in range(0,numCtrlGroup):
      indx = [i for i, e in enumerate(vspCases['desc']) if e == 'Deflecting Control Group: %d' %(iCtrlGroup+1)]
      ControlGroup.append(indx)

      vspHist['cond']['ConGrp_%d' %(iCtrlGroup+1)] = np.full(numCase, 0.0)
      vspHist['cond']['ConGrp_%d' %(iCtrlGroup+1)][indx] = 1.0

    #%% Return
    vspHist['desc'] = vspCases['desc']
    return(vspHist)

#%% Transform the Flat VSP Data into table form
def Hist2Tables(vspHist, indxAvg=1):
    vspTable = {}

    # Leverage the fact that VSP cases are run varying alpha, then mach, then beta
    vspTable['tableDef'] = {}
    vspTable['tableDef']['brkPtVars'] = ['Beta_', 'Mach_', 'AoA_']
    vspBrkNames = ['BetaBrkPts_', 'MachBrkPts_', 'AoABrkPts_']

    # Breakpoints in the Base Aer
    iBase = [i for i, e in enumerate(vspHist['desc']) if e == 'Base Aero']

    for iBreak, vspBrk in enumerate(vspTable['tableDef']['brkPtVars']):
        vspTable['tableDef'][vspBrkNames[iBreak]] = np.unique(vspHist['cond'][vspBrk][iBase])


    # Define the shape of the Aero Tables
    shapeTable = (len(vspTable['tableDef']['BetaBrkPts_']), len(vspTable['tableDef']['MachBrkPts_']), len(vspTable['tableDef']['AoABrkPts_']))


    # Find the idices of each type of run
    runTypes = list(np.unique(vspHist['desc']))
    indxTypes = {}
    for runType in runTypes:
        indxTypes[runType] = [i for i, e in enumerate(vspHist['desc']) if e == runType]

    # Create the Condition Tables
    vspTable['cond'] = {}
    for cond in vspHist['cond'].keys():
        vspTable['cond'][cond] = {}
        for runType in runTypes:
            vspTable['cond'][cond][runType] = vspHist['cond'][cond][indxTypes[runType]].reshape(shapeTable)

    # Create the Coefficient Tables
    vspTable['results'] = {}
    for results in vspHist['results'].keys():
        vspTable['results'][results] = {}
        for runType in runTypes:
            valRaw = vspHist['results'][results][indxTypes[runType]]
            valMean = valRaw[:,indxAvg:].mean(axis=1)
            valStd = valRaw[:,indxAvg:].std(axis=1)

            vspTable['results'][results][runType] = valMean.reshape(shapeTable)

    # Compute the Derivatives


    return (vspTable)
