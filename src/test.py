from ares_call import ARES
import asyncio

company_name = "KOLUMBUS 92, v.o.s."

async def make_call(company_name: str):
    text_result = await ARES.get_base_data(company_name)
    return text_result

result = asyncio.run(make_call(company_name))

print(result)