import clr
import os

clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Drawing")

from System.Windows.Forms import (
    Form,
    Label,
    TextBox,
    Button,
    ComboBox,
    ComboBoxStyle,
    DialogResult,
    FormStartPosition,
    ScrollBars,
    MessageBox,
    MessageBoxButtons,
    MessageBoxIcon
)

from System.Drawing import Point, Size


# ============================================================
# FUNCTIONS
# ============================================================

def expandNodes(spec):

    spec = spec.replace(" ", "")
    spec = spec.replace(";", ",")

    result = []

    tokens = spec.split(",")

    for token in tokens:

        token = token.strip()

        if not token:
            continue

        if "-" in token:

            parts = token.split("-")

            if len(parts) != 2:
                raise Exception(
                    "Gecersiz node araligi: {}".format(token)
                )

            firstNode = int(parts[0])
            lastNode = int(parts[1])

            if firstNode <= 0 or lastNode <= 0:
                raise Exception(
                    "Node ID pozitif olmali: {}".format(token)
                )

            if lastNode < firstNode:
                raise Exception(
                    "Aralik ters girilmis: {}".format(token)
                )

            for nodeId in range(firstNode, lastNode + 1):
                result.append(nodeId)

        else:

            nodeId = int(token)

            if nodeId <= 0:
                raise Exception(
                    "Node ID pozitif olmali: {}".format(token)
                )

            result.append(nodeId)

    return result


def parseInput(text):

    entries = []
    seen = set()

    lines = text.splitlines()

    for line in lines:

        line = line.strip()

        if not line:
            continue

        groupName = ""
        nodeSpec = line

        if ":" in line:

            parts = line.split(":", 1)

            groupName = parts[0].strip()
            nodeSpec = parts[1].strip()

        nodes = expandNodes(nodeSpec)

        for nodeId in nodes:

            key = (groupName, nodeId)

            if key not in seen:

                seen.add(key)

                entries.append(
                    (groupName, nodeId)
                )

    if len(entries) == 0:

        raise Exception(
            "En az bir node ID girilmelidir."
        )

    return entries


def numericValue(value):

    try:
        return float(value)

    except:
        pass

    try:
        return float(value.Value)

    except:
        pass

    text = str(value).strip()

    text = text.replace("D", "E")

    return float(text.split()[0])


def getExistingCs(csName):

    objects = DataModel.GetObjectsByName(csName)

    for obj in objects:

        try:
            test = obj.OriginX
            return obj

        except:
            pass

    return None


# ============================================================
# FORM
# ============================================================

form = Form()

form.Text = "APDL Node Coordinate Systems"
form.ClientSize = Size(560, 390)
form.StartPosition = FormStartPosition.CenterScreen
form.TopMost = True


titleLabel = Label()

titleLabel.Text = "Node ID veya node gruplarini girin:"
titleLabel.Location = Point(20, 20)
titleLabel.Size = Size(500, 25)

form.Controls.Add(titleLabel)


infoLabel = Label()

infoLabel.Text = (
    "Ornekler:\r\n"
    "125\r\n"
    "125,130,140\r\n"
    "125-135\r\n"
    "SupportA: 125,130,140-145"
)

infoLabel.Location = Point(20, 50)
infoLabel.Size = Size(500, 80)

form.Controls.Add(infoLabel)


nodeBox = TextBox()

nodeBox.Multiline = True
nodeBox.ScrollBars = ScrollBars.Vertical

nodeBox.Location = Point(20, 135)
nodeBox.Size = Size(515, 120)

nodeBox.Text = "125"

form.Controls.Add(nodeBox)


unitLabel = Label()

unitLabel.Text = "APDL length unit:"
unitLabel.Location = Point(20, 275)
unitLabel.Size = Size(150, 25)

form.Controls.Add(unitLabel)


unitBox = ComboBox()

unitBox.Location = Point(170, 272)
unitBox.Size = Size(120, 25)
unitBox.DropDownStyle = ComboBoxStyle.DropDownList

for unit in ["mm", "m", "cm", "um", "in", "ft"]:
    unitBox.Items.Add(unit)

