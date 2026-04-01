from enum import IntEnum

# original uses uint16, check whether this is important or not


class TagType(IntEnum):
    # Deleted: Tag revision where this TagGUID has been deleted
    # remarks: This is a special case, Tags may alternate between this
    #          type and their own as they are deleted / undeleted
    DELETED = 0

    # WellTreatment: Describes the treatment state of a well in a file
    WELL_TREATMENT = 1

    # UserAnnotation: Time-based note added to the file by the user
    USER_ANNOTATION = 2

    # SystemAnnotation: Time-based note added to the file by Axis
    SYSTEM_ANNOTATION = 3

    # DataLossEvent: Tag that records any loss of data in the system that affects this
    #                recorded file.
    # Remarks: Coming soon, Currently Unused!
    DATA_LOSS_EVENT = 4

    # StimulationEvent: Tag that describes a stimulation that was applied to the plate
    #                   during recording
    STIMULATION_EVENT = 5

    # StimulationChannelGroup: Tag that lists the channels that were loaded for stimulation for a StimulationEvent
    #                         Many StimulationEvent tags may reference the same StimulationChannelGroup
    STIMULATION_CHANNEL_GROUP = 6

    # StimulationWaveform: Tag that lists the stimulation that was applied for stimulation for a StimulationEvent
    #                     Many StimulationEvent tags may reference the same StimulationWaveform
    STIMULATION_WAVEFORM = 7

    # CalibrationTag: Tag that is used for Axis's internal calibration
    #                 of noise measurements (Use is currently not
    #                 supported in Matlab)
    CALIBRATION_TAG = 8

    # StimulationLedGroup: Tag that lists the LEDs that were loaded for stimulation for a StimulationEvent
    #                     Many StimulationEvent tags may reference the same StimulationLedGroup
    STIMULATION_LED_GROUP = 9

    # DoseEvent: (Unsupported in this library)
    DOSE_EVENT = 10

    # StringDictonaryKeyPair: (Unsupported in this library)
    STRING_DICTIONARY_KEY_PAIR = 11

    # LeapInductionEvent: Tag marking a LEAP induction event for a plate/recording
    LEAP_INDUCTION_EVENT = 12

    # ViabilityImpedanceEvent: Tag marking a Viability Impedance measurement for a plate/recording
    VIABILITY_IMPEDANCE_EVENT = 13
