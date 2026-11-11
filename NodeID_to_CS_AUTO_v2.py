import clr
import os

clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Drawing")

from System.Windows.Forms import (
    Form,
    Label,
    TextBox,
    Button,
    RadioButton,
    DialogResult,
    FormStartPosition,
    FormBorderStyle,
    FlatStyle,
    MessageBox,
    MessageBoxButtons,
    MessageBoxIcon
)

from System.Drawing import Point, Size, Color
from System.Collections.Generic import List
from Ansys.Mechanical.DataModel.Interfaces import IDataModelObject


# ============================================================
# SETTINGS
# ============================================================

# MAPDL *GET koordinatlarinin uzunluk birimi.
# N-mm sistemi kullaniyorsan "mm" olarak birak.
APDL_LENGTH_UNIT = "mm"

COMMAND_NAME = "Node Coordinate Reader (APDL)"


# ============================================================
# NODE ID PARSER
# Desteklenen:
# 125
# 125,130,145
# 125-130
# 125,130-135,150
# ============================================================

def parse_node_ids(text):

    text = text.replace(" ", "")
    text = text.replace(";", ",")

    if not text:
        raise Exception("Node ID girilmedi.")

    node_ids = []

    items = text.split(",")

    for item in items:

        if not item:
            continue

        if "-" in item:

            parts = item.split("-")

            if len(parts) != 2:
                raise Exception(
                    "Gecersiz node araligi: {}".format(item)
                )

            first_id = int(parts[0])
            last_id = int(parts[1])

            if first_id <= 0 or last_id <= 0:
                raise Exception(
                    "Node ID pozitif olmalidir."
                )

            if last_id < first_id:
                raise Exception(
                    "Gecersiz aralik: {}".format(item)
                )

            for node_id in range(first_id, last_id + 1):

                if node_id not in node_ids:
                    node_ids.append(node_id)

        else:

            node_id = int(item)

            if node_id <= 0:
                raise Exception(
                    "Node ID pozitif olmalidir."
                )

            if node_id not in node_ids:
                node_ids.append(node_id)

    if len(node_ids) == 0:
        raise Exception("Gecerli Node ID bulunamadi.")

    return node_ids


# ============================================================
# CONVERT APDL OUTPUT PARAMETER TO FLOAT
# ============================================================

def numeric_value(value):

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


# ============================================================
# FIND EXISTING COORDINATE SYSTEM
# ============================================================

def get_existing_cs(name):

    objects = DataModel.GetObjectsByName(name)

    for obj in objects:

        try:
            dummy = obj.OriginX
            return obj
        except:
            pass

    return None


# ============================================================
# FORM
# ============================================================

form = Form()

form.Text = "Create Coordinate Systems from Node IDs"
form.ClientSize = Size(430, 240)

form.StartPosition = FormStartPosition.CenterScreen
form.FormBorderStyle = FormBorderStyle.FixedDialog

form.MaximizeBox = False
form.MinimizeBox = False

form.BackColor = Color.FromArgb(32, 32, 32)
form.ForeColor = Color.White


# ------------------------------------------------------------
# Title
# ------------------------------------------------------------

title_label = Label()

title_label.Text = "Node ID veya node gruplarini girin:"

title_label.Location = Point(35, 20)
title_label.Size = Size(350, 20)

title_label.ForeColor = Color.White
title_label.BackColor = form.BackColor

form.Controls.Add(title_label)


# ------------------------------------------------------------
# IDs format label
# ------------------------------------------------------------

id_label = Label()

id_label.Text = "IDs:    {1 or 3-6 or 2, 5-9, 47}"

id_label.Location = Point(35, 50)
id_label.Size = Size(350, 20)

id_label.ForeColor = Color.White
id_label.BackColor = form.BackColor

form.Controls.Add(id_label)


# ------------------------------------------------------------
# Input textbox
# ------------------------------------------------------------

id_box = TextBox()

id_box.Location = Point(35, 75)
id_box.Size = Size(370, 22)

id_box.BackColor = Color.White
id_box.ForeColor = Color.Black

form.Controls.Add(id_box)


