"""Elite Dangerous action catalogue: maps each binding name in a .binds file to a
(context, friendly name) pair. Names not listed fall back to heuristics, so new
actions Frontier adds still get a sensible context and a readable label."""
import re

# context tag -> (label shown on the sheet, colour)
CTX = {
    "SHIP": ("SHIP", "#1f5fa8"), "UI": ("UI", "#6b6b6b"), "FSS": ("FSS", "#7a3fa0"),
    "DSS": ("DSS", "#a0408a"), "CAM": ("CAMERA", "#2e7d6b"), "MC": ("MULTICREW", "#8a6d1f"),
    "COL": ("COLONY", "#a0522d"), "SRV": ("SRV", "#4d7a1f"), "FOOT": ("ON FOOT", "#7a4d1f"),
    "MAP": ("GAL/SYS MAP", "#0f7c99"), "STORE": ("STORE/HOLO-ME", "#99520f"),
}
CTX_ORDER = list(CTX)

# Which StartPreset.4.start line (General, Ship, SRV, On foot) each context is read from.
PRESET_SLOT = {"SHIP": 1, "FSS": 1, "DSS": 1, "MC": 1, "SRV": 2, "FOOT": 3}  # everything else: 0

A = {
    "PrimaryFire": ("SHIP", "Primary fire"), "SecondaryFire": ("SHIP", "Secondary fire"),
    "DeployHardpointToggle": ("SHIP", "Deploy hardpoints"), "SelectTarget": ("SHIP", "Select target ahead"),
    "CycleNextTarget": ("SHIP", "Next target"), "CyclePreviousTarget": ("SHIP", "Previous target"),
    "CycleNextHostileTarget": ("SHIP", "Next hostile target"),
    "CyclePreviousHostileTarget": ("SHIP", "Previous hostile target"),
    "SelectHighestThreat": ("SHIP", "Select highest threat"),
    "CycleNextSubsystem": ("SHIP", "Next subsystem"), "CyclePreviousSubsystem": ("SHIP", "Previous subsystem"),
    "SetSpeed25": ("SHIP", "Throttle 25%"), "SetSpeed50": ("SHIP", "Throttle 50%"),
    "SetSpeed75": ("SHIP", "Throttle 75%"), "SetSpeed100": ("SHIP", "Throttle 100%"),
    "SetSpeedZero": ("SHIP", "Throttle 0%"), "SetSpeedMinus25": ("SHIP", "Throttle -25%"),
    "SetSpeedMinus50": ("SHIP", "Throttle -50%"), "SetSpeedMinus75": ("SHIP", "Throttle -75%"),
    "SetSpeedMinus100": ("SHIP", "Throttle -100%"),
    "Hyperspace": ("SHIP", "Hyperspace jump"), "Supercruise": ("SHIP", "Supercruise"),
    "HyperSuperCombination": ("SHIP", "Hyperspace/supercruise"),
    "CycleFireGroupNext": ("SHIP", "Next fire group"), "CycleFireGroupPrevious": ("SHIP", "Previous fire group"),
    "FireChaffLauncher": ("SHIP", "Fire chaff"), "NightVisionToggle": ("SHIP", "Night vision"),
    "TriggerFieldNeutraliser": ("SHIP", "Shutdown field neutraliser"),
    "IncreaseEnginesPower": ("SHIP", "Pips to ENG"), "IncreaseWeaponsPower": ("SHIP", "Pips to WEP"),
    "IncreaseSystemsPower": ("SHIP", "Pips to SYS"), "ResetPowerDistribution": ("SHIP", "Reset pips"),
    "FocusCommsPanel": ("SHIP", "Comms panel"), "FocusRightPanel": ("SHIP", "Right (internal) panel"),
    "FocusRadarPanel": ("SHIP", "Role panel"), "FocusLeftPanel": ("SHIP", "Left (external) panel"),
    "QuickCommsPanel": ("SHIP", "Quick comms"),
    "GalaxyMapOpen": ("SHIP", "Galaxy map"), "SystemMapOpen": ("SHIP", "System map"),
    "UI_Up": ("UI", "UI up"), "UI_Down": ("UI", "UI down"), "UI_Left": ("UI", "UI left"),
    "UI_Right": ("UI", "UI right"), "UI_Select": ("UI", "UI select"), "UI_Back": ("UI", "UI back"),
    "UI_Toggle": ("UI", "UI toggle"), "UIFocus": ("UI", "UI focus"),
    "CycleNextPanel": ("UI", "Next panel tab"), "CyclePreviousPanel": ("UI", "Previous panel tab"),
    "CycleNextPage": ("UI", "Next page"), "CyclePreviousPage": ("UI", "Previous page"),
    "ExplorationFSSEnter": ("FSS", "Enter FSS"), "ExplorationFSSQuit": ("FSS", "Exit FSS"),
    "ExplorationFSSDiscoveryScan": ("FSS", "Discovery scan (honk)"),
    "ExplorationFSSZoomIn": ("FSS", "Zoom in"), "ExplorationFSSZoomOut": ("FSS", "Zoom out"),
    "ExplorationFSSMiniZoomIn": ("FSS", "Mini zoom in"), "ExplorationFSSMiniZoomOut": ("FSS", "Mini zoom out"),
    "ExplorationFSSTarget": ("FSS", "Target"), "ExplorationFSSCameraYaw": ("FSS", "Camera yaw"),
    "ExplorationFSSCameraPitch": ("FSS", "Camera pitch"),
    "ExplorationFSSRadioTuningX_Increase": ("FSS", "Tune up"),
    "ExplorationFSSRadioTuningX_Decrease": ("FSS", "Tune down"),
    "ExplorationFSSRadioTuningAbsoluteX": ("FSS", "Tuning"),
    "ExplorationFSSCameraYawDecreaseButton": ("FSS", "Camera yaw left"),
    "ExplorationFSSCameraYawIncreaseButton": ("FSS", "Camera yaw right"),
    "ExplorationFSSCameraPitchIncreaseButton": ("FSS", "Camera pitch up"),
    "ExplorationFSSCameraPitchDecreaseButton": ("FSS", "Camera pitch down"),
    "ExplorationFSSShowHelp": ("FSS", "Help"),
    "ExplorationSAAChangeScannedAreaViewToggle": ("DSS", "Toggle scanned-area view"),
    "ExplorationSAANextGenus": ("DSS", "Next genus"), "ExplorationSAAPreviousGenus": ("DSS", "Previous genus"),
    "ExplorationSAAExitThirdPerson": ("DSS", "Exit DSS"), "ExplorationSAAShowHelp": ("DSS", "Help"),
    "SAAThirdPersonYawAxisRaw": ("DSS", "Yaw"), "SAAThirdPersonPitchAxisRaw": ("DSS", "Pitch"),
    "SAAThirdPersonFovAxisRaw": ("DSS", "FOV"),
    "SAAThirdPersonFovOutButton": ("DSS", "FOV out"), "SAAThirdPersonFovInButton": ("DSS", "FOV in"),
    "SAAThirdPersonYawLeftButton": ("DSS", "Yaw left"), "SAAThirdPersonYawRightButton": ("DSS", "Yaw right"),
    "SAAThirdPersonPitchUpButton": ("DSS", "Pitch up"), "SAAThirdPersonPitchDownButton": ("DSS", "Pitch down"),
    "VanityCameraScrollRight": ("CAM", "Next ship camera"), "VanityCameraScrollLeft": ("CAM", "Previous ship camera"),
    "QuitCamera": ("CAM", "Exit camera"), "ToggleFreeCam": ("CAM", "Toggle free cam"),
    "FreeCamToggleHUD": ("CAM", "Free cam HUD"),
    "YawCamera": ("CAM", "Free cam yaw"), "PitchCamera": ("CAM", "Free cam pitch"), "RollCamera": ("CAM", "Free cam roll"),
    "RollCameraLeft": ("CAM", "Free cam roll left"), "RollCameraRight": ("CAM", "Free cam roll right"),
    "MoveFreeCamForward": ("CAM", "Free cam forward"), "MoveFreeCamBackwards": ("CAM", "Free cam backward"),
    "MoveFreeCamLeft": ("CAM", "Free cam left"), "MoveFreeCamRight": ("CAM", "Free cam right"),
    "MoveFreeCamUp": ("CAM", "Free cam up"), "MoveFreeCamDown": ("CAM", "Free cam down"),
    "MoveFreeCamX": ("CAM", "Free cam move X"), "MoveFreeCamY": ("CAM", "Free cam move Y"),
    "MoveFreeCamZ": ("CAM", "Free cam move Z"), "FreeCamZoomIn": ("CAM", "Free cam zoom in"),
    "FreeCamZoomOut": ("CAM", "Free cam zoom out"), "FStopInc": ("CAM", "F-stop +"), "FStopDec": ("CAM", "F-stop -"),
    "FreeCamSpeedInc": ("CAM", "Free cam speed +"), "FreeCamSpeedDec": ("CAM", "Free cam speed -"),
    "MultiCrewThirdPersonPitchUpButton": ("MC", "3rd-person pitch up"),
    "MultiCrewThirdPersonPitchDownButton": ("MC", "3rd-person pitch down"),
    "MultiCrewThirdPersonYawLeftButton": ("MC", "3rd-person yaw left"),
    "MultiCrewThirdPersonYawRightButton": ("MC", "3rd-person yaw right"),
    "MultiCrewPrimaryFire": ("MC", "Primary fire"), "MultiCrewSecondaryFire": ("MC", "Secondary fire"),
    "PlaceSettlement": ("COL", "Place settlement"), "ExitSettlementPlacementCamera": ("COL", "Exit placement camera"),
    "RotateSettlement": ("COL", "Rotate settlement"), "RotateSettlementLeft": ("COL", "Rotate settlement left"),
    "RotateSettlementRight": ("COL", "Rotate settlement right"),
    "ChangeConstructionOption": ("COL", "Change construction option"),
    "YawPlacementCamera": ("COL", "Placement cam yaw"), "PitchPlacementCamera": ("COL", "Placement cam pitch"),
    "MovePlacementCamForward": ("COL", "Placement cam forward"),
    "MovePlacementCamBackwards": ("COL", "Placement cam backward"),
    "MovePlacementCamLeft": ("COL", "Placement cam left"), "MovePlacementCamRight": ("COL", "Placement cam right"),
    "MovePlacementCamX": ("COL", "Placement cam X"), "MovePlacementCamY": ("COL", "Placement cam Y"),
    "MovePlacementCamZ": ("COL", "Placement cam Z"),
    "PlacementCamSpeedInc": ("COL", "Placement cam speed +"), "PlacementCamSpeedDec": ("COL", "Placement cam speed -"),
    "YawAxisRaw": ("SHIP", "Yaw"), "PitchAxisRaw": ("SHIP", "Pitch"), "RollAxisRaw": ("SHIP", "Roll"),
    "ThrottleAxis": ("SHIP", "Throttle"), "LateralThrustRaw": ("SHIP", "Lateral thrust"),
    "VerticalThrustRaw": ("SHIP", "Vertical thrust"), "AheadThrust": ("SHIP", "Forward thrust"),
    "ForwardThrustButton": ("SHIP", "Thrust forward"), "BackwardThrustButton": ("SHIP", "Thrust backward"),
    "LeftThrustButton": ("SHIP", "Thrust left"), "RightThrustButton": ("SHIP", "Thrust right"),
    "UpThrustButton": ("SHIP", "Thrust up"), "DownThrustButton": ("SHIP", "Thrust down"),
    "ForwardKey": ("SHIP", "Increase throttle"), "BackwardKey": ("SHIP", "Decrease throttle"),
    "IncreaseSpeedButtonPartial": ("SHIP", "Throttle up (partial)"),
    "DecreaseSpeedButtonPartial": ("SHIP", "Throttle down (partial)"),
    "RollLeftButton": ("SHIP", "Roll left"), "RollRightButton": ("SHIP", "Roll right"),
    "PitchUpButton": ("SHIP", "Pitch up"), "PitchDownButton": ("SHIP", "Pitch down"),
    "YawLeftButton": ("SHIP", "Yaw left"), "YawRightButton": ("SHIP", "Yaw right"),
    "VerticalThrustersButton": ("SHIP", "Vertical thrusters"),
    "LandingGearToggle": ("SHIP", "Landing gear"), "ToggleCargoScoop": ("SHIP", "Cargo scoop"),
    "DeployHeatSink": ("SHIP", "Heat sink"), "ShipSpotLightToggle": ("SHIP", "Ship lights"),
    "UseBoostJuice": ("SHIP", "Boost"), "ToggleFlightAssist": ("SHIP", "Flight assist"),
    "UseShieldCell": ("SHIP", "Shield cell"), "ChargeECM": ("SHIP", "ECM"),
    "OrbitLinesToggle": ("SHIP", "Orbit lines"), "PlayerHUDModeToggle": ("SHIP", "HUD mode"),
    "HeadLookToggle": ("SHIP", "Head look"), "HeadLookYawLeft": ("SHIP", "Head look left"),
    "HeadLookYawRight": ("SHIP", "Head look right"), "HeadLookPitchUp": ("SHIP", "Head look up"),
    "HeadLookPitchDown": ("SHIP", "Head look down"), "HeadLookReset": ("SHIP", "Head look reset"),
    "TargetWingman0": ("SHIP", "Target wingman 1"), "TargetWingman1": ("SHIP", "Target wingman 2"),
    "TargetWingman2": ("SHIP", "Target wingman 3"), "SelectTargetsTarget": ("SHIP", "Wingman's target"),
    "TargetNextRouteSystem": ("SHIP", "Next system in route"), "WingNavLock": ("SHIP", "Wing nav lock"),
    "CamTranslateXAxis": ("MAP", "Move X"), "CamTranslateYAxis": ("MAP", "Move Y"),
    "CamTranslateZHold": ("MAP", "Z translate"), "CamTranslateUp": ("MAP", "Move up"),
    "CamTranslateDown": ("MAP", "Move down"), "CamYawAxis": ("MAP", "Yaw"), "CamPitchAxis": ("MAP", "Pitch"),
    "CamZoomIn": ("MAP", "Zoom in"), "CamZoomOut": ("MAP", "Zoom out"), "CamZoomAxis": ("MAP", "Zoom"),
    "GalaxyMapHome": ("MAP", "Galaxy map home"),
    "StoreToggle": ("STORE", "Toggle preview"), "StoreYawCamera": ("STORE", "Camera yaw"),
    "StorePitchCamera": ("STORE", "Camera pitch"), "StoreCamZoomIn": ("STORE", "Zoom in"),
    "StoreCamZoomOut": ("STORE", "Zoom out"), "CommanderCreator_Undo": ("STORE", "Holo-Me undo"),
    "CommanderCreator_Redo": ("STORE", "Holo-Me redo"), "CommanderCreator_Rotation": ("STORE", "Holo-Me rotate"),
    "ToggleDriveAssist": ("SRV", "Drive assist"), "SteeringAxis": ("SRV", "Steering"),
    "BuggyRollAxisRaw": ("SRV", "Roll"), "BuggyPitchAxis": ("SRV", "Pitch"),
    "BuggyTurretYawAxisRaw": ("SRV", "Turret yaw"), "BuggyTurretPitchAxisRaw": ("SRV", "Turret pitch"),
    "BuggyPrimaryFireButton": ("SRV", "Primary fire"), "BuggySecondaryFireButton": ("SRV", "Secondary fire"),
    "BuggyCycleFireGroupNext": ("SRV", "Next fire group"), "BuggyCycleFireGroupPrevious": ("SRV", "Previous fire group"),
    "ToggleBuggyTurretButton": ("SRV", "Turret mode"), "AutoBreakBuggyButton": ("SRV", "Handbrake"),
    "HeadlightsBuggyButton": ("SRV", "Headlights"), "RecallDismissShip": ("SRV", "Recall/dismiss ship"),
    "SelectTarget_Buggy": ("SRV", "Select target"), "OpenCodexGoToDiscovery_Buggy": ("SRV", "Codex discovery"),
    "ToggleCargoScoop_Buggy": ("SRV", "Cargo scoop"), "ResetPowerDistribution_Buggy": ("SRV", "Reset pips"),
    "IncreaseSystemsPower_Buggy": ("SRV", "Pips to SYS"), "IncreaseEnginesPower_Buggy": ("SRV", "Pips to ENG"),
    "IncreaseWeaponsPower_Buggy": ("SRV", "Pips to WEP"), "PlayerHUDModeToggle_Buggy": ("SRV", "HUD mode"),
    "FocusLeftPanel_Buggy": ("SRV", "Left panel"), "FocusRightPanel_Buggy": ("SRV", "Right panel"),
    "FocusCommsPanel_Buggy": ("SRV", "Comms panel"), "FocusRadarPanel_Buggy": ("SRV", "Role panel"),
    "BuggyToggleReverseThrottleInput": ("SRV", "Reverse"), "IncreaseSpeedButtonMax": ("SRV", "Accelerate"),
    "DecreaseSpeedButtonMax": ("SRV", "Decelerate"), "VerticalThrustersButton_Buggy": ("SRV", "Jump"),
    "HumanoidForwardAxis": ("FOOT", "Move fwd/back"), "HumanoidStrafeAxis": ("FOOT", "Strafe"),
    "HumanoidRotateAxis": ("FOOT", "Look left/right"), "HumanoidPitchAxis": ("FOOT", "Look up/down"),
    "HumanoidSprintButton": ("FOOT", "Sprint"), "HumanoidCrouchButton": ("FOOT", "Crouch"),
    "HumanoidJumpButton": ("FOOT", "Jump"), "HumanoidMeleeButton": ("FOOT", "Melee"),
    "HumanoidPrimaryFireButton": ("FOOT", "Fire"), "HumanoidZoomButton": ("FOOT", "Aim/zoom"),
    "HumanoidReloadButton": ("FOOT", "Reload"), "HumanoidSwitchWeapon": ("FOOT", "Switch weapon"),
    "HumanoidHideWeaponButton": ("FOOT", "Holster weapon"), "HumanoidThrowGrenadeButton": ("FOOT", "Throw grenade"),
    "HumanoidPrimaryInteractButton": ("FOOT", "Interact"),
    "HumanoidSecondaryInteractButton": ("FOOT", "Secondary interact"),
    "HumanoidToggleToolModeButton": ("FOOT", "Tool mode"), "HumanoidToggleShieldsButton": ("FOOT", "Shields"),
    "HumanoidToggleFlashlightButton": ("FOOT", "Flashlight"), "HumanoidToggleNightVisionButton": ("FOOT", "Night vision"),
    "HumanoidSwitchToRechargeTool": ("FOOT", "Energylink"), "HumanoidSwitchToCompAnalyser": ("FOOT", "Profile analyser"),
    "HumanoidSwitchToSuitTool": ("FOOT", "Suit tool"), "HumanoidItemWheelButton": ("FOOT", "Item wheel"),
    "HumanoidItemWheelButton_XAxis": ("FOOT", "Item wheel X"), "HumanoidItemWheelButton_YAxis": ("FOOT", "Item wheel Y"),
    "HumanoidUtilityWheelCycleMode": ("FOOT", "Utility wheel mode"),
    "HumanoidToggleMissionHelpPanelButton": ("FOOT", "Mission help"),
    "HumanoidOpenAccessPanelButton": ("FOOT", "Access panel"),
    "HumanoidConflictContextualUIButton": ("FOOT", "Conflict zone UI"),
    "HumanoidSelectPrimaryWeaponButton": ("FOOT", "Primary weapon"),
    "HumanoidSelectSecondaryWeaponButton": ("FOOT", "Secondary weapon"),
    "HumanoidSelectNextWeaponButton": ("FOOT", "Next weapon"), "HumanoidSelectPreviousWeaponButton": ("FOOT", "Previous weapon"),
    "HumanoidHealthPack": ("FOOT", "Medkit"), "HumanoidBattery": ("FOOT", "Energy cell"),
    "HumanoidClearAuthorityLevel": ("FOOT", "Clear authority level"),
    "QuickCommsPanel_Humanoid": ("FOOT", "Quick comms"),
}


