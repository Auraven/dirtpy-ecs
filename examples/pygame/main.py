from dirtpy import ecs as world
from dirtpy.ecs import Entity, EntityComponent, EntityInstance, EntitySystem

#A serializable component for holding basic data types and classes that inherit from pydantics BaseModel
class Transform(EntityComponent): 
    x: float
    y: float

class Velocity(EntityComponent):
    x: float
    y: float

#A system that must implement the @abstractmethod def update(self, entity: Entity, instances: list[EntityInstance], delta_time: float):
class MovementSystem(EntitySystem):
    def update(self, entity: Entity, instances: list[EntityInstance], delta_time: float):
        for instance in instances:
            trans = instance.get_component(Transform)
            vel = instance.get_component(Velocity)
            trans.x += vel.x
            trans.y += vel.y
            print(instance)

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

#Create an instance of an entity which is added to the ecs for processing in systems
player: EntityInstance = world.spawn('player') #ecs.spawn takes the name of the entity to create and returns an EntityInstance for modification
trans: Transform = player.get_component(Transform) #Use typing to easily access attributes with code autocompletion
trans.x = 100
trans.y = 200

world.update(1)