# ------------------------------------------------------------
# Description
# ------------------------------------------------------------

description_label = Label()

description_label.Text = (
    "Bu arac, girilen Node ID'lerin koordinatlarini APDL *GET komutlari ile alir.\r\n"
    "Her node icin X, Y ve Z koordinatlari MAPDL sonucundan okunur.\r\n"
    "Bu koordinatlar kullanilarak Mechanical icinde Coordinate System olusturulur.\r\n"
    "Birden fazla node ID veya node araligi ayni anda girilebilir."
)

description_label.Location = Point(35, 110)
description_label.Size = Size(370, 75)

description_label.ForeColor = Color.LightGray
description_label.BackColor = form.BackColor

form.Controls.Add(description_label)


# ------------------------------------------------------------
# Create Coordinate System button
# ------------------------------------------------------------

create_button = Button()

create_button.Text = "Create Coordinate System"

create_button.Location = Point(110, 195)
create_button.Size = Size(190, 28)

create_button.FlatStyle = FlatStyle.Flat

create_button.BackColor = Color.FromArgb(95, 95, 95)
create_button.ForeColor = Color.White

form.Controls.Add(create_button)


# ------------------------------------------------------------
# Close button
# ------------------------------------------------------------

close_button = Button()

close_button.Text = "Close"

close_button.Location = Point(315, 195)
close_button.Size = Size(70, 28)

close_button.FlatStyle = FlatStyle.Flat

close_button.BackColor = Color.FromArgb(95, 95, 95)
close_button.ForeColor = Color.White

close_button.DialogResult = DialogResult.Cancel

form.Controls.Add(close_button)

form.CancelButton = close_button


# ============================================================
# FORM STATE
# ============================================================

form_state = {
    "nodes": None
}


# ============================================================
# CREATE BUTTON EVENT
# ============================================================

def create_clicked(sender, event):

    try:

        node_ids = parse_node_ids(id_box.Text)

        form_state["nodes"] = node_ids

        form.DialogResult = DialogResult.OK
        form.Close()

    except Exception as error:

        MessageBox.Show(
            str(error),
            "Invalid Node IDs",
            MessageBoxButtons.OK,
            MessageBoxIcon.Error
        )


create_button.Click += create_clicked


# ============================================================
# SHOW FORM
# ============================================================

result = form.ShowDialog()


# ============================================================
# MAIN
# ============================================================

