from abc import abstractmethod
from pydantic import BaseModel
import json

#Classes
class EntityComponent(BaseModel):
    '''Inherits pydantic.BaseModel and can be serialized to/from JSON'''
    def reset(self):
        self.copy(component_dict[type(self)])        

    def copy(self, other: 'EntityComponent'):
        '''copys values of other EntityComponent to self'''
        for key, value in other.__dict__.items():
            self.__setattr__(key, value)

    def clone(self) -> 'EntityComponent':
        '''returns a unique copy of this type'''        
        return type(self)(**self.__dict__)

class Entity():
    '''Blueprint for spawning EntityInstances, optional global_components can be created and accessed for all instances to utilize'''
    def __init__(self, name: str, *component_types:type[EntityComponent], global_components: list[EntityComponent]=None, on_enable=None, on_disable=None, on_spawn=None, on_despawn=None):
        self.name: str = name
        self.component_types: list[type[EntityComponent]] = component_types
        self.global_component_dict: dict[type[EntityComponent], EntityComponent] = {}
        self.on_enable = on_enable
        self.on_disable = on_disable 
        self.on_spawn = on_spawn
        self.on_despawn = on_despawn       
        
        if global_components is None:
            global_components = []
        for component in global_components:
            self.global_component_dict[type(component)] = component

    def get_global_component(self, component_type: type[EntityComponent]) -> EntityComponent:
        '''returns a global EntityComponent shared by all EntityInstances by type'''
        if component_type in self.global_component_dict:
            return self.global_component_dict[component_type]
        return None

    def set_on_enable(self, on_enable):
        self.on_enable = on_enable
    def set_on_disable(self, on_disable):
        self.on_disable = on_disable

class EntityInstance(BaseModel):
    '''Inherits pydantic.BaseModel and can be serialized to/from JSON'''
    id: int
    entity_name: str
    components: dict[str, EntityComponent]
    name: str = ''
    tags: list[str] = []
    enabled: bool = True

    def set_enabled(self, enabled: bool):
        '''Disabled EntityInstances are ignored by Systems'''
        if enabled != self.enabled:
            entity = entity_dict[self.entity_name]
            if enabled and entity.on_enable is not None:
                entity.on_enable(entity, self)
            elif entity.on_disable is not None:
                entity.on_disable(entity, self)
        self.enabled = enabled

    def get_component(self, component_type: type[EntityComponent]) -> EntityComponent:
        '''returns EntityComponent by type'''
        if str(component_type) in self.components:
            return self.components[str(component_type)]
        return None

    def reset(self):
        '''Sets EntityComponent to their default values'''
        for component in self.components.values():
            component.reset()    

class EntitySystem():
    '''must implement abstract update, on_enable, and on_disable'''
    def __init__(self, *component_types: type[EntityComponent], enabled: bool = True):
        '''on_enable and on_disable are optional function that'''
        self.component_types: list[type[EntityComponent]] = component_types
        self.entity_names: list[str] = []
        self.enabled = enabled       

    def set_enabled(self, enabled: bool):
        '''disabled systems are not updated'''
        if enabled != self.enabled:
            if enabled:
                self.on_enable(self.entity_names)
            else:
                self.on_disable(self.entity_names)
        self.enabled = enabled

    @abstractmethod
    def update(self, entity_instances: dict[Entity, list[EntityInstance]], delta_time: float):
        pass
    @abstractmethod 
    def on_enable(self, entity_names: list[str]):
        pass
    @abstractmethod 
    def on_disable(self, entity_names: list[str]):
        pass

#ECS
entity_dict: dict[str, Entity] = {}
instance_dict: dict[int, EntityInstance] = {}
recycle_dict: dict[str, list[EntityInstance]] = {}
named_instances: dict[str, int] = {}
tagged_instances: dict[str, list[int]] = {}
component_dict: dict[str, EntityComponent] = {}
system_alias: dict[type[EntitySystem], EntitySystem] = {}
system_entity_instances: dict[type[EntitySystem], dict[str, list[int]]] = {} #[system_type, [entity_name, list[instance_id]]]
system_tick: dict[float, dict[int, list[type[EntitySystem]]]] = {} #[tickrate, dict[priority, system]]
tick_counters: dict[float, float] = {} #tickrate, time_passed
next_id: int = 0
recycle_cap: int = 20
'''Limits the number of despawned EntityInstances that can be cached for spawn before deletion'''

def update(delta_time: float = 0):
    '''Updates all systems based on tickrate and the amount of time passed'''
    for tickrate in tick_counters.keys():
        tick_counters[tickrate] += delta_time
        if tick_counters[tickrate] >= tickrate:
            tick_counters[tickrate] = 0.0
            for priority_list in system_tick[tickrate].values():
                for system_type in priority_list:
                    system = system_alias[system_type]
                    if system.enabled:
                        entity_instances: dict[Entity, list[EntityInstance]] = {}
                        for entity_name, instance_ids in system_entity_instances[system_type].items():
                            entity = entity_dict[entity_name]
                            entity_instances[entity] = []
                            for instance_id in instance_ids:
                                instance = instance_dict[instance_id]
                                if instance.enabled:                                        
                                    entity_instances[entity].append(instance_dict[instance_id])                                                
                        system.update(entity_instances, delta_time)    

