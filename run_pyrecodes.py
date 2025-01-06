from pyrecodes import ComponentLibraryCreator
from pyrecodes import SystemCreator
from pyrecodes import System
from pyrecodes import main
import json, os, shapely
import geopandas as gpd
import numpy as np
from pyrecodes.SystemCreator import ConcreteSystemCreator
from pyrecodes import Component

rec_config = json.load("/Users/jinyanzhao/Desktop/SimCenterBuild/pyrecodes/Example 5/tmp.SimCenter/input_data/REC_config.json")

def main(rec_config, inputRWHALE):
    # Form the component library dict using the input dictionary.
    component_library_creator = ComponentLibraryCreator.\
        JSONComponentLibraryCreator(rec_config['ComponentLibrary']) 
    # Change this creator to have a hierarchical component_library     
    component_library = component_library_creator.form_library()

    # Read the system configuration file.
    system_configuration = defineLocality(rec_config)
    
    # Instantiate a BuiltEnvironmentSystem with the necessary arguments.
    system_creator = SystemCreator.R2DSystemCreator()
    
    # Instantiate a BuiltEnvironmentSystem with the necessary arguments.
    system = System.BuiltEnvironmentSystem(system_configuration,\
                                           component_library, system_creator)
    
    realizations_to_run = select_realizations_to_run(\
        system_configuration['DamageInput'],inputRWHALE)
    
    for realization_ind in realizations_to_run:
        system.create_system_from_realization(realization_ind)
        system.start_resilience_assessment()
        system.calculate_resilience()
        system.export_results()

def select_realizations_to_run(damage_input, inputRWHALE):
    rlzs_num = min([item['ApplicationData']['Realizations'] \
                       for _, item in inputRWHALE['Applications']['DL'].items()])
    rlzs_available = np.array(range(rlzs_num))
    if damage_input['Type'] == 'R2DDamageRealization':
        rlz_filter = damage_input['Parameters']['Filter']
        rlzs_requested = []
        for rlzs in rlz_filter.split(','):
            if "-" in rlzs:
                rlzs_low, rlzs_high = rlzs.split("-")
                rlzs_requested += list(range(int(rlzs_low), int(rlzs_high)+1))
            else:
                rlzs_requested.append(int(rlzs))
        rlzs_requested = np.array(rlzs_requested)
        rlzs_in_available = np.in1d(rlzs_requested, rlzs_available)
        if rlzs_in_available.sum() != 0:
            rlzs_to_run = rlzs_requested[
                np.where(rlzs_in_available)[0]]
        else:
            rlzs_to_run = []
    if damage_input['Type'] == 'R2DDamageSample':
        sample_size = damage_input['Parameters']['SampleSize']
        seed = damage_input['Parameters']['SampleSize']
        if sample_size < rlzs_num:
            np.random.seed(seed)
            rlzs_to_run = np.random(rlzs_available, sample_size,\
                                    replace = False).tolist()
        else:
            rlzs_to_run = rlzs_available.tolist()
    return rlzs_to_run



def defineLocality(config_dict: dict) -> dict:
    """Add locality definition in the config_dict.

    Args:
        config_dict (dict): The input dictionary containing System configuration.

    Returns:
        config_dict: The augmented config_dict.
    """
    LocalityBoundaryFile = config_dict.get("LocalityBoundaryFile", None)
    if LocalityBoundaryFile is not None:
        config_dict.pop("LocalityBoundaryFile")
    ComponentsFolder = config_dict.get("ComponentsFolder", None)
    if ComponentsFolder is not None:
        config_dict.pop("ComponentsFolder")
    # components_det_file = os.path.join(ComponentsFolder, 'Results_det.json')
    # with open(components_det_file, 'r') as f:
    #     components_det = json.load(f)
    # infra_types = list(components_det.keys())
    RecoveryResourceSuppliers = config_dict.get("RecoveryResourceSuppliers", None)
    if RecoveryResourceSuppliers is not None:
        config_dict.pop("RecoveryResourceSuppliers")
    LocalityBoundary = gpd.read_file(LocalityBoundaryFile)
    Content = dict()
    for row_ind in LocalityBoundary.index:
        locality_i = dict()
        components = dict()
        geom_i = LocalityBoundary.loc[row_ind, "geometry"]
        loc_id = str(row_ind)
        components.update({"Geometry": geom_i.wkt})
        suppliers = []
        for key in list(RecoveryResourceSuppliers.keys()):
            item = RecoveryResourceSuppliers[key]
            itemCoord = shapely.geometry.Point(item['Longitude'], item['Latitude'])
            if geom_i.contains(itemCoord):
                suppliers.append(key)
                RecoveryResourceSuppliers.pop(key)
        components.update({"RecoveryResourceSuppliers":suppliers})
        components_in_locality, components_det = group_components_to_locality(\
            geom_i, components_det)            
        components.update({"Components":components_in_locality})
        components.update({'ComponentsInfoFolder':ComponentsFolder})
        if "AreaPerPerson" in LocalityBoundary.columns:
            components.update({"AreaPerPerson":LocalityBoundary.loc[\
                row_ind,"AreaPerPerson"]})
        else:
            components.update({"AreaPerPerson":config_dict['Constants'][\
                "DefaultAreaPerPerson"]})
        locality_i.update({"ComponentsInLocality":components})
        Content.update({loc_id: locality_i})