if result == DialogResult.OK:

    node_ids = form_state["nodes"]

    # --------------------------------------------------------
    # ANALYSIS / SOLUTION
    # --------------------------------------------------------

    analysis = DataModel.AnalysisList[0]
    solution = analysis.Solution

    rst_path = solution.ResultFilePath

    if not rst_path or not os.path.exists(rst_path):

        MessageBox.Show(
            "Result file bulunamadi.\n"
            "Once analizi Solve etmelisiniz.",
            "Result File Not Found",
            MessageBoxButtons.OK,
            MessageBoxIcon.Error
        )

        raise Exception(
            "Solved result file bulunamadi."
        )


    # ========================================================
    # FIND OR CREATE COMMAND SNIPPET
    # ========================================================

    cmd = None

    existing = DataModel.GetObjectsByName(
        COMMAND_NAME
    )

    for obj in existing:

        try:

            dummy = obj.OutputSearchPrefix

            if obj.Parent == solution:
                cmd = obj
                break

        except:
            pass


    if cmd is None:

        cmd = solution.AddCommandSnippet()
        cmd.Name = COMMAND_NAME


    # ========================================================
    # APDL OUTPUT PARAMETER PREFIX
    # ========================================================

    cmd.OutputSearchPrefix = "NC"


    # ========================================================
    # GENERATE APDL
    # ========================================================

    apdl = []

    apdl.append("/POST1")
    apdl.append("SET,LAST")
    apdl.append("CSYS,0")
    apdl.append("")

    parameter_map = {}


    for index, node_id in enumerate(node_ids):

        tag = "{:04d}".format(index + 1)

        x_name = "NCX{}".format(tag)
        y_name = "NCY{}".format(tag)
        z_name = "NCZ{}".format(tag)

        parameter_map[node_id] = (
            x_name,
            y_name,
            z_name
        )


        apdl.append(
            "*GET,{0},NODE,{1},LOC,X".format(
                x_name,
                node_id
            )
        )

        apdl.append(
            "*GET,{0},NODE,{1},LOC,Y".format(
                y_name,
                node_id
            )
        )

        apdl.append(
            "*GET,{0},NODE,{1},LOC,Z".format(
                z_name,
                node_id
            )
        )

        apdl.append("")


    cmd.Input = "\n".join(apdl)

    ExtAPI.DataModel.Tree.Refresh()


    # ========================================================
    # EXECUTE ONLY THIS APDL POST COMMAND
    # ========================================================

    command_list = List[IDataModelObject]()

    command_list.Add(cmd)

    solution.ExecutePostCommands(
        command_list
    )


    # ========================================================
    # READ APDL OUTPUT PARAMETERS
    # ========================================================

    values = {}


    if cmd.OutputParameters is not None:

        for parameter in cmd.OutputParameters:

            name = str(parameter.Name).upper()

            try:

                values[name] = numeric_value(
                    parameter.Value
                )

            except:
                pass


    # ========================================================
    # CREATE COORDINATE SYSTEMS
    # ========================================================

    created_count = 0
    updated_count = 0
    failed_nodes = []


    for node_id in node_ids:

        x_name, y_name, z_name = parameter_map[node_id]


        # ----------------------------------------------------
        # CHECK APDL RESULTS
        # ----------------------------------------------------

        if (
            x_name not in values
            or y_name not in values
            or z_name not in values
        ):

            failed_nodes.append(node_id)

            ExtAPI.Log.WriteMessage(
                "Node {} icin APDL koordinatlari alinamadi.".format(
                    node_id
                )
            )

            continue


        # ----------------------------------------------------
        # APDL X Y Z
        # ----------------------------------------------------

        x = values[x_name]
        y = values[y_name]
        z = values[z_name]


        # ----------------------------------------------------
        # CS NAME
        # ----------------------------------------------------

        cs_name = "CS_at_node_{}".format(
            node_id
        )


        # ----------------------------------------------------
        # EXISTING CS?
        # ----------------------------------------------------

        cs = get_existing_cs(
            cs_name
        )


        if cs is None:

            cs = Model.CoordinateSystems.AddCoordinateSystem()

            cs.Name = cs_name

            created_count += 1

        else:

            updated_count += 1


        # ----------------------------------------------------
        # DEFINE ORIGIN
        # ----------------------------------------------------

        cs.OriginDefineBy = (
            CoordinateSystemAlignmentType.Fixed
        )


        cs.OriginX = Quantity(
            "{} [{}]".format(
                x,
                APDL_LENGTH_UNIT
            )
        )

        cs.OriginY = Quantity(
            "{} [{}]".format(
                y,
                APDL_LENGTH_UNIT
            )
        )

        cs.OriginZ = Quantity(
            "{} [{}]".format(
                z,
                APDL_LENGTH_UNIT
            )
        )


        # ----------------------------------------------------
        # LOG
        # ----------------------------------------------------

        ExtAPI.Log.WriteMessage(
            "NodeID: {}    X: {}    Y: {}    Z: {} [{}]".format(
                node_id,
                x,
                y,
                z,
                APDL_LENGTH_UNIT
            )
        )


    # ========================================================
    # REFRESH
    # ========================================================

    ExtAPI.DataModel.Tree.Refresh()


    # ========================================================
    # RESULT MESSAGE
    # ========================================================

    message = (
        "Coordinate System islemi tamamlandi.\n\n"
        "Created: {}\n"
        "Updated: {}"
    ).format(
        created_count,
        updated_count
    )


    if len(failed_nodes) > 0:

        message += (
            "\n\nFailed Nodes: {}"
        ).format(
            ", ".join(
                str(x) for x in failed_nodes
            )
        )


    MessageBox.Show(
        message,
        "Coordinate Systems",
        MessageBoxButtons.OK,
        MessageBoxIcon.Information
    )
