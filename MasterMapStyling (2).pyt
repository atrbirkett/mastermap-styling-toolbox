# -*- coding: utf-8 -*-
"""
MasterMapStyling.pyt
====================

ArcGIS Pro Python toolbox that derives cartographic styling attributes for OS
MasterMap Topography Layer feature classes in a single pass, replacing the set
of saved Field Calculator (.cal) expressions previously run one field at a time.

Tool: Apply MasterMap Cartographic Styling

For each supplied layer the tool:
    1. Confirms the required source fields are present.
    2. Adds the styling output fields (correct type) if they are missing.
    3. Populates the output fields from the source attributes using the same
       classification rules held in the original .cal expressions.

Layers and outputs
------------------
    TopographicArea     -> style_code (LONG), style_description (TEXT)
    TopographicLine     -> style_code (LONG), style_description (TEXT)
    TopographicPoint    -> style_code (LONG), style_description (TEXT)
    BoundaryLine        -> style_code (LONG), style_description (TEXT)
    CartographicSymbol  -> style_code (LONG), style_description (TEXT)
    CartographicText    -> style_code (LONG), style_description (TEXT),
                           colour_code (LONG), font_code (LONG),
                           rotation (DOUBLE), geo_x (DOUBLE),
                           geo_y (DOUBLE), anchor (TEXT)
"""

import arcpy


# ---------------------------------------------------------------------------
# Classification functions (single source of truth for all styling rules)
# Each returns a tuple; the layer configuration below maps each output field
# to the correct tuple index.
# ---------------------------------------------------------------------------

def classify_boundaryline(fc):
    """BoundaryLine -> (style_code, style_description)."""
    if fc == 10136: return 1, "Parish Boundary"
    if fc == 10131: return 2, "District Boundary"
    if fc == 10128: return 3, "Electoral Boundary"
    if fc == 10127: return 4, "County Boundary"
    if fc == 10135: return 5, "Parliamentary Boundary"
    return 99, "Unclassified"


def classify_cartographicsymbol(fc):
    """CartographicSymbol -> (style_code, style_description)."""
    if fc == 10091: return 1, "Culvert Symbol"
    if fc == 10082: return 2, "Direction Of Flow Symbol"
    if fc == 10130: return 3, "Boundary Half Mereing Symbol"
    if fc == 10066 or fc == 10170: return 4, "Bench Mark Symbol"
    if fc == 10165: return 5, "Railway Switch Symbol"
    if fc == 10177: return 6, "Road Related Flow Symbol"
    return 99, "Unclassified"


