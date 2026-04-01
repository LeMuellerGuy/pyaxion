import numpy as np

class StimulationEventData:
    """
    StimulationEventData: Structure that contains the data describing a
    marked, stimulation portion of a file
    """

    def __init__(self, id_:np.uint16, stim_duration:np.double,
                 artifact_elimination_duration:np.double,
                 channel_array_id_list:np.ndarray[np.uint16], description:str):
        self.id = id_
        self.stim_duration = stim_duration
        self.artifact_elim_duration = artifact_elimination_duration
        self.channel_array_id_list = channel_array_id_list
        self.description = description