def pool():
    '''Execute right after registering all components, entities, and systems'''
    for system in system_alias.values():
        if type(system) not in system_entity_instances:
            system_entity_instances[type(system)] = {}

        for entity_name, entity in entity_dict.items():
            valid = True
            for system_component_type in system.component_types:
                if system_component_type not in entity.component_types and system_component_type not in entity.global_component_dict.keys():
                    valid = False
                    break            
            if valid:                
                system.entity_names.append(entity_name)
                system_entity_instances[type(system)][entity_name] = []          
        if system.enabled:
            system.on_enable(system.entity_names)
        else:
            system.on_disable(system.entity_names)

def save(file_name: str):
    '''Serializes and writes out as a .json all spawned EntityInstances and their components into a json array'''
    with open(file_name, 'w') as save_file:
        instance_json = []
        for instance in instance_dict.values():
            instance_json.append(instance.dict())
        json.dump(instance_json, save_file, indent=4)

def load(file_name: str):
    '''Opens .json with an array of EntityInstance objects to spawn into ecs'''
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

            for system_type, system in system_alias.items():
                if instance.entity_name in system.entity_names:
                    system_entity_instances[system_type][instance.entity_name].append(instance.id)

            if instance.name is not None and instance.name != '':
                named_instances[instance.name] = instance.id
            for tag in instance.tags:
                tagged_instances[tag].append(instance.id)
        

def register_entity(entity: Entity):
    '''register entites after components and before systems'''
    entity_dict[entity.name] = entity
    recycle_dict[entity.name] = []
    tagged_instances[entity.name] = []

def get_entity(entity_name: str) -> Entity:
    return entity_dict[entity_name]

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
        instance = EntityInstance(id=id, entity_name=entity_name, components=components)

    #Add Instance To Dict and Tag
    instance_dict[instance.id] = instance
    tagged_instances[instance.entity_name].append(instance.id)
    instance.tags.append(instance.entity_name)
    
    for system_type, system in system_alias.items():
        if entity_name in system.entity_names:
            system_entity_instances[system_type][entity_name].append(instance.id)

    #Check for enables
    if entity.on_spawn is not None:
        entity.on_spawn(entity, instance)
    if instance.enabled and entity.on_enable is not None:
        entity.on_enable(entity, instance)
    elif entity.on_disable is not None:
        entity.on_disable(entity, instance)
        
    return instance

def despawn(id: int):   
    global recycle_cap
    instance: EntityInstance = instance_dict.pop(id)
    entity = entity_dict[instance.entity_name]
    if entity.on_despawn is not None:
        entity.on_despawn(entity, instance)

    for system_type, system in system_alias.items():
        if entity.name in system.entity_names:
            system_entity_instances[system_type][entity.name].remove(id)

    #Untag, Unname
    if instance.name in named_instances:
        named_instances.pop(instance.name)
    for tag in instance.tags:
        tagged_instances[tag].remove(instance.id)
    if len(recycle_dict[instance.entity_name]) < recycle_cap: #Check Recycle
        recycle_dict[instance.entity_name].append(instance)
    else: #Delete
        del instance

def get_instance(id: int) -> EntityInstance:
    '''returns EntityInstance by id'''
    if id in instance_dict:
        return instance_dict[id]
    return None

def get_tagged(tag: str) -> list[EntityInstance]:
    '''returns list of EntityInstances by tag'''
    instances = []
    for instance_id in tagged_instances[tag]:
        instances.append(get_instance(instance_id))
    return instances

def tag_instance(tag: str, id: int):
    '''tag an EntityInstance by id to be reference with get_tagged(tag) -> list[EntityInstance]'''
    if tag not in tagged_instances:
        tagged_instances[tag] = []
    tagged_instances[tag].append(id)
    instance_dict[id].tags.append(tag)

def untag_instance(tag: str, id: int):
    if tag not in tagged_instances:
        return
    if id not in tagged_instances[tag]:
        return
    tagged_instances[tag].remove(id)
    instance_dict[id].tags.remove(tag)

def get_named(name: str) -> EntityInstance:
    '''returns EntityInstance by name'''
    if name in named_instances:
        return get_instance(named_instances[name])
    return None
def name_instance(name: str, id: int):
    '''name an EntityInstance by id to be referenced with get_named(name) -> EntityInstance'''
    named_instances[name] = id
    instance_dict[id].name = name
def unname_instance(name: str):
    named_instances.pop(name)
    instance_dict[id].name = ''

def register_component(component: EntityComponent):
    '''register before entities and systems'''
    component_dict[str(type(component))] = component

def get_default_component(component_type: type[EntityComponent]) -> EntityComponent:
    if component_type in component_dict:
        return component_dict[component_type]
    return None

def register_system(system: EntitySystem, tickrate: float=0.0, priority: int=4):
    '''system=The EntitySystem to register, tickrate=How much time in seconds should pass to update the system, priority(0 to 8) which list to add to for execution, lower is earlier. Systems with a tickrate of 0 execute every frame'''
    system_alias[type(system)] = system
    
    if tickrate not in system_tick:
        system_tick[tickrate] = {
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
    system_tick[tickrate][priority].append(type(system))

def get_system(system_type: type[EntitySystem]) -> EntitySystem:
    if system_type in system_alias:
        return system_alias[system_type]
    return None