def group_components_to_locality(locality_geom, component_det):
    components_in_locality = {}
    asset_types = list(component_det.keys())
    for asset_type in asset_types:
        asset_subtypes = list(component_det[asset_type].keys())
        asset_type_in_locality = dict()
        for asset_subtype in asset_subtypes:
            asset_subtype_in_locality = []
            asset_ids = list(component_det[asset_type][asset_subtype].keys())
            for asset_id in asset_ids:
                asset = component_det[asset_type][asset_subtype][asset_id]
                asset_lat = asset['GeneralInformation']['location']['latitude']
                asset_lon = asset['GeneralInformation']['location']['longitude']
                asset_loc = shapely.geometry.Point(asset_lon, asset_lat)
                if locality_geom.contains(asset_loc):
                    asset_subtype_in_locality.append(asset_id)
                    component_det[asset_type][asset_subtype].pop(asset_id)
            asset_type_in_locality.update({asset_subtype:asset_subtype_in_locality})
        components_in_locality.update({asset_type:asset_type_in_locality})
    return components_in_locality, component_det




class R2DSystemCreator(ConcreteSystemCreator):
# class R2DJsonSystemCreator(ConcreteSystemCreator):
    """
    Create a System based on latest SimCenter R2D Tool's output files for multiple
    infrastructure.
    """
    def __init__(self) -> None:
        super().__init__()
        self.building_area_per_person = {}
        self.scenario_id = None
        self.component_parameters_setter = None
    def setup(self, component_library: dict, system_configuration: dict,\
              realization_to_run: int) -> None:
        super().setup(component_library, system_configuration)
        self.set_building_area_per_person()
        self.scenario_id = realization_to_run
        self.set_component_parameters_setter() 

    def create_components_in_localities(self, locality: str, content: dict) -> list([Component.Component]):
        self.components += self.create_recovery_resource_suppliers(locality, content)
        self.components += self.create_general_components(locality, content)

    def create_recovery_resource_suppliers(self, locality: str, content: dict) -> list([Component.Component]):
        suppliers = []
        for component_name in content.get('RecoveryResourceSuppliers', []):
            component = copy.deepcopy(self.component_library[component_name])
            component.set_locality([self.format_locality_id(locality)])
            suppliers.append(component)
        return suppliers

    def create_general_components(self, locality: str, content: dict) -> list([Component.Component]):
        ComponentsFolder = content['ComponentsInfoFolder']
        if content.get('MaxNumComponents', None):
            max_num_components = content['MaxNumComponents']
        else:
            max_num_components = float('inf')
        num_components = 0
        components = []
        components_det_file = os.path.join(ComponentsFolder, 'Results_det.json')
        with open(components_det_file, 'r') as f:
            components_det = json.load(f)
        components_rlz_file = os.path.join(ComponentsFolder,\
                             f'Results_{int(self.scenario_id)}.json')
        with open(components_rlz_file, 'r') as f:
            components_rlz = json.load(f)
        for asset_typeKey, asset_typeItem in content['Components'].items():
            for asset_subTypeKey, asset_subTypeItem in asset_typeItem.items():
                for asset_id in asset_subTypeItem:
                    component_det_data = components_det[asset_typeKey]\
                        [asset_subTypeKey][asset_id]
                    component_rlz_data = components_rlz[asset_typeKey]\
                        [asset_subTypeKey][asset_id]
                    components.append(self.create_single_general_component(\
                        asset_typeKey, asset_subTypeKey,
                        component_det_data, component_rlz_data))
                    num_components += 1
                    if num_components >= max_num_components:
                        return components
        return components

    def create_single_general_component(self, asset_type, asset_subtype,\
                                        det_data, rlz_data):
        all_DS = []
        for DS_group, DS in rlz_data['Damage'].items():
            all_DS.append(DS)
        component_DS = max(all_DS)
        if asset_type == 'Buildings':
            return self.create_building_component(det_data, rlz_data)
        elif asset_type == ''
