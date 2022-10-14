from dirtpy import Entity, EntityInstance, EntityComponent, EntitySystem
import dirtpy as world

class Transform(EntityComponent):    
    x:float
    y:float

class Velocity(EntityComponent):
    x:float
    y:float

class Sprite(EntityComponent):
    sprite:str

class MovementSystem(EntitySystem):
    def update(self, entity:Entity, instances:list[EntityInstance], delta_time:float):
        for instance in instances:
            trans = instance.get_component(Transform)
            vel = instance.get_component(Velocity)
            trans.x += vel.x*delta_time
            trans.y += vel.y*delta_time
            print(instance)
class RenderSystem(EntitySystem):
    def update(self, entity: Entity, instances: list[EntityInstance], delta_time: float):
        sprite:Sprite = entity.get_global_component(Sprite)
        for instance in instances:
            trans:Transform = instance.get_component(Transform)

world.register_component(Transform(x=0,y=0))
world.register_component(Velocity(x=0,y=0))
world.register_component(Sprite(sprite='default'))

world.register_entity(Entity('player', Transform, Velocity, global_components=[Sprite(sprite='player_sprite')]))

world.register_system(RenderSystem(Transform, Sprite))
world.register_system(MovementSystem(Transform, Velocity))

world.pool()
world.load('instances.json')