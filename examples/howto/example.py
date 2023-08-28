from dirtpy import ecs as world
from dirtpy.ecs import Entity, EntityComponent, EntityInstance, EntitySystem
import os

#A serializable component for holding basic data types and classes that inherits from pydantics BaseModel
class Transform(EntityComponent): 
    x: float
    y: float

class Velocity(EntityComponent):
    x: float
    y: float

class Sprite(EntityComponent):
    color: str
    layer: int

#A system that must implement the @abstractmethod def update(self, entity: Entity, instances: list[EntityInstance], delta_time: float):
class MovementSystem(EntitySystem):
    def update(self, entity_instances: dict[Entity, list[EntityInstance]], delta_time: float):
        for entity, instances in entity_instances.items():
            for instance in instances:
                trans = instance.get_component(Transform)
                vel = instance.get_component(Velocity)
                trans.x += vel.x
                trans.y += vel.y

class RenderSystem(EntitySystem):
    def __init__(self, *component_types: type[EntityComponent]):
        self.render_layers: dict[int, list[str]] = None
        super().__init__(*component_types)

    def update(self, entity_instances: dict[Entity, list[EntityInstance]], delta_time: float):
        print('render')
        for layer, entity_names in self.render_layers.items():
            print(f'Entities in layer {layer}')
            for entity_name in entity_names:
                entity = world.entity_dict[entity_name]
                sprite: Sprite = entity.get_global_component(Sprite)
                for instance in entity_instances[entity]:
                    trans: Transform = instance.get_component(Transform)
                    print(f'{sprite.color} {entity_name} @ {trans}')

    def on_enable(self, entity_names: list[str]):         
        if self.render_layers is None:
            self.render_layers = {}
            for entity_name in entity_names:
                entity: Entity = world.entity_dict[entity_name]
                sprite: Sprite = entity.get_global_component(Sprite)
                if sprite.layer not in self.render_layers:
                    self.render_layers[sprite.layer] = []
                self.render_layers[sprite.layer].append(entity_name)
        
class ExampleSystem(EntitySystem):
    def update(self, entity_instances: dict[Entity, list[EntityInstance]], delta_time: float):
        print('Tick')

#Register in the following order Components -> Entities -> Systems
#Register Components with Default Values
world.register_component(Transform(x=0, y=0))
world.register_component(Velocity(x=0, y=0))
world.register_component(Sprite(color='white', layer=4))

#Register Entities with required Component types for instancing
world.register_entity(Entity('player', Transform, Velocity, global_components=[Sprite(color='blue', layer=2)], on_despawn=lambda entity, instance: print('Despawned', entity.name, instance)))

#Register Entities with on_enable, on_disable, on_spawn, or on_despawn function
def bullet_on_enable(entity: Entity, instance: EntityInstance):
    print('Enabled', entity.name, instance)

world.register_entity(Entity('bullet', Transform, Velocity, global_components=[Sprite(color='red', layer=4)], on_enable=bullet_on_enable, on_spawn=lambda entity, instance: print('Enabled', entity.name, instance)))

#Register Systems with required Component types
world.register_system(MovementSystem(Transform, Velocity))
world.register_system(RenderSystem(Transform, Sprite))
world.register_system(ExampleSystem(Transform), tickrate=1, priority=0) #System Updates Once Every Second

#Must be called after registering to associate entities with systems based off of their required components
world.pool()

#Creates an instance of an entity which is added to the ecs for processing in systems
player: EntityInstance = world.spawn('player') #ecs.spawn takes the name of the entity to create and return an EntityInstance for modification
trans: Transform = player.get_component(Transform) #Use typing to easily access attributes with code autocompletion
trans.x = 100
trans.y = 200

#Name an instance to reference it in the world by name
world.name_instance('my_player', player.id)

#Tag an instance to add it to a collention referenced by tag
world.tag_instance('special', player.id)

#Default value 20, can be set to determine the number of despawned EntityInstances that can be cached for spawning before deletion
#Saves time by avoiding creating new entities and components at the cost of ram
world.recycle_cap = 40

world.update()#No time passed

#Save all spawned instances into .json
save_file_path = str(os.path.dirname(os.path.abspath(__file__))) + '\\instances.json'
world.save(save_file_path)
print('Saved')

#Recycles or Deletes the entity instance
world.despawn(player.id)
world.update()#No time passed

world.load(save_file_path)
print('Loaded')
world.update(1)#1 Second Passed