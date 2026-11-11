import os

# ============================================================
# USER INPUT
# ============================================================

node_id = 125

# APDL solver'daki uzunluk birimi
# Modelin N-mm sistemindeyse "mm"
# MKS ise "m"
apdl_length_unit = "mm"

# ============================================================
# ANALYSIS / SOLUTION
# ============================================================

analysis = DataModel.AnalysisList[0]
solution = analysis.Solution

# ============================================================
# COMMAND SNIPPET
# ============================================================

cmd_name = "__GET_NODE_COORDINATES__"

existing_cmds = DataModel.GetObjectsByName(cmd_name)

cmd = None

for obj in existing_cmds:
    try:
        if obj.Parent == solution:
            cmd = obj
            break
    except:
        pass

if cmd is None:
    cmd = solution.AddCommandSnippet()
    cmd.Name = cmd_name

# ============================================================
# APDL OUTPUT PREFIX
# ============================================================

# CS ile baslayan APDL parametrelerini Mechanical
# output parameter olarak yakalayacak.
cmd.OutputSearchPrefix = "CS"

# ============================================================
# APDL
# ============================================================

cmd.Input = """
/POST1
SET,LAST

*GET,CSXN,NODE,{0},LOC,X
*GET,CSYN,NODE,{0},LOC,Y
*GET,CSZN,NODE,{0},LOC,Z

/COM, ==============================================
*VWRITE,{0},CSXN,CSYN,CSZN
('NodeID: ',I8,'  X: ',F16.6,'  Y: ',F16.6,'  Z: ',F16.6)
/COM, ==============================================
""".format(node_id)

# ============================================================
# EXECUTE APDL
# ============================================================

rst_path = solution.ResultFilePath

executed = False

# Analiz daha once solve edilmisse sadece post commands calistir.
if rst_path and os.path.exists(rst_path):

    try:
        solution.ExecutePostCommands([cmd])
        executed = True

    except Exception as e:

        ExtAPI.Log.WriteMessage(
            "ExecutePostCommands kullanilamadi. Solve yapilacak."
        )

# Sonuc dosyasi yoksa veya ExecutePostCommands basarisizsa solve et.
if not executed:

    Model.Solve(True)

# ============================================================
# GET APDL OUTPUT PARAMETERS
# ============================================================

parameters = {}

for parameter in cmd.OutputParameters:

    parameter_name = str(parameter.Name).upper()

    parameters[parameter_name] = float(parameter.Value)

# ============================================================
# CHECK PARAMETERS
# ============================================================

required_parameters = [
    "CSXN",
    "CSYN",
    "CSZN"
]

for parameter_name in required_parameters:

    if parameter_name not in parameters:

        raise Exception(
            "APDL output parameter bulunamadi: {}".format(
                parameter_name
            )
        )

# ============================================================
# READ APDL VALUES
# ============================================================

x = parameters["CSXN"]
y = parameters["CSYN"]
z = parameters["CSZN"]

# ============================================================
# PRINT
# ============================================================

ExtAPI.Log.WriteMessage(
    "=============================================="
)

ExtAPI.Log.WriteMessage(
    "NodeID: {}    X: {}    Y: {}    Z: {} [{}]".format(
        node_id,
        x,
        y,
        z,
        apdl_length_unit
    )
)

ExtAPI.Log.WriteMessage(
    "=============================================="
)

# ============================================================
# COORDINATE SYSTEM
# ============================================================

cs_name = "CS_at_node_{}".format(node_id)

existing_cs = DataModel.GetObjectsByName(cs_name)

cs = None

for obj in existing_cs:

    try:
        test = obj.OriginX
        cs = obj
        break

    except:
        pass

# Yoksa olustur
if cs is None:

    cs = Model.CoordinateSystems.AddCoordinateSystem()

    cs.Name = cs_name

# ============================================================
# DEFINE ORIGIN
# ============================================================

cs.OriginDefineBy = CoordinateSystemAlignmentType.Fixed

cs.OriginX = Quantity(
    x,
    apdl_length_unit
)

cs.OriginY = Quantity(
    y,
    apdl_length_unit
)

cs.OriginZ = Quantity(
    z,
    apdl_length_unit
)

# ============================================================
# ORIENTATION = GLOBAL
# ============================================================

cs.PrimaryAxisDefineBy = (
    CoordinateSystemAlignmentType.GlobalX
)

cs.SecondaryAxisDefineBy = (
    CoordinateSystemAlignmentType.GlobalZ
)

# ============================================================
# REFRESH
# ============================================================

ExtAPI.DataModel.Tree.Refresh()

# ============================================================
# FINAL MESSAGE
# ============================================================

ExtAPI.Log.WriteMessage(
    "Coordinate System '{}' olusturuldu.".format(
        cs_name
    )
)

ExtAPI.Log.WriteMessage(
    "Origin = ({}, {}, {}) [{}]".format(
        x,
        y,
        z,
        apdl_length_unit
    )
)