unitBox.SelectedItem = "mm"

form.Controls.Add(unitBox)


unitInfo = Label()

unitInfo.Text = "Bu birim MAPDL *GET sonucunun birimi olmalidir."
unitInfo.Location = Point(20, 305)
unitInfo.Size = Size(500, 25)

form.Controls.Add(unitInfo)


okButton = Button()

okButton.Text = "Create CS"
okButton.Location = Point(335, 340)
okButton.Size = Size(95, 30)

form.Controls.Add(okButton)


cancelButton = Button()

cancelButton.Text = "Cancel"
cancelButton.Location = Point(440, 340)
cancelButton.Size = Size(95, 30)
cancelButton.DialogResult = DialogResult.Cancel

form.Controls.Add(cancelButton)


form.CancelButton = cancelButton
form.AcceptButton = okButton


dialogState = {
    "entries": None
}


def onOk(sender, args):

    try:

        entries = parseInput(nodeBox.Text)

        dialogState["entries"] = entries

        form.DialogResult = DialogResult.OK

        form.Close()

    except Exception as error:

        MessageBox.Show(
            str(error),
            "Invalid Node Input",
            MessageBoxButtons.OK,
            MessageBoxIcon.Error
        )


okButton.Click += onOk


# ============================================================
# SHOW FORM
# ============================================================

dialogResult = form.ShowDialog()


# ============================================================
# MAIN SCRIPT
# ============================================================