def classify_topographicarea(dt, dg, mk):
    """TopographicArea -> (style_code, style_description)."""
    # --- Built Environment ---
    if dt == "Multi Surface": return 1, "Multi Surface Fill"
    if dt == "Archway": return 2, "Archway Fill"
    if "Bridge" in str(dt) and ("Road Or Track" in str(dg) or "Roadside" in str(dg)): return 3, "Road Bridge Fill"
    if "Bridge" in str(dt) and "Rail" in str(dg): return 4, "Rail Bridge Fill"
    if "Bridge" in str(dt): return 5, "Bridge Fill"
    if "Level Crossing" in str(dt): return 6, "Level Crossing Fill"
    if dt == "Traffic Calming": return 7, "Traffic Calming Fill"
    if dt == "Pylon": return 8, "Pylon Fill"
    if dt == "Track": return 9, "Track Fill"
    if dt == "Step": return 10, "Step Fill"
    if "Canal" in str(dt): return 11, "Canal Fill"
    if "Footbridge" in str(dt): return 12, "Footbridge Fill"

    # --- Natural Environment ---
    if ("Nonconiferous Trees" in str(dt)) and ("Coniferous Trees" in str(dt)):
        return 13, "Mixed Woodland Fill"
    if "Nonconiferous Trees" in str(dt): return 14, "Nonconiferous Tree Fill"
    if "Coniferous Trees" in str(dt): return 15, "Coniferous Tree Fill"
    if "Agricultural Land" in str(dt): return 16, "Agricultural Land Fill"
    if "Orchard" in str(dt): return 17, "Orchard Fill"
    if "Coppice Or Osiers" in str(dt): return 18, "Coppice Or Osiers Fill"
    if "Scrub" in str(dt): return 19, "Scrub Fill"
    if "Boulders" in str(dt): return 20, "Boulders Fill"
    if "Rock" in str(dt): return 21, "Rock Fill"
    if "Scree" in str(dt): return 22, "Scree Fill"
    if "Rough Grassland" in str(dt): return 23, "Rough Grassland Fill"
    if "Heath" in str(dt): return 24, "Heath Fill"
    if "Marsh Reeds Or Saltmarsh" in str(dt) or "Saltmarsh" in str(dt): return 25, "Saltmarsh Fill"
    if "Sand" in str(dt): return 26, "Sand Fill"
    if "Mud" in str(dt): return 27, "Mud Fill"
    if "Shingle" in str(dt): return 28, "Shingle Fill"
    if "Marsh" in str(dt): return 29, "Marsh Fill"
    if "Reeds" in str(dt): return 30, "Reeds Fill"
    if "Foreshore" in str(dt): return 31, "Foreshore Fill"
    if dt == "Slope": return 32, "Slope Fill"
    if dt == "Cliff": return 33, "Cliff Fill"

    # --- Descriptive Group ---
    if "Building" in str(dg): return 34, "Building Fill"
    if "General Surface" in str(dg) and mk == "Natural": return 35, "Natural Fill"
    if "General Surface" in str(dg) and mk in ("Manmade", "Unknown"): return 36, "Manmade Fill"
    if "Road Or Track" in str(dg) and mk == "Manmade": return 37, "Road Or Track Fill"
    if "Roadside" in str(dg) and mk == "Natural": return 38, "Roadside Natural Fill"
    if "Roadside" in str(dg) and mk in ("Manmade", "Unknown"): return 39, "Roadside Manmade Fill"
    if "Inland Water" in str(dg): return 40, "Inland Water Fill"
    if "Path" in str(dg): return 41, "Path Fill"
    if "Rail" in str(dg) and mk in ("Manmade", "Unknown"): return 42, "Rail Manmade Fill"
    if "Rail" in str(dg) and mk == "Natural": return 43, "Rail Natural Fill"
    if "Structure" in str(dg): return 44, "Structure Fill"
    if dg == "Glasshouse": return 45, "Glasshouse Fill"
    if "Landform" in str(dg) and mk == "Natural": return 46, "Landform Natural Fill"
    if "Tidal Water" in str(dg): return 47, "Tidal Water Fill"
    if "Landform" in str(dg) and mk == "Manmade": return 48, "Landform Manmade Fill"

    return 99, "Unclassified"


def classify_topographicline(dt, dg, mk, pp):
    """TopographicLine -> (style_code, style_description)."""
    # --- Descriptive Term Rules ---
    if dt == "Polygon Closing Link": return 1, "Polygon Closing Line"
    if dt == "Inferred Property Closing Link": return 2, "Property Closing Line"
    if dt == "Bottom Of Slope": return 3, "Bottom Of Slope Line"
    if dt == "Top Of Slope": return 4, "Top Of Slope Line"
    if dt == "Step": return 5, "Step Line"
    if "Mean High Water" in str(dt): return 6, "Mean High Water Line"
    if dt == "Traffic Calming": return 7, "Traffic Calming Line"
    if dt == "Standard Gauge Track": return 8, "Standard Gauge Track Line"
    if dt == "Bottom Of Cliff": return 9, "Bottom Of Cliff Line"
    if dt == "Top Of Cliff": return 10, "Top Of Cliff Line"
    if dt == "Mean Low Water (Springs)": return 11, "Mean Low Water Line"
    if dt == "Unmade Path Alignment": return 12, "Path Line"
    if "Overhead Construction" in str(dt): return 13, "Overhead Construction Line"
    if dt == "Culvert": return 14, "Culvert Line"
    if dt == "Pylon": return 15, "Pylon Line"
    if dt == "Ridge Or Rock Line": return 16, "Ridge Or Rock Line"
    if dt == "Narrow Gauge": return 17, "Narrow Gauge Line"
    if dt == "Buffer": return 18, "Railway Buffer Line"
    if dt == "Tunnel Edge": return 19, "Tunnel Edge Line"
    if "Line Of Posts" in str(dt): return 20, "Line Of Posts Line"
    if dt == "Drain": return 21, "Drain Line"
    if "Normal Tidal Limit" in str(dt): return 22, "Normal Tidal Limit Line"

    # --- Descriptive Group Rules ---
    if "General Feature" in str(dg) and pp != "Edge / Limit": return 23, "Default Line"
    if "Building" in str(dg) and dt == "Outline" and pp == "Obstructing": return 24, "Building Outline Line"
    if "General Feature" in str(dg) and pp == "Edge / Limit": return 25, "Edge Line"
    if "Road Or Track" in str(dg): return 26, "Road Or Track Line"
    if "Building" in str(dg) and dt == "Division" and pp == "Obstructing": return 27, "Building Division Line"
    if "Inland Water" in str(dg): return 28, "Inland Water Line"
    if "General Surface" in str(dg) and mk == "Natural": return 29, "General Surface Natural Line"
    if "Building" in str(dg) and dt == "Outline" and pp == "Overhead": return 30, "Building Overhead Line"
    if dg == "Landform" and mk == "Natural": return 31, "Landform Natural Line"
    if dg == "Historic Interest": return 32, "Historic Interest Line"
    if dg == "Landform" and mk == "Manmade": return 33, "Landform Manmade Line"

    return 99, "Unclassified"


