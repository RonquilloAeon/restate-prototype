import restate
from restate import errors, runtime, Request, KeyedContext
from .models import LightBulb, LightStatus, Location


# State keys
LIGHTBULB_STATE_KEY = "lightbulb"
LOCATION_STATE_KEY = "location"


# Virtual objects
lightbulb_service = restate.service("lightbulb")
location_service = restate.service("location")


@lightbulb_service.keyed
async def register_lightbulb(ctx: KeyedContext, lightbulb: LightBulb) -> LightBulb:
    """Register a new light bulb or update an existing one"""
    # Save lightbulb to state
    await ctx.set(LIGHTBULB_STATE_KEY, lightbulb)
    
    # Update location to include this lightbulb's ID
    try:
        location = await runtime.call(
            location_service.get_location, 
            Request(key=lightbulb.location),
            returns=Location
        )
    except errors.NotFound:
        # Create a new location if it doesn't exist
        location = Location(name=lightbulb.location, light_ids=[lightbulb.id])
    else:
        if lightbulb.id not in location.light_ids:
            location.light_ids.append(lightbulb.id)
    
    await runtime.call(
        location_service.update_location,
        Request(key=lightbulb.location, body=location)
    )
    
    return lightbulb


@lightbulb_service.keyed
async def get_lightbulb(ctx: KeyedContext) -> LightBulb:
    """Get a light bulb by its ID"""
    try:
        return await ctx.get(LIGHTBULB_STATE_KEY, LightBulb)
    except errors.NotFound:
        raise errors.NotFound(f"Light bulb {ctx.key} not found")


@lightbulb_service.keyed
async def toggle_lightbulb(ctx: KeyedContext) -> LightBulb:
    """Toggle a light bulb's status between ON and OFF"""
    try:
        lightbulb = await ctx.get(LIGHTBULB_STATE_KEY, LightBulb)
    except errors.NotFound:
        raise errors.NotFound(f"Light bulb {ctx.key} not found")
    
    # Toggle light status
    if lightbulb.status == LightStatus.ON:
        lightbulb.status = LightStatus.OFF
    else:
        lightbulb.status = LightStatus.ON
    
    # Save updated lightbulb
    await ctx.set(LIGHTBULB_STATE_KEY, lightbulb)
    
    return lightbulb


@location_service.keyed
async def update_location(ctx: KeyedContext, location: Location) -> Location:
    """Update a location's information"""
    await ctx.set(LOCATION_STATE_KEY, location)
    return location


@location_service.keyed
async def get_location(ctx: KeyedContext) -> Location:
    """Get location information by name"""
    try:
        return await ctx.get(LOCATION_STATE_KEY, Location)
    except errors.NotFound:
        raise errors.NotFound(f"Location {ctx.key} not found")


@location_service.keyed
async def get_lights_in_location(ctx: KeyedContext) -> list[LightBulb]:
    """Get all light bulbs in a specific location"""
    try:
        location = await ctx.get(LOCATION_STATE_KEY, Location)
    except errors.NotFound:
        raise errors.NotFound(f"Location {ctx.key} not found")
    
    # Fetch all light bulbs in this location
    lightbulbs = []
    for light_id in location.light_ids:
        try:
            lightbulb = await runtime.call(
                lightbulb_service.get_lightbulb, 
                Request(key=light_id),
                returns=LightBulb
            )
            lightbulbs.append(lightbulb)
        except errors.NotFound:
            # Skip light bulbs that were removed
            continue
    
    return lightbulbs