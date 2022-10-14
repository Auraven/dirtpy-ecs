from dirtpy import ecs as world
from dirtpy.ecs import Entity, EntityComponent, EntityInstance, EntitySystem

#A serializable component for holding basic data types and classes that inherit from pydantics BaseModel
class Transform(EntityComponent): 
    x: float
    y: float

class Velocity(EntityComponent):
    x: float
    y: float

class Sprite(EntityComponent):
    color:str
    layer: int

#A system that must implement the @abstractmethod def update(self, entity: Entity, instances: list[EntityInstance], delta_time: float):
class MovementSystem(EntitySystem):
    def update(self, entity: Entity, instances: list[EntityInstance], delta_time: float):
        for instance in instances:
            trans = instance.get_component(Transform)
            vel = instance.get_component(Velocity)
            trans.x += vel.x
            trans.y += vel.y
            print(instance)

class RenderSystem(EntitySystem):
    def update(self, entity: Entity, instances: list[EntityInstance], delta_time: float):
        sprite: Sprite = entity.get_global_component(Sprite)
   
    def on_enable(self):
        if self.render_layers is None:
            self.render_layers:dict[int, list[str]] = {}

            for entity_name in self.entity_names:
                entity: Entity = world.entity_dict[entity_name]
                sprite: Sprite = entity.get_global_component(Sprite)
                if sprite.layer not in self.render_layers:
                    self.render_layers[sprite.layer] = []
                self.render_layers[sprite.layer].append(entity_name)

#Register in the following order Components -> Entities -> Systems
#Register Components with Default Values
world.register_component(Transform(x=0, y=0))
world.register_component(Velocity(x=0, y=0))

#Register Entities with required Component types for instancing
world.register_entity(Entity('player', Transform, Velocity))

#Register Systems with required Component types
world.register_system(MovementSystem(Transform, Velocity))

#Must be called after registering to associate entities with systems based off of their required components
world.pool()

#Creates or an instance of an entity which is added to the ecs for processing in systems
player: EntityInstance = world.spawn('player') #ecs.spawn takes the name of the entity to create and returns an EntityInstance for modification
trans: Transform = player.get_component(Transform) #Use typing to easily access attributes with code autocompletion
trans.x = 100
trans.y = 200

#Name and instance to reference it in the world by name
world.name_instance('my_player', player.id)

#Tag and instance to add it to a collention referenced by tag
world.tag_instance('special', player.id)

#Default value 20, can be set to determine the number of despawned EntityInstances that can cached for spawning before deletion
world.recycle_cap = 40
#Recycles or Deletes the entity instance
world.despawn(player.id)
world.update(1)