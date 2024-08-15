import adsk.core
import os
from ...lib import fusion360utils as futil
from ... import config

app = adsk.core.Application.get()
ui = app.userInterface
design = adsk.fusion.Design.cast(app.activeProduct)
userParams = design.userParameters

CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_cmdDialog'
CMD_NAME = 'Command Dialog Sample'
CMD_Description = 'A Fusion 360 Add-in Command with a dialog'
IS_PROMOTED = True

WORKSPACE_ID = 'FusionSolidEnvironment'
PANEL_ID = 'SolidScriptsAddinsPanel'
COMMAND_BESIDE_ID = 'ScriptsManagerCommand'
ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', '')

local_handlers = []

PARAMS_CONFIG = {
    "width": {"label": "Width", "unit": "mm", "type": "slider", "min": 0, "max": 100, "step": 150},
    "length": {"label": "Length", "unit": "mm", "type": "slider", "min": 0, "max": 300, "step": 150},
    "hole_size": {"label": "Hole Size", "unit": "mm", "type": "slider", "min": 0, "max": 10},
    "grid_size": {"label": "Grid Size", "type": "dropdown", "options": ["100", "50", "25"]},
    "thickness": {"label": "Thickness", "unit": "mm", "type": "slider", "min": 0, "max": 2},
    "depth": {"label": "Depth", "unit": "mm", "type": "slider", "min": 0, "max": 40},
}

def find_rib_distances_nearest(width, length, grid_size, min_rib_dist=100, max_rib_dist=300, target_dist=150):
    if grid_size <= 0:
        return "Grid size must be a positive integer."
    
    half_grid_size = grid_size // 2
    possible_dists = [d for d in range(min_rib_dist, max_rib_dist + 1) if d % half_grid_size == 0]
    
    if not possible_dists:
        return "Nie można znaleźć odpowiednich odległości między żebrami w podanym przedziale."

    base_dist = min(possible_dists, key=lambda x: abs(x - target_dist))

    hor_ribs_dist = base_dist
    ver_ribs_dist = base_dist

    if length >= 2 * width:
        hor_ribs_dist = 2 * ver_ribs_dist
    elif width >= 2 * length:
        ver_ribs_dist = 2 * hor_ribs_dist

    return hor_ribs_dist, ver_ribs_dist

def start():
    cmd_def = ui.commandDefinitions.addButtonDefinition(CMD_ID, CMD_NAME, CMD_Description, ICON_FOLDER)
    futil.add_handler(cmd_def.commandCreated, command_created)
    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    control = panel.controls.addCommand(cmd_def, COMMAND_BESIDE_ID, False)
    control.isPromoted = IS_PROMOTED

def stop():
    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    command_control = panel.controls.itemById(CMD_ID)
    command_definition = ui.commandDefinitions.itemById(CMD_ID)

    if command_control:
        command_control.deleteMe()
    if command_definition:
        command_definition.deleteMe()

def add_slider(inputs, param_name, config):
    unit = config.get("unit", "")
    slider = inputs.addFloatSliderCommandInput(f'float_slider_{param_name}', config["label"], unit, config["min"], config["max"], False)
    slider.valueOne = userParams.itemByName(param_name).value

def add_dropdown(inputs, param_name, config):
    dropdown = inputs.addDropDownCommandInput(f'dropdown_{param_name}', config["label"], adsk.core.DropDownStyles.TextListDropDownStyle)
    for option in config["options"]:
        dropdown.listItems.add(option, option == config["options"][0])

def add_checkbox(inputs, param_name, config):
    checkbox = inputs.addBoolValueInput(f'checkbox_{param_name}', config["label"], True, '', False)

def command_created(args: adsk.core.CommandCreatedEventArgs):
    futil.log(f'{CMD_NAME} Command Created Event')
    inputs = args.command.commandInputs

    for param_name, config in PARAMS_CONFIG.items():
        if config["type"] == "slider":
            add_slider(inputs, param_name, config)
        elif config["type"] == "dropdown":
            add_dropdown(inputs, param_name, config)
        elif config["type"] == "checkbox":
            add_checkbox(inputs, param_name, config)

    futil.add_handler(args.command.execute, command_execute, local_handlers=local_handlers)
    futil.add_handler(args.command.inputChanged, command_input_changed, local_handlers=local_handlers)
    futil.add_handler(args.command.executePreview, command_preview, local_handlers=local_handlers)
    futil.add_handler(args.command.validateInputs, command_validate_input, local_handlers=local_handlers)
    futil.add_handler(args.command.destroy, command_destroy, local_handlers=local_handlers)

def command_execute(args: adsk.core.CommandEventArgs):
    futil.log(f'{CMD_NAME} Command Execute Event')
    inputs = args.command.commandInputs

    width = userParams.itemByName('width').value
    length = userParams.itemByName('length').value
    grid_size = int(userParams.itemByName('grid_size').value)

    hor_ribs_dist, ver_ribs_dist = find_rib_distances_nearest(width, length, grid_size)

    userParams.itemByName('hor_ribs_dist').expression = f'{hor_ribs_dist} mm'
    userParams.itemByName('ver_ribs_dist').expression = f'{ver_ribs_dist} mm'

    for param_name, config in PARAMS_CONFIG.items():
        param = userParams.itemByName(param_name)
        if config["type"] == "slider":
            slider: adsk.core.FloatSliderCommandInput = inputs.itemById(f'float_slider_{param_name}')
            if slider and param:
                param.expression = slider.expressionOne
        elif config["type"] == "dropdown":
            dropdown: adsk.core.DropDownCommandInput = inputs.itemById(f'dropdown_{param_name}')
            if dropdown and param:
                selected_option = dropdown.selectedItem.name
                param.expression = selected_option
                futil.log(f'Selected option for {param_name}: {selected_option}')
        elif config["type"] == "checkbox":
            checkbox: adsk.core.BoolValueCommandInput = inputs.itemById(f'checkbox_{param_name}')
            if checkbox:
                is_checked = checkbox.value
                futil.log(f'{param_name} is checked: {is_checked}')

def command_preview(args: adsk.core.CommandEventArgs):
    futil.log(f'{CMD_NAME} Command Preview Event')

def command_input_changed(args: adsk.core.InputChangedEventArgs):
    futil.log(f'{CMD_NAME} Input Changed Event fired from a change to {args.input.id}')

def command_validate_input(args: adsk.core.ValidateInputsEventArgs):
    futil.log(f'{CMD_NAME} Validate Input Event')

def command_destroy(args: adsk.core.CommandEventArgs):
    futil.log(f'{CMD_NAME} Command Destroy Event')
    global local_handlers
    local_handlers = []