def classify_topographicpoint(dt, dg):
    """TopographicPoint -> (style_code, style_description)."""
    if dt == "Spot Height": return 1, "Spot Height Point"
    if dt == "Emergency Telephone": return 2, "Emergency Telephone Point"
    if "Site Of Heritage" in str(dt): return 3, "Site Of Heritage Point"
    if "Culvert" in str(dt): return 4, "Culvert Point"
    if dt == "Positioned Nonconiferous Tree": return 5, "Positioned Nonconiferous Tree Point"
    if "Inland Water" in str(dg): return 6, "Inland Water Point"
    if "Roadside" in str(dg): return 7, "Roadside Point"
    if "Overhead Construction" in str(dt): return 8, "Overhead Construction Point"
    if "Rail" in str(dg): return 9, "Rail Point"
    if dt == "Positioned Coniferous Tree": return 10, "Positioned Coniferous Tree Point"
    if dt == "Boundary Post Or Stone": return 11, "Boundary Post Point"
    if dt == "Triangulation Point Or Pillar": return 12, "Triangulation Point Or Pillar Point"
    if dg == "Historic Interest": return 13, "Historic Point"
    if dg == "Landform" or dt == "Positioned Boulder": return 14, "Landform Point"
    if "Tidal Water" in str(dg): return 15, "Tidal Water Point"
    if "Structure" in str(dg): return 16, "Structure Point"
    return 99, "Unclassified"


