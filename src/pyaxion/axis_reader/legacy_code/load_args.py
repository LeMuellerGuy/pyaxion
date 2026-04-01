def _isscalar(__num):
    if isinstance(__num, (float, int)) :return True
    return False

class LoadArgs:
    wellVal = 1
    electrodeVal = 2
    timespanVal = 3
    dimensionsVal = 4
    expansionVal = 5
    
    supportedModifiers = ['SubsamplingFactor']
    
    ByPlateDimensions = 1
    ByWellDimensions = 3
    ByElectrodeDimensions = 5
    
    # i feel like this class could definetly use a rewrite
    # to demystify the argument structure
    # but I am not entirely sure how this class is used yet
    # so I kept it in the orginal state
    def __init__(self, argin):
        """
        Internal support function for AxisFile Construction
        loadAxISFileParseArgs Parses arguments for file readers
        
        Legal forms:
            LoadArgs()
            LoadArgs(well)
            LoadArgs(electrode)
            LoadArgs(well, electrode)
            LoadArgs(timespan)
            LoadArgs(well, timespan)
            LoadArgs(electrode, timespan)
            LoadArgs(well, electrode, timespan)
            LoadArgs(dimensions)
            LoadArgs(well, dimensions)
            LoadArgs(electrode, dimensions)
            LoadArgs(well, electrode, dimensions)
            LoadArgs(timespan, dimensions)
            LoadArgs(well, timespan, dimensions)
            LoadArgs(electrode, timespan, dimensions)
            LoadArgs(well, electrode, timespan, dimensions)
        
            LoadArgs(~, ~, ~, ~, {commands})
        
        
        Required arguments:
            filename    Pathname of the file to load
        
        Optional arguments:
            well        String listing which wells (in a multiwell file) to load.
                        Format is a comma-delimited string with whitespace ignored, e.g.
                        'A1, B2,C3' limits the data loaded to wells A1, B2, and C3.
                        Also acceptable: 'all' to load all wells.
                        If this parameter is omitted, all wells are loaded.
                        For a single-well file, this parameter is ignored.
        
            electrode   Which electrodes to load.  Format is either a comma-delimited string
                        with whitespace ignored (e.g. '11, 22,33') or a single channel number;
                        that is, a number, not part of a string.
                        Also acceptable: 'all' to load all channels and 'none', '-1', or -1
                        to load no data (returns only header information).
                        If this parameter is omitted, all channels are loaded.
        
            timespan    Span of time, in seconds, over which to load data.  Format is a two-element
                        array, [t0 t1], where t0 is the start time and t1 is the end time and both
                        are in seconds after the first sample in the file.  Samples returned are ones
                        that were taken at time >= t0 and <= t1.  The beginning of the file
                        is at 0 seconds.
                        If this parameter is omitted, the data is not filtered based on time.
        
            dimensions  Preferred number of dimensions to report the waveforms in.
                        Value must be a whole number scalar, and only certain values are allowed:
            
                        dimensions = 1 -> ByPlate: returns a vector of Waveform objects, 1 Waveform
                                          per signal in the plate
                        dimensions = 3 -> ByWell: Cell Array of vectors of waveform 1 Waveform per signal
                                          in the electrode with size (well Rows) x (well Columns)
                        dimensions = 5 -> ByElectrode: Cell Array of vectors of waveform 1 Waveform per .
                                          signal in the electrode with size (well Rows) x (well Columns) x
                                          (electrode Columns) x (electrode Rows)
            """
        self.Well = []
        self.Electrode = []
        self.Timespan = []
        self.Dimensions = []
        self.SubsamplingFactor = 1
        
        fLastArg = None
        
        fNumArgs = len(argin)
        
        if fNumArgs > 5:
            raise ValueError('Too many arguments specified')
        
        i = 0
        for i in range(fNumArgs):
            fCurrentArg = argin[i]

            # the idea here seems to be that they iterate the arguments
            # and based on what the last argument was, they perform
            # different actions
            
            if fCurrentArg is None:
                continue
            
            if fLastArg is None:
                fParseAsWell = LoadArgs.ParseWellOrElectrodeArgument(fCurrentArg, LoadArgs.wellVal)
                if fParseAsWell is not None:
                    self.Well = fParseAsWell
                    fLastArg = LoadArgs.wellVal
                    continue
            
            if fLastArg is None or fLastArg == LoadArgs.wellVal:
                fParseAsElectrode = LoadArgs.ParseWellOrElectrodeArgument(fCurrentArg, LoadArgs.electrodeVal)
                if fParseAsElectrode is not None:
                    self.Electrode = fParseAsElectrode
                    fLastArg = LoadArgs.electrodeVal
                    continue
            
            if fLastArg is None or fLastArg == LoadArgs.wellVal or fLastArg == LoadArgs.electrodeVal:
                fParseAsTimespan = LoadArgs.ParseTimespanArgument(fCurrentArg)
                if fParseAsTimespan is not None:
                    if isinstance(fParseAsTimespan, (list, tuple)) and len(fParseAsTimespan) == 2 and fParseAsTimespan[1] < fParseAsTimespan[0]:
                        raise ValueError('Invalid timespan argument: t1 < t0')
                    
                    self.Timespan = fParseAsTimespan
                    fLastArg = LoadArgs.timespanVal
                    continue
            
            if fLastArg is None or fLastArg == LoadArgs.wellVal or fLastArg == LoadArgs.electrodeVal or fLastArg == LoadArgs.timespanVal:
                if isinstance(fCurrentArg, (int, float)):
                    if fCurrentArg in [LoadArgs.ByPlateDimensions, LoadArgs.ByWellDimensions, LoadArgs.ByElectrodeDimensions]:
                        self.Dimensions = fCurrentArg
                    else:
                        self.Dimensions = []
                    fLastArg = LoadArgs.dimensionsVal
                    continue
            
            if fLastArg is None or isinstance(fCurrentArg, list):
                self.ParseExpansionArguments(self, fCurrentArg)
                fLastArg = LoadArgs.expansionVal
                continue
            
            raise ValueError(f'Invalid argument #{i+1} to LoadArgs')
        
        if not self.Well:
            self.Well = 'all'
        
        if not self.Electrode:
            self.Electrode = 'all'
        
        if not self.Timespan:
            self.Timespan = 'all'
        
    @staticmethod
    def ParseWellOrElectrodeArgument(argument, type):
        DELIMITER = ','
        parseOutput = []
        
            
        if isinstance(argument, LoadArgs) and not (LoadArgs.wellVal or LoadArgs.electrodeVal):
            raise ValueError('Internal error: Invalid argument type for parsing')
        
        if str(argument).lower() == 'all':
            parseOutput = 'all'
        elif type == LoadArgs.electrodeVal and _isscalar(argument) and argument == -1:
            parseOutput = 'none'
        elif type == LoadArgs.electrodeVal and _isscalar(argument) and argument > 10:
            parseOutput = [int(argument // 10), int(argument % 10)]
        elif isinstance(argument, str):
            if type == LoadArgs.electrodeVal and (argument.strip() == '-1' or argument.lower() == 'none'):
                parseOutput = 'none'
                return parseOutput
            
            fCanonicalArg = argument.upper().replace(' ', '')
            
            while fCanonicalArg:
                if  len(fCanonicalArg) >= 2 \
                    and \
                    (
                        type == LoadArgs.wellVal        and 
                        fCanonicalArg[0].isalpha()      and 
                        fCanonicalArg[1].isdigit()
                    ) \
                    or \
                    (
                        type == LoadArgs.electrodeVal   and 
                        fCanonicalArg[0].isdigit()      and 
                        fCanonicalArg[1].isdigit()     
                    ):
                    t = fCanonicalArg.split(',', 1)
                    if len(t) > 1:
                        next_well = t[0]
                        fCanonicalArg = t[1]
                    else:
                        next_well = t[0]
                        fCanonicalArg = None
                    next_well = next_well.strip()
                    if type == LoadArgs.wellVal:
                        # while matlab's char() converts to a char type, performing
                        # arithmetic on chars, converts them to utf-8 codes
                        # which is also what python's ord() does
                        parseOutput.append([int(next_well[1:]), ord(next_well[0]) - ord('A') + 1])
                    else:
                        parseOutput.append([int(next_well[0]), int(next_well[1:])])
                else:
                    parseOutput = []
                    break
        return parseOutput
    
    @staticmethod
    def ParseExpansionArguments(loadArgsParent, expansionCommands):
        for supportedModifier in LoadArgs.supportedModifiers:
            supportedMod = [str(x).casefold() == supportedModifier.casefold() for x in expansionCommands]
            
            if any(supportedMod):
                # python workaround for boolean indexing of list 
                setattr(loadArgsParent, supportedModifier, [c for c,t in zip(expansionCommands, supportedMod) if t])
    
    @staticmethod
    def ParseTimespanArgument(argument):
        if isinstance(argument, (list, tuple)) and len(argument) == 2 and _isscalar(argument[0]) and _isscalar(argument[1]):
            return argument
        return []
    
    # isdigit_ax was replaced by builtin method str.isdigit()