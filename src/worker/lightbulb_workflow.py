from restate import Workflow, WorkflowContext
from restate.exceptions import TerminalError

from . import lightbulb_service
from .models import LightbulbDataIo, LightbulbIdInput


installation_workflow = Workflow("InstallationWorkflow")


@installation_workflow.main()
async def run(ctx: WorkflowContext, req: LightbulbDataIo):
    # Install bulb
    await ctx.service_call(lightbulb_service.install_lightbulb, arg=req)
    ctx.set("installation_status", "installed")

    # Get bulb status
    status_result = await ctx.service_call(lightbulb_service.get_lightbulb, arg=LightbulbIdInput(id=req.id))
    ctx.set("installation_status", "status_fetched")

    # Toggle bulb
    toggle_result = await ctx.service_call(lightbulb_service.toggle_lightbulb, arg=LightbulbIdInput(id=req.id))
    ctx.set("installation_status", "toggled")

    # Ensure the toggle operation changed the status
    if status_result.data["status"] == toggle_result.data["status"]:
        await ctx.service_call(lightbulb_service.uninstall_lightbulb, arg=LightbulbIdInput(id=req.id))
        raise TerminalError("Toggle operation did not change the lightbulb status as expected. Try installing.")
    
    # Toggle back to original state
    await ctx.service_call(lightbulb_service.toggle_lightbulb, arg=LightbulbIdInput(id=req.id))
    ctx.set("installation_status", "completed")