def classify_cartographictext(dg, dt, mk, orient, anchorpos):
    """CartographicText -> (style_code, style_description, colour_code,
    font_code, rotation, geo_x, geo_y, anchor)."""
    # Style description + code
    if "Buildings Or Structure" in str(dg): desc, code = "Building Text", 1
    elif "Inland Water" in str(dg): desc, code = "Water Text", 2
    elif "Road Or Track" in str(dg): desc, code = "Road Text", 3
    elif dg == "Terrain And Height": desc, code = "Height Text", 4
    elif "Roadside" in str(dg): desc, code = "Roadside Text", 5
    elif "Structure" in str(dg): desc, code = "Structure Text", 6
    elif dg == "Political Or Administrative": desc, code = "Administrative Text", 7
    elif dg == "General Surface" and mk == "Natural": desc, code = "General Surface Natural Text", 8
    elif dg == "General Surface" and (mk == "Manmade" or mk is None): desc, code = "General Surface Manmade Text", 9
    elif dg == "Landform" and mk == "Natural": desc, code = "Landform Natural Text", 10
    elif dt == "Foreshore": desc, code = "Foreshore Text", 11
    elif "Tidal Water" in str(dg): desc, code = "Tidal Water Text", 12
    elif dg == "Built Environment": desc, code = "Built Environment Text", 13
    elif "Historic Interest" in str(dg): desc, code = "Historic Text", 14
    elif dg == "Rail": desc, code = "Rail Text", 15
    elif "General Feature" in str(dg): desc, code = "General Feature Text", 16
    elif dg == "Landform" and mk == "Manmade": desc, code = "Landform Manmade Text", 17
    else: desc, code = "Unclassified", 99

    # Colour code
    if "Buildings Or Structure" in str(dg): colour = 1
    elif "Inland Water" in str(dg): colour = 2
    elif "Road Or Track" in str(dg): colour = 1
    elif dg == "Terrain And Height": colour = 3
    elif "Roadside" in str(dg): colour = 1
    elif "Structure" in str(dg): colour = 1
    elif dg == "Political Or Administrative": colour = 5
    elif dg == "General Surface" and mk == "Natural": colour = 1
    elif dg == "General Surface" and (mk == "Manmade" or mk is None): colour = 1
    elif dg == "Landform" and mk == "Natural": colour = 4
    elif dt == "Foreshore": colour = 4
    elif "Tidal Water" in str(dg): colour = 2
    elif dg == "Built Environment": colour = 1
    elif "Historic Interest" in str(dg): colour = 1
    elif dg == "Rail": colour = 1
    elif "General Feature" in str(dg): colour = 1
    elif dg == "Landform" and mk == "Manmade": colour = 4
    else: colour = 1

    # Font code
    if "Buildings Or Structure" in str(dg): font = 1
    elif "Inland Water" in str(dg): font = 2
    elif "Road Or Track" in str(dg): font = 1
    elif dg == "Terrain And Height": font = 1
    elif "Roadside" in str(dg): font = 1
    elif "Structure" in str(dg): font = 1
    elif dg == "Political Or Administrative": font = 1
    elif dg == "General Surface" and mk == "Natural": font = 1
    elif dg == "General Surface" and (mk == "Manmade" or mk is None): font = 1
    elif dg == "Landform" and mk == "Natural": font = 1
    elif dt == "Foreshore": font = 1
    elif "Tidal Water" in str(dg): font = 2
    elif dg == "Built Environment": font = 1
    elif "Historic Interest" in str(dg): font = 3
    elif dg == "Rail": font = 1
    elif "General Feature" in str(dg): font = 1
    elif dg == "Landform" and mk == "Manmade": font = 1
    else: font = 1

    # Rotation (orientation stored in tenths of a degree)
    rotation = orient / 10.0 if orient is not None else 0

    # Anchor mapping
    if anchorpos == 0: geo_x, geo_y, anchor = 0, 0, "SW"
    elif anchorpos == 1: geo_x, geo_y, anchor = 0, 0.5, "W"
    elif anchorpos == 2: geo_x, geo_y, anchor = 0, 1, "NW"
    elif anchorpos == 3: geo_x, geo_y, anchor = 0.5, 0, "S"
    elif anchorpos == 4: geo_x, geo_y, anchor = 0.5, 0.5, ""
    elif anchorpos == 5: geo_x, geo_y, anchor = 0.5, 1, "N"
    elif anchorpos == 6: geo_x, geo_y, anchor = 1, 0, "SE"
    elif anchorpos == 7: geo_x, geo_y, anchor = 1, 0.5, "E"
    elif anchorpos == 8: geo_x, geo_y, anchor = 1, 1, "NE"
    else: geo_x, geo_y, anchor = 0, 0, ""

    return code, desc, colour, font, rotation, geo_x, geo_y, anchor


# ---------------------------------------------------------------------------
# Layer configuration
#   source_fields : attributes read (in the order the classify() expects them)
#   outputs       : list of (field_name, field_type, length_or_None, tuple_index)
#   classify      : the function above
# Text length 50 is comfortably above the longest style_description (35 chars);
# anchor values are at most two characters.
# ---------------------------------------------------------------------------

LAYER_CONFIG = {
    "TopographicArea": {
        "source_fields": ["descriptiveterm", "descriptivegroup", "make"],
        "outputs": [
            ("style_code", "LONG", None, 0),
            ("style_description", "TEXT", 50, 1),
        ],
        "classify": classify_topographicarea,
    },
    "TopographicLine": {
        "source_fields": ["descriptiveterm", "descriptivegroup", "make", "physicalpresence"],
        "outputs": [
            ("style_code", "LONG", None, 0),
            ("style_description", "TEXT", 50, 1),
        ],
        "classify": classify_topographicline,
    },
    "TopographicPoint": {
        "source_fields": ["descriptiveterm", "descriptivegroup"],
        "outputs": [
            ("style_code", "LONG", None, 0),
            ("style_description", "TEXT", 50, 1),
        ],
        "classify": classify_topographicpoint,
    },
    "BoundaryLine": {
        "source_fields": ["featurecode"],
        "outputs": [
            ("style_code", "LONG", None, 0),
            ("style_description", "TEXT", 50, 1),
        ],
        "classify": classify_boundaryline,
    },
    "CartographicSymbol": {
        "source_fields": ["featurecode"],
        "outputs": [
            ("style_code", "LONG", None, 0),
            ("style_description", "TEXT", 50, 1),
        ],
        "classify": classify_cartographicsymbol,
    },
    "CartographicText": {
        "source_fields": ["descriptivegroup", "descriptiveterm", "make",
                          "orientation", "anchorposition"],
        "outputs": [
            ("style_code", "LONG", None, 0),
            ("style_description", "TEXT", 50, 1),
            ("colour_code", "LONG", None, 2),
            ("font_code", "LONG", None, 3),
            ("rotation", "DOUBLE", None, 4),
            ("geo_x", "DOUBLE", None, 5),
            ("geo_y", "DOUBLE", None, 6),
            ("anchor", "TEXT", 4, 7),
        ],
        "classify": classify_cartographictext,
    },
}


