import logging
import os
import tempfile
import shutil
from zipfile import ZipFile

from .base import Reader
from .helper.asc_helper import AscHelper

logger = logging.getLogger(__name__)


class AscZipReader(Reader):
    identifier = 'asc_zip_reader'
    priority = 10
    filedata = {}
    # two or more chars in row


    def check(self):
        result = False

        if self.file.suffix.lower() == '.zip' and self.file.mime_type == 'application/zip':
            with ZipFile(self.file.fp, 'r') as zipObj:
                listOfFileNames = zipObj.namelist()
                if any([fileName.lower().endswith('.asc') for fileName in listOfFileNames]):
                    zipdir = os.path.join(tempfile.TemporaryDirectory().name, self.file.name)
                    os.makedirs(zipdir)
                    result = True
                    # Iterate over the file names
                    for fileName in listOfFileNames:
                        # Check filename endswith csv
                        if fileName.lower().endswith('.asc'):
                            # Extract a single file from zip
                            pathFileName = zipObj.extract(fileName, zipdir)
                            with open(pathFileName, mode="r", encoding="latin_1") as f:
                                self.filedata[fileName] = f.readlines()
                    shutil.rmtree(zipdir)
        return result





    ###############################################################################
    # formatResultsElab
    ###############################################################################
    def formatResultsChemotion(self, results):
        """
        Formats results (list of dictionaries) generated by the ALV parser for DLS
        data to fit metadata for eLabFTW.
        Renames metadata, ensures formats are correct.
        """
        metadata = {}
        data = {}

        # sample ID = Samplename
        metadata["Samplename"] = results[0]["Samplename"]
        # DLS device = Device Info --> options
        metadata["Device Info"] = results[0]["Device Info"].split("/")[0]
        # TODO does this make sense?
        # TODO sample description = sample memo? free-fill in elab?
        # if results[0]['SampleMemo']:

        # solvent = nothing, needs to be filled in manually for dls (?)
        # sample volume [ml] = nothing, needs to be filled in manually for dls (?)
        metadata["wavelength [nm]"] = str(results[0]["Wavelength [nm]"])
        # measurement starting time --> earlierst "Date" in all the dates (don't hard code)
        timeObj = AscHelper.getStartdate(results)
        metadata["measurement starting time"]= str(timeObj['startdate_object'])

        data["duration [s]"] = timeObj['time_line']

        # relative time point [s] --> TODO ?
        # refractive index --> refractive index from LIST
        data["refractive index"] = AscHelper.listValues("Refractive Index", results)

        # temperature [K] --> Temperature [K] from LIST
        data["temperature [K]"] = AscHelper.listValues("Temperature [K]", results)

        # viscosity [mPas] --> Viscosity [cp] from LIST
        data["viscosity [mPas]"] = AscHelper.listValues("Viscosity [cp]", results)

        # detection angle [°] --> Angle [°] from LIST TODO decide on unit
        data["detection angle [degrees]"] = AscHelper.listValues("Angle [°]", results)


        # average diffusion coefficient [micron^2/s] --> Diffusion Coefficient 2. order fit [µm²/s] from LIST
        data["average diffusion coefficient [micron^2/s]"] = AscHelper.listValues("Diffusion Coefficient 2. order fit [µm²/s]", results)

        # second cumulant (expansion parameter) --> Expansion Parameter µ2 from LIST
        data["second cumulant (expansion parameter)"] = AscHelper.listValues("Expansion Parameter µ2", results)

        # hydrodynamic radius [nm] --> Hydrodynamic Radius 2. order fit [nm]
        data["hydrodynamic radius [nm]"] = AscHelper.listValues("Hydrodynamic Radius 2. order fit [nm]", results)

        # average diffusion coefficient [micron^2/s] --> Diffusion Coefficient 2. order fit [µm²/s] from LIST
        data["average diffusion coefficient [micron^2/s]"] = AscHelper.listValues("Diffusion Coefficient 2. order fit [µm²/s]", results)

        # second cumulant (expansion parameter) --> Expansion Parameter µ2 from LIST
        data["second cumulant (expansion parameter)"] = AscHelper.listValues("Expansion Parameter µ2", results)

        # hydrodynamic radius [nm] --> Hydrodynamic Radius 2. order fit [nm]
        data["hydrodynamic radius [nm]"] = AscHelper.listValues("Hydrodynamic Radius 2. order fit [nm]", results)

        for (key, val) in data.items():
            metadata[key] = AscHelper.strVals(val)



        # duration [s] = Duration [s]
        metadata["duration [s]"] = str(results[0]["Duration [s]"])



        # first correlation delay [ms] TODO ?

        return {
            'data': data,
            'metadata': metadata
        }


    def get_tables(self):
        tables = []
        table = self.append_table(tables)
        all_results = []  # will contain a dict for each file parsed
        helper = AscHelper()
        for (fileName, fileContent) in self.filedata.items():
            results = helper.parsefileALV(fileName, fileContent)
            all_results.append(results)

        all_results.sort(key=lambda x: x["Datetime"])
        formatedResults = self.formatResultsChemotion(all_results)
        table['metadata'] = formatedResults['metadata']
        col_names = list(formatedResults['data'].keys())
        table['columns'] = [{
            'key': str(idx),
            'name': '{}'.format(value)
        } for idx, value in enumerate(col_names)]
        for idx in range(len(formatedResults['data'][col_names[0]])):
            table['rows'].append([formatedResults['data'][name][idx] for name in col_names])
        table['metadata']['rows'] = str(len(table['rows']))
        table['metadata']['columns'] = str(len(table['columns']))
        return tables
