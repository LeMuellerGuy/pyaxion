import warnings

from numpy import uint32, nonzero

class PlateTypes:
    Empty = uint32(0)
    # All the channels of a Muse, in artichoke order
    LinearSingleWell64 = uint32(0x0400000)
    # Muse single-well plate
    P200D30S = uint32(0x0400001)
    # All the channels of an Maestro Edge, in artichoke order
    LinearSixWell = uint32(0x1800000)
    # Standard 24 well plate
    TwentyFourWell = uint32(0x1800001)
    # Circuit 24 well plate
    TwentyFourWellCircuit = uint32(0x1800002)
    # Maestro Edge 6-well plate
    SixWell = uint32(0x1800003)
    # 24-well Lumos plate
    TwentyFourWellLumos = uint32(0x1800004)
    # Electrode-less 24-Well OptiClear
    TwentyFourWellOptiClear =  uint32(0x1800005)
    # All the channels of a Maestro / Mastro Pro, in artichoke order
    LinearTwelveWell = uint32(0x3000000)
    # Standard Maestro 12 well plate
    TwelveWell = uint32(0x3000001)
    # Opaque Maestro 48 well plate
    FortyEightWell = uint32(0x3000002)
    # Standard Maestro 96 well plate
    NinetySixWell =    uint32(0x3000003)
    # Transparent Maestro 48 well plate
    FortyEightWellTransparent =    uint32(0x3000004)
    # Standard Maestro 384 well plate/ Reserved01
    ThreeEightyFourWell =    uint32(0x3000005)
    # Standard Lumos 48-well plate
    FortyEightWellLumos = uint32(0x3000006)
    # E-Stim+ Classic MEA 48 well plate
    FortyEightWellEStimPlus =    uint32(0x3000007)
    # Circuit Maestro 96 well plate
    NinetySixWellCircuit = uint32(0x3000008)
    # Transparent Maestro 96 well plate
    NinetySixWellTransparent = uint32(0x3000009)
    # 96-well Lumos platee
    NinetySixWellLumos = uint32(0x300000A)
    # Circuit 48 well plate
    FortyEightWellCircuit = uint32(0x300000B)
    # Classic FortyEightWell plates with AccuSpot thingys
    FortyEightWellAccuSpot = uint32(0x300000C)
    # Electrode-less 48-Well OptiClear
    FortyEightWellOptiClear = uint32(0x300000D)
    # Electrode-less 96-Well OptiClear
    NinetySixWellOptiClear = uint32(0x300000E)
    #Reserved 2
    Reserved2 = uint32(0x300000F)
    #CytoView-Z 384 well plate
    ThreeEightyFourWellImpedance = uint32(0x3000010)
    #Netri Dual Link Pro
    NetriDualLinkPro = uint32(0x3000011)
    #Netri DualLinkShift Pro
    NetriDualLinkShiftPro = uint32(0x3000012)
    #Netri TrialLink Pro
    NetriTrialLinkPro = uint32(0x3000013)
    #Reserved
    Reserved04 = uint32(0x3000014)
    #CytoView MEA 48 organoid plate
    FortyEightWellOrganoid = uint32(0x3000015)
    #CytoView MEA 12 well transparent
    TwelveWellTransparent = uint32(0x3000016)
    #Empty Socket
    CreatorKitChipEmpty = uint32(0)
    #Smart Chip
    CreatorKitChipSmart = uint32(1)
    #3DMap chip
    CreatorKitChip3DMap = uint32(2)
    #Sphero-HD chip
    CreatorKitChipSpheroHD = uint32(3)
    #Custom chip
    CreatorKitChipCustom = uint32(4)

    MUSE_MASK = uint32(0x0400000)
    MAESTRO_MASK = uint32(0x3000000)
    EDGE_MASK = uint32(0x1800000)
    CREATOR_MASK = uint32(0x0800000)

    PLATE_ID_MASK = uint32(0x0000003F)

    CHIP_MASK = uint32(0x0000001F)
    LEFT_CHIP_SHIFT = uint32(11)
    RIGHT_CHIP_SHIFT = uint32(6)

    LEFT_CHIP_MASK = CHIP_MASK << LEFT_CHIP_SHIFT
    RIGHT_CHIP_MASK = CHIP_MASK << RIGHT_CHIP_SHIFT


    MuseElectrodeMap = [[1, 1, 8, 8],   # LinearSingleWell64
                        [1, 1, 8, 8]]   # P200D30S

    CreatorElectrodeMap = [[1,2,8,8], # MEA Creator Kit "2-well"
                           [1,2,9,9], # Sarlacc
                           [2,4,6,4]] # Valley

    EdgeElectrodeMap = [[2, 3, 8, 8],   # LinearSixWell
                        [4, 6, 4, 4],   # TwentyFourWell
                        [4, 6, 4, 4],   # TwentyFourWellCircuit
                        [2, 3, 8, 8],   # SixWell
                        [4, 6, 4, 4],   # TwentyFourWellLumos
                        [4, 6, 0, 0],   # TwentyFourWellOptiClear
                        [8, 12, 0, 0],  # NinetySixWellImpedance
                        [8, 12, 0, 0],  # NinetySixWellImpedanceConductiveTech
                        [2,4,11, 5],    # NetriDualLinkEdge
                        [2,4,11, 5],    # NetriDualLinkShiftEdge
                        [2,4,11, 5],    #NetriTrialLinkEdge
                        [2,4,11, 5],    #Reserved03
                        ]

    MaestroElectrodeMap = [ [3, 4, 8, 8],     # LinearTwelveWell
                            [3, 4, 8, 8],     # TwelveWell
                            [6, 8, 4, 4],     # FortyEightWell
                            [8, 12, 3, 3],    # NinetySixWell
                            [6, 8, 4, 4],     # FortyEightWellTransparent
                            [16, 24, 2, 1],   # ThreeEightyFourWell/Reserved01
                            [6, 8, 4, 4],     # FortyEightWellLumos
                            [6, 8, 4, 4],     # FortyEightWellEStimPlus
                            [8, 12, 3, 3],    # NinetySixWellCircuit
                            [8, 12, 3, 3],    # NinetySixWellTransparent
                            [8, 12, 3, 3],    # NinetySixWellLumos
                            [6, 8, 4, 4],     # FortyEightWellCircuit
                            [6, 8, 4, 4],     # FortyEightWellAccuSpot
                            [6, 8, 0, 0],     # FortyEightWellOptiClear
                            [8, 12, 0, 0],    # NinetySixWellOptiClear
                            [8,12,3,3],      #Reserved2
                            [16,24,0,0],     #ThreeEightyFourWellImpedance
                            [4,4,11,5],       #NetriDualLinkPro
                            [4,4,11,5],       #NetriDualLinkShiftPro
                            [4,4,11,5],       #NetriTrialLinkPro
                            [4,4,11,5],       #Reserved04
                            [6,8,4,4],        #FortyEightWellOrganoid
                            [3,4,8,8]]        #TwelveWellTransparent

    @staticmethod
    def get_well_dimensions(plate_type:uint32):
        """Returns a 2-element array of plate dimensions.

        Args:
            plateType (uint32): Numeric identifier of the plate (see static fields of this class)

        Returns:
            Tuple[int, int] | Tuple[]: 
            - Number of well rows, Number of well columns
            - Returns empty tuple if plate is not recognized
        """
        offset = plate_type & PlateTypes.PLATE_ID_MASK
        if plate_type == PlateTypes.Empty:
            return ()
        elif plate_type & PlateTypes.MUSE_MASK == PlateTypes.MUSE_MASK:
            return tuple(PlateTypes.MuseElectrodeMap[offset][:2])
        elif plate_type & PlateTypes.MAESTRO_MASK == PlateTypes.MAESTRO_MASK:
            return tuple(PlateTypes.MaestroElectrodeMap[offset][:2])
        elif plate_type & PlateTypes.EDGE_MASK == PlateTypes.EDGE_MASK:
            return tuple(PlateTypes.EdgeElectrodeMap[offset][:2])
        elif plate_type & PlateTypes.CREATOR_MASK == PlateTypes.CREATOR_MASK:
            offset = PlateTypes.get_chip_offset_chimera(plate_type)
            return tuple(PlateTypes.CreatorElectrodeMap[offset])
        else:
            print("File has an unknown plate type. The matlab scripts this is" \
            "based on may have been outdated.")
            return ()

    @staticmethod
    def get_electrode_dimensions(plate_type:uint32):
        """Returns a 2-element array of plate dimensions.
        
        Notes:
        - wells of a 96-well plates have 3 electrode rows and 3
            electrode columns.  However, the second row contains only 2
            valid electrodes.
        - wells of netri plates generally have 48 electrodes per well but a number of the mapping
            entries have no electrode:
            11, 15, 61, 63, 65, b1, b5
        Args:
            plateType (uint32): Numeric identifier of the plate (see static fields of this class)

        Returns:
            Tuple[int, int, int, int] | Tuple[]: 
            - Number of well rows, Number of well columns, Number of electrode rows,
                Number of electrode columns
            - Returns empty tuple if plate is not recognized
        """
        offset = plate_type & PlateTypes.PLATE_ID_MASK
        if plate_type == PlateTypes.Empty:
            return ()
        elif plate_type & PlateTypes.MUSE_MASK == PlateTypes.MUSE_MASK:
            return tuple(PlateTypes.MuseElectrodeMap[offset])
        elif plate_type & PlateTypes.MAESTRO_MASK == PlateTypes.MAESTRO_MASK:
            return tuple(PlateTypes.MaestroElectrodeMap[offset])
        elif plate_type & PlateTypes.EDGE_MASK == PlateTypes.EDGE_MASK:
            return tuple(PlateTypes.EdgeElectrodeMap[offset])
        elif plate_type & PlateTypes.CREATOR_MASK == PlateTypes.CREATOR_MASK:
            offset = PlateTypes.get_chip_offset_chimera(plate_type)
            return tuple(PlateTypes.CreatorElectrodeMap[offset])
        else:
            print("File has an unknown plate type. The matlab scripts this is based" \
            "on may have been outdated.")
            return ()

    @staticmethod
    def is_chimera(plateType:uint32):
        return (plateType & PlateTypes.CREATOR_MASK) == PlateTypes.CREATOR_MASK

    @staticmethod
    def get_chip_id(plateType:uint32, left_chip:bool):
        if left_chip:
            return (plateType & -PlateTypes.LEFT_CHIP_MASK) >> PlateTypes.LEFT_CHIP_SHIFT
        else:
            return (plateType & -PlateTypes.RIGHT_CHIP_MASK) >> PlateTypes.RIGHT_CHIP_SHIFT

    @staticmethod
    def get_chimera_chip_type(plate_type:uint32):
        chips = [PlateTypes.get_chip_id(plate_type, True),
                 PlateTypes.get_chip_id(plate_type, False)]

        if all(chip == PlateTypes.CreatorKitChipEmpty for chip in chips):
            return PlateTypes.CreatorKitChipEmpty
        else:
            non_smart = nonzero([chip > PlateTypes.CreatorKitChipSmart for chip in chips])[0]
            if len(non_smart) == 0:
                return PlateTypes.CreatorKitChipSmart
            return chips[non_smart[0]]

    @staticmethod
    def get_chip_offset_chimera(plate_type:uint32):
        """Returns appropriate offset into the CreatorElectrodeMap array."""
        # indices reduced by 1 compared to the matlab reference.
        id_ = PlateTypes.get_chimera_chip_type(plate_type)
        match id_:
            case (PlateTypes.CreatorKitChipEmpty, PlateTypes.CreatorKitChipSmart,
                  PlateTypes.CreatorKitChipCustom):
                return 0
            case PlateTypes.CreatorKitChip3DMap:
                return 1
            case PlateTypes.CreatorKitChipSpheroHD:
                return 2
            case _:
                warnings.warn("Unknown chip type in get_chip_offset_chimera, defaulting to 0")
                return 0