ACRONYMS = {"ui": "UI", "fss": "FSS", "hmd": "HMD", "emp": "EMP", "pg": "PG", "fov": "FOV", "srv": "SRV",
            "ecm": "ECM", "hud": "HUD"}


def _words(name):
    landing = name.endswith("_Landing")
    name = re.sub(r"(_Buggy|_Humanoid|_Landing|Button|Raw)$", "", name)
    name = re.sub(r"^(Humanoid|Buggy|MultiCrew|ExplorationFSS|ExplorationSAA|SAAThirdPerson)", "", name)
    name = re.sub(r"^Cam(?=[A-Z])", "", name).replace("_", " ")
    s = re.sub(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])", " ", name).strip().lower()
    s = " ".join(ACRONYMS.get(w, w) for w in s.split())
    s = s[:1].upper() + s[1:] if s else name
    return s + (" (landing)" if landing else "")


def friendly(action):
    """Return (context, label) for an Elite Dangerous binding name."""
    if action in A:
        return A[action]
    a = action
    if a.endswith("_Buggy") or "Buggy" in a or a.startswith("Steer") or a.startswith("DriveSpeed"):
        ctx = "SRV"
    elif a.startswith("Humanoid") or a.endswith("_Humanoid"):
        ctx = "FOOT"
    elif a.startswith("ExplorationFSS"):
        ctx = "FSS"
    elif a.startswith("ExplorationSAA") or a.startswith("SAA"):
        ctx = "DSS"
    elif a.startswith("MultiCrew"):
        ctx = "MC"
    elif a.startswith("Store") or a.startswith("CommanderCreator"):
        ctx = "STORE"
    elif a.startswith("Cam") or "GalaxyMap" in a or "SystemMap" in a:
        ctx = "MAP"
    elif "Placement" in a or "Settlement" in a or "Construction" in a or "Coloni" in a:
        ctx = "COL"
    elif "FreeCam" in a or "Camera" in a or "Vanity" in a or a.startswith("FStop"):
        ctx = "CAM"
    elif a.startswith("UI_") or "Panel" in a or "Page" in a:
        ctx = "UI"
    else:
        ctx = "SHIP"
    return ctx, _words(a)
