import asyncio

from textual.widgets import DataTable, Markdown, Select, Static

from tui import NetArchTUI


def test_tui_smoke():
    async def run():
        app = NetArchTUI()
        async with app.run_test(size=(140, 40)) as pilot:
            await pilot.pause()
            status = str(app.query_one("#status", Static).render())
            assert "verify PASS" in status
            assert app.query_one("#ipplan", DataTable).row_count > 0
            assert app.query_one("#bom", DataTable).row_count > 0
            # switch preset and re-run
            app.query_one("#preset", Select).value = "metro_man"
            await pilot.click("#run")
            await pilot.pause()
            assert "OSPF multi-area" in str(app.query_one("#status", Static).render())
            # what-if on a WAN link
            app.query_one("#element", Select).value = "link:HQ-R1:TenGigabitEthernet0/0/1--BRANCH-R1:TenGigabitEthernet0/0/2"
            app.run_failure()
            await pilot.pause()
            md = app.query_one("#whatif", Markdown)
            assert md is not None
            assert app.result.routing.protocol == "OSPF multi-area"

    asyncio.run(run())
