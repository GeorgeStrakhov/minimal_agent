import asyncio
from smartpup import Pup

async def main():
    pup = Pup(
        instructions="you are a zen master. whatever the user says or asks - just respond with a koan.",
    )

    response = await pup.run("What is your name?")
    print(response)

if __name__ == "__main__":
    asyncio.run(main())

