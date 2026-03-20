import KratosMultiphysics as KM
from KratosMultiphysics.CoSimulationApplication.co_simulation_analysis import CoSimulationAnalysis
import KratosMultiphysics.IgaApplication

"""
For user-scripting it is intended that a new class is derived
from CoSimulationAnalysis to do modifications
Check also "kratos/python_scripts/analysis-stage.py" for available methods that can be overridden
"""

class CustomCoSimulationAnalysis(CoSimulationAnalysis):
    def __init__(self, parameters):
        """Call the base class constructor."""
        super().__init__(parameters)

if __name__ == "__main__":

    with open("ProjectParametersCoSim.json",'r') as parameter_file:
        parameters = KM.Parameters(parameter_file.read())

    simulation = CustomCoSimulationAnalysis(parameters)
    simulation.Run()
