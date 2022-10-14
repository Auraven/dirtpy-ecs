from abc import abstractmethod
from pydantic import BaseModel
import json

#Classes
class EntityComponent(BaseModel):
    def reset(self):
        self.copy(component_dict[type(self)])        

    def copy(self, other: 'EntityComponent'):
        for key, value in other.__dict__.items():
            self.__setattr__(key, value)

    def clone(self) -> 'EntityComponent':        
        return self.__class__(**self.__dict__)

class Entity():
    def __init__(self, name: str, *component_types:type[EntityComponent], global_components: list[EntityComponent] = None):
        self.name: str = name
        self.component_types: list[type[EntityComponent]] = component_types
        self.global_component_dict: dict[type[EntityComponent], EntityComponent] = {}
        if global_components is None:
            global_components = []
        for component in global_components:
            self.global_component_dict[type(component)] = component

    def get_global_component(self, component_type: type[EntityComponent]) -> EntityComponent:
        if component_type in self.global_component_dict:
            return self.global_component_dict[component_type]
        return None    

class EntityInstance(BaseModel):
    id: int
    entity_name: str
    components: dict[str, EntityComponent]
    name: str
    tags: list[str]

    def get_component(self, component_type: type[EntityComponent]) -> EntityComponent:
        if str(component_type) in self.components:
            return self.components[str(component_type)]
        return None

    def reset(self):
        for component in self.components.values():
            component.reset()    

class EntitySystem():
    def __init__(self, *component_types: type[EntityComponent]):
        self.component_types: list[type[EntityComponent]] = component_types
        self.entity_names: list[str] = []

    @abstractmethod
    def update(self, entity: Entity, instances: list[EntityInstance], delta_time: float):
        pass

#ECS
entity_dict: dict[str, Entity] = {}
instance_dict: dict[int, EntityInstance] = {}
recycle_dict: dict[str, list[EntityInstance]] = {}
named_instances: dict[str, int] = {}
tagged_instances: dict[str, list[int]] = {}
component_dict: dict[str, EntityComponent] = {}
system_dict: dict[float, dict[int, list[EntitySystem]]] = {} #[tickrate, dict[priority, system]]
tick_counters: dict[float, float] = {} #tickrate, time_passed
next_id: int = 0
recycle_cap: int = 20

def update(delta_time: float):
    for tickrate in tick_counters.keys():
        tick_counters[tickrate] += delta_time
        if tick_counters[tickrate] >= tickrate:
            tick_counters[tickrate] = 0.0
            for priority_list in system_dict[tickrate].values():
                for system in priority_list:
                    for entity_name in system.entity_names:
                        instances = []
                        for instance_id in tagged_instances[entity_name]:
                            instances.append(instance_dict[instance_id])
                        system.update(entity_dict[entity_name], instances, delta_time)    

def pool():
    for priority_dict in system_dict.values():
        for system_list in priority_dict.values():
            for system in system_list:
                for entity_name, entity in entity_dict.items():
                    valid = True
                    for system_component_type in system.component_types:
                        if system_component_type not in entity.component_types and system_component_type not in entity.global_component_dict.keys():
                            valid = False
                            break            
                    if valid:                
                        system.entity_names.append(entity_name)        

def save(file_name: str):
    with open(file_name, 'w') as save_file:
        instance_json = []
        for instance in instance_dict.values():
            instance_json.append(instance.dict())
        json.dump(instance_json, save_file, indent=4)

def load(file_name: str):
    with open(file_name, 'r') as save_file:
        save_json = json.load(save_file)
        for instance_json in save_json:
            #Extract Components and Build Separate
            instance_components = {}
            components_json = instance_json['components']
            for component_name, component_json in components_json.items():
                instance_component = type(component_dict[component_name])(**component_json)
                instance_components[str(type(instance_component))] = instance_component

            instance_json['components'] = {}
            instance = EntityInstance(**instance_json)
            instance.components = instance_components #Add back Extracted and Built Components
            instance_dict[instance.id] = instance
            if instance.name is not None and instance.name != '':
                named_instances[instance.name] = instance.id
            for tag in instance.tags:
                tagged_instances[tag].append(instance.id)
        

def register_entity(entity: Entity):
    entity_dict[entity.name] = entity
    recycle_dict[entity.name] = []
    tagged_instances[entity.name] = []
def spawn(entity_name: str) -> EntityInstance:
    entity: Entity = entity_dict[entity_name]    
    instance: EntityInstance = None

    if recycle_dict[entity_name]: #Check if Recycled Instance Exists
        instance = recycle_dict[entity_name].pop()
        instance.reset()        
    else: #Create New
        global next_id
        id: int = next_id
        next_id += 1
        components: dict[str, EntityComponent] = {}

        for component_type in entity.component_types:
            component = component_dict[str(component_type)].clone()
            components[str(type(component))] = component
        instance = EntityInstance(id=id, entity_name=entity_name, components=components, name='', tags=[])

    #Add Instance To Dict and Tag
    instance_dict[instance.id] = instance
    tagged_instances[instance.entity_name].append(instance.id)
    instance.tags.append(instance.entity_name)
    return instance
def despawn(id: int):
    global recycle_cap
    instance: EntityInstance = instance_dict.pop(id)
    #Untag, Unname
    if instance.name in named_instances:
        named_instances.pop(instance.name)
    for tag in instance.tags:
        tagged_instances[tag].remove(instance.id)
    if len(recycle_dict[instance.entity_name]) < recycle_cap: #Check Recycle
        recycle_dict[instance.entity_name].append(instance)
    else: #Delete
        del instance

def tag_instance(tag: str, id: int):
    tagged_instances[tag].append(id)
    instance_dict[id].tags.append(tag)
def untag_instance(tag: str, id: int):
    tagged_instances[tag].remove(id)
    instance_dict[id].tags.remove(tag)
def name_instance(name: str, id: int):
    named_instances[name] = id
    instance_dict[id].name = name
def unname_instance(name: str):
    named_instances.pop(name)
    instance_dict[id].name = ''

def register_component(component: EntityComponent):
    component_dict[str(type(component))] = component

def register_system(system: EntitySystem, tickrate: float=0.0, priority: int=4):
    if tickrate not in system_dict:
        system_dict[tickrate] = {
            0:[],
            1:[],
            2:[],
            3:[],
            4:[],
            5:[],
            6:[],
            7:[],
            8:[]           
        }
        tick_counters[tickrate] = 0.0
    system_dict[tickrate][priority].append(system)