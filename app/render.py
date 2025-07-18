import asyncio
from q2report import Q2Report
from io import BytesIO


async def render_report(report: str, data: dict, fmt: str, update_progress):
    rep = Q2Report()
    rep.load(report)
    await update_progress("Parsing report...")
    # await asyncio.sleep(1)

    for k, v in data.get("params", {}).items():
        rep.params[k] = v
    await update_progress("Loading data...")
    # await asyncio.sleep(1)

    await update_progress(f"Rendering {fmt.upper()}...")
    # await asyncio.sleep(2)
    result_file = BytesIO()
    rep.run(result_file, data=data, output_type=fmt)

    await update_progress("Finalizing...")
    # await asyncio.sleep(1)

    return result_file.getvalue()