if dialogResult == DialogResult.OK:

    entries = dialogState["entries"]

    lengthUnit = str(unitBox.SelectedItem)

    analysis = DataModel.AnalysisList[0]

    solution = analysis.Solution


    # --------------------------------------------------------
    # CHECK RESULT FILE
    # --------------------------------------------------------

    rstPath = solution.ResultFilePath

    if not rstPath or not os.path.exists(rstPath):

        MessageBox.Show(
            "Result file bulunamadi.\r\n\r\n"
            "Analizi once Solve ettikten sonra scripti calistirin.",
            "No Result File",
            MessageBoxButtons.OK,
            MessageBoxIcon.Error
        )

        raise Exception(
            "Solved result file bulunamadi."
        )


    # --------------------------------------------------------
    # REMOVE OLD TEMPORARY COMMAND OBJECT
    # --------------------------------------------------------

    cmdName = "Node Coordinate Reader"

    oldCommands = DataModel.GetObjectsByName(cmdName)

    for obj in list(oldCommands):

        try:

            if obj.Parent == solution:

                test = obj.OutputSearchPrefix

                obj.Delete()

        except:
            pass


    # --------------------------------------------------------
    # CREATE APDL COMMAND OBJECT
    # --------------------------------------------------------

    cmd = solution.AddCommandSnippet()

    cmd.Name = cmdName

    cmd.OutputSearchPrefix = "NC"


    # --------------------------------------------------------
    # GENERATE APDL
    # --------------------------------------------------------

    apdlLines = []

    apdlLines.append("! NODE COORDINATE READER")
    apdlLines.append("/POST1")
    apdlLines.append("SET,LAST")
    apdlLines.append("CSYS,0")
    apdlLines.append("")

    indexMap = {}

    for index in range(len(entries)):

        groupName = entries[index][0]
        nodeId = entries[index][1]

        tag = str(index + 1).zfill(4)

        indexMap[tag] = (
            groupName,
            nodeId
        )

        apdlLines.append(
            "*GET,NCX{0},NODE,{1},LOC,X".format(
                tag,
                nodeId
            )
        )

        apdlLines.append(
            "*GET,NCY{0},NODE,{1},LOC,Y".format(
                tag,
                nodeId
            )
        )

        apdlLines.append(
            "*GET,NCZ{0},NODE,{1},LOC,Z".format(
                tag,
                nodeId
            )
        )

        apdlLines.append("")


    cmd.Input = "\n".join(apdlLines)

    ExtAPI.DataModel.Tree.Refresh()


    # --------------------------------------------------------
    # EXECUTE ONLY THIS POST COMMAND
    # --------------------------------------------------------

    try:

        solution.ExecutePostCommands([cmd])

    except:

        try:

            from System.Collections.Generic import List
            from Ansys.Mechanical.DataModel.Interfaces import IDataModelObject

            cmdList = List[IDataModelObject]()

            cmdList.Add(cmd)

            solution.ExecutePostCommands(cmdList)

        except Exception as error:

            MessageBox.Show(
                "APDL Post Command calistirilamadi.\r\n\r\n{}".format(
                    str(error)
                ),
                "APDL Error",
                MessageBoxButtons.OK,
                MessageBoxIcon.Error
            )

            raise


    # --------------------------------------------------------
    # READ APDL OUTPUT PARAMETERS
    # --------------------------------------------------------

    values = {}

    for parameter in cmd.OutputParameters:

        paramName = str(parameter.Name).upper()

        try:

            values[paramName] = numericValue(
                parameter.Value
            )

        except:
            pass


    # --------------------------------------------------------
    # CREATE COORDINATE SYSTEMS
    # --------------------------------------------------------

    createdCount = 0
    updatedCount = 0

    logLines = []

    for index in range(len(entries)):

        groupName = entries[index][0]
        nodeId = entries[index][1]

        tag = str(index + 1).zfill(4)

        xName = "NCX{}".format(tag)
        yName = "NCY{}".format(tag)
        zName = "NCZ{}".format(tag)


        if (
            xName not in values
            or yName not in values
            or zName not in values
        ):

            logLines.append(
                "Node {}: APDL sonucu bulunamadi.".format(
                    nodeId
                )
            )

            continue


        x = values[xName]
        y = values[yName]
        z = values[zName]


        # ----------------------------------------------------
        # COORDINATE SYSTEM NAME
        # ----------------------------------------------------

        if groupName:

            csName = "CS {} N{}".format(
                groupName,
                nodeId
            )

        else:

            csName = "CS N{}".format(
                nodeId
            )


        # ----------------------------------------------------
        # FIND OR CREATE CS
        # ----------------------------------------------------

        cs = getExistingCs(csName)

        if cs is None:

            cs = Model.CoordinateSystems.AddCoordinateSystem()

            cs.Name = csName

            createdCount += 1

        else:

            updatedCount += 1


        # ----------------------------------------------------
        # APPLY APDL COORDINATES
        # ----------------------------------------------------

        cs.OriginDefineBy = (
            CoordinateSystemAlignmentType.Fixed
        )

        cs.OriginX = Quantity(
            x,
            lengthUnit
        )

        cs.OriginY = Quantity(
            y,
            lengthUnit
        )

        cs.OriginZ = Quantity(
            z,
            lengthUnit
        )


        # ----------------------------------------------------
        # LOG
        # ----------------------------------------------------

        logLines.append(
            "Node {} -> X: {}  Y: {}  Z: {} [{}]".format(
                nodeId,
                x,
                y,
                z,
                lengthUnit
            )
        )


    # --------------------------------------------------------
    # REFRESH TREE
    # --------------------------------------------------------

    ExtAPI.DataModel.Tree.Refresh()


    # --------------------------------------------------------
    # LOG OUTPUT
    # --------------------------------------------------------

    ExtAPI.Log.WriteMessage(
        "=============================================="
    )

    ExtAPI.Log.WriteMessage(
        "APDL NODE COORDINATE SYSTEM TOOL"
    )

    for line in logLines:

        ExtAPI.Log.WriteMessage(line)

    ExtAPI.Log.WriteMessage(
        "Created: {}   Updated: {}".format(
            createdCount,
            updatedCount
        )
    )

    ExtAPI.Log.WriteMessage(
        "=============================================="
    )


    # --------------------------------------------------------
    # FINAL MESSAGE
    # --------------------------------------------------------

    MessageBox.Show(
        "Islem tamamlandi.\r\n\r\n"
        "Created CS: {}\r\n"
        "Updated CS: {}\r\n"
        "Requested nodes: {}".format(
            createdCount,
            updatedCount,
            len(entries)
        ),
        "Completed",
        MessageBoxButtons.OK,
        MessageBoxIcon.Information
    )