# ---------------------------------------------------------------------------
# Shared processing routine
# ---------------------------------------------------------------------------

def _existing_field_names(layer):
    return {f.name.lower() for f in arcpy.ListFields(layer)}


def process_layer(layer, key, add_missing):
    """Validate, add fields if required, and populate one layer."""
    config = LAYER_CONFIG[key]
    existing = _existing_field_names(layer)

    # 1. Confirm source fields exist
    missing_sources = [f for f in config["source_fields"] if f.lower() not in existing]
    if missing_sources:
        raise arcpy.ExecuteError(
            "{0}: missing required source field(s): {1}. "
            "Check this is the correct layer and that the OS MasterMap "
            "attributes are present.".format(key, ", ".join(missing_sources))
        )

    # 2. Add output fields if missing (or stop if not allowed to)
    for name, ftype, length, _idx in config["outputs"]:
        if name.lower() not in existing:
            if not add_missing:
                raise arcpy.ExecuteError(
                    "{0}: output field '{1}' is missing and "
                    "'Add output fields if missing' is unticked.".format(key, name)
                )
            if ftype == "TEXT":
                arcpy.management.AddField(layer, name, ftype, field_length=length)
            else:
                arcpy.management.AddField(layer, name, ftype)
            arcpy.AddMessage("    Added field: {0} ({1})".format(name, ftype))

    # 3. Populate with an update cursor (single read of source fields)
    classify = config["classify"]
    src_fields = config["source_fields"]
    out_fields = [o[0] for o in config["outputs"]]
    out_indices = [o[3] for o in config["outputs"]]
    cursor_fields = src_fields + out_fields
    n_src = len(src_fields)

    updated = 0
    with arcpy.da.UpdateCursor(layer, cursor_fields) as rows:
        for row in rows:
            result = classify(*row[:n_src])
            for pos, tuple_idx in enumerate(out_indices):
                row[n_src + pos] = result[tuple_idx]
            rows.updateRow(row)
            updated += 1

    arcpy.AddMessage("    {0}: {1} feature(s) styled.".format(key, updated))


# ---------------------------------------------------------------------------
# Toolbox / Tool
# ---------------------------------------------------------------------------

class Toolbox(object):
    def __init__(self):
        self.label = "OS MasterMap Cartographic Styling"
        self.alias = "MasterMapStyling"
        self.tools = [ApplyMasterMapStyling]


class ApplyMasterMapStyling(object):
    def __init__(self):
        self.label = "Apply MasterMap Cartographic Styling"
        self.description = (
            "Derives style_code / style_description (and the additional text "
            "styling fields for CartographicText) for OS MasterMap Topography "
            "Layer feature classes, from their source attributes. Supply only "
            "the layers you have; each is optional."
        )
        self.canRunInBackground = False

    def getParameterInfo(self):
        # Parameter order matches the keys below
        self._param_keys = [
            "TopographicArea", "TopographicLine", "TopographicPoint",
            "BoundaryLine", "CartographicSymbol", "CartographicText",
        ]
        params = []
        for key in self._param_keys:
            p = arcpy.Parameter(
                displayName=key,
                name=key,
                datatype="GPFeatureLayer",
                parameterType="Optional",
                direction="Input",
            )
            params.append(p)

        add_missing = arcpy.Parameter(
            displayName="Add output fields if missing",
            name="add_missing",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input",
        )
        add_missing.value = True
        params.append(add_missing)
        return params

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        keys = ["TopographicArea", "TopographicLine", "TopographicPoint",
                "BoundaryLine", "CartographicSymbol", "CartographicText"]
        add_missing = parameters[6].value

        supplied = [(keys[i], parameters[i].valueAsText)
                    for i in range(6) if parameters[i].value]

        if not supplied:
            arcpy.AddWarning("No layers supplied - nothing to do.")
            return

        for key, layer in supplied:
            arcpy.AddMessage("Processing {0} ...".format(key))
            process_layer(layer, key, add_missing)

        arcpy.AddMessage("Done.")
