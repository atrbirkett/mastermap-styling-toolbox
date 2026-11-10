# OS MasterMap Cartographic Styling Toolbox for ArcGIS Pro

A Python toolbox (`.pyt`) that derives cartographic styling attributes for Ordnance Survey MasterMap Topography Layer feature classes in a single pass, replacing the set of saved Field Calculator (`.cal`) expressions otherwise run one field at a time.

For each supplied layer the tool confirms the required source attributes are present, adds the styling output fields with the correct type if they are missing, and populates them from the source attributes using a single, maintainable set of classification rules.

## Requirements

- ArcGIS Pro (tested with `arcpy`, Python 3.x)
- OS MasterMap Topography Layer feature classes with their standard attributes (`featurecode`, `descriptivegroup`, `descriptiveterm`, `make`, `physicalpresence`, `orientation`, `anchorposition`)

## Installation

1. Download `MasterMapStyling.pyt`.
2. In ArcGIS Pro, open the **Catalog** pane, right-click **Toolboxes** → **Add Toolbox**, and browse to the file.
3. Expand the toolbox and open **Apply MasterMap Cartographic Styling**.

## Usage

1. Open the tool. Six optional layer slots are provided — supply only the layers you have (drag them in from the **Contents** pane).
2. Leave **Add output fields if missing** ticked on first run so the styling fields are created with the correct types. On subsequent runs it simply overwrites the values.
3. Run. Progress and feature counts are reported in the tool messages.

Apply symbology separately with a unique-value renderer on `style_code` / `style_description` (for example via a saved `.lyrx`).

## Outputs

| Layer | Output fields |
|---|---|
| TopographicArea | `style_code` (Long), `style_description` (Text) |
| TopographicLine | `style_code` (Long), `style_description` (Text) |
| TopographicPoint | `style_code` (Long), `style_description` (Text) |
| BoundaryLine | `style_code` (Long), `style_description` (Text) |
| CartographicSymbol | `style_code` (Long), `style_description` (Text) |
| CartographicText | `style_code` (Long), `style_description` (Text), `colour_code` (Long), `font_code` (Long), `rotation` (Double), `geo_x` (Double), `geo_y` (Double), `anchor` (Text) |

## How it works

The classification rules live once, in Python functions at the top of the toolbox — one per layer. Each returns a tuple, and a configuration block maps every output field to the correct value. This keeps a single source of truth, rather than paired `style_code` / `style_description` expressions that must be kept in step. Population is done in one `UpdateCursor` pass per layer.

## Notes

- The tool reads the standard OS MasterMap attribute names. If your feature classes use different field names, edit the `source_fields` entries in `LAYER_CONFIG`.
- It assumes a non-versioned workspace (for example a file geodatabase). For a versioned enterprise geodatabase, wrap the cursor in an edit session.

## Licence

Released under the MIT Licence — see [LICENSE](LICENSE).

## Citation

If you use this toolbox, please cite it via its Figshare release (DOI to be added on publication) or using the metadata in [CITATION.cff](CITATION.cff).

## Author

Alexander T. R. Birkett — University of Bristol
GitHub: [@atrbirkett](https://github.com/atrbirkett)
